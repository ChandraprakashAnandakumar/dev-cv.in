#!/usr/bin/env python3

import ipaddress
import json
import re
import sys
from pathlib import Path


DOMAIN = "dev-cv.in"

ROOT = Path(__file__).resolve().parent.parent

if len(sys.argv) > 1:
    ROOT = Path(sys.argv[1]).resolve()

DOMAINS_DIR = ROOT / "domains"
RESERVED_FILE = ROOT / "config" / "reserved-subdomains.txt"

SUBDOMAIN_PATTERN = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)

HOSTNAME_LABEL_PATTERN = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
)


def load_reserved_subdomains():
    if not RESERVED_FILE.exists():
        print(f"❌ Reserved-subdomain file does not exist: {RESERVED_FILE}")
        sys.exit(1)

    reserved = set()

    try:
        with RESERVED_FILE.open() as file:
            for line in file:
                line = line.strip().lower()

                if not line or line.startswith("#"):
                    continue

                reserved.add(line)

    except OSError as error:
        print(f"❌ Cannot read reserved-subdomain file.")
        print(f"   {error}")
        sys.exit(1)

    return reserved


def validate_subdomain(subdomain):
    if not isinstance(subdomain, str):
        return False

    if not SUBDOMAIN_PATTERN.fullmatch(subdomain):
        return False

    return True


def validate_cname(value):
    if not isinstance(value, str):
        return False

    value = value.strip()

    if not value:
        return False

    # DNS CNAME targets must not contain URL schemes.
    if "://" in value:
        return False

    # Do not allow paths, ports, whitespace, or control characters.
    if any(character.isspace() for character in value):
        return False

    if "/" in value or "\\" in value or ":" in value:
        return False

    # CNAME target must be a hostname, not an IP address.
    try:
        ipaddress.ip_address(value.rstrip("."))
        return False
    except ValueError:
        pass

    # Remove an optional trailing DNS dot.
    hostname = value.rstrip(".")

    if not hostname or len(hostname) > 253:
        return False

    labels = hostname.split(".")

    if len(labels) < 2:
        return False

    for label in labels:
        if not HOSTNAME_LABEL_PATTERN.fullmatch(label):
            return False

    return True


def validate_target(record_type, value):
    if record_type == "CNAME":
        return validate_cname(value)

    if record_type == "A":
        try:
            ipaddress.IPv4Address(value)
            return True
        except ValueError:
            return False

    if record_type == "AAAA":
        try:
            ipaddress.IPv6Address(value)
            return True
        except ValueError:
            return False

    return False


def load_domains():
    if not DOMAINS_DIR.exists():
        print("❌ domains/ directory does not exist.")
        sys.exit(1)

    domain_files = sorted(DOMAINS_DIR.glob("*.json"))

    if not domain_files:
        print("No domain records found.")
        return []

    reserved = load_reserved_subdomains()

    records = []
    seen_subdomains = set()

    for domain_file in domain_files:
        try:
            with domain_file.open() as file:
                data = json.load(file)

        except json.JSONDecodeError as error:
            print(f"❌ {domain_file}: Invalid JSON")
            print(f"   {error}")
            sys.exit(1)

        except OSError as error:
            print(f"❌ {domain_file}: Cannot read file")
            print(f"   {error}")
            sys.exit(1)

        if not isinstance(data, dict):
            print(f"❌ {domain_file}: Root JSON value must be an object.")
            sys.exit(1)

        subdomain = data.get("subdomain")
        target = data.get("target")

        if not isinstance(subdomain, str) or not subdomain:
            print(f"❌ {domain_file}: Missing subdomain.")
            sys.exit(1)

        if not validate_subdomain(subdomain):
            print(
                f"❌ {domain_file}: Invalid subdomain: {subdomain}"
            )
            sys.exit(1)

        subdomain = subdomain.lower()

        if subdomain in reserved:
            print(
                f"❌ {domain_file}: Reserved subdomain cannot be used: "
                f"{subdomain}"
            )
            sys.exit(1)

        if subdomain in seen_subdomains:
            print(
                f"❌ {domain_file}: Duplicate subdomain: {subdomain}"
            )
            sys.exit(1)

        seen_subdomains.add(subdomain)

        if not isinstance(target, dict):
            print(f"❌ {domain_file}: target must be an object.")
            sys.exit(1)

        record_type = target.get("type")
        value = target.get("value")

        if record_type not in {"CNAME", "A", "AAAA"}:
            print(
                f"❌ {domain_file}: Unsupported DNS record type: "
                f"{record_type}"
            )
            sys.exit(1)

        if not isinstance(value, str) or not value.strip():
            print(f"❌ {domain_file}: Missing DNS target.")
            sys.exit(1)

        value = value.strip()

        if not validate_target(record_type, value):
            print(
                f"❌ {domain_file}: Invalid {record_type} target: {value}"
            )
            sys.exit(1)

        records.append(
            {
                "file": str(domain_file),
                "subdomain": subdomain,
                "type": record_type,
                "value": value,
            }
        )

    return records


def main():
    print("======================================")
    print(" dev-cv.in DNS Synchronization")
    print(" DRY RUN - No DNS changes will be made")
    print("======================================")
    print()

    records = load_domains()

    if not records:
        print("No DNS records to synchronize.")
        return

    print(f"Found {len(records)} domain record(s).")
    print()

    for record in records:
        fqdn = f"{record['subdomain']}.{DOMAIN}"

        print("Would configure:")
        print(f"  Domain : {fqdn}")
        print(f"  Type   : {record['type']}")
        print(f"  Target : {record['value']}")
        print(f"  Source : {record['file']}")
        print()

    print("✅ DNS dry-run completed successfully.")
    print("ℹ️ No Cloudflare API calls were made.")


if __name__ == "__main__":
    main()
