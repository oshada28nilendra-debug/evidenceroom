# Verification — 18 October 2026

## Latest result — GitHub publication verified, 19 October

Bounded release status: **verified, PR #1 open for user review/merge**. Implementation commit `2ea1d8b4eecab736fab6c951f1a9029cde7c41d4` is published on `feat/evidenceroom-first-release`. Its tree hash exactly matches the prepared local release. The follow-up evidence/documentation commit does not change implementation behavior.

- [Ordinary CI](https://github.com/oshada28nilendra-debug/evidenceroom/actions/runs/39179015402): 39 tests passed, zero skips, on each of Python 3.11/3.12/3.13; lint, formatting, compilation, installation and the offline CLI audit/verify flow passed. All three decoded job logs were inspected.
- [Real local-model CI](https://github.com/oshada28nilendra-debug/evidenceroom/actions/runs/39179015444): checksum-pinned llama.cpp b11718 and Qwen3-1.7B Q8_0 passed the fixture gate, with 4 actual requests, 2322 prompt tokens and 642 completion tokens. The downloaded artifact's SHA-256 matched the GitHub digest. Its actual bundle, quotes, original 10000/later 12000 support/opposition and remaining context-only claim were inspected; the local bundle integrity command also passed. No paid model API/key was used.
- [Public source integrations](https://github.com/oshada28nilendra-debug/evidenceroom/actions/runs/39179015431): actual pinned-address HTTPS fetch of `https://www.python.org/` returned 51,765 HTML bytes; actual Crossref discovery returned five bibliographic candidates. The decoded log's metadata/hash report was inspected. These previously blocked integrations are now verified for these requests, not all websites or research questions.

Machine-readable run evidence: `delivery/github-verification.json`. Actual downloaded model artifacts are retained under `delivery/github-live-model/`; source snapshots and JSON/HTML/Markdown reports are present. A clean local Gitleaks scan preceded publication. Automatic planning remains experimental; supplied reviewed factual claims remain the supported release path. This is not a general efficacy, complete-security or production-readiness claim.

The user explicitly permitted publication after changing email privacy on 19 October. These API-created commits use the account email in public commit metadata. Earlier noreply-only local bundle commits were not the remote implementation commits. No history rewrite or automatic merge was performed.

## Historical archive-stage records

## Publication continuation — designated repository

The user designated `oshada28nilendra-debug/evidenceroom` on 18 October. The repository had only its initial README, with no license or AGENTS instructions. The archived implementation and evidence were restored on `feat/evidenceroom-first-release`; commits use the verified GitHub noreply address. Hosted CI and PR results are pending this first publication. A separate public-integration workflow now exercises actual public TLS source fetching and Crossref discovery; the real-model workflow also runs for same-repository implementation PRs. Earlier archive-stage blocker statements below describe the historical checkpoint, not current repository authorization.

**Status: working local source-pack release delivered; public retrieval and GitHub
publication/CI remain blocked. Automatic claim planning is experimental and failed
our semantic-quality check; it now abstains on the observed normative plans.**

## Supported path actually executed

A question plus reviewed factual claims and local text/HTML sources → lexical
retrieval → real local model interpretation → exact quotation validation → cited
audit → explicit human accept/reject review. JSON, Markdown and inert HTML were
produced and inspected. No paid API key, hosted inference API or Docker is used.

`delivery/offline-final/` demonstrates zero-model retrieval; all candidate passages
remain unreviewed context. `delivery/reviewed-final/` records two authored human
decisions identifying the conflicting fictional award limits. These are synthetic
fixtures, not real grants or measured decision-making accuracy.

## Automated/local checks

- **39 unittest cases passed, zero skips**, including the primary CLI subprocess
  flow, case/source budgets, traversal/symlink rejection, exact offsets, fabricated
  citation rejection, duplicate/source priority handling, digest-bound review,
  HTML escaping and malformed input.
- Real local simulated HTTP servers test compatible request serialization,
  provider usage/errors, redirects and malformed response handling. Scripted
  providers are explicitly `test_double`, not real model evidence.
- Real simulated-server regressions trickle body bytes and headers beyond a
  1-second request limit. They now fail at the absolute I/O deadline. System DNS
  resolution is explicitly outside that portable deadline.
- Public-DNS/private-IP and response-type/size tests use controlled boundaries;
  they do **not** establish actual internet TLS/source collection behavior.
- Ruff lint/format, compilation and wheel build passed. The wheel was installed
  to an isolated target and `python -m evidenceroom --help` ran from `/tmp`.
- Gitleaks 8.30.1 scanned the current project with redacted output and detected no
  credentials. This is pattern-based checking of this package, not an account audit.

Commands, return codes, Python version and logs: `delivery/verification.json`,
`delivery/tests.txt`, `delivery/lint.txt`, `delivery/format.txt`,
`delivery/compile.txt`, `delivery/wheel.txt`, `delivery/wheel-install.txt`,
`delivery/installed-cli.txt`, `delivery/secret_scan.txt`.
Implementation/test/workflow hashes: `delivery/implementation-sha256.json`.

## Actual local-model integration

Runtime: official **llama.cpp b11718**, CPU threads=4, context=8192, parallel=1,
loopback binding, reasoning budget=0. Its release archive SHA-256 was checked
against the official GitHub asset digest before extraction:
`99f83b15cea9a4fb8945516c276b5f42b11608f82104fc6fa98a541cac826de7`.

Final model: official **Qwen/Qwen3-1.7B-GGUF Q8_0** (Apache-2.0 as declared in the
model metadata), revision `90862c4b9d2787eaed51d12237eafdfe7c5f6077`.
Model SHA-256:
`061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a`.
Weights and runtime are not included in the source package.
See `delivery/provenance-1.7b.json` and
https://huggingface.co/Qwen/Qwen3-1.7B-GGUF .

Final supplied-claims run: **4 real inference requests, 2322 prompt tokens, 642
completion tokens**, CLI exit 0. Exact quotes passed the gate. The model proposed
support for eligibility and deadline, support for the original 10000 award limit,
and opposition from the later 12000 FAQ. The audited-accounts claim had context
only, not proposed direct support. The original/FAQ quotations and their relations
were inspected manually. Its context rationale on the missing claim drifted to the
overall question: a remaining quality limitation, not hidden success.

Evidence: `delivery/live-model-final/`, `delivery/live-model-final-cli.txt`,
`delivery/final-model-server.log`, and `delivery/live-fixture-gate.json`.
All model evidence remains **unreviewed** in product output; integration inspection
does not automatically impersonate a product reviewer or certify facts.

### Automatic planning limitation and fail-closed behavior

The small models proposed repetitive/normative statements instead of a consistently
good factual claim decomposition. The final planner run made **1 real inference
request, 353 prompt tokens and 112 completion tokens**, then exited 3 with
`Model plan contains a recommendation or question; supply reviewed factual claims`.
No downstream annotation requests were made. The rejected proposal and actual
usage remain in `delivery/live-plan-final/`. This validates honest abstention and
the adapter boundary, **not successful autonomous research planning**. Use supplied,
reviewed claims for this release; a stronger model needs separate evaluation.

### Historical attempts retained

- `live-model-attempt-1` and `live-model-attempt-2`: connection failures against an
  isolated server setup; zero output tokens. These were not inference successes.
- `live-model-attempt-3`: actual Qwen3-0.6B inference identified the award conflict
  but several IDs copied a literal schema placeholder; rejected by the gate.
- `live-model-attempt-4`: actual 0.6B inference after schema changes produced valid
  quotations but inconsistent semantic labels. Not a quality pass.
- `live-plan-attempt-1`/`live-plan-attempt-2`: actual 0.6B planning proposed decision
  options or normative claims; prompted the stricter fail-closed planning gates.
- `live-model-1.7b-attempt-1` and `live-plan-1.7b-attempt-1`: actual larger-model
  comparison confirmed the useful supplied-claims path and weak planning quality.
- `live-model-final`/`live-plan-final`: final implementation outcomes above.

Historical development bundles may not pass the final stricter summary/schema
validator; they retain original outputs rather than being rewritten to look better.
There is no real-issue benchmark, accuracy rate, comparative superiority result,
independently calibrated judge or adoption study.

## Public integrations and publication blockers

Actual Crossref discovery and public HTTPS source fetch were attempted and failed
with `Invalid or unresolved public source URL`. The environment resolver could not
resolve the configured public hosts for the pinned-address transport. No fallback
through a less constrained proxy was used. Logs: `delivery/public-fetch-attempt.json`
and `delivery/crossref-attempt-stderr.txt`. Public discovery/fetch is implemented
and simulated boundaries pass, but **live internet integration is unverified**.

No EvidenceRoom repository was designated. No GitHub commit, branch, PR, hosted CI
or deployment exists for this delivery. Ordinary Python 3.11/3.12/3.13 CI and a
separate manual pinned-runtime live-model workflow are included, but neither was
run on GitHub. `scripts/live_smoke.py` provides the authored live-fixture gate.
The helper was separately executed locally and passed the strict gate: 4 additional
real inference requests, 2322 prompt tokens and 642 completion tokens. Its process
was shut down afterward. Evidence: `delivery/standalone-smoke/` and
`delivery/standalone-smoke-cli.txt`. This does not imply hosted CI has run.

Suggested destination: `oshada28nilendra-debug/evidenceroom`, branch
`feat/evidenceroom-first-release`. Follow `docs/HANDOFF.md` after designation,
verify real public retrieval with normal DNS/egress, inspect CI, and open a PR.

## Continuity and review

The actual IssueForge merged-main ledger, README and verification record were
read at `27f4e888010afaddff648031d08a8f9c89be83e8`; their hashes are in
`delivery/continuity.json`. Its ledger's stale open-PR state was corrected in this
package's batch ledger using the observed merge and previously inspected CI.
IssueForge was not rebuilt. This project occupies `2026-10-18-afternoon`;
DataRescue remains the next brief, and the remaining batch slots are preserved.

Independent code review reproduced two medium issues, and its fix-pass found no
remaining high/medium release blocker; see `docs/REVIEW.md`. This is a bounded
engineering review, not a complete-security or production-readiness guarantee.
