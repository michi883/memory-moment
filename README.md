# Memory Moment

**Words for a caregiver, in the moment. On device. No cloud.**

A fine-tuned Gemma 4 E2B model that helps family caregivers find something to say when a loved one with memory loss is upset, confused, or distant. The caregiver types a short situation; the model returns 3–5 short, mode-tagged lines they can actually say out loud — in a voice built from their loved one's own phrases, history, and the things that calm them.

[Live demo](https://huggingface.co/spaces/michi883/memory-moment-demo) · [Video (3 min)](https://www.youtube.com/watch?v=yrL78gslbco) · [Kaggle writeup](https://www.kaggle.com/competitions/gemma-4-good-hackathon) · [Quantized model (GGUF)](https://huggingface.co/michi883/memory-moment-v5-gemma4-e2b-gguf) · [Training notebook (Colab)](https://colab.research.google.com/drive/191xBczdNB93CE3nFvK2wlhAXcS_676Kb)

Built for the [Gemma 4 Good Hackathon](https://kaggle.com/competitions/gemma-4-good-hackathon) — Impact Track: Health & Sciences. Special Technology Track: Unsloth.

---

## Why this exists

When someone is dying, or losing their memory, the people around them often run out of words. Generic comfort lines don't land. Reasoning with them doesn't work. What does work — sometimes — is hearing something that sounds like *them*: a phrase they used to say, a tone they used to take, a small joke that was theirs. Family members know this intuitively but can't always summon it in the moment.

Memory Moment is a small tool for that moment. Not therapy, not a chatbot, not a replacement for human presence. A second brain for the caregiver who's tired at 2am and trying to think of the right thing to say.

It runs locally on the caregiver's device. The loved one's phrases, history, and habits never leave their phone or laptop.

---

## How it works

```
Onboarding (once)             Compression                Runtime (every use)
─────────────────             ───────────                ─────────────────
Caregiver fills a    ──────▶  Deterministic     ──────▶  Cached Context block
10-question survey            function                   on device
about loved one               (~50 lines of Python)              │
                                                                 ▼
                                                          Caregiver types:
                                                          "She's upset Frank
                                                           forgot to call"
                                                                 │
                                                                 ▼
                                                          Gemma 4 E2B
                                                          (fine-tuned, Q4 GGUF,
                                                          ~3.4 GB, runs on CPU)
                                                                 │
                                                                 ▼
                                                          🤝 He means well, I know.
                                                          🙂 Frank's a Frank.
                                                          🫱 Let's get the bins
                                                             sorted together.
```

The five modes — 🤝 agree-and-move, 🙂 lighten, 🫱 redirect, 🛑 firm-but-kind, 🎯 distract — give the caregiver a small palette of approaches in the moment, rather than a single "answer." The model picks the 3–5 modes that fit the situation and produces one line per mode.

Because everything runs locally, the most private inputs a person can imagine — voice, habits, what triggers them, what calms them down — never touch a server.

---

## Repository contents

```
memory-moment/
├── README.md                       ← you are here
│
├── training/
│   ├── memory-moment.ipynb         ← Colab notebook: Unsloth QLoRA fine-tune
│   │                                  of Gemma 4 E2B on the v5 dataset
│   └── README.md                   ← how to re-run training
│
├── data/
│   ├── memory_moment_train_v5.jsonl  ← training dataset (~500 rows)
│   ├── compress_v5.py              ← deterministic survey → Context compressor
│   └── README.md                   ← schema, mode definitions, examples
│
├── serving/
│   ├── app.py                      ← Gradio app (runs on HF Space and locally)
│   ├── compress_v5.py              ← same compressor, used at runtime
│   ├── Dockerfile                  ← HF Space container
│   ├── Modelfile                   ← Ollama config for local CLI use
│   └── README.md                   ← how to run the demo
│
└── build/
    ├── rebuild.sh                  ← Workbench: merged HF model → GGUF → Q4_K_M
    ├── merge_vanilla.py            ← LoRA + base → merged fp16, vanilla path
    └── README.md                   ← how to rebuild the GGUF from a new adapter
```

---

## What's where, and why

The project lives across four homes by design. Each environment owns the thing it does best, and Hugging Face is the handoff between them.

**Training — Google Colab.** Unsloth's QLoRA pipeline runs cleanly on a free T4 GPU. Gemma 4 is recent enough that not every environment has caught up; Colab has. The notebook trains a LoRA adapter on the v5 dataset, merges it into a full fp16 model, and pushes both to Hugging Face. See [`training/`](training/).

**Conversion + quantization — GCP Workbench.** A stable, non-Unsloth environment for the parts that don't need a GPU: pulling the merged model from HF, running `convert_hf_to_gguf.py`, quantizing to Q4_K_M with `llama-quantize`. The output is a 3.4 GB GGUF that's pushed back to HF. See [`build/`](build/).

**Serving — Hugging Face Space (Docker, free CPU).** The Space pulls the GGUF from HF at startup, loads it via `llama-cpp-python`, and exposes a small Gradio UI. Inference is ~5–10 seconds per generation on free CPU — fine for a thoughtful tool where the caregiver is meant to read each line carefully before deciding. See [`serving/`](serving/).

**Storage of artifacts — Hugging Face.** Three model repos:
- [`memory-moment-v5-gemma4-e2b-lora`](https://huggingface.co/michi883/memory-moment-v5-gemma4-e2b-lora) — the LoRA adapter (~50 MB, smallest portable artifact)
- [`memory-moment-v5-gemma4-e2b-merged`](https://huggingface.co/michi883/memory-moment-v5-gemma4-e2b-merged) — full fp16 merged model (~10 GB, intermediate)
- [`memory-moment-v5-gemma4-e2b-gguf`](https://huggingface.co/michi883/memory-moment-v5-gemma4-e2b-gguf) — Q4 quantized GGUF (~3.4 GB, deployment artifact)

This separation matters: each environment uses only the dependencies it needs, and the project can be rebuilt end-to-end from public artifacts on HF without re-running training.

---

## Run it yourself

### Try the live demo (no setup)

[Open the Space](https://huggingface.co/spaces/michi883/memory-moment-demo) and skip to the "Find words" tab. The "About them" tab shows the survey side; the demo Space has a default profile pre-loaded so you can jump straight to generating lines.

### Run it locally with Ollama (recommended)

Memory Moment is built local-first. The cleanest way to try it as it's meant to be used:

```bash
# 1. Install Ollama: https://ollama.com
# 2. Pull the model directly from Hugging Face
ollama pull hf.co/michi883/memory-moment-v5-gemma4-e2b-gguf

# 3. Run the Gradio app
git clone https://github.com/michi883/memory-moment
cd memory-moment/serving
pip install -r requirements.txt
OLLAMA_URL=http://localhost:11434 python app.py
```

Open `http://localhost:7860` in a browser. The model runs on your machine. Nothing leaves your device.

### Re-run training in Colab

Click the badge at the top of [`training/memory-moment.ipynb`](training/memory-moment.ipynb) to open in Colab. The notebook expects an `HF_TOKEN` secret to push artifacts back to your own Hugging Face account. A full run on a free T4 takes ~30 minutes.

### Rebuild the GGUF on Workbench

After re-training and pushing a new merged model to HF, the conversion + quantization pipeline rebuilds the deployable GGUF in one command. See [`build/README.md`](build/README.md) for the `.env` setup and `./rebuild.sh v6` workflow.

---

## How Gemma 4 is used

This project leans hard on three properties of Gemma 4 specifically:

**Local-first viability.** Gemma 4 E2B at Q4_K_M is ~3.4 GB and runs at usable speed on CPU. That's the whole reason Memory Moment can exist as a privacy-respecting tool — the caregiver doesn't need a GPU, doesn't need internet, and doesn't need to trust a cloud provider with the most intimate facts about a dying person.

**Fine-tunability with small data.** The v5 dataset is ~500 rows, generated through a careful human-in-the-loop process where every line was reviewed and refined. Unsloth's QLoRA on Gemma 4 E2B converged cleanly at this scale (loss from ~4.5 to ~2.7) — large enough to learn the mode-tagged output format and tone, small enough that one person could curate it. Larger base models would have made the dataset construction the bottleneck.

**Instruction-following on a constrained format.** The model has to produce 3–5 lines, each prefixed with one of five exact emoji+name mode tags, each under ~90 characters, with no commentary or framing. Gemma 4 E2B-it picks this up reliably after fine-tuning. Earlier experiments with the base model produced verbose chain-of-thought that was unusable in the product.

The training data, system prompt, and Context block schema are all in the repo — see [`data/`](data/) and [`training/`](training/).

---

## Acknowledgements

- The [Unsloth](https://github.com/unslothai/unsloth) team for the QLoRA training pipeline and Gemma 4 day-one support.
- [Google DeepMind](https://deepmind.google/) for releasing Gemma 4 as open weights.
- The [llama.cpp](https://github.com/ggerganov/llama.cpp) project for GGUF conversion and quantization.
- [Hugging Face](https://huggingface.co/) for free model hosting and Spaces.
- Family caregivers everywhere — the people this is actually for.

## License

Code in this repository: MIT.
Model weights: governed by the [Gemma Terms of Use](https://ai.google.dev/gemma/terms).
