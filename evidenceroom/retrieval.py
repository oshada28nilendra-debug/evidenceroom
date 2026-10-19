"""Small deterministic BM25 baseline. Scores rank lexical relevance, not truth."""

import math
import re
from collections import Counter

STOP = set("a an the is are was were to of for in on and or we can should be it this that with".split())


def tokens(s):
    return [w for w in re.findall(r"\w+", s.casefold()) if w not in STOP]


def rank(claim, sources, limit=3):
    docs = []
    for source in sources:
        # Content-identical sources cannot occupy multiple retrieval slots.
        if source["duplicate_of"]:
            continue
        for m in re.finditer(r"[^\n]+", source["text"]):
            start = m.start()
            while start < m.end():
                end = min(start + 1600, m.end())
                body = source["text"][start:end]
                docs.append(
                    {
                        "id": f"{source['id']}:{start}:{end}",
                        "source_id": source["id"],
                        "start": start,
                        "end": end,
                        "text": body,
                        "_words": Counter(tokens(body)),
                    }
                )
                start = end
    if not docs:
        return []
    avg = sum(sum(d["_words"].values()) for d in docs) / len(docs) or 1
    query = set(tokens(claim))
    df = {w: sum(w in d["_words"] for d in docs) for w in query}
    for d in docs:
        length = sum(d["_words"].values())
        d["score"] = round(
            sum(
                math.log(1 + (len(docs) - df[w] + 0.5) / (df[w] + 0.5))
                * (d["_words"][w] * 2.2)
                / (d["_words"][w] + 1.2 * (0.25 + 0.75 * length / avg))
                for w in query
                if d["_words"][w]
            ),
            6,
        )
        del d["_words"]
    kinds = {s["id"]: s.get("declared_kind", "unknown") for s in sources}
    ordered = sorted(
        [d for d in docs if d["score"] > 0], key=lambda d: (kinds[d["source_id"]] != "primary", -d["score"], d["id"])
    )
    diverse, rest, used = [], [], set()
    for passage in ordered:
        if passage["source_id"] not in used:
            diverse.append(passage)
            used.add(passage["source_id"])
        else:
            rest.append(passage)
    return (diverse + rest)[:limit]
