#!/bin/bash
# ==============================================================================
# MODULA - Smart Auto Failover v2.2
# macOS Apple Silicon (M1 / M2 / M3) .app & .dmg Packaging Script
# Produces: dist_app/MODULA-v2.2-macos-arm64.dmg
# ==============================================================================

set -e

VERSION="v2.2"
ARCH="macos-arm64"
APP_NAME="MODULA"
DMG_NAME="MODULA-${VERSION}-${ARCH}.dmg"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist_app"
BUILD_DIR="${SCRIPT_DIR}/build"
ASSETS_DIR="${SCRIPT_DIR}/assets"

echo "======================================================================"
echo "🍏 BUILDING MODULA ${VERSION} FOR macOS APPLE SILICON (${ARCH})"
echo "======================================================================"

# 1. Check Python & Pip
if ! command -v python3 &> /dev/null; then
    echo "[-] Python 3 not found. Please install Python 3.10+ via brew or python.org"
    exit 1
fi

# 2. Install dependencies
echo "[*] Verifying build dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r "${SCRIPT_DIR}/requirements.txt" pyinstaller

# 3. Compile .app bundle with PyInstaller
echo "[*] Building ${APP_NAME}.app using PyInstaller (arm64)..."
python3 -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --target-arch arm64 \
    --distpath "${DIST_DIR}" \
    --workpath "${BUILD_DIR}/pyi_work_mac" \
    --name "${APP_NAME}" \
    --add-data "${ASSETS_DIR}:assets" \
    --collect-all customtkinter \
    --collect-all darkdetect \
    --collect-all PIL \
    "${SCRIPT_DIR}/main.py"

APP_PATH="${DIST_DIR}/${APP_NAME}.app"
if [ ! -d "${APP_PATH}" ]; then
    echo "[-] App bundle failed to build: ${APP_PATH}"
    exit 1
fi

# 4. Copy launcher helper and readme into bundle
cp "${SCRIPT_DIR}/run_mac.sh" "${DIST_DIR}/run_mac.sh" || true
cp "${SCRIPT_DIR}/README.md" "${DIST_DIR}/README.md" || true

# 5. Build .dmg disk image using native macOS hdiutil
DMG_OUTPUT="${DIST_DIR}/${DMG_NAME}"
DMG_STAGING="${BUILD_DIR}/dmg_staging"

echo "[*] Preparing DMG staging environment at ${DMG_STAGING}..."
rm -rf "${DMG_STAGING}" "${DMG_OUTPUT}"
mkdir -p "${DMG_STAGING}"

# Copy .app and create Applications symlink for drag-and-drop install
cp -R "${APP_PATH}" "${DMG_STAGING}/"
ln -s /Applications "${DMG_STAGING}/Applications"
cp "${SCRIPT_DIR}/README.md" "${DMG_STAGING}/" 2>/dev/null || true

echo "[*] Packaging .dmg with hdiutil: ${DMG_OUTPUT}..."
hdiutil create \
    -volname "MODULA-${VERSION}" \
    -srcfolder "${DMG_STAGING}" \
    -ov \
    -format UDZO \
    "${DMG_OUTPUT}"

# Clean staging
rm -rf "${DMG_STAGING}"

echo "======================================================================"
echo "🎉 macOS BUILD & PACKAGING COMPLETE!"
echo "======================================================================"
echo "📦 Output DMG : ${DMG_OUTPUT}"
echo "📂 App Bundle : ${APP_PATH}"
echo "💡 Usage      : Open .dmg and drag MODULA to Applications."
echo "               (Or run via: sudo python3 main.py for full route metric bonding)"
echo "======================================================================"
