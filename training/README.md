# Training

Fine-tunes Gemma 4 E2B on the Memory Moment v5 dataset using Unsloth QLoRA.

## Files

- **`memory-moment.ipynb`** — the notebook. Loads `unsloth/gemma-4-E2B-it`, attaches a LoRA adapter (r=16, alpha=32, targeting all attention + MLP projections), trains on `data/memory_moment_train_v5.jsonl`, merges, and pushes both the adapter and the merged model to Hugging Face.

## Run in Colab

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/191xBczdNB93CE3nFvK2wlhAXcS_676Kb)

Requires a free T4 GPU runtime. Set `HF_TOKEN` in Colab → Secrets so the notebook can push artifacts to your own account. Update the `MERGED_REPO` and `LORA_REPO` constants at the top of the notebook to match.

A full run takes ~30 minutes (data load + 3 epochs + merge + push).

## Configuration

The notebook is the source of truth, but the headline hyperparameters are:

| Parameter | Value |
|---|---|
| Base model | `unsloth/gemma-4-E2B-it` |
| LoRA r | 16 |
| LoRA alpha | 32 |
| Target modules | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` |
| LoRA dropout | 0 |
| Max seq length | 512 |
| Precision | 4-bit during training, fp16 after merge |
| Random seed | 42 |

## Outputs

Three artifacts are pushed to Hugging Face:

1. **LoRA adapter** (`michi883/memory-moment-v5-gemma4-e2b-lora`) — ~50 MB
2. **Merged fp16 model** (`michi883/memory-moment-v5-gemma4-e2b-merged`) — ~10 GB
3. **Q4_K_M GGUF** (`michi883/memory-moment-v5-gemma4-e2b-gguf`) — ~3.4 GB

The GGUF is built from the merged model on a separate Workbench environment — see [`../build/`](../build/). Training and quantization are split because Unsloth and llama.cpp's converters have conflicting torch requirements; keeping them in different environments avoids the dependency wars.
