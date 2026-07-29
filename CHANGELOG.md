# Changelog

All notable changes to this project will be documented in this file. The format
is based on Keep a Changelog, and the project follows Semantic Versioning.

## [Unreleased]

## [0.2.0] - 2026-07-28

### Removed

- The `model_training/` China Biographical Database extraction and training
  pipeline. It shared no code with the Envoy guard and was never exercised by
  CI, so the project is now scoped to the request-filtering lab it describes.
- The `pandas`, `numpy`, `scikit-learn`, `joblib`, and `tqdm` dependencies,
  which were only used by that pipeline.

### Changed

- Updated `README.md`, `.gitignore`, and the Ruff configuration to drop the
  training pipeline references.
- Moved `actions/checkout` to v7 and `actions/setup-python` to v7.

### Fixed

- Dependabot no longer opens a duplicate pull request for every pip upgrade.
  The root pip entry already scans the repository recursively, so the
  per-directory entries were redundant.

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

[Unreleased]: https://github.com/jeevanbisht/AISecurityGuard/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/jeevanbisht/AISecurityGuard/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jeevanbisht/AISecurityGuard/releases/tag/v0.1.0

