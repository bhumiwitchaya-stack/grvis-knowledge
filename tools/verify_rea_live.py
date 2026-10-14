"""Exercise pinned REA on owned browser/native fixtures, retaining original Evidence."""
import argparse
import hashlib
import http.server
import json
from pathlib import Path
import subprocess
import threading


def run(args, output):
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", timeout=600)
    output.write_text(result.stdout, encoding="utf-8")
    output.with_suffix(".stderr.txt").write_text(result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"REA returned {result.returncode}; inspect {output.name}")
    value = json.loads(result.stdout)
    assert value.get("evidence_id", "").startswith("ev_"), "Missing Evidence ID"
    assert isinstance(value.get("normalized_result"), dict), "Missing normalized result"
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rea", required=True)
    parser.add_argument("--browser", required=True)
    parser.add_argument("--native", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = root / "results"
    out.mkdir(exist_ok=True)
    fixture = root / "tests/fixtures/browser-chart"
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(fixture), **kw)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    scenario = {"browser": {"mode": "launch", "executable_path": args.browser},
                "start_url": {"url": f"http://127.0.0.1:{server.server_port}/"},
                "actions": [
                    {"step_id": "initial-ready", "action": "wait_for", "locator": {"kind": "css", "selector": '#state[data-timeframe="1m"]'}, "state": "visible", "timeout_ms": 10000},
                    {"step_id": "select-five", "action": "click", "locator": {"kind": "css", "selector": "#five"}, "timeout_ms": 10000},
                    {"step_id": "five-ready", "action": "wait_for", "locator": {"kind": "css", "selector": '#state[data-timeframe="5m"]'}, "state": "visible", "timeout_ms": 10000}],
                "capture": {"after_each_step": ["dom"], "at_end": ["dom", "accessibility", "url"]}}
    scenario_path = out / "browser-scenario.json"
    scenario_path.write_text(json.dumps(scenario), encoding="utf-8")
    try:
        browser = run([args.rea, "capture-browser-scenario", str(scenario_path), "--json"], out / "rea-browser-evidence.json")
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
    capture = browser["normalized_result"]
    assert capture["completeness"]["status"] == "complete"
    assert capture["browser"]["cleanup"] == "terminated-owned-process"
    steps = capture["steps"]
    doms = [s["artifacts"]["dom"] for s in steps]
    captured = [d["value"]["text"] for d in doms if d["state"] == "captured"]
    assert any('data-timeframe="1m"' in d and "Timeframe: 1m" in d for d in captured)
    assert 'data-timeframe="5m"' in captured[-1] and "Timeframe: 5m" in captured[-1]
    native = run([args.rea, "function", args.native, "--procedure", "grvis_rule", "--provider", "ghidra", "--json"], out / "rea-native-evidence.json")
    text = json.dumps(native["normalized_result"])
    assert "grvis_rule" in text, "Named fixture function absent"
    summary = {"scope": "owned finite browser transition and native function analysis only",
               "browser_evidence_id": browser["evidence_id"], "browser": capture["browser"],
               "native_evidence_id": native["evidence_id"], "native_provider": native.get("provider"),
               "native_sha256": hashlib.sha256(Path(args.native).read_bytes()).hexdigest(),
               "browser_transition": "1m -> 5m", "status": "PASS"}
    (out / "rea-live-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
