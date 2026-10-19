# Security and privacy boundaries

This is a local CLI, not a public multi-user service. Source packs, model output,
review files and reports are untrusted. No source code, shell command, JavaScript,
model-supplied tool action or source instruction is executed. Models only propose
claims and evidence records. Exact source spans are checked deterministically.
Semantic relevance and truth remain review tasks; inferences are not facts.

Source URLs are supplied by the user, never chosen by model output. Public fetches
require explicit consent and exact host allowlisting. All DNS answers must be global
addresses. TLS connects to a validated pinned address with the original hostname
for certificate verification; redirects, proxies, auth/cookies, compression and
nonstandard ports are unsupported. Local/private/reserved IPs are blocked. DNS
resolution itself relies on system resolver behavior and has no independent hard
wall-clock timeout. Firewall egress controls are recommended for deployment. This
is not a claim of complete SSRF resistance across arbitrary resolver/network setups.

Local source paths stay under the case directory and reject symlinks/traversal.
The filesystem must not be concurrently hostile: there is no atomic descriptor walk
through every parent directory. Output must be a fresh path. Use private directories
and appropriate OS permissions; no application-level encryption/access control exists.

Model endpoints are configured separately by the user. Remote endpoints require
HTTPS and explicit source-transfer/cost consent. Local proxies can themselves use
cloud models. Provider response bodies and credentials are omitted from errors.
Both HTTP paths ignore system HTTP proxy settings. A shared absolute I/O deadline
limits connection/TLS, headers and body reads; system DNS resolution is excluded
because libc resolver calls are not portably interruptible. Do not point it
at an untrusted provider or set credentials for a server you do not trust.

No bundled key, telemetry, automatic secret scan or guaranteed secret redaction.
Source text and model suggestions can include sensitive data. Bundles retain full
normalized source text, rejected proposals and reviewer names/notes. Review before
sending, publishing or uploading. Source URL query strings may also contain private
information: do not use credential-bearing URLs. The CLI never automatically uploads
reports. The optional live-model workflow uploads fictional fixture evidence only.

HTML is escaped, has no scripts/external resources/active links, and includes a
restrictive CSP. Markdown is escaped; render only with a renderer that preserves
these protections. JSON is canonical. An integrity hash is not a signature or
external attestation; an attacker can modify data and recompute it. Reviewer names
are declarations, not authenticated identities. Do not trust a bundle from an
unknown party merely because `verify` passes.

Report vulnerabilities privately to the repository owner once a repository is
assigned. Do not include credentials, private source or personal information in
public issues. Revoke a real exposed credential at its provider rather than
relying on deleting a file. No complete-security or compliance claim is made.
