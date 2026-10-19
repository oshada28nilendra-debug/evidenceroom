# EvidenceRoom Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver a portable claim/evidence decision audit with strict provenance and human review.
**Architecture:** Separate ingestion, retrieval, model HTTP, annotation validation and reporting. Deterministic gates constrain model output; source/model content has no tools or execution privileges.
**Tech Stack:** Python >=3.11, standard library; Ruff as optional development tooling.
**Spec:** docs/superpowers/specs/2026-10-18-evidenceroom-design.md

## Global constraints

12 sources; 8 claims; 40,000 chars/source and 160,000 total; 512 KB fetch; 3 passages/claim <=1600 chars; <=9 model calls, <=2048 completion tokens, <=120 seconds/request; no paid API without opt-in. Fresh output directory only. No repository designated.

## Review focus

- A real quotation can fail to support its claim: label model interpretation and retain human review.
- DNS names may resolve privately or rebind: validate all addresses and pin the connection; reject redirects.
- Paths can escape a case directory: reject traversal and symlinks.
- Identical documents can inflate corroboration: group by content hash and flag common publisher.
- Reports can execute untrusted HTML/Markdown: escape HTML; do not use raw source HTML.

## Task 1 — source records and retrieval

Files: tests/test_core.py, evidenceroom/core.py, evidenceroom/retrieval.py.
- [x] Write tests for bounded case loading, source hashes, safe paths, HTML extraction, BM25 relevance and duplicate grouping.
- [x] Run unittest; confirm missing behavior fails.
- [x] Implement load_case(path), ingest(case, root, fetcher), rank(claim, sources).
- [x] Run tests; inspect paragraph offsets.

## Task 2 — model and deterministic evidence gates

Files: tests/test_pipeline.py, tests/test_transport.py, evidenceroom/provider.py, evidenceroom/pipeline.py, evidenceroom/network.py.
- [x] Test exact-quote/ID rejection, conflicts, unknown relations, inference labels, no-evidence abstention and request budgets.
- [x] Test real simulated HTTP serialization, redirects, malformed/auth responses, private URLs and public DNS pinning boundary.
- [x] Observe failures, then implement CompatibleProvider.complete(messages), fetch_https(url, allowed_hosts), build(case_path, provider=None, fetcher=None).
- [x] Run suite and explicitly label simulated integration separately from live behavior.

## Task 3 — exports, human review and delivery

Files: tests/test_cli.py, evidenceroom/report.py, evidenceroom/cli.py, README.md, SECURITY.md, .github/workflows/ci.yml.
- [x] Test offline CLI E2E, invalid input, immutable evidence output, digest-bound review and escaped HTML.
- [x] Observe failures, then implement report export and run/discover/review/verify commands.
- [x] Run actual offline demo and public integrations, inspect exported outputs; attempt live model only without paid credentials.
- [x] Run tests, lint/format, compile, wheel/install smoke, secret scan; package with actual ledger and verification logs.
