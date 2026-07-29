# Security Policy

## Supported versions

Security fixes are applied to the latest release and the default branch.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting feature. Do not open a public
issue for an undisclosed vulnerability and do not include secrets or personal
data in reports.

Include the affected component, reproduction steps, impact, and any suggested
remediation. Maintainers will acknowledge valid reports as soon as practical
and coordinate disclosure after a fix is available.

## Deployment guidance

This repository is a demonstration project, not a production web application
firewall. Generate unique TLS keys, use a trusted certificate in production,
disable registry admin credentials in favor of workload identity, pin deployed
images by digest, and keep backend services on private networks.

