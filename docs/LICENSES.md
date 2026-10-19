# License review — 18 October 2026

Original implementation and fictional GreenHall fixtures: MIT (see root LICENSE).
Python standard library is the only runtime dependency (Python Software Foundation
license). Build tooling is setuptools (MIT); optional development tooling Ruff is
MIT. No sources from competitor projects or research datasets were copied into
runtime code or fixtures.

Inspected alternatives: GPT Researcher Apache-2.0; STORM MIT; Open Deep Research
MIT, as declared by their repositories on the research date. These projects are
research references, not dependencies. Their licenses do not grant rights to the
sources their tools collect.

Optional external runtimes/models remain separate. Ollama and llama.cpp declare
MIT licenses. Official Qwen3-0.6B-GGUF model card declares Apache-2.0:
https://huggingface.co/Qwen/Qwen3-0.6B-GGUF
Runtime/model binaries and weights are not included in the source package.

Crossref public metadata access documentation:
https://www.crossref.org/documentation/retrieve-metadata/rest-api/
Metadata discovery does not license publisher full text. User-collected sources
retain their original rights and website terms. The shipped source fixtures are
authored synthetic text to avoid distributing third-party full-text documents.
