"""Opt-in real public TLS/Crossref check; saves metadata/hashes, no inference."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from evidenceroom.core import Error
from evidenceroom.network import discover, fetch_https


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-network", action="store_true", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    checks = {}
    try:
        raw, mime = fetch_https("https://www.python.org/", {"www.python.org"})
        assert mime == "text/html" and b"Python" in raw and len(raw) > 100
        checks["public_source"] = {
            "passed": True,
            "url": "https://www.python.org/",
            "mime": mime,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    except (Error, AssertionError) as exc:
        checks["public_source"] = {"passed": False, "error": str(exc)}
    try:
        result = discover("retrieval augmented generation")
        assert 1 <= len(result["results"]) <= 5
        assert all(isinstance(r["doi"], str) and r["doi"] and isinstance(r["title"], str) for r in result["results"])
        checks["crossref"] = {"passed": True, "metadata": result}
    except (Error, AssertionError) as exc:
        checks["crossref"] = {"passed": False, "error": str(exc)}
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "passed": all(c["passed"] for c in checks.values()),
        "scope": "Actual public TLS source fetch and bibliographic discovery; no truth or research-quality claim",
    }
    (args.out / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
