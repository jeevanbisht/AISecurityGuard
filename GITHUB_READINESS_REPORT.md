# GitHub Readiness Report

Date: 2026-07-28
Scope: full pre-publication review of the Envoy AI Guard Lab repository.

## Files removed

Generated or sensitive artifacts that were present in the working tree:

- `build/aci-deployment.yaml`, a generated Azure Container Instances manifest
  that embedded a base64-encoded RSA private key and registry credentials.
- `certs/envoy.crt` and `certs/envoy.key`, locally generated TLS material.
- `__pycache__/` directories and compiled Python bytecode.
- `.ruff_cache/`.

Removed in the earlier cleanup pass and confirmed absent:

- `aci-deployment.yaml` at the repository root.
- `run_local_lab.py`, an obsolete duplicate of the maintained Compose workflow.
- Generated CBDB database, datasets, embeddings, and trained model artifacts.

## Files renamed

Carried over from the earlier pass and verified:

- `Model/` to `model_training/`.
- `Attacker/recovered-model/` to `reference_filter/`.
- `test_azure_deployment.py` to `test_remote_deployment.py`.

## Files added in this pass

- `docs/screenshots/README.md`, capture instructions for the README placeholders.
- `.dockerignore` for `ai_model_service/`, `webserver/`, and `reference_filter/`,
  so build contexts exclude `.env` files, bytecode, and test files.

## Security issues fixed

- No secrets remain in any tracked file. A full-tree scan for passwords, API
  keys, tokens, PEM blocks, registry hostnames, tenant or subscription
  identifiers, corporate email domains, and local user paths returned only
  environment variable names and placeholder values.
- `prepare_aci_yaml.py` reads `ACR_SERVER`, `ACR_USERNAME`, and `ACR_PASSWORD`
  from the environment, fails fast when they are unset, and writes only to the
  ignored `build/` directory.
- `.gitignore` was extended to cover `bin/`, `obj/`, `node_modules/`,
  `coverage/`, `*.egg-info/`, `.ipynb_checkpoints/`, and editor backup files, in
  addition to the existing `.env`, `certs/`, `*.key`, `*.pem`, and `build/`
  rules. Coverage was verified with `git check-ignore` after regenerating
  certificates.
- A fresh Git history was initialized for this working tree, so no removed
  secret exists in any commit that will be published.
- Backend and authorization service ports remain unpublished by Docker Compose,
  request logging records only method, path, and body length, and remote TLS
  verification stays enabled unless `ALLOW_INSECURE_TLS` is set explicitly.

## Secrets removed

- One Azure Container Registry password.
- One unencrypted RSA private key and its base64-encoded copy.

Both were previously present in generated files. Treat the registry credential
and the TLS key as compromised: rotate or disable the registry credential before
publication, and never reuse the generated key.

## Personal and internal information

No usernames, internal email addresses, tenant identifiers, subscription
identifiers, machine names, private endpoints, or local developer paths were
found. The only hostnames in the repository are `localhost`, the Docker Compose
service names `ai_model_service` and `webserver`, and `example.com` or
`example.azurecr.io` placeholders.

## Dependencies

All pins were checked against the current package index. Runtime and tooling
pins are at the latest available release.

| Package | Pinned | Latest available |
| --- | --- | --- |
| `flask` | 3.1.3 | 3.1.3 |
| `torch` | 2.13.0 | 2.13.0 |
| `transformers` | 5.14.1 | 5.14.1 |
| `cryptography` | 49.0.0 | 49.0.0 |
| `pip-audit` | 2.10.1 | 2.10.1 |
| `ruff` | 0.16.0 | 0.16.0 |

Updated during publication, after Dependabot flagged them:

| Package | From | To |
| --- | --- | --- |
| `joblib` | 1.5.1 | 1.5.3 |
| `numpy` | 2.3.2 | 2.5.1 |
| `scikit-learn` | 1.7.1 | 1.9.0 |
| `tqdm` | 4.67.1 | 4.70.0 |
| `actions/checkout` | v4 | v7 |
| `actions/setup-python` | v5 | v7 |

Held back deliberately:

- `pandas` stays at 2.3.1. Version 3.0.5 is a major release with breaking
  changes, and the training dependencies are not installed locally, so the
  upgrade could not be validated against `model_training/cbdb_extractor.py`.
- The `python:3.11-slim` container base stays as is. Dependabot proposes
  `3.14-slim`, but `torch` and `transformers` wheel availability for that
  interpreter could not be verified without a working Docker daemon, and
  `pyproject.toml` targets `py311`.

`pip-audit` across all five requirement files reports no known vulnerabilities.
No unused packages were found. Dependabot is configured for every pip directory,
both Docker build contexts, and GitHub Actions, and was confirmed working on the
published repository.

## Documentation

Present and verified:

- `README.md` with description, features, architecture, screenshot placeholders,
  installation, usage, examples, configuration, development, roadmap,
  contributing, and license sections.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`, and an
  MIT `LICENSE`.
- Issue forms, pull request template, Dependabot config, CI workflow, and
  release workflow under `.github/`.
- `model_training/README.md` and `examples/requests.json` sample payloads that
  contain no sensitive data.
- All relative Markdown links resolve.

## Validation

| Check | Result |
| --- | --- |
| `ruff check .` | Passed |
| `ruff format --check .` | Passed, 14 files already formatted |
| `ai_model_service` unit tests | 6 passed |
| `reference_filter` unit tests | 3 passed |
| `python -m compileall` | Passed |
| `pip-audit` on all requirement files | No known vulnerabilities |
| `docker compose config --quiet` | Valid |
| Relative Markdown links | No broken links |
| Secret and PII scan | No findings |
| Docker image build | Not run, local Docker daemon unavailable. CI builds both images. |

## Publication

The repository was published to
[`jeevanbisht/AISecurityGuard`](https://github.com/jeevanbisht/AISecurityGuard)
as a public repository with the recommended description and topics applied. The
target repository was empty beforehand, so the clean history created during this
review is the only history it contains.

## Remaining TODOs

- Rotate or disable the Azure Container Registry credential that was previously
  written into the generated manifest.
- The published repository `jeevanbisht/AISecurityGuard` was empty before the
  first push, so the clean history is the only history it contains.
- Start Docker Desktop and run `docker compose build --pull` once before the
  first release, since image builds could not be exercised locally.
- Capture the two screenshots described in `docs/screenshots/README.md`.
- Enable GitHub private vulnerability reporting so `SECURITY.md` is actionable.
- Decide on the `pandas` 3.x and `python:3.14-slim` upgrades once a Docker
  daemon is available to validate them.
- Optional hardening not applied because it could not be build-tested: run the
  container images as a non-root user and set `HF_HOME` so the prefetched
  MobileBERT cache stays readable.

## Recommended GitHub repository description

Educational Envoy ext_authz lab that combines MobileBERT and deterministic
checks to block SQL injection and prompt-injection payloads.

## Recommended repository topics

`envoy`, `ext-authz`, `api-security`, `sql-injection`, `prompt-injection`,
`machine-learning`, `flask`, `docker-compose`, `security-lab`, `mobilebert`

## Suggested release version

`v0.1.0`

## Suggested commit message

```text
chore: prepare repository for public release

Remove generated TLS material and deployment manifests, extend ignore rules,
add Docker build context exclusions and screenshot placeholders, and refresh
the readiness report after a full lint, test, audit, and secret scan.
```
