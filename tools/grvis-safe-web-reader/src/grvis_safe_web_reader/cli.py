"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import sys

from .core import SafetyError, fetch_public_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="grvis-safe-web-reader",
        description="Extract text from an allowlisted public HTML page (read-only).",
    )
    parser.add_argument("--max-response-mib", type=int, default=2, help="Response body limit: 1–20 MiB")
    parser.add_argument("--timeout", type=int, default=10, help="Socket timeout: 1–60 seconds")
    parser.add_argument("--max-redirects", type=int, default=3, help="Validated redirect limit: 0–5")
    parser.add_argument("url", help="Public HTTP(S) page URL")
    parser.add_argument(
        "--allow-domain",
        action="append",
        required=True,
        metavar="HOST",
        help="Exact allowed hostname; repeat to add hosts. Wildcards are not supported.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = fetch_public_text(args.url, set(args.allow_domain),
                                   max_response_bytes=args.max_response_mib * 1024 * 1024,
                                   timeout_seconds=args.timeout, max_redirects=args.max_redirects)
    except SafetyError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except Exception as exc:  # keep transport/parser details out of normal output
        print(json.dumps({"error": f"fetch failed ({type(exc).__name__})"}), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
