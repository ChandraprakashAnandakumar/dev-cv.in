import json
import os
import sys

import requests


def fail(message):
    print(f"❌ PR AUTHOR CHECK FAILED: {message}")
    sys.exit(1)


def success(message):
    print(f"✅ {message}")


token = os.environ.get("GH_TOKEN")

if not token:
    fail("GitHub token is missing.")


event_path = os.environ.get("GITHUB_EVENT_PATH")

if not event_path:
    fail("GITHUB_EVENT_PATH is missing.")


try:
    with open(event_path, "r", encoding="utf-8") as file:
        event = json.load(file)
except Exception as error:
    fail(f"Could not read GitHub event: {error}")


pr = event.get("pull_request")

if not pr:
    fail("This workflow must run from a Pull Request.")


pr_author = pr.get("user", {}).get("login")

if not pr_author:
    fail("Could not determine PR author.")


# Find the request file
changed_files_url = pr.get("url")

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}",
    "X-GitHub-Api-Version": "2022-11-28",
}


# Get files changed by the PR
try:
    response = requests.get(
        f"{changed_files_url}/files",
        headers=headers,
        timeout=15,
    )
except requests.RequestException as error:
    fail(f"GitHub API request failed: {error}")


if response.status_code != 200:
    fail(
        f"Could not retrieve changed files "
        f"(HTTP {response.status_code})."
    )


files = response.json()

request_files = [
    item["filename"]
    for item in files
    if item["filename"].startswith("requests/")
    and item["filename"].endswith(".yml")
]


if len(request_files) != 1:
    fail(
        "Exactly one request YAML file must be changed."
    )


request_file = request_files[0]


# Download the request file from the PR branch
repo = os.environ.get("GITHUB_REPOSITORY")
sha = pr.get("head", {}).get("sha")

if not repo or not sha:
    fail("Could not determine repository or PR commit.")


raw_url = (
    f"https://raw.githubusercontent.com/"
    f"{repo}/{sha}/{request_file}"
)


try:
    response = requests.get(
        raw_url,
        timeout=15,
    )
except requests.RequestException as error:
    fail(f"Could not retrieve request file: {error}")


if response.status_code != 200:
    fail(
        f"Could not retrieve request YAML "
        f"(HTTP {response.status_code})."
    )


import yaml

try:
    data = yaml.safe_load(response.text)
except Exception as error:
    fail(f"Invalid YAML: {error}")


try:
    requested_username = data["request"]["github_username"]
except (KeyError, TypeError):
    fail("github_username is missing from request.")


print("=" * 60)
print("DEV-CV.IN PR AUTHOR VERIFICATION")
print("=" * 60)

print(f"PR author          : {pr_author}")
print(f"Requested username : {requested_username}")
print(f"Request file       : {request_file}")


if pr_author.lower() != requested_username.lower():
    fail(
        "PR author does not match github_username."
    )


success("PR author matches requested GitHub username.")

print()
print("=" * 60)
print("✅ PR AUTHOR CHECK PASSED")
print("=" * 60)
