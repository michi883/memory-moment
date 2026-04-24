---
title: Memory Moment
emoji: 💭
colorFrom: indigo
colorTo: pink
sdk: gradio
sdk_version: 5.0.0
python_version: "3.11"
app_file: app.py
pinned: false
license: apache-2.0
models:
  - michi883/memory-moment-gemma4-e2b-gguf
---

# Memory Moment

Words for a family caregiver, in the moment.

When someone you love has memory loss, knowing what to say in a hard moment
is exhausting. Memory Moment takes a situation you're in and gives you 3-5
short lines you can actually say — built around phrases they used to say,
tagged with the tone that fits.

All inference runs locally in this Space. No data is stored.

## The model

This app uses [memory-moment-gemma4-e2b](https://huggingface.co/michi883/memory-moment-gemma4-e2b-gguf),
a fine-tune of Gemma 4 E2B on a custom schema designed for caregiver
situations. Dataset: 30 curated examples covering medication refusal,
recognition failures, agitation, sweet moments, and more.

## How to use

Describe what's happening in the text box. The app will return 3-5 lines
tagged with modes like 🤝 agree-and-move, 🙂 lighten, 🫱 redirect.