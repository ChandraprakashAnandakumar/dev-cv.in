import glob
import os
import re
import socket
import sys
from urllib.parse import urlparse

import requests
import yaml


DOMAIN = "dev-cv.in"

RESERVED_SUBDOMAINS = {
    "www",
    "admin",
    "api",
    "app",
    "mail",
    "ftp",
    "ns1",
    "ns2",
    "status",
    "support",
    "help",
    "docs",
    "blog",
    "cdn",
    "assets",
}

ALLOWED_PROJECT_CATEGORIES = {
    "portfolio",
    "project",
    "blog",
    "documentation",
    "open-source",
    "other",
}


def fail(message):
    print(f"❌ VALIDATION FAILED: {message}")
    sys.exit(1)


def success(message):
    print(f"✅ {message}")


def require_string(value, field):
    if not isinstance(value, str) or not value.strip():
        fail(f"{field} must be a non-empty string.")

    return value.strip()


def validate_url(value, field):
    try:
        parsed = urlparse(value)
    except Exception:
        fail(f"Invalid {field}.")

    if parsed.scheme != "https":
        fail(f"{field} must use HTTPS.")

    if not parsed.netloc:
        fail(f"{field} must contain a valid hostname.")

    return parsed


# --------------------------------------------------
# FIND REQUEST
# --------------------------------------------------

files = [
    f for f in glob.glob("requests/*")
    if f.endswith((".yml", ".yaml"))
    and not f.endswith(".gitkeep")
]

if len(files) == 0:
    fail("No request file found in requests/.")

if len(files) > 1:
    fail("Only one request file should exist in a PR.")

request_file = files[0]

print("=" * 60)
print("DEV-CV.IN REQUEST VALIDATION")
print("=" * 60)
print(f"Request file: {request_file}")
print()


# --------------------------------------------------
# YAML
# --------------------------------------------------

