#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${COMFYUI_ROOT:-/workspace/ComfyUI}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DOWNLOAD_MODELS="${DOWNLOAD_MODELS:-0}"

mkdir -p "$(dirname "$ROOT")"
if [[ ! -d "$ROOT/.git" ]]; then
  git clone --depth 1 https://github.com/Comfy-Org/ComfyUI.git "$ROOT"
else
  git -C "$ROOT" pull --ff-only || true
fi

"$PYTHON_BIN" -m venv --system-site-packages "$ROOT/.venv" 2>/dev/null || true
PY="$ROOT/.venv/bin/python"
PIP="$ROOT/.venv/bin/pip"
[[ -x "$PY" ]] || { PY="$PYTHON_BIN"; PIP="$PYTHON_BIN -m pip"; }

$PIP install --upgrade pip
$PIP install -r "$ROOT/requirements.txt"

mkdir -p "$ROOT/custom_nodes"
if [[ ! -d "$ROOT/custom_nodes/ComfyUI-LTXVideo/.git" ]]; then
  git clone --depth 1 https://github.com/Lightricks/ComfyUI-LTXVideo.git \
    "$ROOT/custom_nodes/ComfyUI-LTXVideo"
else
  git -C "$ROOT/custom_nodes/ComfyUI-LTXVideo" pull --ff-only || true
fi
$PIP install -r "$ROOT/custom_nodes/ComfyUI-LTXVideo/requirements.txt" || true

mkdir -p "$ROOT/models/checkpoints" "$ROOT/models/loras" \
  "$ROOT/models/text_encoders" "$ROOT/models/latent_upscale_models" \
  "$ROOT/input" "$ROOT/output"

if [[ "$DOWNLOAD_MODELS" == "1" ]]; then
  command -v huggingface-cli >/dev/null 2>&1 || $PIP install -U huggingface_hub
  HF="${HF_TOKEN:-}"
  AUTH=()
  [[ -n "$HF" ]] && AUTH=(--token "$HF")
  huggingface-cli download Lightricks/LTX-2.3-fp8 \
    ltx-2.3-22b-dev-fp8.safetensors \
    --local-dir "$ROOT/models/checkpoints" "${AUTH[@]}"
  huggingface-cli download Comfy-Org/ltx-2.3 \
    split_files/loras/ltx_2.3_22b_distilled_1.1_lora_dynamic_fro09_avg_rank_111_bf16.safetensors \
    --local-dir "$ROOT/models/loras" "${AUTH[@]}"
  huggingface-cli download Comfy-Org/ltx-2 \
    split_files/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors \
    --local-dir "$ROOT/models/text_encoders" "${AUTH[@]}"
  wget -nc -P "$ROOT/models/latent_upscale_models" \
    https://huggingface.co/Lightricks/LTX-2.3/resolve/main/ltx-2.3-spatial-upscaler-x2-1.1.safetensors
fi

echo "Kurulum tamamlandı: $ROOT"
echo "Başlatmak için: $ROOT/start_comfyui.sh"
