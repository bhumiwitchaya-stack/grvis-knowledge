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
        result = fetch_public_text(args.url, set(args.allow_domain))
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
