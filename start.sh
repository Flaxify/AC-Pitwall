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
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./start_browser.ps1
  else
    chrome_bin=""
    for candidate in chromium chromium-browser google-chrome google-chrome-stable chrome; do
      if command -v "$candidate" >/dev/null 2>&1; then
        chrome_bin="$candidate"
        break
      fi
    done

    if [ -z "$chrome_bin" ]; then
      echo "[warn] Chrome remote debugging is not reachable at localhost:9222." >&2
      echo "[warn] Install Chrome/Chromium or start it manually with --remote-debugging-port=9222." >&2
    else
      echo "[browser] starting Chrome remote debugging at localhost:9222"
      mkdir -p .chrome-debug
      "$chrome_bin" \
        --remote-debugging-port=9222 \
        --user-data-dir="$(pwd)/.chrome-debug" \
        --no-first-run \
        --no-default-browser-check >/dev/null 2>&1 &

      for _ in $(seq 1 20); do
        sleep 0.5
        if curl -fsS --max-time 2 http://localhost:9222/json/version >/dev/null; then
          echo "[browser] ready"
          break
        fi
      done
    fi
  fi
fi

if [ "$#" -eq 0 ]; then
  set -- scrape
fi

.venv/bin/pitwall "$@"
