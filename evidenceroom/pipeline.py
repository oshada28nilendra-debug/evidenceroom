"""Bounded workflow; model suggestions never become verified facts automatically."""

import re
from datetime import datetime, timezone
from pathlib import Path

from .core import Error, digest, ingest, load_case, text
from .retrieval import rank

RELATIONS = {"support", "oppose", "context", "inference"}


def validate_annotations(output, passages, claim_id):
    accepted, rejected, seen = [], [], set()
    evidence = output.get("evidence") if isinstance(output, dict) else None
    if not isinstance(evidence, list) or len(evidence) > 6:
        return [], [{"reason": "Expected evidence list of at most 6 entries"}]
    lookup = {p["id"]: p for p in passages}
    for i, item in enumerate(evidence):
        try:
            if not isinstance(item, dict):
                raise Error("Evidence entry must be an object")
            pid = text(item.get("passage_id"), "passage ID", 100)
            if pid not in lookup:
                raise Error("Unknown passage ID")
            p = lookup[pid]
            quote = text(item.get("quote"), "quote", 1600)
            if quote not in p["text"]:
                raise Error("Quote does not occur verbatim in the cited passage")
            relation = item.get("relation")
            if relation not in RELATIONS:
                raise Error("Unknown relation")
            rationale = text(item.get("rationale"), "rationale", 1000)
            key = (pid, quote, relation)
            if key in seen:
                raise Error("Duplicate annotation")
            seen.add(key)
            start = p["start"] + p["text"].index(quote)
            accepted.append(
                {
                    "id": f"{claim_id}-e{i + 1}",
                    "source_id": p["source_id"],
                    "passage_id": pid,
                    "quote": quote,
                    "start": start,
                    "end": start + len(quote),
                    "relation": relation,
                    "rationale": rationale,
                    "review": "unreviewed",
                    "origin": "model_interpretation",
                }
            )
        except (Error, TypeError) as exc:
            # Keep bounded rejected records for audit without treating them as facts.
            rejected.append(
                {
                    "index": i,
                    "reason": str(exc)[:300],
                    "proposal": item,
                }
            )
    return accepted, rejected


def summarize(evidence, sources):
    relevant = [e for e in evidence if e["review"] != "rejected"]
    relations = {e["relation"] for e in relevant}
    ids = {e["source_id"] for e in relevant}
    chosen = [s for s in sources if s["id"] in ids]
    return {
        "coverage": (
            "support_or_opposition_proposed"
            if relations & {"support", "oppose"}
            else "context_or_inference_only"
            if relevant
            else "missing"
        ),
        "potential_conflict": {"support", "oppose"} <= relations,
        "human_accepted": sum(e["review"] == "accepted" for e in relevant),
        "unreviewed": sum(e["review"] == "unreviewed" for e in relevant),
        "content_groups": len({s["content_group"] for s in chosen}),
        "publisher_groups": len({s["publisher"].strip().casefold() for s in chosen}),
        "notice": "Counts and quote matches are provenance signals, not factual confidence or proof of entailment.",
    }


