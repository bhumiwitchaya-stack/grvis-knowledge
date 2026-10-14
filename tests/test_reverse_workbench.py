"""Regression tests on synthetic records; never target/runtime certification."""
import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("workbench", ROOT / "tools/reverse_workbench.py")
workbench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workbench)
BASE = json.loads((ROOT / "tests/fixtures/reverse-evidence.json").read_text(encoding="utf-8"))

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.doc = copy.deepcopy(BASE)

    def result(self):
        return workbench.evaluate(self.doc)

    def no_claim(self):
        self.doc["claims"] = []

    def test_comparable_match(self):
        r, code = self.result()
        self.assertEqual((r["result"], code), ("pass", 0))
        self.assertEqual(r["provenance_authenticity"], "not_verified")

    def test_divergence(self):
        self.doc["obligations"][0]["observed"] = "1m"
        self.assertEqual(self.result()[1], 1)

    def test_missing_observation_unknown(self):
        del self.doc["obligations"][0]["observed"]
        self.assertEqual(self.result()[1], 2)

    def test_partial_never_passes(self):
        self.no_claim()
        self.doc["sources"][0]["coverage"] = "partial"
        self.assertEqual(self.result()[1], 2)

    def test_not_requested_never_means_absence(self):
        self.no_claim()
        self.doc["sources"][0]["coverage"] = "not_requested"
        self.assertEqual(self.result()[1], 2)

    def test_stale_revision_unknown(self):
        self.no_claim()
        self.doc["sources"][0]["target_revision"] = "fixture-v0"
        self.assertEqual(self.result()[1], 2)

    def test_environment_mismatch_unknown(self):
        self.no_claim()
        self.doc["obligations"][0]["environment_id"] = "other"
        self.assertEqual(self.result()[1], 2)

    def test_marketing_cannot_prove_behavior(self):
        self.doc["sources"][0]["kind"] = "marketing"
        self.assertEqual(self.result()[1], 3)

    def test_static_cannot_prove_behavior(self):
        self.doc["sources"][0]["kind"] = "static_analysis"
        self.assertEqual(self.result()[1], 3)

    def test_documented_claim_is_not_behavior(self):
        self.doc["sources"][0]["kind"] = "marketing"
        self.doc["claims"][0]["kind"] = "documented"
        self.doc["claims"][0]["text"] = "The submitted promotional record made this statement."
        self.assertEqual(self.result()[1], 2)

    def test_e2_copied_lineage_rejected(self):
        other = copy.deepcopy(self.doc["sources"][0])
        other["id"] = "S-02"
        self.doc["sources"].append(other)
        self.doc["claims"][0].update(tier="E2", evidence=["S-01", "S-02"])
        self.assertEqual(self.result()[1], 3)

    def test_e2_distinct_declared_lineages(self):
        other = copy.deepcopy(self.doc["sources"][0])
        other.update(id="S-02", lineage="fixture-run-2")
        self.doc["sources"].append(other)
        self.doc["claims"][0].update(tier="E2", evidence=["S-01", "S-02"])
        self.assertEqual(self.result()[1], 0)

    def test_contradiction_preserved(self):
        self.doc["claims"][0]["contradictions"] = ["S-01"]
        self.assertEqual(self.result()[1], 3)

    def test_required_unknown_blocks(self):
        self.doc["unknowns"] = [{"id": "U-01", "question": "Does reconnect duplicate the state?",
            "kind": "behavioral", "state": "open", "required": True, "owner": "fixture-evaluator",
            "resolution_evidence": []}]
        self.assertEqual(self.result()[1], 2)

    def test_resolved_unknown_needs_evidence(self):
        self.doc["unknowns"] = [{"id": "U-01", "question": "Does reconnect duplicate the state?",
            "kind": "behavioral", "state": "resolved", "required": True, "owner": "fixture-evaluator",
            "resolution_evidence": []}]
        self.assertEqual(self.result()[1], 3)

    def test_no_empty_success(self):
        self.doc["obligations"] = []
        self.assertEqual(self.result()[1], 3)

    def test_injected_pass_flag_rejected(self):
        self.doc["obligations"][0]["result"] = "pass"
        self.assertEqual(self.result()[1], 3)

    def test_dangling_source_rejected(self):
        self.doc["obligations"][0]["source_id"] = "missing"
        self.assertEqual(self.result()[1], 3)

    def test_duplicate_ids_rejected(self):
        self.doc["sources"].append(copy.deepcopy(self.doc["sources"][0]))
        self.assertEqual(self.result()[1], 3)

    def test_numeric_tolerance_boundary(self):
        self.doc["obligations"][0].update(expected=100, observed=101, abs_tol=1)
        self.assertEqual(self.result()[1], 0)
        self.doc["obligations"][0]["observed"] = 101.001
        self.assertEqual(self.result()[1], 1)

    def test_bad_tolerance_rejected(self):
        for tolerance in [-1, True, float("nan"), "1"]:
            self.doc["obligations"][0].update(expected=100, observed=100, abs_tol=tolerance)
            self.assertEqual(self.result()[1], 3)

    def test_extreme_numeric_range(self):
        self.doc["obligations"][0].update(expected=10 ** 400, observed=0.0, abs_tol=1)
        self.assertEqual(self.result()[1], 3)
        self.doc["obligations"][0].update(expected=1e308, observed=-1e308, abs_tol=1)
        self.assertEqual(self.result()[1], 1)

    def test_bool_not_numeric(self):
        self.doc["obligations"][0].update(expected=True, observed=1)
        self.assertEqual(self.result()[1], 1)

    def test_nested_value_types(self):
        self.doc["obligations"][0].update(expected={"a": [True]}, observed={"a": [1]})
        self.assertEqual(self.result()[1], 1)

    def test_malformed_enums_do_not_crash(self):
        for field in ["kind", "label", "tier", "status"]:
            d = copy.deepcopy(BASE)
            d["claims"][0][field] = []
            self.assertEqual(workbench.evaluate(d)[1], 3)
        for field in ["kind", "uri", "coverage"]:
            d = copy.deepcopy(BASE)
            d["sources"][0][field] = []
            self.assertEqual(workbench.evaluate(d)[1], 3)

    def test_credentials_rejected(self):
        self.doc["sources"][0]["uri"] = "https://user:password@example.invalid/"
        self.assertEqual(self.result()[1], 3)

    def test_timezone_required(self):
        self.doc["sources"][0]["retrieved_at"] = "2026-01-01T00:00:00"
        self.assertEqual(self.result()[1], 3)

    def test_unknown_schema_rejected(self):
        self.doc["schema_version"] = "other"
        self.assertEqual(self.result()[1], 3)

    def test_record_budget(self):
        self.doc["sources"] = [self.doc["sources"][0]] * 501
        self.assertEqual(self.result()[1], 3)

    def test_cli_utf8_roundtrip(self):
        self.doc["obligations"][0]["id"] = "ผล-01"
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "ไทย.json"
            p.write_text(json.dumps(self.doc, ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run([sys.executable, str(ROOT / "tools/reverse_workbench.py"), str(p)],
                capture_output=True, env={**os.environ, "PYTHONIOENCODING": "cp1252"}, timeout=10)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            output = json.loads(completed.stdout.decode("utf-8"))
            self.assertEqual(output["obligations"][0]["id"], "ผล-01")

    def test_json_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "bad.json"
            p.write_text('{"a":1,"a":2}')
            with self.assertRaises(ValueError):
                workbench.load_document(p)

    def test_depth_budget(self):
        nested = None
        for _ in range(55):
            nested = [nested]
        self.doc["obligations"][0]["observed"] = nested
        self.assertEqual(self.result()[1], 3)

if __name__ == "__main__":
    unittest.main()
