#!/bin/bash
# ~/rebuild.sh — download merged model → convert to GGUF → quantize.
# Merge happens in Colab; this script only does the Workbench-side work.
set -e

# ---- Load config from .env ----
if [ -f ~/.env ]; then
    set -a
    source ~/.env
    set +a
else
    echo "ERROR: ~/.env not found. Create it with HF_TOKEN, HF_REPO, etc."
    exit 1
fi

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: ./rebuild.sh <version>  (e.g., v3)"
    echo "Current HF_REPO: ${HF_REPO:-unset}"
    exit 1
fi
shift

FORCE_QUANTIZE=false
for arg in "$@"; do
    [ "$arg" = "--force-quantize" ] && FORCE_QUANTIZE=true
done

# ---- Validate config ----
: "${HF_TOKEN:?HF_TOKEN not set in .env}"
: "${HF_REPO:?HF_REPO not set in .env}"
: "${BASE_DIR:=/home/jupyter}"
: "${LLAMA_CPP_DIR:=$BASE_DIR/llama.cpp}"

MERGED_DIR="$BASE_DIR/memory-moment-merged"
F16_GGUF="$BASE_DIR/memory-moment-${VERSION}-f16.gguf"
Q4_GGUF="$BASE_DIR/memory-moment-${VERSION}-Q4_K_M.gguf"

log() { echo "[$(date +%H:%M:%S)] $*"; }
skip() { echo "  ✓ $* (already done, skipping)"; }

# ---- llama.cpp (idempotent) ----
log "Checking llama.cpp..."

if [ ! -d "$LLAMA_CPP_DIR" ]; then
    log "Cloning llama.cpp..."
    git clone https://github.com/ggerganov/llama.cpp.git "$LLAMA_CPP_DIR"
else
    skip "llama.cpp present"
fi

if ! grep -q -i "gemma.4\|gemma4" "$LLAMA_CPP_DIR/convert_hf_to_gguf.py"; then
    log "Updating llama.cpp for Gemma 4 support..."
    (cd "$LLAMA_CPP_DIR" && git pull)
fi

if [ ! -x "$LLAMA_CPP_DIR/build/bin/llama-quantize" ]; then
    log "Building llama.cpp..."
    (cd "$LLAMA_CPP_DIR" && mkdir -p build && cd build && \
        (cmake .. -DLLAMA_CUBLAS=ON 2>/dev/null || cmake ..) && \
        cmake --build . --config Release -j)
else
    skip "llama.cpp already built"
fi

# ---- Download merged model from HF ----
log "Syncing merged model from $HF_REPO..."

PREV_HASH=""
if [ -d "$MERGED_DIR" ] && [ -f "$MERGED_DIR/.repo_hash" ]; then
    PREV_HASH=$(cat "$MERGED_DIR/.repo_hash")
fi

export MERGED_DIR
export HF_REPO
export HF_TOKEN

NEW_HASH=$(python - <<PY
import os
from huggingface_hub import snapshot_download, HfApi

repo = os.environ["HF_REPO"]
token = os.environ["HF_TOKEN"]
target = os.environ["MERGED_DIR"]

snapshot_download(repo_id=repo, local_dir=target, token=token)

api = HfApi()
info = api.model_info(repo_id=repo, token=token)
print(info.sha)
PY
)

echo "$NEW_HASH" > "$MERGED_DIR/.repo_hash"

if [ "$PREV_HASH" = "$NEW_HASH" ] && [ -n "$PREV_HASH" ]; then
    skip "merged model unchanged ($NEW_HASH)"
    MODEL_CHANGED=false
else
    log "Merged model updated ($NEW_HASH)"
    MODEL_CHANGED=true
fi

# ---- Convert to f16 GGUF ----
if [ -f "$F16_GGUF" ] && [ "$MODEL_CHANGED" = false ] && [ "$FORCE_QUANTIZE" = false ]; then
    skip "f16 GGUF exists for $VERSION"
else
    log "Converting to f16 GGUF..."
    python "$LLAMA_CPP_DIR/convert_hf_to_gguf.py" \
        "$MERGED_DIR" --outtype f16 --outfile "$F16_GGUF"
fi

# ---- Quantize to Q4_K_M ----
if [ -f "$Q4_GGUF" ] && [ "$Q4_GGUF" -nt "$F16_GGUF" ] && [ "$FORCE_QUANTIZE" = false ]; then
    skip "Q4_K_M GGUF up to date"
else
    log "Quantizing to Q4_K_M..."
    "$LLAMA_CPP_DIR/build/bin/llama-quantize" "$F16_GGUF" "$Q4_GGUF" Q4_K_M
fi

log "Done. GGUF: $Q4_GGUF"