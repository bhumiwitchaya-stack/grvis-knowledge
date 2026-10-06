# Runtime contract

## Execution and budgets

Run `grvis-safe-web-reader capabilities` before relying on optional features. HTML uses Python's standard library; PDF uses optional `pypdf`. Do not silently install dependencies or infer networking from import success. No proxy environment variable, cookie jar, credential or browser profile is reused.

Defaults: HTTPS only; 2 MiB compressed/body and decompressed limits; three validated redirects; 20 seconds total per job including DNS/parsing; PDF 30 pages; 12 selected URLs maximum per batch; 120 seconds total batch budget; zero automatic retries. Socket operations also have a maximum 10-second timeout. Configuration caps: 20 MiB, five redirects, 60 seconds/job, 100 PDF pages, 300 seconds/batch. Worker JSON output is capped at 4 MiB; oversized extraction omits secondary fields and retains a shortened text with `partial/output_budget` and explicit coverage markers. `--chunks` replaces `text` with chunks; `--include-all-text` requests secondary cleaned full-page text. PDF page records index character offsets into `text` rather than duplicating the same text. Sources are never auto-crawled.

Fetch exit status is zero only for `ok`; other outcomes still return structured JSON. Batch exit status is zero only when every source is `ok`. Inspect each source rather than interpreting a nonzero exit as loss of all batch results. `duplicate_of` marks matching content hashes but does not prove common authorship or complete source independence.

The parent kills a child exceeding its deadline. Unix workers additionally limit address space to 512 MiB and CPU; systems without `resource` retain byte/page/node/time limits but have no OS memory cap. Child processes are resource boundaries, not security sandboxes. Sensitive production services need externally enforced destination/network controls and deployment review. Checked-IP connections prevent re-resolution of the hostname between validation and socket connect; every redirect gets new checks. TLS SNI and certificate verification use the canonical hostname. Private/non-global, multicast and IPv6 transition addresses are rejected.

## Result interpretation

`schema_version`, `reader_version`, requested/final URL, redirect chain, UTC retrieval time, content SHA-256 and transport status support provenance. HTTP 401/403/429 are blocked. Empty pages are `empty`; likely challenge pages are `blocked` using a documented heuristic. Unknown charset uses UTF-8 replacement and `partial`. Semantic article/main extraction removes explicit hidden subtrees and obvious navigation; CSS layout, visibility, external styles and page authenticity are not verified. Structured links/images are references only, with `approved_for_fetch: false`. PDF page numbers are preserved; scanned pages can yield no text, OCR is not performed, and encrypted files are unsupported. No output asserts complete website coverage.

Recover according to `reason`: DNS/connect/deadline → authorized host reader/search; unsupported PDF/dependency → host PDF tool; blocked/login/CAPTCHA → public alternate source or authorized connector/browser; page budget → adjust within caps if useful; document limit → another reader and report the gap. Never widen permissions, fake DNS, disable TLS or bypass authentication to make a test pass.

## Optional MCP

Run the minimal stdio server using Python and a preapproved host allowlist:

```sh
grvis-research-mcp --allow-domain example.com
```

It implements JSON-RPC stdio initialization, ping, tools/list and tools/call for protocol versions 2024-11-05, 2025-03-26 and 2025-06-18. Tools: `grvis_capabilities`, `grvis_fetch`, `grvis_batch`. Only the server startup configuration can approve domains; tool arguments cannot widen that list. MCP remains HTTPS-only. Requests execute sequentially, so cancellation notifications do not interrupt a running fetch; deadlines still bound it. Input messages are capped at 64 KiB. No network listener or remote endpoint is created. Register it only in a host that supports local stdio and for which configuration is authorized. This skill does not change host configuration.

Primary protocol references:
- https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
- https://modelcontextprotocol.io/specification/2025-06-18/server/tools

## Origin

Reimplementation of the reviewed GRVIS public reader's behavior, with safer connection handling, extraction classification and coordination. Review baseline: `bhumiwitchaya-stack/grvis-knowledge`, branch `feat/grvis-safe-web-reader-v0.1`, commit `039a565427f1083c8280b0239e113d9dec1780a3`, reader version 0.2.0. Bundled runtime version 0.3.0 is independent of the upstream branch; installation does not update that repository. See `research-policy.md` for orchestration rules.
