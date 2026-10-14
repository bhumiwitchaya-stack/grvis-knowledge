"""Check actual CLI output from the owned static fixture, not a target app."""
import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence_file")
    args = parser.parse_args()
    evidence = json.loads(Path(args.evidence_file).read_text(encoding="utf-8"))
    if not isinstance(evidence, dict) or not isinstance(evidence.get("evidence_id"), str) or not evidence["evidence_id"]:
        raise SystemExit("REA did not return an Evidence record with identity")
    normalized = evidence.get("normalized_result")
    if not isinstance(normalized, dict):
        raise SystemExit("REA normalized_result is missing or not an object")
    if "selectTimeframe" not in json.dumps(normalized):
        raise SystemExit("Owned fixture export selectTimeframe not found in actual normalized output")
    print(json.dumps({"status": "pass", "evidence_id": evidence["evidence_id"],
        "package": "rea-agents@6.4.0", "scope": "Owned JavaScript fixture static CLI only; not native/browser/ChatGPT activation."},
        sort_keys=True))

if __name__ == "__main__":
    main()
