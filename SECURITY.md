# Security Policy

## About This Project

`dev-cv.in` is a GitHub-based developer subdomain registry that allows developers to request subdomains under `dev-cv.in`.

The project uses automated validation, GitHub Pull Requests, repository rules, and controlled Cloudflare DNS synchronization to protect the production DNS infrastructure.

## Supported Versions

Security fixes are applied to the latest version of the project available on the `main` branch.

| Version                | Supported |
| ---------------------- | --------- |
| `main`                 | ✅ Yes     |
| Older commits/releases | ❌ No      |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it privately rather than opening a public GitHub issue.

Please include:

* A clear description of the vulnerability
* Steps to reproduce the issue
* The potential security impact
* Any relevant logs, screenshots, or proof of concept
* A suggested mitigation, if available

### Please Do Not

Do not:

* Attempt to access or modify another user's systems or data
* Perform denial-of-service attacks
* Spam the service or repository
* Expose credentials, API tokens, passwords, or other secrets
* Modify production DNS records without authorization
* Use vulnerabilities to disrupt the service

## Security-Sensitive Components

The following components are considered security-sensitive:

### GitHub Actions

GitHub Actions are used to validate domain requests and synchronize approved domains with Cloudflare.

Production DNS synchronization runs only from the trusted `main` branch.

### Pull Requests

User-submitted domain requests are processed through Pull Requests.

Automated validation checks:

* Allowed file paths
* JSON schema compliance
* Domain naming rules
* Reserved subdomains
* Duplicate subdomains
* Target validation
* Request validation

### Domain Registry

Production domain records are stored under:

```text
domains/
```

User requests are submitted under:

```text
requests/
```

Untrusted Pull Requests are not permitted to directly modify production domain records.

### Cloudflare Credentials

Cloudflare API credentials are stored as GitHub Actions secrets and must never be committed to the repository.

Secrets must never be included in:

* Source code
* JSON files
* Workflow files
* Documentation
* Issues
* Pull Requests
* Commit messages

## Responsible Disclosure

Please allow reasonable time for a vulnerability to be investigated and addressed before publicly disclosing it.

Security reports will be reviewed and handled as soon as reasonably possible.

## Contact

For security issues, please use GitHub's private vulnerability reporting/security advisory mechanism for this repository when available.

For general questions or non-security issues, please open a GitHub Issue.

Thank you for helping keep `dev-cv.in` secure.
