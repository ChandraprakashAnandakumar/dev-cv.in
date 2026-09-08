#!/usr/bin/env python3

import subprocess
import sys
from pathlib import PurePosixPath


ALLOWED_PREFIX = PurePosixPath("requests")
ALLOWED_SUFFIX = ".json"


def fail(message):
    print(f"❌ {message}")
    sys.exit(1)


def get_changed_files(base_sha):
    try:
        result = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                "--diff-filter=ACMR",
                f"{base_sha}...HEAD",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        fail(
            "Unable to determine changed files: "
            f"{error.stderr.strip()}"
        )

    return [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def is_allowed(path):
    pure_path = PurePosixPath(path)

    return (
        len(pure_path.parts) == 2
        and pure_path.parts[0] == ALLOWED_PREFIX
        and pure_path.parts[1].endswith(ALLOWED_SUFFIX)
        and pure_path.parts[1] != ALLOWED_SUFFIX
    )


def main():
    if len(sys.argv) != 2:
        fail("Usage: python3 scripts/check_pr_changes.py <base-sha>")

    base_sha = sys.argv[1]

    changed_files = get_changed_files(base_sha)

    if not changed_files:
        fail("No changed files were detected.")

    print("Changed files:")
    for path in changed_files:
        print(f"  - {path}")

    invalid_files = [
        path for path in changed_files
        if not is_allowed(path)
    ]

    if invalid_files:
        print()
        print("❌ Pull Request contains forbidden file changes:")

        for path in invalid_files:
            print(f"  - {path}")

        print()
        print("Only files matching requests/*.json may be changed.")
        sys.exit(1)

    print()
    print("✅ Pull Request file changes are allowed.")
    print("Only requests/*.json files were modified.")


if __name__ == "__main__":
    main()
