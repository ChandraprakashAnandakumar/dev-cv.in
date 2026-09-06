#!/usr/bin/env python3

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if len(sys.argv) > 2:
    ROOT = Path(sys.argv[2]).resolve()

DOMAINS_DIR = ROOT / "domains"
REQUESTS_DIR = ROOT / "requests"
RESERVED_FILE = ROOT / "config" / "reserved-subdomains.txt"


SUBDOMAIN_PATTERN = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)


def load_reserved():
    if not RESERVED_FILE.exists():
        return set()

    return {
        line.strip().lower()
        for line in RESERVED_FILE.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    }


def domain_exists(subdomain):
    domain_file = DOMAINS_DIR / f"{subdomain}.json"
    return domain_file.exists()


def request_exists(subdomain):
    if not REQUESTS_DIR.exists():
        return False

    for request_file in REQUESTS_DIR.glob("*.json"):
        try:
            data = json.loads(request_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        if data.get("subdomain", "").lower() == subdomain:
            return True

    return False


def check_availability(subdomain):
    subdomain = subdomain.strip().lower()

    if not SUBDOMAIN_PATTERN.fullmatch(subdomain):
        return False, "Invalid subdomain format."

    if subdomain in load_reserved():
        return False, "This subdomain is reserved."

    if domain_exists(subdomain):
        return False, "This subdomain is already registered."

    if request_exists(subdomain):
        return False, "This subdomain already has a pending request."

    return True, "Subdomain is available."


def main():
    import sys

    if len(sys.argv) != 2:
        print("Usage: python3 scripts/check_availability.py <subdomain>")
        sys.exit(2)

    subdomain = sys.argv[1]

    available, message = check_availability(subdomain)

    if available:
        print(f"AVAILABLE: {subdomain}.dev-cv.in")
        print(message)
        sys.exit(0)

    print(f"UNAVAILABLE: {subdomain}.dev-cv.in")
    print(message)
    sys.exit(1)


if __name__ == "__main__":
    main()
