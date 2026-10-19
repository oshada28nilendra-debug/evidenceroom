# EvidenceRoom

**Turn competing documents into a reviewable claim-and-evidence decision audit.**

For researchers, analysts and small organizations who need to explain why a decision
is supported, disputed or still missing evidence. EvidenceRoom stores the passage
behind each citation, rejects invented quotations and keeps human review separate
from AI interpretation.

Repository: [oshada28nilendra-debug/evidenceroom](https://github.com/oshada28nilendra-debug/evidenceroom).
The first release is being published on `feat/evidenceroom-first-release` for review.
Publication check results are recorded in [verification](docs/VERIFICATION.md).

## Contents

- [What it does](#what-it-does)
- [Install](#install)
- [Try the offline example](#try-the-offline-example)
- [Use a real AI model](#use-a-real-ai-model)
- [Find and collect sources](#find-and-collect-sources)
- [Review evidence](#review-evidence)
- [Input format](#input-format)
- [Outputs and interpretation](#outputs-and-interpretation)
- [Commands and configuration](#commands-and-configuration)
- [Architecture](#architecture)
- [Verification](#verification)
- [Privacy and limitations](#privacy-and-limitations)
- [Contributing and license](#contributing-and-license)

## What it does

1. Takes a question, competing options and a bounded source pack.
2. Uses your claims, or asks a real model to propose verifiable claims.
3. Retrieves passages with BM25, preferring declared primary sources and source diversity.
4. Optionally asks the model to label supporting, opposing, contextual and inferred evidence.
5. Checks passage IDs, exact quotes and offsets against saved source snapshots.
6. Exports JSON, Markdown, inert HTML and a digest-bound review template.
7. Records your accept/reject decisions and highlights unresolved opposing evidence.

A matching quote proves the text exists in the snapshot. **It does not prove that
the source is true or that the quote supports the claim.** EvidenceRoom does not
choose a winner by counting sources, certify facts or make your decision for you.

See [validation and alternatives](docs/VALIDATION.md) for the comparison with GPT
Researcher, STORM and Open Deep Research. The differentiator is an inspectable audit
bundle and review queue; no claim of global novelty or competitive superiority.

## Install

Python **3.11+** is required. Runtime dependencies: Python standard library only.
Extract the source ZIP and open a terminal in its project directory:

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
python -m pip install -e .
python -m evidenceroom --help
```

The installed `evidenceroom` command is equivalent to `python -m evidenceroom`.
Docker is not required: no source or model-generated code is executed.
Model weights and provider runtimes are not bundled or downloaded by the CLI.

## Try the offline example

```bash
python -m evidenceroom run --case examples/grant-case.json --offline --out runs/grant-offline
python -m evidenceroom verify --bundle runs/grant-offline/bundle.json
```

Open `runs/grant-offline/report.html`. The fictional council rules say 10000
credits while its later FAQ says 12000. A blogger repeats eligibility information.
All fixture documents are original synthetic examples, **not real grant advice**.

Offline mode retrieves candidate passages only: all relations are `context` and all
records are `unreviewed`. It does not perform AI reasoning or automatically detect
semantic contradiction. Label the relevant passages yourself using the review flow,
or use model mode. Lexical relevance can miss paraphrases and retrieve irrelevant text. Primary-source
priority uses your declarations and is not an authority or truth score.

The default output directory must be new. Exit 0 means an audit was generated,
not that its claims are true or its question is resolved.

## Use a real AI model

Start an OpenAI-compatible local server separately. For example, install Ollama
from its [official documentation](https://docs.ollama.com/) and deliberately download
a suitable model. Check disk/RAM needs and the model's license first.

```bash
ollama pull qwen2.5:7b-instruct
python -m evidenceroom run --case examples/grant-case.json \
  --model qwen2.5:7b-instruct --endpoint http://localhost:11434/v1 \
  --out runs/grant-ai
```

The provider must support Chat Completions with `response_format: json_object`,
`max_tokens` and the configured model name. The Ollama command is a setup example;
consult [verification](docs/VERIFICATION.md) for combinations actually exercised.
The experimental planning variant `examples/plan-case.json` omits claims, so the
first model call proposes them. Option repeats and obvious normative/question
forms are rejected rather than automatically researched. This is a conservative
wording heuristic, not semantic verification. Our tested small models produced
weak plans: **use your own reviewed factual claims for the supported release path**.
Rejected plan text is preserved as `plan_proposal` with exit 3.

For an explicitly authorized remote provider, set `EVIDENCEROOM_API_KEY` through
secure environment configuration, then supply its HTTPS `/v1` base, model name
and `--allow-remote-model`. That flag consents to transferring source passages and
possible provider charges. No paid API calls are made by default. No credentials
are bundled; local endpoints can still proxy to cloud services, so check yours.

Malformed responses, authentication/rate-limit errors and exhausted budgets are
recorded as errors. A partial model audit is exported with exit 3. Invalid source
input fails before export with exit 2. No hidden retries or replacement with fake
AI output occur. An empty evidence list is abstention, not disproof.

## Find and collect sources

Optional Crossref discovery returns five bibliographic candidates:

```bash
python -m evidenceroom discover --query "evidence traceability deep research" --allow-network
```

Discovery metadata is **not claim evidence**. Review the results, find the primary
publication or official document, and add its text/HTML or public HTTPS URL to the
case. DOI redirects are not followed; use the final publisher URL or save an
authorized text extract yourself. Crossref is literature discovery, not general web
search. There is no unrestricted crawler or claim of exhaustive research.

For URL sources, collection also needs an exact hostname allowlist:

```bash
python -m evidenceroom run --case my-case.json --offline --out runs/my-case \
  --allow-network --allow-host docs.example.org
```

The hostname above is illustrative. Fetching blocks private/reserved addresses,
mixed DNS responses, non-HTTPS URLs, credentials, nonstandard ports and redirects.
It pins the validated public address for TLS and ignores HTTP proxy settings for
source fetching. Some corporate/proxied environments therefore fail closed. Only
UTF-8 plain text and HTML are supported; PDF, OCR, compressed bodies and browser
rendering are deferred. Respect access restrictions, copyright and website terms.

## Review evidence

Copy the generated `review-template.json`, edit the reviewer and decisions, and
bind the review to the original `bundle_digest`:

```json
{
  "bundle_digest": "COPY_FROM_YOUR_BUNDLE",
  "reviewer": "Your name",
  "decisions": [
    {
      "evidence_id": "c1-e1",
      "decision": "accept",
      "relation": "support",
      "note": "I read the quoted eligibility rule and checked its scope."
    }
  ]
}
```

```bash
python -m evidenceroom review --bundle runs/grant-offline/bundle.json \
  --decisions my-review.json --out runs/grant-reviewed
```

Allowed decisions: `accept`, `reject`. Relations: `support`, `oppose`, `context`,
`inference`. Notes are required; unknown/duplicate IDs and wrong bundle digests fail.
Original relations and the parent digest remain in the reviewed bundle. Review is
append-only through a new output directory. A reviewer name is a declaration,
not an authenticated identity or signature.

## Input format

Paths are relative to the case file's directory, with no symlinks or traversal.
Each source has **either** `path` **or** `url`.

```json
{
  "question": "Should we apply now or request clarification?",
  "options": ["Apply now", "Request clarification"],
  "claims": ["Nonprofit groups are eligible."],
  "sources": [
    {
      "id": "rules",
      "title": "Official eligibility rules",
      "publisher": "Issuing organization",
      "kind": "primary",
      "published": "2026-10-01",
      "path": "sources/rules.txt"
    }
  ]
}
```

`claims` may be omitted only in model mode. `options` and `published` are optional.
`kind` is `primary`, `secondary` or `unknown`: this and publisher/date are **user
assertions**, not automatic authority certification. Review dates and context when
sources disagree. Exact matching is against whitespace-normalized, NFC source
text; offsets are Python Unicode character indices, not original HTML byte offsets.

## Outputs and interpretation

| File / field | Meaning |
| --- | --- |
| `bundle.json` | Canonical source snapshots, hashes, claims, retrieved passages, accepted/rejected proposals, review state and model usage |
| `report.html` | Inert, escaped, self-contained report; no scripts, external assets or active source links |
| `report.md` | Escaped readable report; JSON remains canonical |
| `review-template.json` | A deliberately conservative reject example to replace after inspection |
| `potential_conflict` | Both support and oppose annotations exist; their semantic correctness/scope requires review |
| `content_groups` | Distinct source-text hashes among active annotations; identical copies count once |
| `publisher_groups` | Distinct declared publishers; does not establish real source independence |
| `rejected` proposals | Invalid IDs, invented quotes, malformed records or duplicate annotations; not evidence |
| `verify` | Checks bundle consistency, source hashes and exact quote spans; not authenticity, truth or protection against a deliberate rehash |

The bundle retains **full normalized source text**, rejected proposals and reviewer
notes for reproducibility. Do not publish a private-data bundle casually. Hashes
refer to normalized text, not website authenticity or a Git commit. Raw bytes are
not retained, but their SHA-256 is recorded at ingestion.

## Commands and configuration

| Command / option | Purpose |
| --- | --- |
| `run --case FILE --out NEW_DIR --offline` | Deterministic retrieval audit; zero model/network calls for local sources |
| `run ... --model NAME` | Real configured HTTP adapter; claim planning if needed and passage interpretation |
| `discover --query TEXT --allow-network` | Crossref public metadata candidates |
| `review --bundle FILE --decisions FILE --out NEW_DIR` | Record human decisions without editing the original bundle |
| `verify --bundle FILE` | Check internal integrity and citation spans |
| `--allow-network --allow-host HOST` | Explicit public-source collection permission; hostname flag repeatable |
| `--allow-remote-model` | Explicit remote model transfer/cost consent |
| `--model-timeout N` | 1–120 seconds/request; default 120 |
| `--max-calls N` | 1–9 calls/run; default 9; no automatic retries |
| `EVIDENCEROOM_BASE_URL` | Default model base URL; CLI `--endpoint` overrides |
| `EVIDENCEROOM_API_KEY` | Optional provider credential; never written into reports by the adapter |

`.env.example` is a reference, not automatically loaded. Exit codes: 0 generated
or verified; 2 invalid input/configuration/I/O; 3 partial model audit. Source fetches
are <=512 KB/request. Cases allow 12 sources, 8 claims and 6 options; 40,000
normalized chars/source, 160,000 total. Retrieval supplies 3 passages/claim, each
<=1600 chars. Calls request <=2048 completion tokens. The I/O deadline covers
connection/TLS, headers and body after system DNS resolution; DNS is outside this
bound because the system resolver is not portably interruptible. Budgets cap requests, not
currency spend or a provider's internal processing.

## Architecture

| Module | Responsibility |
| --- | --- |
| `core.py` | Case validation, local path policy, HTML text extraction, normalization and provenance |
| `retrieval.py` | Deterministic BM25 candidate ranking with exact offsets |
| `httpio.py` | Shared absolute I/O deadline and direct HTTP/TLS transport; DNS prerequisite documented |
| `network.py` | Public HTTPS retrieval with DNS/address validation and pinning; Crossref discovery |
| `provider.py` | Genuine compatible HTTP model adapter, consent, limits and generic errors |
| `pipeline.py` | Optional planning, bounded per-claim interpretation, citation validation and conflict summaries |
| `report.py` | Digest checks, human review, safe JSON/Markdown/HTML exports |
| `cli.py` | Explicit user modes and output/error handling |

No vector database or swarm is needed for this release. Independent agents would
add cost without a demonstrated benefit on this bounded source-pack workflow.

## Verification

```bash
python -m unittest discover -v
python -m compileall -q evidenceroom
python -m pip install ruff
python -m ruff check .
python -m ruff format --check .
```

See [the actual verification record](docs/VERIFICATION.md), [security boundaries](SECURITY.md)
and `delivery/` for executed checks, model attempts and blockers. The ordinary CI workflow is provided for Python 3.11/3.12/3.13; it has not run on
GitHub at the initial archive checkpoint. A separate `live-model` workflow
uses checksum-pinned llama.cpp and Qwen3-1.7B Q8 weights against the fictional
fixture. Its helper is `scripts/live_smoke.py`; it is not a broad benchmark. See
[GitHub handoff](docs/HANDOFF.md). Simulated HTTP/test-double checks do not establish actual inference.

## Privacy and limitations

- Review source packs before model use. Secret detection/redaction is not guaranteed;
  the selected documents, issue/question and model output may contain private data.
- Model output and source text never receive shell, filesystem-writing or URL-fetch
  privileges. Prompt-injection instructions can still influence interpretation.
- Offline retrieval is a baseline, not semantic contradiction detection. Model
  interpretations require review, including apparently exact supporting quotes.
- No claim of exhaustive sources, empirical accuracy, calibrated confidence,
  medical/legal/financial suitability or general decision quality is made.
- Source selection bias, false publisher declarations, version mismatch and
  semantic paraphrase failures remain. No numeric confidence or majority-vote truth.
- Local path checking assumes no adversary concurrently mutating directories.
  Use source packs you are permitted to read; no public multi-user server is provided.

## Contributing and license

Read [CONTRIBUTING.md](CONTRIBUTING.md), open focused changes with reproducible
fixtures, and keep secrets/private documents out of issues and artifacts.

MIT for original code and authored fixtures. No competitor code, research dataset,
model weights or third-party document corpus is bundled. External model/runtime
licenses and source rights remain separate; see [LICENSES.md](docs/LICENSES.md).
