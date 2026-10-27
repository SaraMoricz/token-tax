#!/usr/bin/env bash
# Full pipeline: FLORES-200 devtest -> token counts per tokenizer -> data/data.csv
# (+ data/country_premiums.csv). Needs Node 18+, Python 3.10+ and git; see README.md.
# ANTHROPIC_API_KEY (optional) adds or refreshes the Claude column via Anthropic's free count_tokens endpoint.
set -euo pipefail
cd "$(dirname "$0")/.."

# FLORES-200 devtest as published in Petrov et al.'s repository (CC BY-SA 4.0), pinned to the commit we measured.
FLORES_REPO=https://github.com/AleksandarPetrov/tokenization-fairness
FLORES_COMMIT=365c3f85bdb302fdcf6d389f5f1651e4ef041741
FLORES_DIR="${FLORES_DIR:-flores/flores200_dataset/devtest}"
if [ ! -d "$FLORES_DIR" ]; then
  git init -q flores
  git -C flores fetch -q --depth 1 "$FLORES_REPO" "$FLORES_COMMIT"
  git -C flores checkout -q FETCH_HEAD
fi
[ -f tokenizers/extra_tokenizers.json ] || bash scripts/fetch_tokenizers.sh

C=data/counts
mkdir -p "$C"
node scripts/count_openai.js "$FLORES_DIR" "$C/openai.json"
python3 -I scripts/count_gemini.py "$FLORES_DIR" tokenizers/gemma3.spm "$C/gemini.json"
python3 -I scripts/count_more.py "$FLORES_DIR" "$C/more.json" tokenizers/extra_tokenizers.json
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  # count_claude.py resumes: languages already in claude.json are skipped. Delete the file to recount.
  python3 -I scripts/count_claude.py "$FLORES_DIR" "$C/claude.json"
else
  echo "ANTHROPIC_API_KEY not set: using data/counts/claude.json as it is (the Claude column is left out if it is missing)"
fi

if [ -n "${GEMINI_API_KEY:-}" ]; then
  # Gemini 4 Argon (new tokenizer) and Gemini 3.8 Flash (the 3.x tokenizer, = Gemma 4). Resumes like count_claude.py.
  python3 -I scripts/count_gemini_api.py "$FLORES_DIR" "$C/gemini_api.json" --model gemini-4-argon --key gemini4_argon
  python3 -I scripts/count_gemini_api.py "$FLORES_DIR" "$C/gemini_api.json" --model gemini-3.8-flash --key gemini38_flash
else
  echo "GEMINI_API_KEY not set: using data/counts/gemini_api.json as it is"
fi

python3 -I scripts/build_csv.py data/flores_language_map.csv data/data.csv \
  "$C/openai.json" "$C/gemini.json" "$C/more.json" "$C/claude.json" "$C/gemini_api.json"
node scripts/country_csv.js data/data.csv data/country_language_map.json data/country_premiums.csv
python3 -I scripts/country_population.py data/country_population.json 2025   # World Bank, for ordering countries by size
