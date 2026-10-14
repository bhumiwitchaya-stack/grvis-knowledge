# GRVIS reverse workbench — finite record contract
Status: Candidate v0.1. This is an original offline comparator, not a REA engine or universal evidence verifier.

## Run
```sh
python3 -m unittest discover -s tests -v
python3 tools/reverse_workbench.py tests/fixtures/reverse-evidence.json
```
The included records are synthetic. A pass says only that submitted comparable values match declared expectations. No target is contacted/executed, source authenticity is not verified, and no global parity or GRVIS S2/S3 claim is produced.

## grvis-reverse/1 input
Use the complete fixture as the executable example. Every top-level key is required:
- schema_version: grvis-reverse/1
- target: nonempty id and exact revision
- environment: nonempty id; optional profile
- sources: bounded array of source records
- claims: atomic assertion records
- unknowns: open/resolved questions with an owner
- obligations: at least one required finite comparison

### Source record
Required fields: id, kind, uri, location, retrieved_at, lineage, coverage, target_revision, environment_id.
Optional sha256 is a 64-character lowercase hex digest. Its format is checked, not recomputed or authenticated.
kind: runtime_observation / measurement / static_analysis / documentation / marketing.
coverage: complete / partial / unavailable / not_requested.
Coverage refers to the explicitly bounded record scope, not an entire application or website. Use a timezone-aware ISO timestamp. Credential-bearing URL userinfo is rejected; this is not a comprehensive secret scanner.
Lineage identifies acquisition origin. Two copied documents are not two independent sources. The validator detects duplicate declared lineages but cannot prove independence when users falsely label them.

### Atomic claim
Required: id, text, kind, label, tier, status, evidence, contradictions.
kind: behavioral / static / documented.
label: FACT / INFERENCE / UNCERTAIN / SPECULATION.
tier: E1–E5. status: supported / inferred / uncertain / refuted / not tested / blocked.
evidence and contradictions contain source IDs. A FACT needs supported status, E1/E2, in-scope qualifying complete records and no declared contradiction. E2 needs two distinct qualifying declared lineages.
A documented claim may describe what documentation/marketing stated; it must not be used as a behavioral FACT. Semantic relevance of the text to the cited passage must still be checked by an actual reader/evaluator.

### Required unknown
Required: id, question, kind, state, required (boolean), owner, resolution_evidence.
An open required unknown prevents a finite pass. A resolved unknown needs qualifying complete in-context sources for its kind. This contract has no CAS updater or immutable persistence service; maintain revisioned ledgers in git or a verified adapter. Register all load-bearing omitted obligations manually; omission cannot be detected automatically.

### Comparison obligation
Required: id, description, kind (behavioral/static), required (boolean), source_id, target_revision, environment_id, expected.
Optional: observed and abs_tol.
observed missing is unknown, even if expected is null. Explicit observed=null is a value that can be compared.
abs_tol is finite, nonnegative and applicable only to numerical expected/observed; booleans are not numbers. Without tolerance equality is recursively type-aware for objects/arrays/scalars; int/float numeric equality is allowed.
Source kind/coverage, target revision and environment must qualify. Partial, unavailable, not_requested, wrong-kind or stale-context records remain unknown rather than equality/absence. A caller-provided result field is rejected.

## Results and exit status
| Result | Meaning | Exit |
|---|---|---|
| pass | All declared required comparable records match; no required open unknown | 0 |
| fail | At least one required comparable record diverges | 1 |
| unknown | No known required divergence, but required missing/incomparable observation or open unknown remains | 2 |
| invalid | Schema, references, IDs, types, tiers or assertion rules invalid | 3 |

Known required divergence takes precedence over unknown; both remain visible in the output. Optional failures do not change required-obligation readiness and remain in individual results. Every successful evaluation retains provenance_authenticity=not_verified.
This tool neither acquires source evidence nor authenticates declared observed values, timestamps, lineages, hashes, context, authority, or semantic relevance. Never use its pass as target verification without separate acquisition proof.

## Budgets and failure boundaries
CLI input: 2 MiB maximum, 500 records per collection, depth 50; duplicate JSON keys and non-finite numbers are rejected. Read one input file and write JSON to stdout. No shell, eval, network, target execution, or file mutation.
Python programmatic callers should apply the same byte budget before parsing; the 2 MiB limit is enforced by the CLI loader. Limits constrain input processing, not authenticity or a production sandbox.

## Tests
31 synthetic contract tests exercise partial/not-requested, stale context, missing values, source-kind confusion, false independence, contradictions, unresolved unknowns, injected pass, dangling references, tolerance boundaries, boolean/numeric distinctions, malformed types, credential URI, timestamp/schema/record/depth limits and duplicate JSON keys.
Repository checks cover board integrity and actual skill metadata/references. GitHub Actions runs those checks on Linux and Windows.
A separate job installs rea-agents@6.4.0 on Node 24.11.0, records actual capabilities and analyzes only the source-owned chart JavaScript fixture. The smoke checker verifies the returned Evidence identity and expected export; it does not translate the entire REA Evidence schema or claim native/browser/host activation.
Read workflow logs and artifacts for the exact tested commit before claiming these jobs passed. Fixtures and author-written tests are not independent held-out evaluation.

## Live adapter acceptance gate
Before real target execution: approved target/method; provider/schema/version discovery; owned-fixture result; data/export controls; numeric capture budgets; concrete readiness predicate; lifecycle/cleanup proof; complete cited outputs; run/environment/ref and residual unknowns.
Adapter integration is a separate task. No automatic MCP installation, browser login, machine-code analysis, trading order, or premium-feature unlock is performed here.
