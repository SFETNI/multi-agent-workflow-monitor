# Security

Agent Workflow Monitor is local-first and read-only by design.

## Architecture boundary

The monitor runs locally, binds to loopback by default in normal use, and reads only explicitly configured sources. It does not start, restart, patch, approve, delete, execute, or otherwise control external workflows.

The static demo has no backend service, telemetry sender, or dependency on remote assets.

Do not place credentials, private workflow records, environment files, or unrestricted filesystem roots in configuration. Keep runtime state under `.local/` or another ignored directory.

Review every adapter for strict read-only access patterns, input normalization, path restrictions, and safe error handling.

## Reporting security issues

Report vulnerabilities via GitHub Security Advisories / Private Vulnerability Reporting on this project repository.

This project intentionally does not expose a personal contact address, and does not promise a fixed response-time SLA.

## Limitations

Security tooling in this release validates scoped leakage and policy patterns used by this project. It does not claim a security certification, and it cannot guarantee all upstream user content is safe in every environment.
