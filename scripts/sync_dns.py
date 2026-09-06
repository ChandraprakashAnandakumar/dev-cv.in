#!/usr/bin/env python3

import ipaddress
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

if len(sys.argv) > 1:
    ROOT = Path(sys.argv[1]).resolve()

DOMAINS_DIR = ROOT / "domains"


def validate_target(record_type, value):
    if record_type == "CNAME":
        return bool(value) and "." in value and " " not in value

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

    records = []

    for domain_file in domain_files:
        try:
            with domain_file.open() as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            print(f"❌ {domain_file}: Invalid JSON")
            print(f"   {error}")
            sys.exit(1)

        subdomain = data.get("subdomain")
        target = data.get("target", {})

        record_type = target.get("type")
        value = target.get("value")

        if not subdomain:
            print(f"❌ {domain_file}: Missing subdomain.")
            sys.exit(1)

        if not record_type or not value:
            print(f"❌ {domain_file}: Missing DNS target.")
            sys.exit(1)

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
        return

    print(f"Found {len(records)} domain record(s).")
    print()

    for record in records:
        fqdn = f"{record['subdomain']}.dev-cv.in"

        print(f"Would configure:")
        print(f"  Domain : {fqdn}")
        print(f"  Type   : {record['type']}")
        print(f"  Target : {record['value']}")
        print(f"  Source : {record['file']}")
        print()

    print("✅ DNS dry-run completed successfully.")
    print("ℹ️ No Cloudflare API calls were made.")


if __name__ == "__main__":
    main()
