# Lower-limit extraction architecture

## Shipped in 0.2

The public HTTP reader now follows validated redirects, supports bounded response/timeout settings, retains full extracted text within its body budget, emits chunks, and preserves title, links, image references and table cell text. It emits explicit coverage fields rather than claiming completeness. No JavaScript browser or social-platform adapter is installed.

## Recommended extension

Use separate workers, selected by source type, rather than one unrestricted scraper:

1. HTTP worker for static public pages (implemented).
2. Isolated browser worker for JavaScript pages: Playwright or Scrapling DynamicFetcher, fresh browser context per job, browser sandbox enabled, disposable container/VM, outbound firewall enforced for ALL browser traffic including redirects, subresources and WebSockets. Browser contexts isolate cookies but are not an OS/network security boundary. No arbitrary user-supplied page scripts. Limit page/time/scroll budgets, wait for known selectors, capture rendered DOM and record stop reason. Avoid treating network-idle or a stable page height as proof of completeness.
3. YouTube adapter: yt-dlp metadata and available manual/automatic subtitles, with language/time offsets and caption type retained. Never claim a missing transcript exists. Audio transcription requires a separate authorized download/transcription stage and has its own accuracy limits.
4. X/Reddit adapters: prefer official APIs when accessible; otherwise retrieve authorized visible content through the isolated browser. Preserve post IDs, pagination cursors and retrieval timestamps. Account-required content needs a separately authorized session; do not reuse unrelated browser profiles or auto-import user cookies.
5. Coordinator: record source, retrieval method, pages/segments retrieved, expected counts when available, failures, and stop reasons. Continue pagination only within an explicit budget; deduplicate by source ID. Store large results as separate output chunks and surface unresolved coverage gaps.

## Network routing

The local test runtime only exposes a managed proxy route. The earlier live test adapted proxy handling and stubbed validation DNS in a temporary harness. It demonstrates a real HTTP response and extraction, not real DNS verification or production-default networking. Production workers should use public DNS and verified egress controls, or a reviewed gateway that enforces destination rules. Do not use fake DNS answers as a deployment workaround.

## Constraints that remain

Login, CAPTCHA, rate limits, unavailable/deleted content, missing captions, platform permissions and site terms cannot be removed by adding a library. Dynamic workers cost more CPU/memory and time. A cloud worker avoids corporate-laptop installation but still needs a real runtime, network policy and deployment; it is not deployed by this branch.

## Primary references

- https://scrapling.readthedocs.io/en/latest/fetching/dynamic.html
- https://playwright.dev/python/docs/api/class-browsercontext
- https://github.com/yt-dlp/yt-dlp
