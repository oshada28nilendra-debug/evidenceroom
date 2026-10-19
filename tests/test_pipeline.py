import json
import tempfile
import unittest
from pathlib import Path

from evidenceroom.core import digest
from evidenceroom.pipeline import build, summarize, validate_annotations


class ScriptedProvider:
    """Offline test double, never a live model result."""

    mode = "test_double"
    calls = 0
    usage = {}

    def __init__(self, outputs):
        self.outputs = iter(outputs)

    def complete(self, task):
        self.calls += 1
        return next(self.outputs)


class AnnotationTests(unittest.TestCase):
    def setUp(self):
        self.p = {
            "id": "s1:0:20",
            "source_id": "s1",
            "start": 0,
            "end": 20,
            "text": "Nonprofits may apply",
        }
        self.valid = {
            "passage_id": self.p["id"],
            "quote": "Nonprofits may apply",
            "relation": "support",
            "rationale": "The rule explicitly permits nonprofit applicants.",
        }

    def test_exact_span_and_label(self):
        accepted, rejected = validate_annotations({"evidence": [self.valid]}, [self.p], "c1")
        self.assertEqual(rejected, [])
        self.assertEqual(accepted[0]["start"], 0)
        self.assertEqual(accepted[0]["quote"], self.p["text"])
        self.assertEqual(accepted[0]["review"], "unreviewed")

    def test_fabricated_quote_and_id_rejected(self):
        for patch in [
            {"quote": "Invented fact"},
            {"passage_id": "bad"},
            {"quote": ""},
            {"relation": "certain"},
        ]:
            a, r = validate_annotations({"evidence": [{**self.valid, **patch}]}, [self.p], "c1")
            self.assertEqual(a, [])
            self.assertEqual(len(r), 1)

    def test_rejects_wrong_envelope_and_duplicate_annotations(self):
        for value in [{}, {"evidence": "not-list"}, {"evidence": [None]}]:
            a, r = validate_annotations(value, [self.p], "c1")
            self.assertEqual(a, [])
            self.assertTrue(r)
        a, r = validate_annotations({"evidence": [self.valid, self.valid]}, [self.p], "c1")
        self.assertEqual(len(a), 1)
        self.assertEqual(len(r), 1)

    def test_conflicts_visible_without_resolving_truth(self):
        evidence = [
            {"relation": x, "source_id": f"s{i}", "review": "unreviewed"} for i, x in enumerate(["support", "oppose"])
        ]
        sources = [
            {"id": "s0", "content_group": "a", "publisher": "Same"},
            {"id": "s1", "content_group": "b", "publisher": "Same"},
        ]
        summary = summarize(evidence, sources)
        self.assertTrue(summary["potential_conflict"])
        self.assertEqual(summary["human_accepted"], 0)
        self.assertEqual(summary["publisher_groups"], 1)
        self.assertNotIn("confidence", summary)

    def test_empty_evidence_is_missing_not_false(self):
        summary = summarize([], [])
        self.assertEqual(summary["coverage"], "missing")
        self.assertFalse(summary["potential_conflict"])

    def test_full_pipeline_records_rejected_and_unreviewed_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "s.txt").write_text("Nonprofits may apply")
            p = root / "case.json"
            p.write_text(
                json.dumps(
                    {
                        "question": "Can nonprofits apply?",
                        "claims": ["Nonprofits may apply"],
                        "sources": [
                            {
                                "id": "s1",
                                "title": "Rules",
                                "publisher": "Council",
                                "kind": "primary",
                                "path": "s.txt",
                            }
                        ],
                    }
                )
            )
            provider = ScriptedProvider([{"evidence": [self.valid, {**self.valid, "quote": "made up"}]}])
            report = build(p, provider=provider)
            self.assertEqual(report["mode"], "test_double")
            self.assertEqual(len(report["claims"][0]["evidence"]), 1)
            self.assertEqual(len(report["claims"][0]["rejected"]), 1)
            self.assertEqual(report["decision"], "human_review_required")
            self.assertEqual(
                report["bundle_digest"],
                digest({k: v for k, v in report.items() if k != "bundle_digest"}),
            )

    def test_ai_plan_then_annotation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "s.txt").write_text("Nonprofits may apply")
            p = root / "case.json"
            p.write_text(
                json.dumps(
                    {
                        "question": "Who can apply?",
                        "sources": [
                            {
                                "id": "s1",
                                "title": "Rules",
                                "publisher": "Council",
                                "kind": "primary",
                                "path": "s.txt",
                            }
                        ],
                    }
                )
            )
            provider = ScriptedProvider([{"claims": ["Nonprofits may apply"]}, {"evidence": [self.valid]}])
            report = build(p, provider=provider)
            self.assertEqual(provider.calls, 2)
            self.assertEqual(report["claims"][0]["origin"], "model_proposal")


if __name__ == "__main__":
    unittest.main()


class PlanningRegressionTests(unittest.TestCase):
    def test_model_must_not_repeat_decision_options_as_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "s.txt").write_text("Nonprofits may apply")
            p = root / "case.json"
            p.write_text(
                json.dumps(
                    {
                        "question": "Can we apply?",
                        "options": ["Apply now"],
                        "sources": [
                            {"id": "s1", "title": "Rules", "publisher": "Council", "kind": "primary", "path": "s.txt"}
                        ],
                    }
                )
            )
            report = build(p, provider=ScriptedProvider([{"claims": ["Apply now"]}]))
            self.assertEqual(report["workflow_status"], "partial")
            self.assertEqual(report["claims"], [])
            self.assertIn("decision option", report["errors"][0])

    def test_normative_model_plan_abstains_instead_of_auto_researching(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "s.txt").write_text("Nonprofits may apply")
            p = root / "case.json"
            p.write_text(
                json.dumps(
                    {
                        "question": "Can we apply?",
                        "sources": [
                            {"id": "s1", "title": "Rules", "publisher": "Council", "kind": "primary", "path": "s.txt"}
                        ],
                    }
                )
            )
            provider = ScriptedProvider([{"claims": ["Nonprofits should request clarification first"]}])
            report = build(p, provider=provider)
            self.assertEqual(report["workflow_status"], "partial")
            self.assertEqual(provider.calls, 1)
            self.assertEqual(report["claims"], [])
            self.assertIn("recommendation", report["errors"][0])
