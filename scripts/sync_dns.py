#!/usr/bin/env python3

import ipaddress
import json
import os
import re
import sys
import urllib.error
import urllib.request
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


def fail(message):
    print(f"❌ {message}")
    sys.exit(1)


def load_reserved_subdomains():
    if not RESERVED_FILE.exists():
        fail(f"Reserved-subdomain file does not exist: {RESERVED_FILE}")

    reserved = set()

    try:
        with RESERVED_FILE.open() as file:
            for line in file:
                line = line.strip().lower()

                if not line or line.startswith("#"):
                    continue

                reserved.add(line)

    except OSError as error:
        fail(f"Cannot read reserved-subdomain file: {error}")

    return reserved


def validate_subdomain(subdomain):
    return (
        isinstance(subdomain, str)
        and SUBDOMAIN_PATTERN.fullmatch(subdomain) is not None
    )


def validate_cname(value):
    if not isinstance(value, str):
        return False

    value = value.strip()

    if not value:
        return False

    if "://" in value:
        return False

    if any(character.isspace() for character in value):
        return False

    if "/" in value or "\\" in value or ":" in value:
        return False

    try:
        ipaddress.ip_address(value.rstrip("."))
        return False
    except ValueError:
        pass

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
        fail("domains/ directory does not exist.")

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
            fail(f"{domain_file}: Invalid JSON: {error}")

        except OSError as error:
            fail(f"{domain_file}: Cannot read file: {error}")

        if not isinstance(data, dict):
            fail(f"{domain_file}: Root JSON value must be an object.")

        subdomain = data.get("subdomain")
        target = data.get("target")

        if not isinstance(subdomain, str) or not subdomain:
            fail(f"{domain_file}: Missing subdomain.")

        if not validate_subdomain(subdomain):
            fail(f"{domain_file}: Invalid subdomain: {subdomain}")

        subdomain = subdomain.lower()

        if subdomain in reserved:
            fail(
                f"{domain_file}: Reserved subdomain cannot be used: "
                f"{subdomain}"
            )

        if subdomain in seen_subdomains:
            fail(f"{domain_file}: Duplicate subdomain: {subdomain}")

        seen_subdomains.add(subdomain)

        if not isinstance(target, dict):
            fail(f"{domain_file}: target must be an object.")

        record_type = target.get("type")
        value = target.get("value")

        if record_type not in {"CNAME", "A", "AAAA"}:
            fail(
                f"{domain_file}: Unsupported DNS record type: "
                f"{record_type}"
            )

        if not isinstance(value, str) or not value.strip():
            fail(f"{domain_file}: Missing DNS target.")

        value = value.strip()

        if not validate_target(record_type, value):
            fail(
                f"{domain_file}: Invalid {record_type} target: {value}"
            )

        records.append(
            {
                "file": str(domain_file),
                "subdomain": subdomain,
                "type": record_type,
                "value": value,
            }
        )

    return records


def cloudflare_request(method, url, token, payload=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    data = None

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_body = response.read().decode("utf-8")
            return json.loads(response_body)

    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        fail(
            f"Cloudflare API returned HTTP {error.code}: "
            f"{body[:500]}"
        )

    except urllib.error.URLError as error:
        fail(f"Cloudflare API request failed: {error}")


def get_existing_record(zone_id, token, fqdn, record_type):
    url = (
        f"https://api.cloudflare.com/client/v4/zones/{zone_id}"
        f"/dns_records"
        f"?type={record_type}"
        f"&name={fqdn}"
        f"&per_page=100"
    )

    result = cloudflare_request("GET", url, token)

    if not result.get("success"):
        fail("Cloudflare API failed while looking up DNS record.")

    records = result.get("result", [])

    if not records:
        return None

    return records[0]


def create_record(zone_id, token, fqdn, record_type, value):
    url = (
        f"https://api.cloudflare.com/client/v4/zones/"
        f"{zone_id}/dns_records"
    )

    payload = {
        "type": record_type,
        "name": fqdn,
        "content": value,
        "ttl": 1,
        "proxied": False,
    }

    result = cloudflare_request(
        "POST",
        url,
        token,
        payload,
    )

    if not result.get("success"):
        fail(f"Cloudflare failed to create {fqdn}.")

    print(f"✅ Created {record_type} {fqdn} → {value}")


def update_record(zone_id, token, record, fqdn, record_type, value):
    url = (
        f"https://api.cloudflare.com/client/v4/zones/"
        f"{zone_id}/dns_records/{record['id']}"
    )

    payload = {
        "type": record_type,
        "name": fqdn,
        "content": value,
        "ttl": 1,
        "proxied": False,
    }

    result = cloudflare_request(
        "PUT",
        url,
        token,
        payload,
    )

    if not result.get("success"):
        fail(f"Cloudflare failed to update {fqdn}.")

    print(f"🔄 Updated {record_type} {fqdn} → {value}")


def sync_record(zone_id, token, record):
    fqdn = f"{record['subdomain']}.{DOMAIN}"

    # Defense-in-depth:
    # The DNS name is ALWAYS generated from the validated subdomain.
    if not fqdn.endswith(f".{DOMAIN}"):
        fail(f"Unsafe DNS name generated: {fqdn}")

    existing = get_existing_record(
        zone_id,
        token,
        fqdn,
        record["type"],
    )

    if existing is None:
        create_record(
            zone_id,
            token,
            fqdn,
            record["type"],
            record["value"],
        )
        return

    if (
        existing.get("name") != fqdn
        or existing.get("type") != record["type"]
    ):
        fail(f"Unexpected existing DNS record at {fqdn}.")

    if existing.get("content") == record["value"]:
        print(
            f"✔️ Already correct: "
            f"{record['type']} {fqdn} → {record['value']}"
        )
        return

    update_record(
        zone_id,
        token,
        existing,
        fqdn,
        record["type"],
        record["value"],
    )


def main():
    print("======================================")
    print(" dev-cv.in DNS Synchronization")
    print("======================================")
    print()

    zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")
    token = os.environ.get("CLOUDFLARE_API_TOKEN")

    if not zone_id:
        fail("CLOUDFLARE_ZONE_ID is not set.")

    if not token:
        fail("CLOUDFLARE_API_TOKEN is not set.")

    records = load_domains()

    if not records:
        print("No DNS records to synchronize.")
        return

    print(f"Found {len(records)} DNS record(s).")
    print()

    for record in records:
        sync_record(zone_id, token, record)

    print()
    print("✅ DNS synchronization completed successfully.")


if __name__ == "__main__":
    main()
