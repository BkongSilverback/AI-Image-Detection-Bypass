#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "Installing DeAI Mobile's CPU-only dependencies..."
python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install "Pillow>=10" "numpy>=1.24" "opencv-python-headless>=4.8" "rich>=13" "requests>=2.31"
.venv/bin/python -m py_compile phone_app.py scripts/deai.py
echo "DeAI Mobile setup complete."
