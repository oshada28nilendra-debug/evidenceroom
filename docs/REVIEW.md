# Independent review and fixes

A separate read-only reviewer examined the completed source, then reviewed the fix pass.
Two medium issues were reproduced and corrected:

1. A simulated HTTP endpoint trickling response bytes every 0.3 seconds could return after 1.8 seconds despite a 1-second model timeout. The shared direct transport now applies an absolute I/O deadline and watchdog socket shutdown. Real simulated-server tests cover trickled bodies and source headers. DNS remains explicitly outside the bound.
2. List-valued source kinds/review decisions and malformed Crossref items could cause TypeError/AttributeError. Explicit shape checks return controlled errors. Incomplete audit bundles are rejected; an additional regression covers rehashed invalid reporting fields and inconsistent claim summaries.

The independent fix-pass review found no remaining high/medium release blocker and independently ran 37 passing tests. The final nested-report validation regression subsequently brought the suite to 38; that regression and the subsequent normative-planning regression (39 total) were checked locally, not by the second reviewer.

Additional live-model observations led to specific fixes: a planner repeating decision options is rejected, literal schema placeholders were replaced with proper JSON schema descriptions/enums, primary-source preference and source diversity were added, and context/inference-only coverage is distinguished from proposed support/opposition. These gates do not verify semantic truth.

No penetration test, external account-log audit or complete-security claim is implied. The source HTTP path still needs verification from an environment with normal public DNS/egress. Live model quality is recorded separately, with unsuccessful/weak attempts retained.
