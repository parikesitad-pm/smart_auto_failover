#!/usr/bin/env bash
# AutoFailover 3.0 Release Verification & Dispatch Script
# Author: parikesitad-pm
# © 2026

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VERSION_FILE="desktop/VERSION"
CHANGELOG_FILE="CHANGELOG.md"

if [ ! -f "$VERSION_FILE" ]; then
    echo "❌ Error: $VERSION_FILE not found."
    exit 1
fi

VERSION=$(cat "$VERSION_FILE" | tr -d '[:space:]')
TAG="v${VERSION}"

echo "=========================================================="
echo "  AutoFailover 3.0 Release Pipeline — ${TAG}"
echo "=========================================================="

echo "[1/4] Running Core Python Characterization Tests..."
python3 -m unittest discover -s desktop/tests
echo "✅ Core characterization tests passed."

echo "[2/4] Verifying Website Build..."
npm --prefix website run build
echo "✅ Website production bundle compiled successfully."

echo "[3/4] Validating Changelog Coverage..."
if ! grep -E "## \[(v)?${VERSION}\]" "$CHANGELOG_FILE" > /dev/null 2>&1; then
    echo "⚠️ Warning: $CHANGELOG_FILE does not have an explicit section for [${VERSION}]."
    echo "   Ensure [Unreleased] is organized or create a [${VERSION}] section."
fi

echo "[4/4] Release Tag Verification..."
if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "ℹ️ Git tag $TAG already exists locally."
else
    echo "Creating git tag $TAG..."
    git tag -a "$TAG" -m "Release AutoFailover ${VERSION}"
    echo "✅ Created tag $TAG."
fi

echo ""
echo "To publish the release and trigger native CI runners:"
echo "  git push origin main --tags"
echo "=========================================================="
