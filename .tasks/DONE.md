# Done

## TASK-005: Consolidate GRVIS research and reverse workflows into the research workbench
**Priority:** P1 | **Tags:** reverse, verification

Make `bhumiwitchayasig-bit/grvis-research-workbench` the single canonical repository for GRVIS `/find`, GRVIS Safe Web Reader, `/reverse`, and the finite Reverse Workbench. Remove duplicate installable skill packages and duplicate workbench guide from this portal; update public discovery pages and links.

### Done summary

- Canonical source and portal consolidation merged in Research Workbench PRs #13/#14 and knowledge portal PR #9. Current canonical source: `58c1e829ef9cb143a43e869c75d4890f27237630`.
- Resolved the Skills workspace sync by updating existing installed package IDs in place. Superseded reader copies were deleted inside the installed package. Fresh backend readback at `8ce2098ab19d6abf1df56d9087531fdf8d51d134` matched all 13 canonical skill files, with exactly one `find` and one `reverse` and no extra package files.
- Added the bounded real stdio MCP terminal client with source-pin verification before launch and UTF-8 child transport. The reader remains implemented once in the canonical source. Actual local MCP and Cloud retrieval succeeded on the same selected URLs; matching hashes and coverage limits are recorded under `verification/2026-10-19/task005/`.
- Verification: 40 Reader tests and 9 client tests locally; repository CI and scoped native Linux/Windows checks passed on PR #14, and post-merge main CI run 39233544543 passed. Fresh-context use on the Python documentation homepage exercised both real routes and source verification before launch.
- Scope limits: local invocation is `local_stdio_via_terminal`, not new native tool registration. This conversation's initial skill catalog remains cached; its refresh was not claimed. No new S2/S3 or global certification is asserted.

---

## TASK-003: Verify contracts through deterministic tests and GitHub CI
**Priority:** P1 | **Tags:** reverse, rea, verification

### Done summary

- Run 38505999112 passed all three jobs: 38 Linux tests, 38 Windows tests, pinned REA static fixture operation.
- Fixed the first observed Windows cp1252 failure and added Thai UTF-8 CLI regression.
- Fresh-context skill forward-use completed within static fixture scope; S3 remains not run.
- Evidence: docs/GRVIS_REA_VERIFICATION.md.

---
## TASK-002: Implement GRVIS reverse investigation contracts and skill extension
**Priority:** P1 | **Tags:** reverse, rea, verification

### Done summary

- Extended /reverse with capability, scenario, residual-unknown and finite-obligation workflow.
- Implemented bounded original offline comparator and fixture/test contracts; no target execution in comparator.
- Read back 18 implementation files at reviewed head; runtime regression evidence in run 38505999112.
- Detailed adaptation and limitations: docs/GRVIS_REA_ADAPTATION_TH.md and docs/REVERSE_WORKBENCH.md.

---

## TASK-001: Verify supplied REA claims and pin authoritative sources
**Priority:** P1 | **Tags:** reverse, rea, verification

### Done summary

- Reviewed upstream README, LICENSE, package.json and three evidence/scenario/readiness documents at d901561640121272bf1498d85e38e1ac8b3f5793.
- Recorded unsupported promotional claims and scoped GRVIS adaptation in docs/GRVIS_REA_ADAPTATION_TH.md.
- Current star snapshot does not establish the historical two-day claim; premium unlock and named model availability remain unverified.

---
