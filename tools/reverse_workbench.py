"""Offline GRVIS finite evidence-record comparator. No network or target execution."""
import argparse
import datetime as dt
import json
import math
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA = "grvis-reverse/1"
KINDS = {
    "behavioral": {"runtime_observation", "measurement"},
    "static": {"static_analysis", "measurement"},
    "documented": {"documentation", "marketing"},
}
COVERAGE = {"complete", "partial", "unavailable", "not_requested"}
STATUS = {"supported", "inferred", "uncertain", "refuted", "not tested", "blocked"}
MAX_BYTES = 2 * 1024 * 1024
MAX_RECORDS = 500

def real(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False

def equal(a, b):
    if real(a) and real(b):
        return a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b

def tree_check(value, depth=0):
    if depth > 50:
        raise ValueError("maximum nesting exceeded")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite number")
    if isinstance(value, dict):
        for v in value.values():
            tree_check(v, depth + 1)
    elif isinstance(value, list):
        for v in value:
            tree_check(v, depth + 1)

def eligible(source, kind, doc):
    return (source["kind"] in KINDS[kind]
            and source["coverage"] == "complete"
            and source["target_revision"] == doc["target"]["revision"]
            and source["environment_id"] == doc["environment"]["id"])

def validate(doc):
    errors = []
    def issue(path, reason):
        errors.append({"path": path, "reason": reason})
    def fields(obj, required, optional, path):
        if not isinstance(obj, dict):
            issue(path, "object_required")
            return False
        missing = set(required) - obj.keys()
        extra = obj.keys() - set(required) - set(optional)
        if missing or extra:
            issue(path, "field_set_mismatch")
            return False
        return True
    def text(obj, names, path):
        valid = True
        for name in names:
            if not isinstance(obj.get(name), str) or not obj[name].strip():
                issue(path + "." + name, "nonempty_string_required")
                valid = False
        return valid
    try:
        tree_check(doc)
    except ValueError as exc:
        return [{"path": "$", "reason": str(exc)}]
    top = ["schema_version", "target", "environment", "sources", "claims", "unknowns", "obligations"]
    if not fields(doc, top, [], "$"):
        return errors
    if doc["schema_version"] != SCHEMA:
        issue("schema_version", "unsupported_schema")
    if fields(doc["target"], ["id", "revision"], [], "target"):
        text(doc["target"], ["id", "revision"], "target")
    if fields(doc["environment"], ["id"], ["profile"], "environment"):
        text(doc["environment"], ["id"], "environment")
    collections = {}
    for name in ["sources", "claims", "unknowns", "obligations"]:
        records = doc[name]
        if not isinstance(records, list) or len(records) > MAX_RECORDS:
            issue(name, "bounded_array_required")
            continue
        index = {}
        for i, rec in enumerate(records):
            if not isinstance(rec, dict) or not isinstance(rec.get("id"), str) or not rec["id"]:
                issue(name + "[" + str(i) + "]", "record_id_required")
                continue
            if rec["id"] in index:
                issue(name + "." + rec["id"], "duplicate_id")
            index[rec["id"]] = rec
        collections[name] = index
    if errors:
        return errors
    sources = collections["sources"]
    for sid, src in sources.items():
        required = ["id", "kind", "uri", "location", "retrieved_at", "lineage", "coverage", "target_revision", "environment_id"]
        if not fields(src, required, ["sha256"], "sources." + sid):
            continue
        if not text(src, required, "sources." + sid):
            continue
        if src["kind"] not in set().union(*KINDS.values()):
            issue(sid, "unsupported_source_kind")
        if src["coverage"] not in COVERAGE:
            issue(sid, "unsupported_coverage")
        try:
            timestamp = dt.datetime.fromisoformat(src["retrieved_at"].replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                raise ValueError("timezone required")
        except (ValueError, TypeError, AttributeError):
            issue(sid, "timezone_timestamp_required")
        try:
            if urlsplit(src["uri"]).username is not None:
                issue(sid, "credential_uri_forbidden")
        except ValueError:
            issue(sid, "invalid_uri")
        if "sha256" in src and (not isinstance(src["sha256"], str)
                or len(src["sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in src["sha256"])):
            issue(sid, "invalid_digest")
    if errors:
        return errors
    def refs(rec, name, path):
        values = rec[name]
        if not isinstance(values, list) or any(not isinstance(x, str) or x not in sources for x in values):
            issue(path, "dangling_or_invalid_source_reference")
            return []
        if len(set(values)) != len(values):
            issue(path, "duplicate_reference")
        return values
    for cid, claim in collections["claims"].items():
        required = ["id", "text", "kind", "label", "tier", "status", "evidence", "contradictions"]
        if not fields(claim, required, [], "claims." + cid):
            continue
        text(claim, ["text"], cid)
        evidence = refs(claim, "evidence", cid)
        contradictions = refs(claim, "contradictions", cid)
        if any(not isinstance(claim[k], str) for k in ["kind", "label", "tier", "status"]):
            issue(cid, "invalid_claim_enum")
            continue
        if claim["kind"] not in KINDS or claim["label"] not in {"FACT", "INFERENCE", "UNCERTAIN", "SPECULATION"} or claim["tier"] not in {"E1", "E2", "E3", "E4", "E5"} or claim["status"] not in STATUS:
            issue(cid, "invalid_claim_enum")
            continue
        if claim["label"] == "FACT":
            qualifying = [sources[e] for e in evidence if eligible(sources[e], claim["kind"], doc)]
            if claim["status"] != "supported" or claim["tier"] not in {"E1", "E2"} or contradictions or not qualifying:
                issue(cid, "fact_not_supported_in_scope")
            if claim["tier"] == "E2" and len({s["lineage"] for s in qualifying}) < 2:
                issue(cid, "independent_lineages_required")
    for uid, unknown in collections["unknowns"].items():
        required = ["id", "question", "kind", "state", "required", "owner", "resolution_evidence"]
        if not fields(unknown, required, [], "unknowns." + uid):
            continue
        text(unknown, ["question", "owner"], uid)
        evidence = refs(unknown, "resolution_evidence", uid)
        if not isinstance(unknown["kind"], str) or not isinstance(unknown["state"], str):
            issue(uid, "invalid_unknown_enum")
            continue
        if unknown["kind"] not in KINDS or unknown["state"] not in {"open", "resolved"} or type(unknown["required"]) is not bool:
            issue(uid, "invalid_unknown_enum")
            continue
        if unknown["state"] == "resolved" and not any(eligible(sources[e], unknown["kind"], doc) for e in evidence):
            issue(uid, "resolution_requires_qualifying_evidence")
    if not collections["obligations"] or not any(o.get("required") is True for o in collections["obligations"].values()):
        issue("obligations", "at_least_one_required_obligation")
    for oid, obligation in collections["obligations"].items():
        required = ["id", "description", "kind", "required", "source_id", "target_revision", "environment_id", "expected"]
        if not fields(obligation, required, ["observed", "abs_tol"], "obligations." + oid):
            continue
        text(obligation, ["description", "target_revision", "environment_id"], oid)
        if not isinstance(obligation["kind"], str) or obligation["kind"] not in {"behavioral", "static"} or type(obligation["required"]) is not bool:
            issue(oid, "invalid_obligation_enum")
        if not isinstance(obligation["source_id"], str) or obligation["source_id"] not in sources:
            issue(oid, "dangling_source_reference")
        if "abs_tol" in obligation and (not real(obligation["abs_tol"]) or obligation["abs_tol"] < 0 or not real(obligation["expected"]) or ("observed" in obligation and not real(obligation["observed"]))):
            issue(oid, "invalid_numeric_tolerance")
    return errors

def evaluate(doc):
    errors = validate(doc)
    if errors:
        return {"schema_version": SCHEMA, "status": "invalid", "result": "unknown", "issues": errors,
                "provenance_authenticity": "not_verified"}, 3
    sources = {s["id"]: s for s in doc["sources"]}
    results = []
    for o in doc["obligations"]:
        src = sources[o["source_id"]]
        reason = None
        if o["target_revision"] != doc["target"]["revision"] or o["environment_id"] != doc["environment"]["id"]:
            reason = "obligation_context_mismatch"
        elif not eligible(src, o["kind"], doc):
            reason = "source_not_comparable"
        elif "observed" not in o:
            reason = "observation_missing"
        if reason:
            result = "unknown"
        else:
            matches = abs(o["expected"] - o["observed"]) <= o["abs_tol"] if "abs_tol" in o else equal(o["expected"], o["observed"])
            result = "pass" if matches else "fail"
            reason = "declared_value_match" if matches else "declared_value_divergence"
        results.append({"id": o["id"], "required": o["required"], "result": result, "reason": reason, "source_id": o["source_id"]})
    open_required = [u["id"] for u in doc["unknowns"] if u["required"] and u["state"] == "open"]
    required_results = [r["result"] for r in results if r["required"]]
    result = "fail" if "fail" in required_results else "unknown" if "unknown" in required_results or open_required else "pass"
    return {"schema_version": SCHEMA, "status": "valid", "result": result, "obligations": results,
            "required_unknowns": open_required, "provenance_authenticity": "not_verified",
            "scope": "Finite comparison of submitted records only; no target execution, factual certification, global parity, or S2/S3 claim."}, {"pass": 0, "fail": 1, "unknown": 2}[result]

def unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON key: " + key)
        out[key] = value
    return out

def load_document(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("input byte budget exceeded")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("non-finite JSON constant")))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="GRVIS JSON evidence-record file; never executed")
    args = parser.parse_args()
    try:
        report, code = evaluate(load_document(args.input))
    except (OSError, ValueError, UnicodeError, RecursionError) as exc:
        report, code = {"schema_version": SCHEMA, "status": "invalid", "result": "unknown", "issues": [{"reason": str(exc)}], "provenance_authenticity": "not_verified"}, 3
    print(json.dumps(report, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return code

if __name__ == "__main__":
    raise SystemExit(main())
