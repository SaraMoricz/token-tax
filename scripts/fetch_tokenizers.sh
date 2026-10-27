#!/usr/bin/env bash
# Collects the open tokenizer files into ./tokenizers and writes tokenizers/extra_tokenizers.json.
# Run from the repo root after `npm install` and `pip install -r requirements.txt`. Every download is
# pinned to a commit, so the counts can be reproduced exactly. No Hugging Face account is needed.
set -euo pipefail
cd "$(dirname "$0")/.."
T=tokenizers
mkdir -p "$T"
HF=https://huggingface.co

# Gemini 2.0-3.0: Gemma 3 SentencePiece model (the file Google's google-genai SDK downloads)
curl -fsSL -o "$T/gemma3.spm" \
  https://raw.githubusercontent.com/google/gemma_pytorch/014acb7ac4563a5f77c76d7ff98f31b568c16508/tokenizer/gemma3_cleaned_262144_v2.spiece.model

# Gemini 3.1+: Gemma 4 (Apache-2.0, not gated)
curl -fsSL -o "$T/gemma4.json" "$HF/google/gemma-4-E4B/resolve/411aa17b749aa952df1359d2dcea73917a544d9a/tokenizer.json"

# Qwen 3.5+ (Apache-2.0, not gated; the same file for the 0.8B-9B models)
curl -fsSL -o "$T/qwen35.json" "$HF/Qwen/Qwen3.5-4B-Base/resolve/1001bb4d826a52d1f399e183466143f4da7b741b/tokenizer.json"

# Llama 3, DeepSeek V3/V4, Qwen 3: Hugging Face tokenizer.json files bundled in npm packages
cp node_modules/@lenml/tokenizer-llama3_1/models/tokenizer.json "$T/llama3.json"
cp node_modules/@lenml/tokenizer-deepseek_v4/models/tokenizer.json "$T/deepseek_v4.json"
cp node_modules/@lenml/tokenizer-qwen3/models/tokenizer.json "$T/qwen3.json"

# Mistral Tekken: bundled in the mistral-common pip package
python3 -c "import mistral_common, os, shutil; shutil.copy(os.path.join(os.path.dirname(mistral_common.__file__), 'data', 'tekken_240911.json'), '$T/tekken_240911.json')"

# Llama 4: tiktoken file and pre-tokenizer pattern from Meta's llama-models repo on GitHub
LLAMA=https://raw.githubusercontent.com/meta-llama/llama-models/0e0b8c519242d5833d8c11bffc1232b77ad7f301/models/llama4
curl -fsSL -o "$T/llama4.tiktoken" "$LLAMA/tokenizer.model"
curl -fsSL -o "$T/llama4_tokenizer.py" "$LLAMA/tokenizer.py"

python3 - <<'EOF'
import json, re
pat = re.search(r'O200K_PATTERN = r"""(.*?)"""', open("tokenizers/llama4_tokenizer.py").read()).group(1)
cfg = {
    "gemma4": {"kind": "hf_json", "path": "gemma4.json"},
    "llama3": {"kind": "hf_json", "path": "llama3.json"},
    "llama4_muse": {"kind": "tiktoken", "path": "llama4.tiktoken", "pat_str": pat},
    "deepseek_v4": {"kind": "hf_json", "path": "deepseek_v4.json"},
    "qwen3": {"kind": "hf_json", "path": "qwen3.json"},
    "qwen35": {"kind": "hf_json", "path": "qwen35.json"},
    "mistral_tekken": {"kind": "tekken", "path": "tekken_240911.json"},
}
json.dump(cfg, open("tokenizers/extra_tokenizers.json", "w"), indent=1)
print("wrote tokenizers/extra_tokenizers.json")
EOF
ls -la "$T"
