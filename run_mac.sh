#!/usr/bin/env bash
# ==============================================================================
# Smart Auto-Failover Network Monitor - macOS Launcher
# Automatically requests sudo/root elevation if needed to modify network order
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================================"
echo " Starting Smart Auto-Failover Network Monitor (macOS)"
echo "======================================================================"

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 could not be found. Please install Python 3 on your Mac."
    exit 1
fi

# Install dependencies if customtkinter missing
python3 -c "import customtkinter, psutil" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required packages (customtkinter, psutil)..."
    python3 -m pip install -r requirements.txt
fi

# Check root / sudo
if [ "$EUID" -ne 0 ]; then
    echo "Requesting administrator (sudo) privileges to allow network routing changes..."
    exec sudo python3 main.py "$@"
else
    python3 main.py "$@"
fi

