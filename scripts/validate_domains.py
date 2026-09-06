#!/usr/bin/env python3

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parent.parent

if len(sys.argv) > 1:
    ROOT = Path(sys.argv[1]).resolve()

DOMAINS_DIR = ROOT / "domains"
SCHEMA_FILE = ROOT / "schema" / "domain.schema.json"


def load_schema():
    with SCHEMA_FILE.open() as file:
        return json.load(file)


def validate_domain(domain_file, validator):
    try:
        with domain_file.open() as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        print(f"❌ {domain_file}: Invalid JSON")
        print(f"   {error}")
        return False

    errors = sorted(
        validator.iter_errors(data),
        key=lambda error: list(error.path)
    )

    if errors:
        print(f"❌ {domain_file}: Validation failed")

        for error in errors:
            path = ".".join(str(item) for item in error.path)
            location = path if path else "root"
            print(f"   {location}: {error.message}")

        return False

    print(f"✅ {domain_file}: Valid")
    return True


def main():
    if not DOMAINS_DIR.exists():
        print("❌ domains/ directory does not exist.")
        sys.exit(1)

    schema = load_schema()
    validator = Draft202012Validator(schema)

    domain_files = sorted(DOMAINS_DIR.glob("*.json"))

    if not domain_files:
        print("No domain files found.")
        sys.exit(0)

    success = True

    for domain_file in domain_files:
        if not validate_domain(domain_file, validator):
            success = False

    if not success:
        sys.exit(1)

    print()
    print(f"🎉 Successfully validated {len(domain_files)} domain file(s).")


if __name__ == "__main__":
    main()
