import glob
import re
import sys

import yaml


RESERVED = {
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


def fail(message):
    print(f"❌ SUBDOMAIN CHECK FAILED: {message}")
    sys.exit(1)


def success(message):
    print(f"✅ {message}")


files = [
    f for f in glob.glob("requests/*")
    if f.endswith((".yml", ".yaml"))
    and not f.endswith(".gitkeep")
]

if len(files) != 1:
    fail("Exactly one request file is required.")

current_file = files[0]

try:
    with open(current_file, "r", encoding="utf-8") as file:
        current_data = yaml.safe_load(file)
except Exception as error:
    fail(f"Invalid YAML: {error}")

try:
    requested = (
        current_data["request"]
        ["subdomain"]
        ["requested"]
        .strip()
        .lower()
    )
except (KeyError, TypeError, AttributeError):
    fail("Requested subdomain is missing.")

pattern = (
    r"^[a-z0-9]"
    r"(?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"\.dev-cv\.in$"
)

if not re.fullmatch(pattern, requested):
    fail(
        "Invalid subdomain. Use format: "
        "username.dev-cv.in"
    )

label = requested.removesuffix(".dev-cv.in")

if label in RESERVED:
    fail(
        f"'{label}' is reserved and cannot be requested."
    )

for file_path in files:
    if file_path == current_file:
        continue

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        existing = (
            data["request"]
            ["subdomain"]
            ["requested"]
            .strip()
            .lower()
        )

    except Exception:
        fail(
            f"Could not inspect existing request: {file_path}"
        )

    if existing == requested:
        fail(
            f"Subdomain '{requested}' is already requested "
            f"by {file_path}"
        )

print("=" * 60)
print("DEV-CV.IN SUBDOMAIN AVAILABILITY CHECK")
print("=" * 60)

success(f"Requested hostname: {requested}")
success("Hostname format is valid")
success("Hostname is not reserved")
success("No duplicate request found")

print()
print("=" * 60)
print("✅ SUBDOMAIN AVAILABILITY CHECK PASSED")
print("=" * 60)