def build(case_path, provider=None, fetcher=None):
    case_path = Path(case_path)
    case = load_case(case_path)
    sources = ingest(case, case_path.parent, fetcher)
    report = {
        "schema_version": 1,
        "question": case["question"],
        "options": case["options"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": provider.mode if provider else "offline_retrieval",
        "sources": sources,
        "claims": [],
        "warnings": [],
        "errors": [],
        "decision": "human_review_required",
    }
    if any(s["duplicate_of"] for s in sources):
        report["warnings"].append("Identical source content detected; duplicates are not independent corroboration.")
    publishers = [s["publisher"].strip().casefold() for s in sources]
    if len(set(publishers)) < len(publishers):
        report["warnings"].append("Some sources share a declared publisher; independence is not established.")
    report["warnings"].append(
        "Source kind, publisher and publication date are user declarations, not independently verified."
    )
    report["warnings"].append(
        "Dates can differ; opposing passages may describe different versions or scopes. Resolve manually."
    )
    claims = case["claims"]
    origin = "user_input"
    if not claims and provider:
        try:
            planned = provider.complete(
                {
                    "task": "plan",
                    "question": case["question"],
                    "options": case["options"],
                    "schema": {
                        "type": "object",
                        "properties": {
                            "claims": {"type": "array", "minItems": 1, "maxItems": 8, "items": {"type": "string"}}
                        },
                    },
                    "instruction": "Break the question into 1–8 factual propositions that sources could support or oppose. Do not repeat decision options, commands, recommendations or questions. Example: Nonprofits are eligible, not Apply now. These are hypotheses, not assumed facts.",
                }
            )
            report["plan_proposal"] = planned.get("claims")
            claims = planned.get("claims")
            if not isinstance(claims, list) or not 1 <= len(claims) <= 8:
                raise Error("Model plan needs 1–8 claims")
            claims = [text(c, "planned claim", 500) for c in claims]
            if any(c.casefold() in {o.casefold() for o in case["options"]} for c in claims):
                raise Error("Model repeated a decision option instead of proposing a verifiable claim")
            if any(re.search(r"\b(?:should|ought|recommend)\b", c, re.I) or c.endswith("?") for c in claims):
                raise Error("Model plan contains a recommendation or question; supply reviewed factual claims")
            origin = "model_proposal"
        except Error as exc:
            report["errors"].append(str(exc))
            claims = []
    elif not claims:
        raise Error("Offline mode requires explicit claims in the case")
    for i, claim in enumerate(claims):
        cid = f"c{i + 1}"
        passages = rank(claim, sources)
        row = {
            "id": cid,
            "text": claim,
            "origin": origin,
            "passages": passages,
            "evidence": [],
            "rejected": [],
        }
        if provider and passages:
            try:
                output = provider.complete(
                    {
                        "task": "annotate",
                        "question": case["question"],
                        "claim": claim,
                        "passages": passages,
                        "schema": {
                            "type": "object",
                            "required": ["evidence"],
                            "properties": {
                                "evidence": {
                                    "type": "array",
                                    "maxItems": 6,
                                    "items": {
                                        "type": "object",
                                        "required": ["passage_id", "quote", "relation", "rationale"],
                                        "properties": {
                                            "passage_id": {"type": "string", "enum": [p["id"] for p in passages]},
                                            "quote": {
                                                "type": "string",
                                                "description": "Exact contiguous substring of the referenced passage",
                                            },
                                            "relation": {"type": "string", "enum": sorted(RELATIONS)},
                                            "rationale": {
                                                "type": "string",
                                                "description": "Explain the relationship to this specific claim",
                                            },
                                        },
                                    },
                                }
                            },
                        },
                        "instruction": "Find supporting AND opposing evidence; do not choose a winner. No evidence means empty evidence list.",
                    }
                )
                row["evidence"], row["rejected"] = validate_annotations(output, passages, cid)
            except Error as exc:
                report["errors"].append(f"{cid}: {exc}")
        elif not provider:
            row["evidence"] = [
                {
                    "id": f"{cid}-e{n + 1}",
                    "source_id": p["source_id"],
                    "passage_id": p["id"],
                    "quote": p["text"],
                    "start": p["start"],
                    "end": p["end"],
                    "relation": "context",
                    "rationale": "Lexical retrieval only; no semantic claim verification performed.",
                    "review": "unreviewed",
                    "origin": "lexical_retrieval",
                }
                for n, p in enumerate(passages)
            ]
        row["summary"] = summarize(row["evidence"], sources)
        report["claims"].append(row)
    report["model"] = {"calls": provider.calls, "usage": provider.usage} if provider else {"calls": 0, "usage": {}}
    report["workflow_status"] = "partial" if report["errors"] else "review_ready"
    report["bundle_digest"] = digest(report)
    return report
