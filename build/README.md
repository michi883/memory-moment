# Build

The Workbench-side pipeline that turns a fine-tuned LoRA adapter into a deployable Q4_K_M GGUF.

## Files

- **`rebuild.sh`** — one-command pipeline. Reads config from `~/.env`, downloads the merged model from Hugging Face, runs `convert_hf_to_gguf.py` to produce an fp16 GGUF, then quantizes to Q4_K_M with `llama-quantize`. Idempotent: re-running on the same version is a no-op once the artifacts exist.
- **`merge_vanilla.py`** — vanilla `transformers + peft` merge of a LoRA adapter into the base Gemma 4 model. Used as a fallback when the adapter is downloaded directly to Workbench (rather than already-merged on Colab).

## Why this lives on Workbench, not Colab

Training happens in Colab because Unsloth needs a recent torch + GPU. Conversion + quantization happens on Workbench because llama.cpp's `convert_hf_to_gguf.py` is pure-Python and works on any environment with a stable transformers install — and crucially, it doesn't need a GPU. Splitting the pipeline this way means each environment uses only the dependencies it needs, and an old Workbench instance keeps working even when Unsloth pushes a breaking change.

The handoff between environments is Hugging Face: Colab pushes a merged fp16 model up; Workbench pulls it down.

## Setup (one-time)

```bash
# Install the Workbench-side Python deps (no-deps protects torch from being upgraded)
pip install --quiet peft --no-deps
pip install --quiet "transformers>=4.50" --no-deps
pip install --quiet huggingface_hub

# Clone and build llama.cpp
git clone https://github.com/ggerganov/llama.cpp.git ~/llama.cpp
cd ~/llama.cpp
cmake -B build && cmake --build build --config Release -j

# Create ~/.env with your config
cat > ~/.env <<'EOF'
HF_TOKEN=hf_your_token_here
HF_REPO=michi883/memory-moment-v5-gemma4-e2b-merged
BASE_DIR=/home/jupyter
LLAMA_CPP_DIR=/home/jupyter/llama.cpp
EOF
chmod 600 ~/.env
```

## Build a new GGUF

```bash
./rebuild.sh v5
```

Steps the script runs:

1. Pull the merged model from `HF_REPO` (skip if already downloaded and HF commit hash matches)
2. Run `convert_hf_to_gguf.py` to produce `memory-moment-v5-f16.gguf`
3. Run `llama-quantize` to produce `memory-moment-v5-Q4_K_M.gguf`

Output lands in `$BASE_DIR/`. Upload the Q4 file to your GGUF repo on Hugging Face:

```bash
huggingface-cli upload michi883/memory-moment-v5-gemma4-e2b-gguf \
  ~/memory-moment-v5-Q4_K_M.gguf \
  memory-moment-v5-Q4_K_M.gguf
```

## Why the version goes in the filename

GGUFs are versioned (`memory-moment-v5-Q4_K_M.gguf`), not overwritten. This makes rollback trivial — if v6 is worse than v5, the demo can pin v5 by changing one line in `serving/app.py`. It also means the Hugging Face Space's cached model is always unambiguous about which version it has.
