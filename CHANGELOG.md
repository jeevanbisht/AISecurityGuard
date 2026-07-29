# Changelog

All notable changes to this project will be documented in this file. The format
is based on Keep a Changelog, and the project follows Semantic Versioning.

## [Unreleased]

## [0.1.0] - 2026-07-28

### Added

- Envoy HTTP and HTTPS listeners with fail-closed external authorization.
- MobileBERT-backed SQL injection classification with deterministic pattern
  checks and explicit prompt-injection checks.
- Docker Compose environment for the proxy, guard, and sample web application.
- Local and remote integration test scripts.
- Optional heuristic reference filter with regression cases.
- Public project documentation, community health files, CI, and release
  automation.
- Environment-driven deployment configuration and safe example values.
- Dependency, formatting, test, and container configuration checks.
- Docker build context exclusions and screenshot capture instructions.

### Security

- Removed committed registry credentials and TLS private key material.
- Removed private deployment endpoints and raw request-body logging.
- Stopped publishing internal service ports from Docker Compose.
- Removed generated TLS material and deployment manifests from the working tree
  and broadened the ignore rules that keep them out of version control.

[Unreleased]: https://github.com/jeevanbisht/AISecurityGuard/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jeevanbisht/AISecurityGuard/releases/tag/v0.1.0

