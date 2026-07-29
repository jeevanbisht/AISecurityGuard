# Changelog

All notable changes to this project will be documented in this file. The format
is based on Keep a Changelog, and the project follows Semantic Versioning.

## [Unreleased]

### Added

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

