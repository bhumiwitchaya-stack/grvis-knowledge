# In Progress

## TASK-005: Consolidate GRVIS research and reverse workflows into the research workbench
**Priority:** P1 | **Tags:** reverse, verification

Make `bhumiwitchayasig-bit/grvis-research-workbench` the single canonical repository for GRVIS `/find`, GRVIS Safe Web Reader, `/reverse`, and the finite Reverse Workbench. Remove duplicate installable skill packages and duplicate workbench guide from this portal; update public discovery pages and links.

### Plan
- [x] Consolidate source, portal, and installed skill packages; retain one `/find` and one `/reverse`.
- [ ] Connect the local stdio Reader to ChatGPT as a native MCP tool using a supported, private transport.
- [ ] Refresh/install the host connection and start a fresh conversation with the Reader tool exposed.
- [ ] Verify the new conversation invokes native Reader and GRVIS Research Cloud on the same selected URLs; record real tool calls, status, hash, coverage, and failures.
- [ ] Keep the task In Progress with the exact account, workspace, permission, or runtime blocker until native calls succeed.

### Completed so far
- Canonical source and portal consolidation merged in Research Workbench PRs #13/#14 and knowledge portal PR #9. Current canonical source: `58c1e829ef9cb143a43e869c75d4890f27237630`.
- Skills workspace sync now updates the existing installed package IDs in place. Fresh backend readback matched all 13 canonical skill files, exactly one `find` and one `reverse`, with no extra package files.
- The bounded stdio terminal fallback enforces the pinned Reader source before launch and has passed local and CI checks. It proves the reader works locally, not that ChatGPT has registered it natively.

### Remaining gate
The current host tool registry exposes GRVIS Research Cloud capabilities/fetch/batch only. The current `/find` package can invoke the real Reader through terminal stdio, but the Reader is not a native host tool. A fresh skill read confirms the updated package content; it does not refresh this conversation's registered tool list.

The GRVIS OpenAI Platform organization currently has no MCP tunnels. ChatGPT Plugins supports a custom MCP server using Tunnel; the draft is staged as `GRVIS Safe Web Reader`, but its tunnel ID is blank, the security warning is unchecked, and no connection was created. OpenAI's documented setup requires a tunnel ID, a runtime API key, and an MCP server reachable over stdio or HTTP from a host that keeps `tunnel-client` running. The only connected Desktop Commander device, `THRAY-C-0383388`, is offline (last seen 124 hours ago), so a persistent runtime host has not been confirmed. Creating a tunnel and connecting the custom app are still pending action-time authorization. Keep TASK-005 In Progress until a native Reader call succeeds in a fresh conversation.
