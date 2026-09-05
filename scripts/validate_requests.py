#!/usr/bin/env python3

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parent.parent
REQUESTS_DIR = ROOT / "requests"
SCHEMA_FILE = ROOT / "schema" / "request.schema.json"


def load_schema():
    with SCHEMA_FILE.open() as file:
        return json.load(file)


def validate_request(request_file, validator):
    try:
        with request_file.open() as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        print(f"❌ {request_file}: Invalid JSON")
        print(f"   {error}")
        return False
    except OSError as error:
        print(f"❌ {request_file}: Cannot read file")
        print(f"   {error}")
        return False

    errors = sorted(
        validator.iter_errors(data),
        key=lambda error: list(error.path)
    )

    if errors:
        print(f"❌ {request_file}: Validation failed")

        for error in errors:
            path = ".".join(str(item) for item in error.path)
            location = path if path else "root"
            print(f"   {location}: {error.message}")

        return False

    print(f"✅ {request_file}: Valid")
    print("   Terms accepted: Y")
    return True


def main():
    if not REQUESTS_DIR.exists():
        print("No requests/ directory found.")
        sys.exit(0)

    schema = load_schema()
    validator = Draft202012Validator(schema)

    request_files = sorted(REQUESTS_DIR.glob("*.json"))

    if not request_files:
        print("No pending request files found.")
        sys.exit(0)

    success = True

    for request_file in request_files:
        if not validate_request(request_file, validator):
            success = False

    if not success:
        sys.exit(1)

    print()
    print(f"🎉 Successfully validated {len(request_files)} request(s).")


if __name__ == "__main__":
    main()
