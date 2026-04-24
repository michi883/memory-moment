# app.py
import os
import re
import gradio as gr

# Pick backend based on environment
USE_OLLAMA = os.getenv("USE_OLLAMA", "false").lower() == "true"

MODE_LABELS = {
    "🤝": "Agree & move on",
    "🙂": "Lighten it",
    "🫱": "Redirect",
    "🛑": "Firm but kind",
    "🎯": "Distract",
}

SYSTEM_PROMPT = """You help a family caregiver find words that work in a hard moment with someone they love who has memory loss. Given a phrase the person would say, a situation, and context about them, produce short lines the caregiver can say out loud. Each line should feel like something she would accept. Tag each line with a mode: 🤝 agree-and-move, 🙂 lighten, 🫱 redirect, 🛑 firm-but-kind, or 🎯 distract. Produce 3 to 5 lines. Skip modes that don't fit. Output only the lines, one per line, mode emoji first."""

# ---- Backend setup ----

if USE_OLLAMA:
    import httpx

    def call_model(user_prompt: str) -> str:
        response = httpx.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "memory-moment",
                "prompt": user_prompt,
                "system": SYSTEM_PROMPT,
                "stream": False,
                "options": {"temperature": 0.8, "top_p": 0.9},
            },
            timeout=120,
        )
        return response.json()["response"]

else:
    from llama_cpp import Llama
    from huggingface_hub import hf_hub_download

    print("Downloading GGUF from Hugging Face...")
    model_path = hf_hub_download(
        repo_id="michi883/memory-moment-gemma4-e2b-gguf",
        filename="memory-moment-v3-Q4_K_M.gguf",
    )
    print(f"Loading model from {model_path}...")
    llm = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_threads=4,
        verbose=False,
    )
    print("Model loaded.")

    def call_model(user_prompt: str) -> str:
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            top_p=0.9,
            max_tokens=300,
        )
        return response["choices"][0]["message"]["content"]


# ---- Profile + anchor selection ----

PROFILE = {
    "name": "Mom",
    "husband": "Frank",
    "calming": "tea",
    "phrases": [
        {"text": "He means well", "tags": ["husband", "frank", "dad"]},
        {"text": "Don't fuss", "tags": ["help", "dress", "bath"]},
        {"text": "What a day", "tags": ["tired", "evening", "night"]},
        {"text": "I'll do it in a minute", "tags": ["pills", "medication"]},
        {"text": "Bless his heart", "tags": ["husband", "frank"]},
    ],
}

def pick_anchor(situation: str) -> str:
    s = situation.lower()
    for phrase in PROFILE["phrases"]:
        if any(tag in s for tag in phrase["tags"]):
            return phrase["text"]
    return PROFILE["phrases"][0]["text"]

def build_context(situation: str) -> str:
    s = situation.lower()
    parts = []
    if any(t in s for t in ["husband", "frank", "dad"]):
        parts.append(f"Husband is {PROFILE['husband']}.")
    if PROFILE["calming"]:
        parts.append(f"Calms down with {PROFILE['calming']}.")
    return " ".join(parts) or "Keep it gentle."


# ---- Main function ----

def generate_lines(situation: str) -> str:
    if not situation.strip():
        return "Please describe what's happening."

    anchor = pick_anchor(situation)
    context = build_context(situation)
    user_prompt = f'Phrase: "{anchor}"\nSituation: {situation}\nContext: {context}'

    raw = call_model(user_prompt)

    # Parse into markdown cards
    cards = []
    for line in raw.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^(\S+)\s*(.+)$", line)
        if not match:
            continue
        emoji, text = match.group(1), match.group(2)
        if emoji in MODE_LABELS:
            label = MODE_LABELS[emoji]
            cards.append(f"### {emoji} {text}\n\n*{label}*")

    return "\n\n---\n\n".join(cards) if cards else raw


# ---- UI ----

demo = gr.Interface(
    fn=generate_lines,
    inputs=gr.Textbox(
        label="What's happening right now?",
        placeholder="e.g., She's annoyed that Frank forgot to call",
        lines=3,
    ),
    outputs=gr.Markdown(label="Things you could say"),
    title="Memory Moment",
    description="Words for a family caregiver, in the moment. Model: [memory-moment-gemma4-e2b](https://huggingface.co/michi883/memory-moment-gemma4-e2b-gguf) (fine-tuned Gemma 4).",
    flagging_mode="never",  # This is the new parameter name in Gradio 5.x
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)