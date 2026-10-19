# GitHub handoff

Update, 18 October: the user designated `oshada28nilendra-debug/evidenceroom` and authorized publication. The inspected starting repository contained only its initial README and no license/instructions. The release is being prepared on `feat/evidenceroom-first-release`, using the noreply email verified from the repository's initial commit. See the latest publication section in VERIFICATION.md for subsequent CI/PR evidence. The archive-stage checklist below is historical; repository designation is resolved.

No repository was explicitly designated for EvidenceRoom. No GitHub push, commit,
PR, deployment or hosted CI run is claimed. The source ZIP is the actual delivery.
Suggested repository: `oshada28nilendra-debug/evidenceroom`.
Suggested project branch: `feat/evidenceroom-first-release` (not created remotely).

Once the user designates a repository:

1. Inspect its main branch, instructions, license and any existing work; do not
   assume it is empty or overwrite unrelated files.
2. Clone it and create the project branch from the actual default branch. Copy
   this package's source into that checkout while preserving `.git` and repository
   instructions. Confirm MIT licensing fits the designated destination.
3. Configure the exact noreply address shown in GitHub Settings → Emails. Do not
   restore a personal email to public commit metadata. Enable email privacy and
   command-line push protection in GitHub settings.
4. Run README tests/lint/format/compile and the offline/review demos. In an
   environment with public DNS/egress, verify Crossref discovery and a real public
   HTTPS text/HTML source fetch. Preserve failures rather than claiming success.
5. Commit, push the isolated branch and open a PR against the default branch.
   Do not merge automatically. Let ordinary CI run and inspect its logs.
6. The optional `live-model` workflow is manual and downloads a checksum-pinned
   llama.cpp CPU runtime plus official Qwen3-1.7B Q8 weights, then runs an authored
   fixture gate. It uses no hosted model API/key. Actual model quality can vary;
   a failed gate retains fixture evidence for review.

The essential supported local source-pack path accepts reviewed factual claims,
produces model-assisted evidence suggestions and records human review. Automatic
claim planning remains experimental: our small-model plans included normative
recommendations, so the conservative wording gate now abstains. General web
research, automatic authority verification, PDF/OCR and broad accuracy evaluation
remain deferred.
