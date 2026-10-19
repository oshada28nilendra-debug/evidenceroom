# Contributing

Use Python 3.11+ and run unittest, Ruff and compilation commands in README.
Keep changes focused and add meaningful regression fixtures for behavior changes.
Label synthetic data, test doubles and simulated HTTP servers explicitly; do not
replace failed live model output with scripted success. Never commit credentials,
real private documents, model weights, caches or virtual environments. Preserve
source attribution and validate licenses when adding dependencies or examples.
For a new model/provider, show real request/result evidence and exact model/runtime
versions separately from deterministic tests. Do not treat a passing citation-span
check as proof of semantic accuracy. Open a reviewable PR; do not merge automatically.
