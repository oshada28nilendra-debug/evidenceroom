import json
import tempfile
import unittest
from pathlib import Path

from evidenceroom.core import Error, ingest, load_case, normalize_html
from evidenceroom.retrieval import rank


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "a.txt").write_text(
            "Council grant rules.\n\nNonprofits can apply.\n\nAward maximum is 10000 credits."
        )
        self.case = {
            "question": "Can we apply?",
            "options": ["apply", "wait"],
            "claims": ["Nonprofits can apply."],
            "sources": [
                {
                    "id": "s1",
                    "title": "Rules",
                    "path": "a.txt",
                    "publisher": "Council",
                    "kind": "primary",
                }
            ],
        }

    def load(self):
        p = self.root / "case.json"
        p.write_text(json.dumps(self.case))
        return load_case(p)

    def test_valid_case_and_stable_hashes(self):
        c = self.load()
        sources = ingest(c, self.root)
        self.assertEqual(sources[0]["sha256"], ingest(c, self.root)[0]["sha256"])
        self.assertIn("Nonprofits can apply.", sources[0]["text"])

    def test_rejects_traversal_and_symlinks(self):
        for path in ["../outside.txt", "/etc/passwd"]:
            self.case["sources"][0]["path"] = path
            with self.assertRaises(Error):
                ingest(self.load(), self.root)
        (self.root / "link.txt").symlink_to(self.root / "a.txt")
        self.case["sources"][0]["path"] = "link.txt"
        with self.assertRaises(Error):
            ingest(self.load(), self.root)

    def test_rejects_duplicate_ids_and_over_budget(self):
        self.case["sources"] *= 2
        with self.assertRaises(Error):
            self.load()
        self.case["sources"] = self.case["sources"][:1]
        self.case["claims"] *= 9
        with self.assertRaises(Error):
            self.load()

    def test_rejects_missing_question_and_ambiguous_source(self):
        for key in ["question", "sources"]:
            broken = dict(self.case)
            del broken[key]
            (self.root / "case.json").write_text(json.dumps(broken))
            with self.assertRaises(Error):
                load_case(self.root / "case.json")
        self.case["sources"][0]["url"] = "https://example.org"
        with self.assertRaises(Error):
            self.load()

    def test_html_is_text_and_hides_active_content(self):
        self.assertEqual(
            normalize_html("<h1>Rules</h1><script>bad()</script><p>Good &amp; safe.</p>"),
            "Rules\n\nGood & safe.",
        )

    def test_binary_and_huge_source_rejected(self):
        for data in [b"\xff", b"a" * 524289]:
            (self.root / "a.txt").write_bytes(data)
            with self.assertRaises(Error):
                ingest(self.load(), self.root)

    def test_retrieval_offsets_and_relevance(self):
        sources = ingest(self.load(), self.root)
        passages = rank("Nonprofits apply", sources)
        self.assertIn("Nonprofits", passages[0]["text"])
        for p in passages:
            self.assertEqual(sources[0]["text"][p["start"] : p["end"]], p["text"])
        self.assertEqual(rank("xyznonexistent", sources), [])

    def test_duplicates_not_counted_as_independent_sources(self):
        second = dict(self.case["sources"][0], id="s2")
        self.case["sources"].append(second)
        sources = ingest(self.load(), self.root)
        self.assertEqual(sources[0]["content_group"], sources[1]["content_group"])
        self.assertTrue(sources[1]["duplicate_of"])


if __name__ == "__main__":
    unittest.main()


class SourcePriorityTests(unittest.TestCase):
    def test_retrieval_prioritizes_declared_primary_and_diverse_sources(self):
        sources = []
        for sid, kind, body in [
            ("blog", "secondary", "Grant maximum award grant maximum award."),
            ("rules", "primary", "Grant maximum award is 10000.\n\nAward rules apply."),
            ("faq", "primary", "Grant maximum award is now 12000."),
        ]:
            sources.append({"id": sid, "text": body, "duplicate_of": None, "declared_kind": kind})
        passages = rank("Grant maximum award", sources)
        self.assertEqual({p["source_id"] for p in passages[:2]}, {"rules", "faq"})
        self.assertEqual(len({p["source_id"] for p in passages}), 3)
