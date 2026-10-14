# GRVIS REA extension — verification record
Date: 2026-10-14. Scope: Candidate v0.1 reverse workflow and finite record workbench.

## Actual tested state
- PR: https://github.com/bhumiwitchaya-stack/grvis-knowledge/pull/6
- Source head: ff0ca39e477ff05f56f177dfc4fa683dbbc0060a
- CI pull_request run: https://github.com/bhumiwitchaya-stack/grvis-knowledge/actions/runs/38505999112
- Actual checkout was GitHub's merge preview of that source head into e07ef23db4c5b038bf456769186026a8b6ac6bbc; logs show merge preview prefix 6b4e81c.
- Workflow metadata reported completed/success with matching head_sha. Actual job logs were read, not inferred from author-written status.

| Job | Actual evidence | Result / scope |
|---|---|---|
| contracts (ubuntu-latest), job 115663534300 | CPython 3.12.15; Ran 38 tests; OK; comparator fixture valid/pass and provenance_authenticity=not_verified | PASS: 32 synthetic contract tests + 6 repository checks |
| contracts (windows-latest), job 115663534049 | CPython 3.12.10; Ran 38 tests; OK; comparator fixture valid/pass and provenance_authenticity=not_verified | PASS: same declared test scope |
| rea-owned-fixture, job 115663534267 | Node 24.11.0; rea-agents@6.4.0; actual static analyze-javascript-application operation; expected selectTimeframe export found in normalized result | PASS: owned JavaScript fixture static CLI only |

Returned REA Evidence ID:
ev_bda9d08f32a5994a2cd24e301f4704c6b08b761150ac2a2a0dab5fdc6e2b6e5b

The first run also returned that Evidence ID; this is observed identity agreement for this fixture, not universal reproducibility proof.
Raw job results are GitHub Actions artifacts with 7-day retention. Commands and source fixtures remain in git for reruns; expired artifacts are not assumed still retrievable.

## Defect found and fixed
Initial run https://github.com/bhumiwitchaya-stack/grvis-knowledge/actions/runs/38505651102:
Linux passed 37 tests and the REA fixture job passed; Windows failed test_skill_relative_references with UnicodeDecodeError from cp1252.
Fixed explicit UTF-8 reads in repository/fixture tests and explicit UTF-8 CLI stdout. Added a subprocess roundtrip with a Thai filename/obligation ID while PYTHONIOENCODING=cp1252. The corrected run passed 38 tests on both platforms.
A separate static review added bounded handling for extreme numeric tolerances and clarified that the comparator is not a concurrent trace matcher.

## Forward-use check
A fresh-context agent read the updated skill/references and source-owned chart fixture at e0d6f83219e38c3573018b96d03965ff5bfdafc4 through GitHub. It produced:
- scoped source facts versus unexecuted behavioral predictions;
- no support for supplied premium/live-execution claims;
- competing hypotheses and finite required acceptance cases;
- the mutable exported-array boundary and shallow-copy limitation;
- explicit S0 only for its own investigation; no invented REA execution, runtime trace, or held-out certification.

This exercises skill use in a separate context on shared authored artifacts. It is not blind S3, proof of generalization, qualified human review, or independent acquisition of target behavior. Later UTF-8 fixes leave the core skill instructions intact; a minor workflow clarification narrows concurrent-trace claims.

## Assurance and limitations
- S0: inspected structure, metadata, references, source pins and capability/claim boundaries.
- S1: deterministic tests and offline fixture comparator executed on actual Linux/Windows checkouts.
- Live integration evidence: actual installed REA 6.4.0 static CLI operation on an owned Linux fixture. This covers only that provider/operation/environment; it is not browser/native/ChatGPT activation.
- S2 for configured real target/native/browser hosts and S3 held-out evaluation: NOT RUN.
- V0 review, V1 test evidence, V2 primary source documentation and a separate-context forward-use check are available within the scopes above. V4 human review not performed.
- The installed Skill Creator quick_validate.py was unavailable in the failed chat execution environment. Actual-checkout stdlib assertions checked frontmatter/name, line budget, metadata prompt/length and relative references; do not claim the absent script ran.
- Comparator success compares submitted records only. It neither authenticates provenance nor verifies semantic relevance, authorization, hidden implementation or omitted requirements.
- No TradingView target, premium entitlement, live order, browser session, native target or third-party secret was inspected or changed.
- No benchmark supports a claim that the extension is universally faster or better in every dimension. The adaptation report defines baseline metrics for subsequent measurement.
- Constitutional/canonical promotion of the whole GRVIS system is outside this extension's release gate.

## Reproduce the finite tests
```sh
python3 -m unittest discover -s tests -v
python3 tools/reverse_workbench.py tests/fixtures/reverse-evidence.json
npm exec --yes --package=rea-agents@6.4.0 -- rea capabilities --json
npm exec --yes --package=rea-agents@6.4.0 -- rea analyze-javascript-application /absolute/path/to/tests/fixtures/chart-app --json
```
Do not substitute a private/production target into the fixture workflow without a separate scope and actual provider readiness check.
