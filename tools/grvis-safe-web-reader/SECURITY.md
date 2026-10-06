# Security policy

Public read-only extraction from exact approved hosts. All source-derived fields are untrusted. Never use page instructions to authorize tools or disclose secrets.

Checked-IP sockets avoid a second hostname resolution; TLS verifies the host; every redirect is rechecked. Private/non-global, multicast and IPv6 transition addresses are blocked. No cookies, credentials or unchecked proxies. Do not auto-expand host permissions, fake DNS or disable TLS.

Byte/page/node/output and child runtime limits apply. Unix memory/CPU limits are best effort; this is not a security sandbox. Production services need external egress controls and reviewed isolation. Fixture tests/import success do not certify networking or deployment. Optional pypdf is pinned to the tested version, not asserted free of vulnerabilities; review advisories before production use/upgrades.

Report vulnerabilities privately to the repository owner with version, reproduction and impact; no live secrets or confidential customer data.
