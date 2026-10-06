# GRVIS Safe Web Reader 0.3.0

Bounded public HTML/PDF extraction, provenance, status, multi-source coordination and optional local stdio MCP. HTML uses the standard library; optional PDF support uses pinned pypdf. No JavaScript, login, CAPTCHA bypass, media downloads or remote deployment.

## Install and run

In a virtual environment:

```sh
python -m pip install -e .
# Optional PDF:
python -m pip install -e '.[pdf]'
grvis-safe-web-reader capabilities
grvis-safe-web-reader fetch https://example.com/article --allow-domain example.com
grvis-safe-web-reader batch --allow-domain example.com --url https://example.com/a --url https://example.com/b
```

Legacy single-URL CLI invocation still selects fetch. HTTPS is now the default; public HTTP requires explicit `--allow-http`. `--timeout` is replaced by `--deadline`, a total process deadline including DNS/parsing. Python API/result schema changed: use `run_job`/`batch_jobs` and inspect `status`/`reason`. No output certifies source truth or full coverage.

Exact hosts, checked public DNS addresses, direct checked-IP sockets and TLS hostname/certificate verification apply to every redirect. No proxy environment, cookies or credentials are reused. Defaults: 2 MiB body/decompressed bytes, 3 redirects, 20 seconds/job, 30 PDF pages, 12 sources/batch and 120 seconds/batch. Output JSON capped at 4 MiB; oversized output returns explicit partial coverage. Child workers bound runtime and Unix resource usage; they are not security sandboxes. Sensitive services still require reviewed external egress controls.

HTML honors base URLs, removes scripts/explicitly hidden subtrees consistently from structured fields and prefers article/main content. Challenge detection is heuristic. CSS visibility, OCR, dynamic/social APIs, exact table layout and media are unsupported. PDF pages index text offsets; blank pages and page budgets are recorded. Encrypted PDFs are unsupported. Every source-derived field is untrusted.

## Local MCP

```sh
grvis-research-mcp --allow-domain example.com
```

Minimal stdio JSON-RPC with initialization, ping, tools/list and tools/call for capabilities/fetch/batch. Only startup configuration approves hosts. Calls execute sequentially with deadlines; cancellation notifications do not interrupt active calls. No HTTP listener, remote endpoint or host registration is created.

## Check

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```

Tests use offline fixtures, actual deadline/MCP subprocesses and optional PDF fixtures. They do not certify public networking; current Work live attempts return DNS unavailable. An independent skill task exercised authorized GitHub connector fallback. No fake DNS or wider permissions were used for live checks. See RESEARCH_POLICY.md and ARCHITECTURE.md.

## Managed runtime networking (v0.4.0)

When OS DNS is unavailable in an approved managed runtime, explicitly use:

```sh
grvis-safe-web-reader fetch https://example.com/ --allow-domain example.com --network-route managed-proxy
grvis-research-mcp --allow-domain example.com --network-route managed-proxy
```

This uses only the platform loopback HTTPS proxy and a fixed reviewed public host registry plus the per-task exact allowlist. It reports delegated DNS and no IP pinning. It cannot authorize unknown hosts, source credentials, HTTP or unchecked redirects. Direct checked-IP mode remains the default. This resolves reader availability without claiming the platform OS resolver has been changed. See SECURITY.md.

The separately deployed owner-private GRVIS Research Cloud offers HTML/PDF, bounded batch and remote MCP. Connection requires installation/OAuth in the host; publication alone is not automatic activation. See CLOUD.md.
