# Reverse Engineering Field Playbook

## How to use this file

Select only the route that matches the target. Combine routes when evidence crosses domains. Keep the user-authorized target boundary in view. Tool access or technical possibility never creates authorization.

## 1. Public post, document, image, audio, or video

- Record exact URL/ID, author if visible, posted/updated time, retrieval time, language, and the content actually accessible.
- Separate post text, captions, transcript, visible frames, comments, OCR, narration, and search snippets. A share link or preview is not the full source.
- For video/audio, index claims and observations by time. Record sampling gaps, cuts, edits, unreadable areas, OCR/transcription uncertainty, and missing context.
- Convert each assertion to actor/action/condition/result/metric. A post directly proves only that the author made the statement, not that its underlying performance claim is true.
- If login, audience permissions, region, deleted media, or reader limitations prevent access, mark source-specific analysis **BLOCKED**. Do not infer the post's contents from snippets or an analogous post. Ask for the smallest useful artifact and keep independent research separate.

## 2. Software, application, protocol, or firmware

- Confirm ownership/authorization, artifact source, version, hash, architecture, build environment, and permitted static/dynamic scope. Do not capture third-party private traffic.
- Start with non-executing identification: file type, hashes, signatures, package layout, metadata, symbols, strings, imports, resources, configuration, dependencies, and available source/build artifacts.
- Form a control/data-flow map: entry points, trust boundaries, state, external interfaces, sensitive data, error handling, and persistence. Mark decompiler output as an interpretation that needs corroboration.
- Use dynamic observation only in an approved isolated lab with known test inputs, snapshot/rollback, bounded network access, logs, and stop conditions. Distinguish passive observation from instrumentation that changes execution.
- Compare static predictions with observed runtime behavior. Consider server-side logic, build/version drift, feature flags, environment, missing source, and measurement error before concluding.
- Use format specifications and vendor documentation for file/protocol facts. Do not bypass protections or turn a defensive finding into an exploit or evasion recipe.

## 3. Website, product, workflow, dashboard, or UI demo

Build one use-case map per observed task:

| Field | Capture |
|---|---|
| Actor and goal | Role, starting state, intended outcome |
| Trigger and inputs | User action, fields, source, units, defaults |
| Transitions | State before/after, conditions, branches, timing |
| Outputs | Visible result, formula, labels, status, confidence |
| Failure paths | Empty, invalid, stale, unavailable, denied, timeout |
| Dependencies | API, model, database, connector, schedule only when evidenced |
| Acceptance | Observable test and tolerance for each requirement |

For dashboards, reconstruct numerator, denominator, unit, window, filters, aggregation, missingness, and drill-down before interpreting values. A screenshot reveals pixels and labels, not hidden code or data lineage. Use synthetic data in prototypes and mark it synthetic.

## 4. AI agent, model, or automation demonstration

- Capture the exact prompt and response, model/version if visible, configuration, tools, knowledge sources, connectors, logs, and runtime traces when available.
- Treat narrated architecture, role names, routing diagrams, and model labels as claims unless runtime configuration or logs support them.
- Distinguish proposed architecture from deployed runtime. Output similarity does not prove the same model, hidden reasoning, independent agents, memory, or tool execution.
- Test prompt variation, context changes, permissions, tool failures, stale data, refusal, timeout, and repeated runs. Use held-out prompts only after fixing expected behavior.

## 5. Mechanical or industrial system

- Identify asset/model, boundary, operating mode, process conditions, drawings, OEM/site docs, instruments, units, and failure criteria.
- Prioritize measured/test evidence, applicable OEM/site documents, validated calculation/simulation, then literature/expert inference. Record instrument accuracy, calibration, sampling window, and conditions.
- Use approved risk assessment, site authorization, isolation/LOTO where required, MOC, and acceptance criteria before tests. Never manipulate production controls or defeat a protective function to obtain evidence.
- Separate symptom, containment, candidate cause, discriminating measurement, confirmed root cause, corrective action, and recurrence verification. Correlation or temporal order alone is not root cause.

## 6. Data, algorithm, or machine learning

- Define unit of analysis, schema, provenance, time window, missingness, transformations, labels, and leakage risk before interpreting output.
- Recompute metrics deterministically with explicit formulas and denominators. Preserve train/validation/held-out boundaries. Do not infer training data or hidden rules from a few examples.
- Test normal, boundary, missing, noisy, shifted, and benign adversarial inputs. Report population coverage, uncertainty, and what would falsify the inferred rule.

## 7. Trading or financial automation

- Keep work in RESEARCH/SHADOW; do not place live orders or move funds without an explicitly governed live system and exact authorization.
- Define venue/instrument, source and timestamp, timeframe, inputs, decision rule, entry/exit, invalidation, risk limits, and duplicate/reconnect behavior.
- Test out of sample and across regimes. Include fees, spread, funding, slippage, latency, partial fills, liquidity, rejection, and liquidation mechanics. Keep forecast separate from fact.
- Report gross/net results, sample size, drawdown, expectancy, exposure, rejected/partial orders, and cost sensitivity. A screenshot, backtest, or claimed PnL does not establish a live edge.

## 8. Business method, policy, or operating procedure

- Establish source authority, owner, revision, effective date, scope, exceptions, and precedence. Separate formal requirements from observed practice and promotional descriptions.
- Model roles, inputs, decisions, approvals, records, exceptions, and outcomes. Do not infer permission to act from a process diagram.
- Protect confidential methods and personal data; reproduce only within authorization and for the stated purpose.

## Experiment design checklist

Before testing, write:

1. The hypothesis and at least one competing explanation.
2. The observation that would support, falsify, or leave each unresolved.
3. Test setup, input, controls, measurement, tolerances, and environmental conditions.
4. Authorization, data handling, safety controls, stop criteria, and rollback.
5. Expected outcomes before execution; observed outcomes afterward; deviations and coverage.
6. A next discriminating test if uncertainty remains.

## Technical references

- [OWASP MASTG](https://mas.owasp.org/MASTG/) — mobile app testing and reverse engineering, not a universal process.
- [NIST SP 800-115](https://csrc.nist.gov/pubs/sp/800/115/final) — information-security testing and assessment; apply within authorization.
- [NSA Ghidra documentation](https://github.com/NationalSecurityAgency/ghidra/tree/master/GhidraDocs) — software analysis reference.
