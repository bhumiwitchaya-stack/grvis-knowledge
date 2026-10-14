# REA-informed investigation workflow for GRVIS
Use after intake when analyzing software or recreating an observed workflow. This extends /reverse; it does not register REA or grant target access.

## 1. Route by real capability
Read the actual provider/CLI/MCP version and advertised schema. Distinguish repository reading from execution. Public upstream is morluto/rea; prefer a pinned release and inspect updates before changing persistent registrations. Use a configured project canonical; never choose model/version or claim platform activation from this file.

REA supports capabilities by target/provider/host; use the available subset. Native tools, static JavaScript analysis, browser scenario captures, process observation and media transcription are different boundaries. Treat unsupported/unavailable as explicit states. Map REA Evidence into a GRVIS ledger only through a tested versioned adapter; preserve originals. REA capture version names are not GRVIS V assurance levels.

## 2. Observe the question, not just a URL
Write initial state, action, input/control, readiness predicate, expected observation, capture selection, numeric budgets, scope/authorization, stop and cleanup.
For a UI use DOM/accessibility for visible text/structure, screenshot for canvas/pixels, and minimal events when needed. URL-only completeness does not answer a rendered-content question. Wait for the current response state; an existing container or old data is not readiness. not_requested means not observed, not empty.
Do not widen capture to cookies/storage/traffic without need and authority. Ordinary page requests can leave the start origin; a browser/proxy/process capture is not a sandbox. Attached-session cleanup does not undo side effects.

## 3. Preserve identity and residual uncertainty
Record target/ref/hash, source scope/coverage, environment, input, timestamp, provider version, limitations and evidence IDs. Cache retained source Evidence and request bounded projections before repeating producers.
Maintain each required unknown with ID, question, owner, current revision, evidence for/against, dependencies, and next discriminating test. Resolve only with qualifying evidence. A stale CAS revision must be reread; matching patterns/static cochange do not establish causality. Incomplete frontier or artifact pagination cannot prove absence.

## 4. Compile a finite reconstruction specification
Each requirement needs ID, behavioral/static kind, source evidence, expected outcome/tolerance, representative normal/boundary/failure cases, owner and required/optional status.
Use explicit state transitions and interfaces; include input units/timezone, dependencies, exception paths and persistence. Separate observed behavior, specified behavior and hidden implementation candidates.
For independent implementation, use an authorized behavior specification and original/licensed code, formulas and assets. Public observation or REA's MIT licence does not convey target premium entitlements or licences. Preserve relevant notices when copying allowed code.

## 5. Evaluate without turning incomplete data into pass
Use tools/reverse_workbench.py on a grvis-reverse/1 record file when deterministic record checks help. It evaluates declared comparable records, not actual target behavior or semantic source truth:
- pass: required comparable submitted values match their declared expectations
- fail: a required comparable value diverges
- unknown: missing/stale/context-mismatched/partial/not-requested observations or required open unknown
- invalid: malformed/dangling/duplicate/unsupported record contract or unsupported FACT assertion

The tool reports provenance_authenticity=not_verified even on pass. Validate source acquisition separately; finite pass is not global parity, absence proof, production certification or S2/S3.
CLI: python3 tools/reverse_workbench.py PATH.json
Exit codes: 0 pass; 1 fail; 2 unknown; 3 invalid. No network requests, target execution, Python eval or external writes occur.

## 6. Quant adaptation
For charts/strategies define price source, venue, timestamp/event time, closed vs partial candles, timezone, gaps, numerator/denominator, warm-up, cost/fill model and held-out split. BiG's trading prices use Binance Futures only. Include fees/spread/slippage/funding/partial fills/rejections/liquidation when applicable. Account for unit conventions and peak-to-trough drawdown. Avoid future-data leakage and data snooping. Keep financial automation RESEARCH/SHADOW unless a separate live runtime and exact authority cover it.

## 7. Verify and release within scope
S0: structure/links/contracts. S1: deterministic fixture tests on exact revision. S2: configured provider/host and representative authorized live workflow. S3: predefined held-out cases and independent evaluation where possible.
Run source-owned fixtures before target work. A REA CLI smoke test proves only that version/host/operation/fixture. Add an obligation-to-test traceability matrix; skipped/truncated/unsupported remain visible.
Export reproducible inputs/results, hashes/ref, environment, finite scope and unresolved owners. Claim improvements only against measured baseline dimensions.

## Primary references
Pinned reviewed upstream: d901561640121272bf1498d85e38e1ac8b3f5793, package.json version 6.4.0 (source metadata, not proof npm publication).
- https://github.com/morluto/rea/blob/d901561640121272bf1498d85e38e1ac8b3f5793/.agents/skills/reverse-engineer-anything/references/evidence-workflows.md
- https://github.com/morluto/rea/blob/d901561640121272bf1498d85e38e1ac8b3f5793/docs/browser-scenario-contract.md
- https://github.com/morluto/rea/blob/d901561640121272bf1498d85e38e1ac8b3f5793/docs/reconstruction-readiness.md
