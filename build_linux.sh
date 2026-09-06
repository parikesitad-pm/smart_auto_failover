#!/bin/bash
# ==============================================================================
# MODULA - Smart Auto Failover v2.2
# Linux x86_64 Standalone Bundle Packaging Script
# Produces: dist_app/MODULA-v2.2-linux-x86_64.tar.gz
# ==============================================================================

set -e

VERSION="v2.2"
ARCH="linux-x86_64"
APP_NAME="MODULA"
TAR_NAME="MODULA-${VERSION}-${ARCH}.tar.gz"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist_app"
BUILD_DIR="${SCRIPT_DIR}/build"
ASSETS_DIR="${SCRIPT_DIR}/assets"

echo "======================================================================"
echo "🐧 BUILDING MODULA ${VERSION} FOR LINUX (${ARCH})"
echo "======================================================================"

# 1. Verify Python & Pip
if ! command -v python3 &> /dev/null; then
    echo "[-] Python 3 not found. Please install python3, python3-pip, python3-tk"
    exit 1
fi

# 2. Install dependencies
echo "[*] Verifying build dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r "${SCRIPT_DIR}/requirements.txt" pyinstaller

# 3. Compile standalone Linux binary with PyInstaller
echo "[*] Compiling ${APP_NAME} binary using PyInstaller..."
python3 -m PyInstaller \
    --noconfirm \
    --clean \
    --onedir \
    --windowed \
    --distpath "${DIST_DIR}" \
    --workpath "${BUILD_DIR}/pyi_work_linux" \
    --name "${APP_NAME}" \
    --add-data "${ASSETS_DIR}:assets" \
    --collect-all customtkinter \
    --collect-all darkdetect \
    --collect-all PIL \
    "${SCRIPT_DIR}/main.py"

APP_FOLDER="${DIST_DIR}/${APP_NAME}"
if [ ! -d "${APP_FOLDER}" ]; then
    echo "[-] App directory build failed: ${APP_FOLDER}"
    exit 1
fi

# 4. Copy launcher and documentation
cat << 'EOF' > "${APP_FOLDER}/run_linux.sh"
#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[*] Launching MODULA with sudo privileges for network metric routing..."
sudo "${DIR}/MODULA" "$@"
EOF
chmod +x "${APP_FOLDER}/run_linux.sh"
cp "${SCRIPT_DIR}/README.md" "${APP_FOLDER}/README.md" || true

# 5. Create tar.gz archive
TAR_OUTPUT="${DIST_DIR}/${TAR_NAME}"
echo "[*] Compressing archive: ${TAR_OUTPUT}..."
tar -czf "${TAR_OUTPUT}" -C "${DIST_DIR}" "${APP_NAME}"

TAR_SIZE_MB=$(du -m "${TAR_OUTPUT}" | cut -f1)

echo "======================================================================"
echo "🎉 LINUX BUILD & PACKAGING COMPLETE!"
echo "======================================================================"
echo "📦 Output Archive : ${TAR_OUTPUT} (~${TAR_SIZE_MB} MB)"
echo "📂 App Directory  : ${APP_FOLDER}"
echo "💡 Usage           : cd ${APP_FOLDER} && ./run_linux.sh"
echo "======================================================================"
