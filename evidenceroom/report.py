"""Deterministic integrity checks, digest-bound review, and inert exports."""

import copy
import hashlib
import html
import json
from pathlib import Path

from .core import Error, digest, text
from .pipeline import RELATIONS, summarize


def verify_bundle(bundle):
    if not isinstance(bundle, dict) or bundle.get("schema_version") != 1:
        raise Error("Unsupported bundle schema")
    required = {
        "question",
        "options",
        "created_at",
        "mode",
        "sources",
        "claims",
        "warnings",
        "errors",
        "decision",
        "model",
        "workflow_status",
        "bundle_digest",
    }
    if (
        not required <= bundle.keys()
        or not isinstance(bundle.get("sources"), list)
        or not 1 <= len(bundle["sources"]) <= 12
        or not isinstance(bundle.get("claims"), list)
        or len(bundle["claims"]) > 8
        or not isinstance(bundle.get("question"), str)
        or not isinstance(bundle.get("options"), list)
        or not isinstance(bundle.get("warnings"), list)
        or not isinstance(bundle.get("errors"), list)
        or not isinstance(bundle.get("model"), dict)
    ):
        raise Error("Incomplete or malformed audit bundle")
    for key in ("question", "created_at", "mode", "decision", "workflow_status", "bundle_digest"):
        text(bundle.get(key), "bundle " + key, 2000)
    for key in ("options", "warnings", "errors"):
        if any(not isinstance(item, str) for item in bundle[key]):
            raise Error("Bundle reporting lists must contain strings")
    expected = digest({k: v for k, v in bundle.items() if k != "bundle_digest"})
    if bundle.get("bundle_digest") != expected:
        raise Error("Bundle digest mismatch")
    try:
        sources = {s["id"]: s for s in bundle["sources"]}
        if len(sources) != len(bundle["sources"]):
            raise Error("Duplicate source IDs")
        for s in sources.values():
            for key in ("id", "text", "title", "publisher", "location", "declared_kind", "sha256", "content_group"):
                if not isinstance(s.get(key), str):
                    raise Error("Malformed source reporting field")
            if (
                s["content_group"] != s["sha256"]
                or s.get("published") is not None
                and not isinstance(s["published"], str)
            ):
                raise Error("Malformed source provenance")
            if hashlib.sha256(s["text"].encode()).hexdigest() != s["sha256"]:
                raise Error("Source text hash mismatch")
        ids = set()
        for c in bundle["claims"]:
            if (
                not isinstance(c, dict)
                or not isinstance(c.get("text"), str)
                or not isinstance(c.get("origin"), str)
                or not isinstance(c.get("id"), str)
                or not isinstance(c.get("rejected"), list)
                or not isinstance(c.get("evidence"), list)
                or c.get("summary") != summarize(c["evidence"], bundle["sources"])
            ):
                raise Error("Malformed claim records or inconsistent summary")
            for e in c["evidence"]:
                s = sources[e["source_id"]]
                if (
                    type(e["start"]) is not int
                    or type(e["end"]) is not int
                    or not 0 <= e["start"] < e["end"] <= len(s["text"])
                    or s["text"][e["start"] : e["end"]] != e["quote"]
                    or e["id"] in ids
                    or e["relation"] not in RELATIONS
                    or e["review"] not in {"accepted", "rejected", "unreviewed"}
                ):
                    raise Error("Invalid evidence span, ID or label")
                ids.add(e["id"])
    except (KeyError, TypeError, AttributeError):
        raise Error("Malformed bundle records") from None
    return True


def review_bundle(bundle, decisions):
    verify_bundle(bundle)
    if not isinstance(decisions, dict) or decisions.get("bundle_digest") != bundle["bundle_digest"]:
        raise Error("Review must name the exact input bundle digest")
    reviewer = text(decisions.get("reviewer"), "reviewer", 100)
    items = decisions.get("decisions")
    if not isinstance(items, list) or not items or len(items) > 48:
        raise Error("Provide 1–48 review decisions")
    updated = copy.deepcopy(bundle)
    lookup = {e["id"]: e for c in updated["claims"] for e in c["evidence"]}
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            raise Error("Invalid review entry")
        eid = item.get("evidence_id")
        if not isinstance(eid, str) or eid not in lookup or eid in seen:
            raise Error("Unknown or duplicate review evidence ID")
        seen.add(eid)
        if not isinstance(item.get("decision"), str) or item.get("decision") not in {"accept", "reject"}:
            raise Error("Review decision must be accept or reject")
        e = lookup[eid]
        relation = item.get("relation", e["relation"])
        if not isinstance(relation, str) or relation not in RELATIONS:
            raise Error("Invalid reviewed relation")
        note = text(item.get("note"), "review note", 1000)
        e.setdefault("original_relation", e["relation"])
        e.update(
            {
                "relation": relation,
                "review": "accepted" if item["decision"] == "accept" else "rejected",
                "reviewer": reviewer,
                "review_note": note,
            }
        )
    for c in updated["claims"]:
        c["summary"] = summarize(c["evidence"], updated["sources"])
    updated["parent_bundle_digest"] = bundle["bundle_digest"]
    updated.setdefault("review_history", []).append(decisions)
    updated.pop("bundle_digest")
    updated["bundle_digest"] = digest(updated)
    return updated


