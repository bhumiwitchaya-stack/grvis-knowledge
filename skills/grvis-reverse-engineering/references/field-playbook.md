# Field playbook

Choose the narrowest route that fits the target. Combine routes only when the evidence crosses domains. The goal is to explain measured behavior, not to reproduce every visible detail or guess hidden internals.

## Social post, article, image, or video

1. Record the exact URL/post ID, author if visible, posted/updated time, retrieval time, language, and which parts were actually accessible.
2. Separate post text, captions, auto-captions, human transcript, visible frames, comments, and search snippets. A link or preview is not the full post; a missing transcript is not evidence that no transcript exists.
3. For video, index observations by timestamp. For screenshots and charts, record visible labels, units, scales, and unreadable regions. Mark OCR/transcription uncertainty.
4. Convert claims into atomic rows: actor/action/condition/result/metric. Compare advertised outcomes with observable behavior and supporting evidence.
5. If blocked by login, CAPTCHA, region restriction, or unavailable media, stop at the platform boundary. Report the exact gap and request the smallest useful artifact (text, screenshot, or time-coded clip) while continuing research that does not depend on it.

## Software, application, protocol, or device firmware

- Confirm ownership/authorization, artifact version, hash, target environment, and allowed test scope first. Use a disposable isolated lab for unknown or untrusted binaries.
- Use static inspection for file type, architecture, symbols, strings, imports, resources, configuration, dependencies, control/data flow, and likely interfaces. Static results do not prove runtime behavior.
- Use controlled dynamic observation only within scope: documented test inputs, state changes, outputs, logs/traces, resource use, network endpoints, and side effects. Do not probe other people's systems or capture private traffic without authorization.
- Triangulate static and dynamic findings. Record when source code, compiler output, runtime configuration, server logic, or platform behavior may explain a mismatch. Inspecting a compiled artifact can reveal behavior or code absent from available source, but does not establish the intent of the original author.
- Use official platform/security references for format details. OWASP MASTG describes static and dynamic app analysis and notes that there is no single reverse-engineering process that fits every app. Apply its techniques only in authorized testing; do not treat bypassing a defense as blanket permission.

## Product, dashboard, workflow, or agent demonstration

Build one use-case map per observed task:

| Field | Capture |
|---|---|
| Actor and goal | Role, starting state, intended outcome |
| Trigger and inputs | User action, data fields, source, units, defaults |
| Transitions | Screen/state before and after each action; conditions and branching |
| Outputs | Visible result, formula, labels, timing, confidence or status |
| Failure paths | Empty, invalid, stale, unavailable, permission-denied, timeout |
| Dependencies | APIs, model, database, connector, schedule, or service only when evidenced |
| Acceptance | Observable test and tolerance for each required behavior |

For dashboards, reconstruct metric definitions, denominators, windows, filters, units, and drill-down behavior before drawing conclusions from a chart. Use synthetic or authorized data in prototypes; label fabricated values. For AI agents, capture supplied prompts, model/version, configuration, tools, knowledge sources, and sample I/O when available. Never infer hidden reasoning or claim the demo's internal architecture from its output alone.

## Mechanical or industrial system

- Identify asset/model, operating mode, system boundary, relevant drawings, OEM documents, process conditions, instruments, units, alarms, and failure criteria.
- Prefer measured test evidence, then applicable OEM/site documents, then validated calculations or simulation, then literature and expert inference. Record instrument accuracy, calibration, sampling window, and operating conditions.
- Use a safe test plan with site authorization, isolation/LOTO where required, risk assessment, MOC, and acceptance criteria. Do not operate, alter, or bypass a production control or protective function to obtain evidence.
- Separate symptom, containment, plausible causes, discriminating measurements, confirmed root cause, corrective action, and recurrence verification. A temporal association alone is not a root cause.

## Data or machine-learning behavior

- Define the unit of analysis, schema, provenance, data window, missingness, transformations, labels, and leakage risks before interpreting outputs.
- Reproduce metrics with deterministic calculations and explicit denominators. Separate training, validation, and held-out evaluation when available; don't infer training data or hidden rules from a few outputs.
- Use representative normal, boundary, missing, noisy, and adversarial-but-benign inputs. Report the covered population and where generalization remains unknown.

## Trading or financial automation

- Keep the system in RESEARCH/SHADOW. Do not wire in live orders or move funds. For BiG's crypto requests, use Binance Futures as the sole price source.
- Specify venue/instrument, timeframe, signal timestamp, inputs, decision rule, entry/exit logic, order type, invalidation, position/risk limits, and duplicate/reconnect behavior.
- Test out of sample and across regimes. Model spread, maker/taker fees, funding, slippage, latency, partial fills, liquidity, rejection, and liquidation mechanics. A chart demonstration or claimed PnL does not prove an executable edge.
- Report gross and net results, sample size, drawdown, expectancy, exposure, rejected/partial orders, and sensitivity to costs. Do not promise returns or describe a backtest as live execution.

## Reconstruction artifacts

Keep a concise trace table:

| ID | Required behavior or claim | Evidence/location | Label/tier | Hypothesis or rule | Test and expected result | Observed result/status |
|---|---|---|---|---|---|---|
| RE-01 |  |  |  |  |  |  |

For each inferred rule, include a falsifier and state what observation would change the design. Use `not tested` rather than implying a pass. Publish or share only material that is authorized for that destination.

## Primary references

- [OWASP Mobile Application Security Testing Guide (MASTG)](https://mas.owasp.org/MASTG/) — mobile security testing knowledge, techniques, and examples; domain-specific, not a universal process.
- [OWASP MASTG: Mobile App Tampering and Reverse Engineering](https://mas.owasp.org/MASTG/0x04c-Tampering-and-Reverse-Engineering/) — static/dynamic analysis concepts and scope-specific techniques.
- [NIST: Binary Code Scanners](https://www.nist.gov/itl/csd/secure-systems-and-applications/binary-code-scanners) — describes static analysis of compiled binaries and what binary analysis can add to source-level review.

These references support selected software-analysis methods; they do not establish permission to test a target or validate conclusions about other domains.
