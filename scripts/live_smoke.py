"""Run the authored fixture against a deliberately supplied local llama.cpp runtime.

This starts a real model process; it does not substitute canned evidence. Runtime
and weights must be downloaded and checksum-verified separately. No API keys.
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from evidenceroom.report import verify_bundle


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--server", type=Path, required=True)
    p.add_argument("--weights", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    log = (args.out / "model-server.log").open("w", encoding="utf-8")
    command = [
        str(args.server.resolve()),
        "-m",
        str(args.weights.resolve()),
        "--host",
        "127.0.0.1",
        "--port",
        "18081",
        "--alias",
        "evidenceroom-qwen3",
        "--threads",
        "4",
        "--ctx-size",
        "8192",
        "--parallel",
        "1",
        "--n-gpu-layers",
        "0",
        "--reasoning-budget",
        "0",
    ]
    server = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
    try:
        ready = False
        for _ in range(60):
            if server.poll() is not None:
                break
            try:
                with urllib.request.urlopen("http://127.0.0.1:18081/health", timeout=1) as response:
                    ready = response.status == 200
                if ready:
                    break
            except OSError:
                time.sleep(0.25)
        if not ready:
            raise RuntimeError("Local model failed readiness; inspect model-server.log")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "evidenceroom",
                "run",
                "--case",
                "examples/grant-case.json",
                "--model",
                "evidenceroom-qwen3",
                "--endpoint",
                "http://127.0.0.1:18081/v1",
                "--out",
                str(args.out / "audit"),
            ],
            timeout=600,
            check=False,
        )
        if result.returncode:
            raise RuntimeError("Model audit failed; original evidence retained")
        bundle = json.loads((args.out / "audit" / "bundle.json").read_text())
        verify_bundle(bundle)
        if bundle["mode"] != "live_model" or bundle["model"]["usage"].get("completion_tokens", 0) <= 0:
            raise RuntimeError("Missing actual model usage")
        records = bundle["claims"][1]["evidence"]
        if not (
            any(e["relation"] == "support" and "10000" in e["quote"] for e in records)
            and any(e["relation"] == "oppose" and "12000" in e["quote"] for e in records)
        ):
            raise RuntimeError("Fixture support/opposition gate failed; inspect model output")
        if any(e["relation"] in {"support", "oppose"} for e in bundle["claims"][3]["evidence"]):
            raise RuntimeError("Model proposed direct evidence for an unsupported fixture claim")
        (args.out / "gate.json").write_text(
            json.dumps(
                {
                    "status": "passed",
                    "bundle_digest": bundle["bundle_digest"],
                    "model": bundle["model"],
                    "limit": "One authored fixture; human review still required.",
                },
                indent=2,
            )
            + "\n"
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
        log.close()


if __name__ == "__main__":
    main()
