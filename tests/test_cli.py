import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from evidenceroom.cli import main
from evidenceroom.core import Error, digest, read_json
from evidenceroom.pipeline import build
from evidenceroom.report import render_html, review_bundle, verify_bundle


class CLITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "s.txt").write_text("Nonprofits may apply.\n\nThe award limit is 10000 credits.")
        self.case = self.root / "case.json"
        self.case.write_text(
            json.dumps(
                {
                    "question": "Can we apply?",
                    "claims": ["Nonprofits may apply."],
                    "sources": [
                        {
                            "id": "s1",
                            "title": "<script>alert(1)</script>",
                            "publisher": "Council",
                            "kind": "primary",
                            "path": "s.txt",
                        }
                    ],
                }
            )
        )

    def test_offline_cli_end_to_end_exports_and_integrity(self):
        output = self.root / "out"
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "evidenceroom",
                "run",
                "--case",
                str(self.case),
                "--offline",
                "--out",
                str(output),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = read_json(output / "bundle.json")
        self.assertEqual(data["mode"], "offline_retrieval")
        self.assertTrue(verify_bundle(data))
        self.assertTrue((output / "report.html").is_file())
        self.assertIn("Lexical retrieval", (output / "report.md").read_text())
        self.assertNotIn("<script>", (output / "report.html").read_text())
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "evidenceroom",
                "run",
                "--case",
                str(self.case),
                "--offline",
                "--out",
                str(output),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)

    def test_tampered_source_or_quote_detected(self):
        bundle = build(self.case)
        bundle["sources"][0]["text"] = "modified"
        with self.assertRaises(Error):
            verify_bundle(bundle)
        bundle = build(self.case)
        bundle["claims"][0]["evidence"][0]["quote"] = "fabricated"
        bundle["bundle_digest"] = digest({k: v for k, v in bundle.items() if k != "bundle_digest"})
        with self.assertRaises(Error):
            verify_bundle(bundle)

    def test_digest_bound_review_changes_relation_and_preserves_original(self):
        bundle = build(self.case)
        eid = bundle["claims"][0]["evidence"][0]["id"]
        decisions = {
            "bundle_digest": bundle["bundle_digest"],
            "reviewer": "Example reviewer",
            "decisions": [
                {
                    "evidence_id": eid,
                    "decision": "accept",
                    "relation": "support",
                    "note": "Explicit eligibility rule.",
                }
            ],
        }
        reviewed = review_bundle(bundle, decisions)
        self.assertEqual(bundle["claims"][0]["evidence"][0]["review"], "unreviewed")
        e = reviewed["claims"][0]["evidence"][0]
        self.assertEqual(e["review"], "accepted")
        self.assertEqual(e["relation"], "support")
        self.assertEqual(e["original_relation"], "context")
        self.assertTrue(verify_bundle(reviewed))
        self.assertEqual(reviewed["parent_bundle_digest"], bundle["bundle_digest"])
        decisions["bundle_digest"] = "wrong"
        with self.assertRaises(Error):
            review_bundle(bundle, decisions)

    def test_unknown_or_duplicate_review_ids_rejected(self):
        b = build(self.case)
        for ds in [
            [{"evidence_id": "unknown", "decision": "reject", "note": "Unknown"}],
            [{"evidence_id": "c1-e1", "decision": "accept", "note": "Okay"}] * 2,
        ]:
            with self.assertRaises(Error):
                review_bundle(
                    b,
                    {
                        "bundle_digest": b["bundle_digest"],
                        "reviewer": "R",
                        "decisions": ds,
                    },
                )

    def test_html_is_inert_and_cannot_link_to_javascript(self):
        b = build(self.case)
        b["question"] = "<img src=x onerror=alert(1)>"
        b["sources"][0]["location"] = "javascript:alert(1)"
        html = render_html(b)
        self.assertNotIn("<img", html)
        self.assertNotIn('href="javascript:', html)
        self.assertIn("Content-Security-Policy", html)

    def test_invalid_case_fails_without_secret_output(self):
        with (
            contextlib.redirect_stderr(io.StringIO()),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            code = main(
                [
                    "run",
                    "--case",
                    str(self.root / "missing.json"),
                    "--offline",
                    "--out",
                    str(self.root / "out"),
                ]
            )
        self.assertEqual(code, 2)
        self.assertFalse((self.root / "out").exists())
