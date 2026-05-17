#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

NODE_DIR=".tools/node-v22.14.0-darwin-arm64"
if [[ -x "$NODE_DIR/bin/npm" ]]; then
  export PATH="$PWD/$NODE_DIR/bin:$PATH"
elif ! command -v npm >/dev/null 2>&1; then
  echo "npm not found. Install Node.js from https://nodejs.org/ or run scripts/bootstrap-node.sh"
  exit 1
fi

cd frontend
if [[ ! -d node_modules ]]; then
  npm install
fi
if [[ ! -f .env ]]; then
  cp .env.example .env
fi

echo "Starting frontend at http://localhost:5173"
exec npm run dev
