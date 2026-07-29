# Screenshots

This directory holds documentation screenshots referenced by the project
`README.md`. No images are committed yet.

To produce them, start the lab with `docker compose up --build -d` and capture:

1. `sample-app.png`: the sample search page served through Envoy on
   `http://localhost:8080`.
2. `blocked-request.png`: the `403` JSON response returned for a blocked
   payload, for example `https://localhost:8443/search?q=SELECT%20*%20FROM%20users%3B--`.

Do not include real hostnames, credentials, tokens, or personal data in
captured images.
