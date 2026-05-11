FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    cmake \
    git \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:/home/user/llama.cpp/build/bin:$PATH"
WORKDIR /home/user

# Build llama.cpp directly (the C++ project, not the Python bindings).
# This is faster and more reliable than llama-cpp-python in Spaces.
RUN git clone --depth 1 https://github.com/ggml-org/llama.cpp && \
    cd llama.cpp && \
    cmake -B build -DGGML_CURL=OFF && \
    cmake --build build --config Release -j 2

# Python deps for the Gradio UI and the HTTP calls to llama-server. 
# (No llama-cpp-python — we shell out to the llama-server binary above.)
# `requests` is a transitive dep of Gradio's CLI; it must stay even though
# our app uses httpx for its own HTTP work.
RUN pip install --no-cache-dir --user \
    gradio==5.34.2 \
    "huggingface_hub>=0.28.1" \
    requests \
    httpx

WORKDIR /home/user/app
COPY --chown=user . .

EXPOSE 7860

CMD ["python", "app.py"]