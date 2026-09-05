import glob
import os
import sys

import yaml


def fail(message):
    print(f"❌ DUPLICATE CHECK FAILED: {message}")
    sys.exit(1)


def success(message):
    print(f"✅ {message}")


files = [
    f for f in glob.glob("requests/*.yml")
    if not f.endswith(".gitkeep")
]

if not files:
    fail("No request file found.")


subdomains = {}

for file_path in files:

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except Exception as error:
        fail(f"Could not read {file_path}: {error}")

    try:
        subdomain = data["request"]["subdomain"]["requested"]
    except (KeyError, TypeError):
        fail(f"Missing requested subdomain in {file_path}")

    subdomain = subdomain.lower().strip()

    if subdomain in subdomains:
        fail(
            f"Duplicate subdomain detected: {subdomain}\n"
            f"Files: {subdomains[subdomain]} and {file_path}"
        )

    subdomains[subdomain] = file_path


print("=" * 60)
print("DEV-CV.IN DUPLICATE SUBDOMAIN CHECK")
print("=" * 60)

for subdomain, file_path in subdomains.items():
    success(f"{subdomain} → {file_path}")

print()
success("No duplicate subdomains found.")

print("=" * 60)
print("✅ DUPLICATE CHECK PASSED")
print("=" * 60)
