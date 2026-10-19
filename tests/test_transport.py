import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from evidenceroom.core import Error
from evidenceroom.network import fetch_https, validate_public_url
from evidenceroom.provider import CompatibleProvider


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.status = 200
        self.body = {
            "choices": [{"message": {"content": '{"claims":["A claim"]}'}}],
            "usage": {"completion_tokens": 6, "prompt_tokens": 40},
        }
        self.seen = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                outer.seen.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                self.send_response(outer.status)
                if outer.status == 302:
                    self.send_header("Location", "http://127.0.0.1:1")
                self.end_headers()
                self.wfile.write(json.dumps(outer.body).encode())

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = f"http://127.0.0.1:{self.server.server_port}/v1"

    def test_real_http_json_and_usage_with_simulated_model(self):
        p = CompatibleProvider(self.url, "simulated", max_calls=1)
        self.assertEqual(p.complete({"task": "plan"})["claims"], ["A claim"])
        self.assertEqual(p.usage["completion_tokens"], 6)
        self.assertEqual(self.seen[0]["response_format"], {"type": "json_object"})
        with self.assertRaises(Error):
            p.complete({})

    def test_http_failures_hide_response_and_refuse_redirect(self):
        for status in [401, 429, 500, 302]:
            self.status = status
            self.body = {"secret": "sensitive-response-body"}
            with self.assertRaises(Error) as e:
                CompatibleProvider(self.url, "simulated").complete({})
            self.assertNotIn("sensitive-response-body", str(e.exception))

    def test_malformed_json_content_rejected(self):
        self.body = {"choices": [{"message": {"content": "not json"}}]}
        with self.assertRaises(Error):
            CompatibleProvider(self.url, "simulated").complete({})

    def test_remote_provider_requires_explicit_https_consent(self):
        for url in [
            "http://example.org/v1",
            "https://example.org/v1",
            "https://u:p@example.org/v1",
            "https://example.org/v1?key=secret",
        ]:
            with self.assertRaises(Error):
                CompatibleProvider(url, "x")
        CompatibleProvider("https://example.org/v1", "x", allow_remote=True)

    def test_private_urls_and_unlisted_hosts_blocked(self):
        for url in [
            "http://example.org",
            "https://127.0.0.1",
            "https://[::1]",
            "https://169.254.169.254",
            "https://example.org@localhost",
            "file:///etc/passwd",
        ]:
            with self.assertRaises(Error):
                validate_public_url(url, {"example.org"})
        with self.assertRaises(Error):
            fetch_https("https://not-allowed.invalid", {"example.org"})

    def test_all_dns_results_checked_including_mixed_private(self):
        records = [
            (2, 1, 6, "", ("93.184.216.34", 443)),
            (2, 1, 6, "", ("10.0.0.1", 443)),
        ]
        with patch("evidenceroom.network.socket.getaddrinfo", return_value=records):
            with self.assertRaises(Error):
                validate_public_url("https://example.org", {"example.org"})
        with patch("evidenceroom.network.socket.getaddrinfo", return_value=records[:1]):
            host, path, ip = validate_public_url("https://example.org/a?q=b", {"example.org"})
            self.assertEqual((host, path, ip), ("example.org", "/a?q=b", "93.184.216.34"))


class FetchTests(unittest.TestCase):
    def test_source_redirect_size_and_mime_fail_closed(self):
        from unittest.mock import MagicMock

        records = [(2, 1, 6, "", ("93.184.216.34", 443))]
        for status, mime, data in [
            (302, "text/html", b"ok"),
            (200, "application/pdf", b"pdf"),
            (200, "text/plain", b"too long"),
        ]:
            conn = MagicMock()
            response = conn.getresponse.return_value
            response.status = status
            response.getheaders.return_value = [("Content-Type", mime)]
            response.getheader.side_effect = lambda k, default=None: mime if k == "Content-Type" else "identity"
            response.read1.side_effect = [data, b""]
            with (
                patch("evidenceroom.network.socket.getaddrinfo", return_value=records),
                patch("evidenceroom.network.PinnedHTTPS", return_value=conn),
                self.assertRaises(Error),
            ):
                fetch_https("https://example.org", {"example.org"}, max_bytes=3)
            conn.close.assert_called_once()

    def test_pinned_connection_receives_validated_address(self):
        from unittest.mock import MagicMock

        records = [(2, 1, 6, "", ("93.184.216.34", 443))]
        conn = MagicMock()
        response = conn.getresponse.return_value
        response.status = 200
        response.getheaders.return_value = [("Content-Type", "text/plain")]
        response.getheader.side_effect = lambda k, default=None: "text/plain" if k == "Content-Type" else "identity"
        response.read1.side_effect = [b"hello", b""]
        with (
            patch("evidenceroom.network.socket.getaddrinfo", return_value=records),
            patch("evidenceroom.network.PinnedHTTPS", return_value=conn) as pinned,
        ):
            body, mime = fetch_https("https://example.org", {"example.org"})
            self.assertEqual((body, mime), (b"hello", "text/plain"))
            pinned.assert_called_once_with("example.org", "93.184.216.34", 20)

    def test_crossref_metadata_is_discovery_not_claim_evidence(self):
        from evidenceroom.network import discover

        def fake(url, hosts, **kwargs):
            return json.dumps(
                {
                    "message": {
                        "items": [
                            {"title": ["A paper"], "URL": "https://doi.org/10.example/test", "DOI": "10.example/test"}
                        ]
                    }
                }
            ).encode(), "application/json"

        result = discover("question", fetcher=fake)
        self.assertEqual(len(result["results"]), 1)
        self.assertIn("not evidence", result["notice"])
        with self.assertRaises(Error):
            discover("")
