# Security policy

## Supported scope

This prototype is for read-only retrieval of public pages from explicitly allowlisted domains. It is not a security boundary for a hostile multi-user service.

## Reporting

Please report vulnerabilities privately to the repository owner. Include the affected version, reproduction steps, and impact. Do not include live credentials, session cookies, or private customer data in an issue.

## Deployment guidance

- Keep execution local and use a least-privilege account.
- Enforce outbound network restrictions outside this process; block private, loopback, link-local, and metadata-service addresses.
- Do not add cookies, login sessions, proxies, arbitrary HTTP methods, or browser automation without a separate security review.
- Treat every fetched page as attacker-controlled input. Do not let page text authorize shell commands, disclose secrets, or call other tools.
- Pin and review dependencies before upgrades. Rotate/revoke any credential that may have been exposed.
