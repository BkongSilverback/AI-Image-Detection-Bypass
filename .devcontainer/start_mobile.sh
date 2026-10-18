#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! test -f .venv/bin/python; then
  echo "Python environment not ready; skipping automatic start."
  exit 0
fi
if curl -fsS --max-time 2 http://127.0.0.1:8000/health >/dev/null 2>&1; then
  echo "DeAI Mobile is already running on port 8000."
  exit 0
fi
echo "Starting DeAI Mobile on port 8000 (private Codespaces port)."
nohup .venv/bin/python phone_app.py > /tmp/deai-mobile.log 2>&1 < /dev/null &
sleep 2
if curl -fsS --max-time 4 http://127.0.0.1:8000/health >/dev/null 2>&1; then
  echo "DeAI Mobile is running. Open forwarded port 8000."
else
  echo "Mobile app may still be starting. Check /tmp/deai-mobile.log if needed."
fi
