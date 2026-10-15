#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${COMFYUI_ROOT:-/workspace/ComfyUI}"
PORT="${PORT:-8188}"
exec "$ROOT/.venv/bin/python" "$ROOT/main.py" \
  --listen 0.0.0.0 \
  --port "$PORT" \
  --preview-method auto
