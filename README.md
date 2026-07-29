# Envoy AI Guard Lab

Envoy AI Guard Lab is a reference environment for evaluating request filtering
with Envoy's External Authorization (`ext_authz`) filter. A Flask service uses
a MobileBERT classifier for SQL injection detection and a small set of explicit
prompt-injection checks before Envoy forwards traffic to a sample application.

This project is educational. It is not a replacement for a production web
application firewall, secure coding, authentication, or authorization.

## Features

- Envoy HTTP and HTTPS listeners with fail-closed external authorization.
- MobileBERT-backed SQL injection classification.
- Explicit prompt-injection and unsafe-payload checks.
- Docker Compose environment for the proxy, guard, and sample web application.
- Local and remote integration test scripts.
- Optional CBDB model-training examples in `model_training/`.
- Heuristic reference filter with regression cases in `reference_filter/`.

## Architecture

```text
Client
  |
  v
Envoy Proxy ---- authorization request ----> AI Guard
  |                                         | 200 allow
  |<----------------------------------------| 403 block
  v
Sample Web Application
```

Envoy is the only component that publishes host ports. The guard and sample
application remain on the private Compose network. See
[`architecture.html`](architecture.html) for an interactive walkthrough.

## Screenshots

Screenshots are not committed yet. Capture instructions and the expected file
names are in [`docs/screenshots/README.md`](docs/screenshots/README.md).

| View | Placeholder |
| --- | --- |
| Sample search page through Envoy | `docs/screenshots/sample-app.png` |
| Blocked request response | `docs/screenshots/blocked-request.png` |

## Installation

Requirements:

- Docker with Docker Compose
- Python 3.11 or later for local tooling

```bash
git clone https://github.com/jeevanbisht/AISecurityGuard.git
cd AISecurityGuard
cp .env.example .env
python generate_certs.py
docker compose up --build -d
```

The model is downloaded during the first guard image build.

## Usage

Open `http://localhost:8080` or use the HTTPS listener with the locally
generated self-signed certificate:

```bash
curl -k "https://localhost:8443/search?q=laptops"
curl -k "https://localhost:8443/search?q=SELECT%20*%20FROM%20users%3B--"
```

The first request should return `200`. The second should return `403`.

Run the end-to-end check:

```bash
python test_lab.py
```

Example request payloads are available in [`examples/requests.json`](examples/requests.json).

## Configuration

Copy `.env.example` to `.env`. Supported guard settings:

| Variable | Default | Purpose |
| --- | --- | --- |
| `SQL_INJECTION_MODEL_ID` | `cssupport/mobilebert-sql-injection-detect` | Compatible Hugging Face model |
| `SQL_INJECTION_TOKENIZER_ID` | `google/mobilebert-uncased` | Tokenizer expected by the default model |
| `SQL_INJECTION_THRESHOLD` | `0.70` | Probability at or above which a request is blocked |
| `LOG_LEVEL` | `INFO` | Python logging level |

Remote test and Azure deployment variables are documented in `.env.example`.
Never commit `.env`, generated certificates, registry credentials, or generated
deployment manifests.

## Azure Container Instances example

The optional generator reads credentials and deployment names from environment
variables and writes an ignored file at `build/aci-deployment.yaml`:

```bash
python generate_certs.py
python prepare_aci_yaml.py
az container create --resource-group <resource-group> \
  --file build/aci-deployment.yaml
```

Use workload identity and image digests for production deployments.

## Development

```bash
python -m venv .venv
python -m pip install -r requirements-dev.txt
python -m pip install -r ai_model_service/requirements.txt
python -m pip install -r webserver/requirements.txt
ruff check .
ruff format --check .
```

Run focused unit tests:

```bash
cd ai_model_service && python -m unittest discover
cd ../reference_filter && python -m unittest discover
```

The CBDB training pipeline has separate dependencies and setup instructions in
[`model_training/README.md`](model_training/README.md). Generated datasets and model artifacts are
intentionally excluded from version control.

## Roadmap

- Add model calibration and benchmark reporting.
- Add structured observability without logging request contents.
- Add signed, digest-pinned container release artifacts.
- Add configurable policies for routes and content types.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Please report security issues using
the process in [`SECURITY.md`](SECURITY.md).

## License

Licensed under the [MIT License](LICENSE).
