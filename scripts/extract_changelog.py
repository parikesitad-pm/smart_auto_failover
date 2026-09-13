#!/usr/bin/env python3
"""
AutoFailover 3.0 Changelog Section Extractor
Author: parikesitad-pm
© 2026
"""

import sys
import os
import re


def extract_changelog(version_file: str, changelog_file: str) -> str:
    if not os.path.exists(version_file):
        return f"Release version file not found: {version_file}"
    if not os.path.exists(changelog_file):
        return f"Changelog file not found: {changelog_file}"

    with open(version_file, "r", encoding="utf-8") as f:
        version = f.read().strip().lstrip("v")

    with open(changelog_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Match section ## [version] or ## [vversion] up to next ##
    pattern = rf"##\s+\[(?:v)?{re.escape(version)}\][^\n]*\n(.*?)(?=\n##\s+\[|\Z)"
    match = re.search(pattern, content, re.DOTALL)

    if match:
        return match.group(1).strip()

    # Fallback to [Unreleased] if specific version not yet tagged
    unreleased_pattern = r"##\s+\[Unreleased\][^\n]*\n(.*?)(?=\n##\s+\[|\Z)"
    unreleased_match = re.search(unreleased_pattern, content, re.DOTALL)
    if unreleased_match:
        return f"### AutoFailover v{version}\n\n" + unreleased_match.group(1).strip()

    return f"AutoFailover {version} Release"


if __name__ == "__main__":
    v_file = sys.argv[1] if len(sys.argv) > 1 else "desktop/VERSION"
    c_file = sys.argv[2] if len(sys.argv) > 2 else "CHANGELOG.md"
    print(extract_changelog(v_file, c_file))
