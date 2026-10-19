"""CLI: explicit model and network consent; no automatic provider charges."""

import argparse
import json
import os
import sys
from pathlib import Path

from .core import Error, read_json
from .network import discover, fetch_https
from .pipeline import build
from .provider import CompatibleProvider
from .report import export_bundle, review_bundle, verify_bundle


def main(argv=None):
    parser = argparse.ArgumentParser(prog="evidenceroom", description="Reviewable claim/evidence decision audits")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--case", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True, help="New directory; never overwritten")
    mode = run.add_mutually_exclusive_group(required=True)
    mode.add_argument("--offline", action="store_true", help="Lexical retrieval only; no model calls")
    mode.add_argument("--model", help="Use your chosen compatible model")
    run.add_argument(
        "--endpoint",
        default=os.environ.get("EVIDENCEROOM_BASE_URL", "http://localhost:11434/v1"),
    )
    run.add_argument(
        "--allow-remote-model",
        action="store_true",
        help="Consent to remote source transfer and possible API charges",
    )
    run.add_argument("--model-timeout", type=int, default=120)
    run.add_argument("--max-calls", type=int, default=9)
    run.add_argument(
        "--allow-network",
        action="store_true",
        help="Consent to fetch explicitly listed public source URLs",
    )
    run.add_argument(
        "--allow-host",
        action="append",
        default=[],
        help="Exact lowercase public source hostname; repeatable",
    )
    search = commands.add_parser("discover")
    search.add_argument("--query", required=True)
    search.add_argument("--allow-network", action="store_true", required=True)
    review = commands.add_parser("review")
    review.add_argument("--bundle", type=Path, required=True)
    review.add_argument("--decisions", type=Path, required=True)
    review.add_argument("--out", type=Path, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "discover":
            print(json.dumps(discover(args.query), ensure_ascii=False, indent=2))
            return 0
        if args.command == "verify":
            verify_bundle(read_json(args.bundle))
            print("Bundle hashes and quote spans are consistent. This is not a truth or authenticity certificate.")
            return 0
        if args.out.exists() or args.out.is_symlink():
            raise Error("Output already exists; choose a new directory")
        if args.command == "review":
            report = review_bundle(read_json(args.bundle), read_json(args.decisions, 64_000))
        else:
            if args.allow_host and not args.allow_network:
                raise Error("--allow-host requires --allow-network")
            provider = (
                CompatibleProvider(
                    args.endpoint,
                    args.model,
                    os.environ.get("EVIDENCEROOM_API_KEY", ""),
                    allow_remote=args.allow_remote_model,
                    max_calls=args.max_calls,
                    timeout=args.model_timeout,
                )
                if args.model
                else None
            )
            fetcher = (lambda url: fetch_https(url, args.allow_host)) if args.allow_network else None
            report = build(args.case, provider, fetcher)
        export_bundle(report, args.out)
        print(
            json.dumps(
                {
                    "status": report["workflow_status"],
                    "mode": report["mode"],
                    "claims": len(report["claims"]),
                    "bundle": str(args.out / "bundle.json"),
                    "decision": report["decision"],
                    "model_calls": report["model"]["calls"],
                },
                indent=2,
            )
        )
        return 3 if report["workflow_status"] == "partial" else 0
    except (Error, OSError, UnicodeError) as exc:
        # Do not stringify OS/decode errors: filenames or bytes can contain private data.
        message = (
            str(exc)
            if isinstance(exc, Error)
            else "Input/output operation failed; check paths, permissions and UTF-8 encoding"
        )
        print("evidenceroom: " + message, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
