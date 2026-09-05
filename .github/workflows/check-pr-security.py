import os
import subprocess
import sys


PROTECTED_PATHS = [
    ".github/",
    "schema/",
    "docs/",
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
]


def fail(message):
    print(f"❌ SECURITY CHECK FAILED: {message}")
    sys.exit(1)


def success(message):
    print(f"✅ {message}")


# Get files changed by the PR
try:
    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "origin/main...HEAD",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
except subprocess.CalledProcessError as error:
    fail(f"Unable to determine changed files: {error}")


changed_files = [
    line.strip()
    for line in result.stdout.splitlines()
    if line.strip()
]

if not changed_files:
    fail("No changed files detected.")


print("=" * 60)
print("DEV-CV.IN PR SECURITY CHECK")
print("=" * 60)

print("\nChanged files:")
for path in changed_files:
    print(f"  - {path}")


# --------------------------------------------------
# Check protected files
# --------------------------------------------------

for path in changed_files:

    for protected in PROTECTED_PATHS:

        if path == protected or path.startswith(protected):

            fail(
                f"Protected file/directory cannot be modified: {path}"
            )


# --------------------------------------------------
# Only requests/ files allowed
# --------------------------------------------------

for path in changed_files:

    if not path.startswith("requests/"):
        fail(
            f"Only files inside requests/ may be changed. "
            f"Found: {path}"
        )


# --------------------------------------------------
# Only YAML request files
# --------------------------------------------------

for path in changed_files:

    if not path.endswith(".yml") and not path.endswith(".yaml"):
        fail(
            f"Request files must be YAML: {path}"
        )


# --------------------------------------------------
# Only one request file
# --------------------------------------------------

request_files = [
    path
    for path in changed_files
    if path.startswith("requests/")
]


if len(request_files) != 1:
    fail(
        "A Pull Request must contain exactly one request file."
    )


request_file = request_files[0]


# --------------------------------------------------
# Validate filename
# --------------------------------------------------

filename = os.path.basename(request_file)

username = os.path.splitext(filename)[0]


if not username:
    fail("Request filename cannot be empty.")


if username in {".gitkeep"}:
    fail("Invalid request filename.")


print()
success(f"Request file detected: {request_file}")
success("No protected files modified")
success("Only requests/ directory modified")
success("Request file format is valid")

print()
print("=" * 60)
print("✅ PR SECURITY CHECK PASSED")
print("=" * 60)
