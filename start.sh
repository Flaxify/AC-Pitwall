#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.11+ is required. Install python3, then rerun ./start.sh" >&2
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "[setup] creating .venv"
  python3 -m venv .venv
fi

echo "[setup] installing pitwall into .venv"
.venv/bin/python -m pip --disable-pip-version-check install -e .

if ! curl -fsS --max-time 2 http://localhost:9222/json/version >/dev/null; then
  echo "[warn] Chrome remote debugging is not reachable at localhost:9222." >&2
  echo "[warn] Start Chrome/Chromium with: chromium --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug" >&2
fi

if [ "$#" -eq 0 ]; then
  set -- scrape
fi

.venv/bin/pitwall "$@"
