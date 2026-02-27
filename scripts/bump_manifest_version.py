#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def bump(version: str, part: str) -> str:
    match = VERSION_RE.match(version)
    if not match:
        raise ValueError(f"Unsupported version format: {version!r}. Expected: X.Y.Z")

    major, minor, patch = (int(v) for v in match.groups())
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bump version in Home Assistant manifest.json and print new version."
    )
    parser.add_argument("manifest", type=Path, help="Path to manifest.json")
    parser.add_argument(
        "--part",
        choices=("major", "minor", "patch"),
        default="patch",
        help="Version part to bump (default: patch).",
    )
    args = parser.parse_args()

    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    current = data.get("version")
    if not isinstance(current, str):
        raise ValueError("manifest.json is missing string field: version")

    data["version"] = bump(current, args.part)
    args.manifest.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(data["version"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
