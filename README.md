# Token tax: How many more tokens a language needs, compared to English, for the same text

Swedish needs 35 % more tokens than English for the same text on ChatGPT, and Santali 1 273 % more.
This repository measures that premium for 204 languages on the tokenizers behind ChatGPT, Gemini,
Claude, Meta's Llama, DeepSeek, Qwen and Mistral. The interactive globe built on it is at
https://sara.moricz.se/token-tax/.

More tokens for the same text means a quota used up faster, a context window that holds less, and
slower answers.

## Method

The premium follows Petrov et al., [Language Model Tokenizers Introduce Unfairness Between
Languages](https://arxiv.org/abs/2305.15425) (NeurIPS 2023):

**premium = tokens(language) ÷ tokens(English)**, on the same text, per tokenizer.

- **Text:** the FLORES-200 devtest split, 1,012 sentences translated into 204 languages, as published
  in [Petrov et al.'s repository](https://github.com/AleksandarPetrov/tokenization-fairness/tree/365c3f85bdb302fdcf6d389f5f1651e4ef041741/flores200_dataset/devtest)
  (commit 365c3f8). `run_all.sh` downloads it; the text is not redistributed here.
- **Counting:** each language is one text, its sentences joined by line breaks, without special tokens.
- **Claude:** Anthropic does not publish its tokenizer, so Claude is counted through the free
  [`count_tokens`](https://platform.claude.com/docs/en/build-with-claude/token-counting) endpoint. Its
  fixed 8-token message overhead is measured two independent ways and subtracted.
- **Gemini:** Google does not publish Gemini's tokenizer either, so Gemini is counted through the free
  [`countTokens`](https://ai.google.dev/gemini-api/docs/tokens) endpoint, on Gemini 3.8 Flash (the 3.x
  models in the free Gemini app) and Gemini 4 Argon (the paid flagship, a new tokenizer). Gemini 3.x
  equals Google's open Gemma 4 tokenizer in 201 of 204 languages (max 0.012 % apart).
- **Check:** the GPT-4 (cl100k) premiums match Petrov et al.'s own counts
  (`assets/tokenization_lengths.csv` in their repository) to a median 0.30 % (max 2.2 %) over the 204
  languages; Swedish is 1.577 here and 1.578 there.

## Output

| File | What it is |
|---|---|
| `data/data.csv` | One row per language: `<tokenizer>_tokens` and `<tokenizer>_premium` per tokenizer |
| `data/tokenizers.csv` | One row per tokenizer column: models, when introduced, current or not, exact source file and version |
| `data/country_premiums.csv` | One row per country (main language, ISO codes, premiums), ready for a choropleth map |
| `data/country_population.json` | Population per country (World Bank SP.POP.TOTL, 2025), used to list a language's biggest countries first |
| `data/counts/*.json` | Raw counts per counting script |

Older tokenizers (GPT-4 2023, Gemma 3, Llama 3, Qwen 3) stay in the data next to their successors,
so before/after comparisons are possible. `tokenizers.csv`'s `pill` column says which ones the web page
shows; the rest (e.g. Gemini 4 Argon, Mistral) are in the data only.

## Run it

Needs Node 18+, Python 3.10+ and git. No Hugging Face account: every tokenizer file is public and
pinned to a commit.

```bash
npm install
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
bash scripts/run_all.sh
```

About 4 minutes. It downloads FLORES and the tokenizers, recounts everything and rewrites the CSVs.
A fresh run reproduces the committed CSV exactly.

**Claude and Gemini (optional):** copy `.env.example` to `.env` and add an Anthropic and/or a Gemini API
key, then `set -a; . ./.env; set +a` before `run_all.sh`. Counting is free and takes a few minutes. Without
a key, the committed `data/counts/claude.json` or `gemini_api.json` is used. To recount, delete it first.

## Add a tokenizer

Open tokenizers: add an entry to the config at the end of `scripts/fetch_tokenizers.sh`
(`hf_json` for a Hugging Face `tokenizer.json`, `tiktoken` with its `pat_str`, or `tekken`), rerun,
and the new key becomes a column. Add a row to `data/tokenizers.csv` describing it.

Not included yet: xAI's Grok (no public tokenizer), and national models such as GPT-SW3 (Swedish),
Viking/Poro (Nordic), NorMistral (Norwegian) and Sarvam (Indian languages).

## Limits

- Each country on the globe is coloured by one main language, which simplifies multilingual countries.
- Anthropic calls its count an estimate; repeated counts were identical. Both API counts include a fixed
  request overhead, measured and subtracted per model.
- FLORES-200 is 842 English Wikinews, Wikijunior and Wikivoyage articles, professionally translated
  (a few languages via Spanish, French, Russian or Arabic; see
  [Meta's FLORES-200 README](https://github.com/facebookresearch/flores/blob/main/flores200/README.md)).
  Chat, code or other text may give other premiums.

## Licence

Code: MIT. Data: CC BY-SA 4.0, matching FLORES-200. See `LICENSE`.