try:
    with open(request_file, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
except Exception as error:
    fail(f"Invalid YAML: {error}")


if not isinstance(data, dict):
    fail("Root YAML structure must be an object.")

if set(data.keys()) != {"request"}:
    fail("YAML may contain only the 'request' section.")

request = data["request"]

if not isinstance(request, dict):
    fail("'request' must be an object.")


# --------------------------------------------------
# TOP LEVEL FIELDS
# --------------------------------------------------

allowed_fields = {
    "github_username",
    "owner_name",
    "email",
    "github_repository",
    "vercel",
    "subdomain",
    "project",
    "agreements",
}

missing = allowed_fields - set(request.keys())
unknown = set(request.keys()) - allowed_fields

if missing:
    fail(f"Missing required fields: {', '.join(sorted(missing))}")

if unknown:
    fail(f"Unknown fields are not allowed: {', '.join(sorted(unknown))}")

success("Request structure is valid")


# --------------------------------------------------
# GITHUB USERNAME
# --------------------------------------------------

github_username = require_string(
    request["github_username"],
    "github_username",
)

if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", github_username):
    fail("Invalid GitHub username format.")

if github_username.startswith("YOUR_"):
    fail("Template GitHub username has not been replaced.")

success(f"GitHub username: {github_username}")


# --------------------------------------------------
# OWNER NAME
# --------------------------------------------------

owner_name = require_string(
    request["owner_name"],
    "owner_name",
)

if len(owner_name) < 2 or len(owner_name) > 100:
    fail("owner_name must contain 2-100 characters.")

success("Owner name valid")


# --------------------------------------------------
# EMAIL
# --------------------------------------------------

email = require_string(
    request["email"],
    "email",
)

email_pattern = (
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
)

if not re.fullmatch(email_pattern, email):
    fail("Invalid email address.")

if len(email) > 254:
    fail("Email address is too long.")

success("Email format valid")


# --------------------------------------------------
# GITHUB REPOSITORY
# --------------------------------------------------

github_repository = request["github_repository"]

if not isinstance(github_repository, dict):
    fail("github_repository must be an object.")

if set(github_repository.keys()) != {
    "url",
    "owner_confirmed",
}:
    fail(
        "github_repository must contain only "
        "'url' and 'owner_confirmed'."
    )

repo_url = require_string(
    github_repository["url"],
    "github_repository.url",
)

validate_url(repo_url, "GitHub repository URL")

parsed_repo = urlparse(repo_url)

if parsed_repo.netloc.lower() != "github.com":
    fail("GitHub repository must belong to github.com.")

repo_parts = [
    part
    for part in parsed_repo.path.strip("/").split("/")
    if part
]

if len(repo_parts) != 2:
    fail(
        "GitHub repository URL must be in the format "
        "https://github.com/username/repository"
    )

repo_owner = repo_parts[0]
repo_name = repo_parts[1]

if repo_owner.lower() != github_username.lower():
    fail(
        "GitHub repository owner must match github_username."
    )

if not re.fullmatch(
    r"[A-Za-z0-9_.-]+",
    repo_name,
):
    fail("Invalid GitHub repository name.")

if github_repository["owner_confirmed"] is not True:
    fail("GitHub repository ownership must be confirmed.")

success("GitHub repository information valid")


# --------------------------------------------------
# VERCEL
# --------------------------------------------------

vercel = request["vercel"]

if not isinstance(vercel, dict):
    fail("vercel must be an object.")

if set(vercel.keys()) != {
    "deployment_url",
    "ownership_confirmed",
}:
    fail(
        "vercel must contain only "
        "'deployment_url' and 'ownership_confirmed'."
    )

vercel_url = require_string(
    vercel["deployment_url"],
    "vercel.deployment_url",
)

parsed_vercel = validate_url(
    vercel_url,
    "Vercel deployment URL",
)

hostname = parsed_vercel.hostname.lower()

if not hostname.endswith(".vercel.app"):
    fail(
        "Deployment must use a *.vercel.app hostname."
    )

if hostname == "vercel.app":
    fail("Invalid Vercel deployment hostname.")

if vercel["ownership_confirmed"] is not True:
    fail("Vercel ownership must be confirmed.")

success("Vercel deployment information valid")


# --------------------------------------------------
# SUBDOMAIN
# --------------------------------------------------

subdomain = request["subdomain"]

if not isinstance(subdomain, dict):
    fail("subdomain must be an object.")

if set(subdomain.keys()) != {
    "requested",
    "type",
}:
    fail(
        "subdomain must contain only "
        "'requested' and 'type'."
    )

requested = require_string(
    subdomain["requested"],
    "subdomain.requested",
).lower()

subdomain_type = require_string(
    subdomain["type"],
    "subdomain.type",
).lower()

if subdomain_type != "portfolio":
    fail("Only 'portfolio' subdomains are currently supported.")

pattern = (
    r"^[a-z0-9]"
    r"(?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"\.dev-cv\.in$"
)

if not re.fullmatch(pattern, requested):
    fail(
        "Invalid subdomain. Example: "
        "username.dev-cv.in"
    )

label = requested[: -(len(DOMAIN) + 1)]

if label in RESERVED_SUBDOMAINS:
    fail(
        f"'{label}' is a reserved subdomain."
    )

success(f"Requested subdomain: {requested}")


# --------------------------------------------------
# PROJECT
# --------------------------------------------------

project = request["project"]

if not isinstance(project, dict):
    fail("project must be an object.")

if set(project.keys()) != {
    "name",
    "description",
    "category",
}:
    fail(
        "project must contain only "
        "'name', 'description', and 'category'."
    )

project_name = require_string(
    project["name"],
    "project.name",
)

project_description = require_string(
    project["description"],
    "project.description",
)

category = require_string(
    project["category"],
    "project.category",
).lower()

if not 2 <= len(project_name) <= 100:
    fail("Project name must contain 2-100 characters.")

if not 10 <= len(project_description) <= 500:
    fail(
        "Project description must contain "
        "10-500 characters."
    )

if category not in ALLOWED_PROJECT_CATEGORIES:
    fail(
        "Invalid project category. Allowed values: "
        + ", ".join(sorted(ALLOWED_PROJECT_CATEGORIES))
    )

success("Project information valid")


# --------------------------------------------------
# AGREEMENTS
# --------------------------------------------------

agreements = request["agreements"]

if not isinstance(agreements, dict):
    fail("agreements must be an object.")

required_agreements = {
    "github_ownership",
    "vercel_ownership",
    "dns_only",
    "deployment_responsibility",
    "acceptable_use",
    "removal_policy",
    "automated_verification",
    "one_subdomain_per_request",
    "terms",
}

if set(agreements.keys()) != required_agreements:
    fail(
        "Agreement fields do not exactly match "
        "the required agreement list."
    )

for agreement in required_agreements:
    if agreements[agreement] is not True:
        fail(
            f"Agreement not accepted: {agreement}"
        )

success("All required agreements accepted")


# --------------------------------------------------
# GITHUB API VERIFICATION
# --------------------------------------------------

repo_path = f"{repo_owner}/{repo_name}"

api_url = (
    f"https://api.github.com/repos/{repo_path}"
)

headers = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

token = os.environ.get("GH_TOKEN")

if token:
    headers["Authorization"] = f"Bearer {token}"

try:
    response = requests.get(
        api_url,
        headers=headers,
        timeout=15,
    )
except requests.RequestException as error:
    fail(f"GitHub API request failed: {error}")

if response.status_code != 200:
    fail(
        "GitHub repository could not be verified "
        f"(HTTP {response.status_code})."
    )

repo_data = response.json()

actual_owner = (
    repo_data
    .get("owner", {})
    .get("login", "")
)

if actual_owner.lower() != github_username.lower():
    fail(
        "GitHub API owner does not match "
        "github_username."
    )

success("GitHub repository exists")
success("GitHub repository owner verified")


# --------------------------------------------------
# VERCEL DEPLOYMENT VERIFICATION
# --------------------------------------------------

try:
    response = requests.get(
        vercel_url,
        timeout=20,
        allow_redirects=True,
    )

    status = response.status_code
    final_url = response.url

except requests.RequestException as error:
    fail(
        f"Vercel deployment could not be reached: {error}"
    )

if status >= 400:
    fail(
        f"Vercel deployment returned HTTP {status}."
    )

success(
    f"Vercel deployment reachable: HTTP {status}"
)

success(f"Final URL: {final_url}")


# --------------------------------------------------
# DNS VERIFICATION
# --------------------------------------------------

try:
    addresses = socket.gethostbyname_ex(
        hostname
    )[2]
except socket.gaierror:
    fail(
        "Vercel hostname does not resolve through DNS."
    )

if not addresses:
    fail("No DNS address found for Vercel hostname.")

success(f"DNS resolves: {hostname}")


# --------------------------------------------------
# FINAL RESULT
# --------------------------------------------------

print()
print("=" * 60)
print("✅ AUTOMATED VALIDATION PASSED")
print("=" * 60)
print()
print(f"Subdomain : {requested}")
print(f"GitHub    : {repo_url}")
print(f"Vercel    : {vercel_url}")
print()
print("STATUS: WAITING FOR ADMIN APPROVAL")
