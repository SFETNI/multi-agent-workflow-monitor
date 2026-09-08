# Changelog

## 0.1.0

- Replaced the simplified demo/runtime with the accepted public v2 renderer.
- Restricted complete app inputs to normalized `PublicSnapshot` models.
- Added host-metrics load-average portability so Windows environments use `psutil.getloadavg()` when `os.getloadavg()` is unavailable.
- Added regression coverage for the load-average fallback and strengthened identity-safety assertions for host metrics.
- Tightened adapter, rendering, and release checks; finalized v0.1.0 publication metadata (license, security, contributing, changelog).
