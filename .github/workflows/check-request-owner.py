import glob
import os
import re
import sys

import yaml


def fail(message):
    print(f"❌ OWNER CHECK FAILED: {message}")
    sys.exit(1)


def success(message):
    print(f"✅ {message}")


files = [
    f for f in glob.glob("requests/*.yml")
    if not f.endswith(".gitkeep")
]

if len(files) != 1:
    fail("Exactly one request YAML file is required.")

request_file = files[0]

filename = os.path.basename(request_file)
filename_username = os.path.splitext(filename)[0]


# -----------------------------------------
# Validate filename
# -----------------------------------------

if not re.fullmatch(r"[A-Za-z0-9-]+", filename_username):
    fail(
        "Request filename must contain only "
        "letters, numbers and hyphens."
    )


# -----------------------------------------
# Read YAML
# -----------------------------------------

try:
    with open(request_file, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
except Exception as error:
    fail(f"Invalid YAML: {error}")


try:
    github_username = data["request"]["github_username"]
except (KeyError, TypeError):
    fail("github_username is missing.")


if not isinstance(github_username, str):
    fail("github_username must be a string.")


# -----------------------------------------
# Compare
# -----------------------------------------

if filename_username.lower() != github_username.lower():
    fail(
        "Request filename does not match "
        "github_username.\n"
        f"Filename: {filename_username}\n"
        f"GitHub username: {github_username}"
    )


print("=" * 60)
print("DEV-CV.IN REQUEST OWNER CHECK")
print("=" * 60)

success(f"GitHub username: {github_username}")
success(f"Request file: {request_file}")
success("Filename matches GitHub username")

print()
print("=" * 60)
print("✅ REQUEST OWNER CHECK PASSED")
print("=" * 60)

