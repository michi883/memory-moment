# Serving

The Gradio app that runs the demo, in two deployment modes.

## Files

- **`app.py`** — the Gradio app. Two tabs: "About them" (the survey) and "Find words" (situation → mode-tagged lines). Switches between two model backends based on the `OLLAMA_URL` environment variable:
  - If `OLLAMA_URL` is set → talk to a local Ollama server over HTTP. Used for local development and the Workbench-hosted version that drove the demo video.
  - Otherwise → load the GGUF directly via `llama-cpp-python`. Used in the Hugging Face Space.
- **`compress_v5.py`** — the deterministic survey → Context compressor. Same file as in [`../data/`](../data/), copied here so the serving environment is self-contained.
- **`Dockerfile`** — pinned-Python build for the HF Space. Installs `llama-cpp-python` from a pre-built wheel, downloads the GGUF from HF at startup, runs the Gradio app on port 7860.
- **`Modelfile`** — Ollama config that pins the v5 system prompt and sampling parameters (temperature 0.8, top_p 0.9). Lets you `ollama create memory-moment -f Modelfile` and use it from any Ollama client.

## Run locally with Ollama

```bash
# Pull the GGUF
ollama pull hf.co/michi883/memory-moment-v5-gemma4-e2b-gguf

# Optional: register it as `memory-moment` with the v5 system prompt + sampling
ollama create memory-moment -f Modelfile

# Run the Gradio app
pip install gradio httpx
OLLAMA_URL=http://localhost:11434 python app.py
```

Open `http://localhost:7860`. First request takes a few seconds for Ollama to load the model into memory; subsequent requests are 2–5 seconds on a recent laptop.

## Run as a Hugging Face Space

The live Space at [`michi883/memory-moment-demo`](https://huggingface.co/spaces/michi883/memory-moment-demo) is built from this directory. The Dockerfile downloads the GGUF from HF at container start and serves Gradio on port 7860.

To deploy your own copy:

1. Create a new HF Space, choose "Docker" as the SDK, "CPU basic" as the hardware
2. Clone the Space's git repo locally
3. Copy `app.py`, `compress_v5.py`, and `Dockerfile` from this directory into it
4. `git push` — the Space rebuilds and starts automatically

First build takes 5–10 minutes; restarts after that are fast because the GGUF is cached.

## Why two backends in one app

During development, Ollama on Workbench is the fastest path — it's already running, it caches the model in memory, and iteration on `app.py` doesn't restart inference. For the public demo, the Space needs to be self-contained: no external Ollama server. Using `llama-cpp-python` directly removes that dependency at the cost of slower cold-starts.

The same `app.py` file deploys to both. Choose by setting (or not setting) `OLLAMA_URL`.
