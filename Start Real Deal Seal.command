#!/bin/bash
# Double-click to run Real Deal Seal on this Mac at http://localhost:8000
# First run installs what it needs (2-3 minutes). Close this window to stop the app.
set -e
cd "$(dirname "$0")"

# 1. Python 3.13 via uv (installs uv once if it's missing)
if ! command -v uv >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/uv" ]; then
  echo "Installing uv (one time)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
UV="$(command -v uv || echo "$HOME/.local/bin/uv")"
if [ ! -x .venv/bin/python ]; then
  echo "Setting up Python 3.13 (one time)..."
  "$UV" venv -q --python 3.13 .venv
fi
"$UV" pip install -q --python .venv/bin/python -r requirements.txt

# 2. The website: use the included build, or build it if Node is installed
if [ ! -f web/build/index.html ]; then
  if command -v npm >/dev/null 2>&1; then (cd web && npm install && npm run build)
  else echo "web/build is missing and Node isn't installed; install Node 22 from nodejs.org"; exit 1; fi
fi

# 3. Build the data warehouse (stops here if a data gate fails)
.venv/bin/python data_platform/run/build.py | tail -1

# 4. Start. The app reads .env by itself.
( sleep 4; open "http://localhost:8000" ) &
echo
echo "Real Deal Seal is running at http://localhost:8000  (close this window to stop)"
exec .venv/bin/uvicorn rds.main:app --app-dir api --port 8000
