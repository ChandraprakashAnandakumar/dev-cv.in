# Contributing to dev-cv.in

Thank you for your interest in contributing to **dev-cv.in**! 🚀

dev-cv.in is an open-source developer subdomain platform that provides free subdomains for developers, portfolios, projects, blogs, documentation, and other legitimate developer-related websites.

We welcome contributions that improve the platform's security, reliability, automation, documentation, and developer experience.

## 🌐 Request a Subdomain

If you want to request a free subdomain, follow the instructions in the project README.

Subdomain requests must be submitted through the designated request process.

Example:

```text
yourname.dev-cv.in
```

Do not directly modify files under:

```text
domains/
```

Production domain records are maintained through the approved project workflow.

## 🛠️ Development Contributions

Before making changes:

1. Fork the repository.
2. Clone your fork.
3. Create a new branch.
4. Make your changes.
5. Test your changes locally.
6. Commit your changes.
7. Push your branch.
8. Open a Pull Request.

Example:

```bash
git clone https://github.com/ChandraprakashAnandakumar/dev-cv.in.git
cd dev-cv.in

git checkout -b feature/my-change
```

After making changes:

```bash
git add .
git commit -m "Describe your change"
git push origin feature/my-change
```

Then open a Pull Request against the `main` branch.

## 🔐 Security

Security is a priority for this project.

Please do not publicly disclose security vulnerabilities or expose secrets such as:

* Cloudflare API tokens
* GitHub tokens
* Passwords
* API keys
* Access credentials

For security vulnerabilities, please follow the instructions in [`SECURITY.md`](SECURITY.md).

## 🤖 GitHub Actions

Pull Requests are automatically validated using GitHub Actions.

Validation may include:

* JSON schema validation
* Domain-name validation
* Reserved-subdomain checks
* Duplicate-subdomain checks
* Request validation
* Allowed-file checks
* DNS target validation
* Security checks

Pull Requests must pass the required checks before they can be merged.

## 📁 File Changes

For developer subdomain requests, only the approved request format should be used:

```text
requests/*.json
```

Do not modify production domain records as part of a normal subdomain request.

Production records under:

```text
domains/
```

are managed through the project's approved maintainer workflow.

## 📝 Pull Request Guidelines

Please make your Pull Request:

* Clear
* Focused
* Easy to review
* Properly tested
* Related to the project's goals

Use a meaningful title.

Good:

```text
Add validation for IPv6 targets
```

Avoid:

```text
Update
```

Include a short description explaining:

* What changed
* Why it was needed
* How it was tested

## ✅ Before Opening a Pull Request

Please verify:

```text
☐ Changes are related to the issue or feature
☐ No secrets or credentials are included
☐ Tests pass locally
☐ JSON files are valid
☐ Documentation is updated when necessary
☐ No unnecessary files were modified
☐ Pull Request description explains the changes
```

## 🚫 Prohibited Use

The `dev-cv.in` service must not be used for:

* Phishing
* Malware
* Fraud
* Spam
* Illegal activities
* Credential harvesting
* Malicious redirects
* Abuse of third-party services
* Content intended to harm or compromise systems

The maintainers reserve the right to reject or remove domains that violate the project's policies.

## 👥 Maintainer Review

All contributions are subject to maintainer review.

A Pull Request may be:

* Approved
* Requested for changes
* Rejected
* Closed

Passing automated checks does not guarantee acceptance.

The maintainer may perform additional security or policy checks before merging.

## 📜 License

By contributing to this project, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).

Thank you for helping improve **dev-cv.in**! ❤️

**Build. Share. Deploy.**

🌐 https://dev-cv.in
