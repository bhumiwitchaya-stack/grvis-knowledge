# GRVIS Safe Web Reader

A small, read-only prototype for extracting text from **public web pages**. Python's standard-library HTTP client performs the request; Scrapling parses the returned HTML. It does not use browser automation or stealth mode.

## Safety defaults

- Requires an exact hostname allowlist for every run. Wildcards are not supported.
- Accepts only `http`/`https` on ports 80/443, rejects URL credentials and IP-literal hosts.
- Resolves the host and rejects private, loopback, link-local, reserved, and non-global addresses.
- Does not follow redirects, send cookies, use proxies, log in, or make non-GET requests.
- Uses TLS certificate verification, a 10-second timeout, zero retries, and a 2 MiB response-body limit enforced while reading.
- Emits extracted page text as **untrusted data** in JSON. It is not an instruction to the agent.
- Does not write fetched content to disk or start an MCP/HTTP server.

The DNS check is defense in depth, not a complete SSRF boundary: DNS can change between validation and connection. Run with outbound network controls that block private/link-local destinations when using this on a sensitive machine. The 2 MiB body cap bounds response buffering; the extracted text is separately limited to 50,000 characters.

## Install

Python 3.10+ is required. Create a virtual environment, then install the pinned dependency and this project:

```sh
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .
```

The application uses Scrapling's HTML parser only. It does not install browser binaries or optional AI/MCP, stealth, proxy, or browser-fetcher dependencies.

## Example

```sh
grvis-safe-web-reader \
  --allow-domain example.com \
  https://example.com/article
```

The allowlist is exact: `example.com` does not allow `sub.example.com`. Add each approved hostname explicitly. Output is one JSON object on stdout; the process exits non-zero on validation or fetch failure.

## Scope and limits

This prototype does not search social platforms, access login-only content, schedule monitoring, or guarantee that a website permits automated access. Check the site's terms and applicable law. Do not use it with company or customer data without approval from the relevant IT/security owner.

Scrapling is a third-party dependency under BSD-3-Clause. This wrapper is independently authored and does not include Scrapling source code. See `THIRD_PARTY_NOTICES.md`.

## Tests

```sh
python -m unittest discover -s tests -v
```