def report_lines(b):
    lines = [
        "EvidenceRoom decision audit",
        b["question"],
        "",
        f"Mode: {b['mode']}",
        "Decision: human review required. This report does not establish truth or make the decision.",
        "Quote matching verifies text existence only; support/opposition are interpretations.",
        f"Options under consideration: {', '.join(b['options']) or 'none supplied'}",
        "",
    ]
    lines += ["LIMITATION: " + w for w in b["warnings"]]
    lines += ["BLOCKER: " + e for e in b["errors"]]
    source_map = {s["id"]: s for s in b["sources"]}
    for c in b["claims"]:
        lines += [
            "",
            f"CLAIM {c['id']} ({c['origin']}): {c['text']}",
            f"Coverage: {c['summary']['coverage']}; potential conflict: {c['summary']['potential_conflict']}; "
            f"human accepted: {c['summary']['human_accepted']}; unreviewed: {c['summary']['unreviewed']}",
        ]
        if c["summary"]["potential_conflict"]:
            lines.append("ACTION: resolve opposing interpretations and check source dates/scope; do not majority-vote.")
        if not c["evidence"]:
            lines.append("MISSING: find additional evidence or narrow this claim; absence is not disproof.")
        for e in c["evidence"]:
            s = source_map[e["source_id"]]
            lines += [
                f"[{e['id']}] {e['relation'].upper()} — {e['review']} — {e['origin']}",
                f"Source {s['id']}: {s['title']} | {s['location']} | published: {s['published'] or 'unknown'}",
                f"Exact normalized-text span {e['start']}:{e['end']}: {e['quote']}",
                f"Interpretation: {e['rationale']}",
            ]
            if e.get("review_note"):
                lines.append(f"Review: {e['reviewer']}: {e['review_note']}")
        lines += [f"REJECTED proposal {r.get('index', '?')}: {r['reason']}" for r in c["rejected"]]
    lines += ["", "SOURCE PROVENANCE"]
    for s in b["sources"]:
        lines += [
            f"{s['id']}: {s['title']}; declared kind={s['declared_kind']}; publisher={s['publisher']}; "
            f"sha256={s['sha256']}; duplicate_of={s['duplicate_of'] or 'none'}"
        ]
    lines += [
        "",
        "Suggested next steps: review quote relevance, source authority, temporal scope and missing claims.",
        "A human-accepted annotation is a recorded reviewer assertion, not independent factual certification.",
        f"Bundle digest: {b['bundle_digest']}",
    ]
    return lines


def render_html(bundle):
    paragraphs = "\n".join("<p>" + html.escape(line) + "</p>" for line in report_lines(bundle))
    return (
        """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>EvidenceRoom decision audit</title><style>
body{max-width:980px;margin:40px auto;padding:0 24px;font:16px/1.6 system-ui;background:#f8f6f0;color:#202521}
p{white-space:pre-wrap;overflow-wrap:anywhere;border-bottom:1px solid #deded5;padding-bottom:8px}
p:first-child{font-size:32px;font-weight:bold}p:nth-child(2){font-size:22px}
</style><main>"""
        + paragraphs
        + "</main></html>\n"
    )


def export_bundle(bundle, out):
    verify_bundle(bundle)
    out = Path(out)
    # mkdir without exist_ok prevents accidental overwrite, including existing symlinks.
    out.mkdir(parents=True, exist_ok=False)
    (out / "bundle.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "report.html").write_text(render_html(bundle), encoding="utf-8")

    # Escape HTML, Markdown links/autolinks and formatting metacharacters in untrusted text.
    def escape_md(line):
        line = html.escape(line, quote=False)
        for char in "\\`*_{}[]()#+!|":
            line = line.replace(char, "\\" + char)
        return line

    (out / "report.md").write_text(
        "\n\n".join(escape_md(line) for line in report_lines(bundle)) + "\n",
        encoding="utf-8",
    )
    template = {
        "bundle_digest": bundle["bundle_digest"],
        "reviewer": "YOUR NAME",
        "decisions": [
            {
                "evidence_id": e["id"],
                "decision": "reject",
                "note": "Replace this example after inspecting source and claim.",
            }
            for c in bundle["claims"]
            for e in c["evidence"]
        ][:1],
    }
    (out / "review-template.json").write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
