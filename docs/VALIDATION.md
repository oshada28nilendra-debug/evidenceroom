# Validation decision — 18 October 2026

**Target user:** analysts, researchers and small organizations preparing a decision from a modest set of competing documents.
**Pain point:** a polished research report can hide unsupported links between sources, claims and recommendations. Checking each claim against the original passage is slow.
**Evidence:** [HiEviDR-Bench, 27 July 2026](https://arxiv.org/abs/2607.25151) explicitly studies evidence-to-claim traceability and reports weaknesses in intermediate claim construction. [DRACO, 12 February 2026](https://arxiv.org/abs/2602.11685) evaluates accuracy, completeness, objectivity and citation quality on complex research tasks. These motivate auditability; they do not establish demand for this product or its effectiveness.

## Alternatives inspected

| Alternative | Documented capability | Positioning of this release |
| --- | --- | --- |
| [GPT Researcher](https://github.com/assafelovic/gpt-researcher) | Web/local research, planner/execution flows, reports with citations; Apache-2.0 | Smaller explicit claim/evidence records with exact passage validation and human review rather than a general research platform |
| [Stanford STORM/Co-STORM](https://github.com/stanford-oval/storm) | Perspective-driven knowledge curation, cited articles and collaborative discourse; MIT | A bounded decision audit, not long-form article generation |
| [Open Deep Research](https://github.com/langchain-ai/open_deep_research) | Configurable LangGraph research agent, search/model/MCP integrations; MIT | No orchestration framework required; a portable review bundle and deterministic integrity checks |

These products may support comparable auditing through extensions. We do not claim they lack all evidence checking, or that our approach is unprecedented. No competitor code is reused.

**Gap (hypothesis):** a small, local-first tool whose default deliverable is an inspectable claim matrix and review queue may be easier to fork for small decision processes than adopting an entire research stack.
**Differentiator:** exact passage offsets plus source hashes; rejected citations retained; content/publisher duplication warnings; unresolved opposing evidence; explicit human acceptance/rejection; no numeric confidence masquerading as truth.
**Feasibility:** deterministic ingestion/retrieval/validation/review works without a model. A genuine compatible HTTP adapter supplies claim planning and passage interpretation. Network source collection is opt-in and constrained; no paid API is called automatically.
**Risks:** exact quote existence does not establish entailment, source quality or truth; duplicate grouping can under/overestimate independence; small local models may fail structured output; source selection bias remains.
**Decision:** narrow and proceed. Build a source-pack decision audit with opt-in public HTTPS fetching and Crossref discovery, not unrestricted autonomous web research or a swarm. General-purpose search crawling, PDF/OCR, SaaS and automatic truth certification are deferred.
