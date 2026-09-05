import glob
import os
import re
import socket
import sys

import requests
import yaml


DOMAIN = "dev-cv.in"

RESERVED_SUBDOMAINS = {
    "www",
    "admin",
    "api",
    "mail",
    "ftp",
    "ns1",
    "ns2",
    "status",
    "support",
    "help",
}


def fail(message):
    print(f"❌ {message}")
    sys.exit(1)


def success(message):
    print(f"✅ {message}")


files = [
    f for f in glob.glob("requests/*.yml")
    if not f.endswith(".gitkeep")
]

if len(files) == 0:
    fail("No request file found in requests/")

if len(files) > 1:
    fail("Only one request file should be changed per PR.")


request_file = files[0]

print("=" * 60)
print("DEV-CV.IN REQUEST VALIDATION")
print("=" * 60)
print(f"Request: {request_file}")
print()


# --------------------------------------------------
# YAML
# --------------------------------------------------

try:
    with open(request_file, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
except Exception as error:
    fail(f"Invalid YAML: {error}")


if not isinstance(data, dict) or "request" not in data:
    fail("Missing 'request' section.")

request = data["request"]


# --------------------------------------------------
# Required fields
# --------------------------------------------------

required = [
    "github_username",
    "owner_name",
    "email",
    "github_repository",
    "vercel",
    "subdomain",
    "project",
    "agreements",
]

for field in required:
    if field not in request:
        fail(f"Missing required field: {field}")

success("Required fields exist")


# --------------------------------------------------
# GitHub username
# --------------------------------------------------

github_username = request["github_username"]

if (
    not isinstance(github_username, str)
    or github_username == ""
    or github_username.startswith("YOUR_")
):
    fail("Invalid GitHub username.")

if not re.fullmatch(r"[A-Za-z0-9-]+", github_username):
    fail("Invalid GitHub username format.")

success(f"GitHub username: {github_username}")


# --------------------------------------------------
# GitHub repository
# --------------------------------------------------

github_repo = request["github_repository"]

if not isinstance(github_repo, dict):
    fail("github_repository must be an object.")

repo_url = github_repo.get("url", "")

if not repo_url.startswith("https://github.com/"):
    fail("GitHub repository must use https://github.com/")

expected_prefix = f"https://github.com/{github_username}/"

if not repo_url.startswith(expected_prefix):
    fail("GitHub repository must belong to the requesting GitHub username.")

success("GitHub repository format valid")


# --------------------------------------------------
# Vercel URL
# --------------------------------------------------

vercel = request["vercel"]

if not isinstance(vercel, dict):
    fail("vercel must be an object.")

vercel_url = vercel.get("deployment_url", "")

if not vercel_url.startswith("https://"):
    fail("Vercel deployment must use HTTPS.")

if ".vercel.app" not in vercel_url:
    fail("Deployment URL must be a Vercel deployment URL.")

success("Vercel deployment URL valid")


# --------------------------------------------------
# Subdomain
# --------------------------------------------------

subdomain = request["subdomain"]

if not isinstance(subdomain, dict):
    fail("subdomain must be an object.")

requested = subdomain.get("requested", "")

expected_suffix = f".{DOMAIN}"

if not requested.endswith(expected_suffix):
    fail(f"Subdomain must end with {expected_suffix}")

label = requested[: -len(expected_suffix)]

if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label):
    fail("Invalid subdomain format.")

if label in RESERVED_SUBDOMAINS:
    fail(f"'{label}' is a reserved subdomain.")

success(f"Requested subdomain: {requested}")


# --------------------------------------------------
# Project
# --------------------------------------------------

project = request["project"]

if not project.get("name"):
    fail("Project name is required.")

if not project.get("description"):
    fail("Project description is required.")

success("Project information valid")


# --------------------------------------------------
# Agreements
# --------------------------------------------------

agreements = request["agreements"]

required_agreements = [
    "github_ownership",
    "vercel_ownership",
    "dns_only",
    "deployment_responsibility",
    "acceptable_use",
    "removal_policy",
    "automated_verification",
    "one_subdomain_per_request",
    "terms",
]

for agreement in required_agreements:
    if agreements.get(agreement) is not True:
        fail(f"Agreement not accepted: {agreement}")

success("All required agreements accepted")


# --------------------------------------------------
# GitHub API verification
# --------------------------------------------------

repo_path = repo_url.replace("https://github.com/", "").rstrip("/")

api_url = f"https://api.github.com/repos/{repo_path}"

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {os.environ.get('GH_TOKEN', '')}",
}

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
        f"GitHub repository could not be verified "
        f"(HTTP {response.status_code})."
    )

repo_data = response.json()

actual_owner = repo_data.get("owner", {}).get("login", "")

if actual_owner.lower() != github_username.lower():
    fail("GitHub repository owner does not match username.")

success("GitHub repository exists")
success("GitHub repository owner verified")


# --------------------------------------------------
# Vercel deployment verification
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
    fail(f"Vercel deployment could not be reached: {error}")

if status >= 400:
    fail(f"Vercel deployment returned HTTP {status}.")

success(f"Vercel deployment reachable: HTTP {status}")
success(f"Final URL: {final_url}")


# --------------------------------------------------
# DNS verification of Vercel URL
# --------------------------------------------------

hostname = vercel_url.split("://", 1)[1].split("/", 1)[0]

try:
    addresses = socket.gethostbyname_ex(hostname)[2]
except socket.gaierror:
    fail("Vercel hostname does not resolve through DNS.")

if not addresses:
    fail("No DNS address found for Vercel hostname.")

success(f"DNS resolves: {hostname}")
print(f"   Addresses: {', '.join(addresses)}")


# --------------------------------------------------
# Final result
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
