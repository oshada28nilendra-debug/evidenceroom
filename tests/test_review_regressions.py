import json
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from evidenceroom.core import Error, digest, load_case
from evidenceroom.network import discover
from evidenceroom.pipeline import build
from evidenceroom.provider import CompatibleProvider
from evidenceroom.report import review_bundle, verify_bundle


class ReviewRegressionTests(unittest.TestCase):
    def test_trickle_response_cannot_extend_model_deadline(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                body = json.dumps({"choices": [{"message": {"content": "{}"}}]}).encode() + b" " * 80
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                try:
                    for i in range(0, len(body), 20):
                        self.wfile.write(body[i : i + 20])
                        self.wfile.flush()
                        time.sleep(0.3)
                except OSError:
                    pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            start = time.monotonic()
            with self.assertRaises(Error):
                CompatibleProvider(f"http://127.0.0.1:{server.server_port}/v1", "simulated", timeout=1).complete({})
            self.assertLess(time.monotonic() - start, 1.6)
        finally:
            server.shutdown()
            server.server_close()

    def test_list_valued_source_kind_and_review_decision_are_controlled_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "s.txt").write_text("Nonprofits may apply")
            c = {
                "question": "Eligibility?",
                "claims": ["Nonprofits may apply"],
                "sources": [{"id": "s1", "title": "Rules", "publisher": "Council", "path": "s.txt", "kind": []}],
            }
            f = p / "case.json"
            f.write_text(json.dumps(c))
            with self.assertRaises(Error):
                load_case(f)
            c["sources"][0]["kind"] = "primary"
            f.write_text(json.dumps(c))
            b = build(f)
            with self.assertRaises(Error):
                review_bundle(
                    b,
                    {
                        "bundle_digest": b["bundle_digest"],
                        "reviewer": "R",
                        "decisions": [{"evidence_id": "c1-e1", "decision": [], "note": "Bad value"}],
                    },
                )

    def test_malformed_discovery_items_are_controlled_errors(self):
        for items in [[None], [[]], None, {}]:

            def fake(*args, **kwargs):
                return json.dumps({"message": {"items": items}}).encode(), "application/json"

            with self.assertRaises(Error):
                discover("question", fetcher=fake)

    def test_incomplete_bundle_cannot_pass_verification(self):
        b = {"schema_version": 1, "sources": [], "claims": []}
        b["bundle_digest"] = digest(b)
        with self.assertRaises(Error):
            verify_bundle(b)

    def test_source_slow_headers_cannot_extend_deadline(self):
        from unittest.mock import patch

        from evidenceroom.httpio import DeadlineHTTP
        from evidenceroom.network import fetch_https

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                try:
                    self.wfile.write(b"HTTP/1.1 200 OK\r\n")
                    self.wfile.flush()
                    for _ in range(8):
                        self.wfile.write(b"X-Slow: yes\r\n")
                        self.wfile.flush()
                        time.sleep(0.3)
                    self.wfile.write(b"Content-Length: 2\r\nContent-Type: text/plain\r\n\r\nok")
                    self.wfile.flush()
                except OSError:
                    pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with (
                patch("evidenceroom.network.validate_public_url", return_value=("example.org", "/", "93.184.216.34")),
                patch(
                    "evidenceroom.network.PinnedHTTPS",
                    side_effect=lambda h, ip, t: DeadlineHTTP("127.0.0.1", server.server_port, t),
                ),
            ):
                start = time.monotonic()
                with self.assertRaises(Error):
                    fetch_https("https://example.org", {"example.org"}, timeout=1)
                self.assertLess(time.monotonic() - start, 1.6)
        finally:
            server.shutdown()
            server.server_close()

    def test_rehashed_invalid_reporting_fields_do_not_verify(self):
        import copy

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "s.txt").write_text("Nonprofits may apply")
            c = {
                "question": "Eligibility?",
                "claims": ["Nonprofits may apply"],
                "sources": [{"id": "s1", "title": "Rules", "publisher": "Council", "path": "s.txt", "kind": "primary"}],
            }
            f = p / "case.json"
            f.write_text(json.dumps(c))
            base = build(f)
            for key, value in [("options", [{}]), ("warnings", [None]), ("errors", [1]), ("mode", [])]:
                b = copy.deepcopy(base)
                b[key] = value
                b["bundle_digest"] = digest({k: v for k, v in b.items() if k != "bundle_digest"})
                with self.subTest(key=key), self.assertRaises(Error):
                    verify_bundle(b)
            b = copy.deepcopy(base)
            b["claims"][0]["summary"] = {}
            b["bundle_digest"] = digest({k: v for k, v in b.items() if k != "bundle_digest"})
            with self.assertRaises(Error):
                verify_bundle(b)
