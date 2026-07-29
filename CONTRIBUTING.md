# Contributing

Thank you for helping improve Envoy AI Guard Lab.

## Development setup

1. Fork and clone the repository.
2. Copy `.env.example` to `.env` and adjust only the values you need.
3. Create a virtual environment and install development dependencies:

   ```bash
   python -m venv .venv
   python -m pip install -r requirements-dev.txt
   python -m pip install -r ai_model_service/requirements.txt
   python -m pip install -r webserver/requirements.txt
   ```

4. Generate local TLS material with `python generate_certs.py`.
5. Run the focused unit tests and `ruff check .` before submitting.

## Pull requests

Keep changes focused, add tests for behavioral changes, and update documentation
when configuration or user-facing behavior changes. Do not commit credentials,
private keys, generated model files, datasets, or deployment manifests.

By contributing, you agree that your contributions are licensed under the MIT
License.
