"""Usage: python3 -I build_csv.py <language_map.csv> <out.csv> <counts1.json> [counts2.json ...]
Merges per-language token counts from any number of JSON files (missing files are skipped)
and writes one row per FLORES-200 language: total tokens and premium vs English per tokenizer.
Premium = tokens(language) / tokens(English) on the same parallel FLORES devtest text."""
import csv
import json
import os
import sys

# (CSV column prefix, key in the JSON files). Order = column order. Unknown keys are ignored.
COLUMNS = [
    ("chatgpt_o200k", "o200k"),
    ("gemini_gemma3", "gemma3"),
    ("gemini_gemma4", "gemma4"),
    ("gemini_3x_flash", "gemini38_flash"),   # Google countTokens, gemini-3.8-flash
    ("gemini_4_argon", "gemini4_argon"),     # Google countTokens, gemini-4-argon
    ("claude", "claude"),
    ("llama3", "llama3"),
    ("llama4_muse", "llama4_muse"),
    ("deepseek_v4", "deepseek_v4"),
    ("qwen3", "qwen3"),
    ("qwen35", "qwen35"),
    ("mistral_tekken", "mistral_tekken"),
    ("gpt4_cl100k_2023", "cl100k"),
]

map_f, out_f, *count_files = sys.argv[1:]
names = {r[" FLORES-200 code"].strip(): r["Language"].strip() for r in csv.DictReader(open(map_f))}
merged = {}
for f in count_files:
    if not os.path.exists(f):
        print("skipping missing", f)
        continue
    for code, vals in json.load(open(f)).items():
        merged.setdefault(code, {}).update(vals)

META = {"sentences", "chars", "chunks", "model", "overhead"}
cols = [(c, k) for c, k in COLUMNS if any(k in v for v in merged.values())]
known = {k for _, k in COLUMNS}
extra = sorted({k for v in merged.values() for k in v if k not in known and k not in META and not k.endswith(("_per_sentence", "_model", "_overhead"))})
cols += [(k, k) for k in extra]  # any new tokenizer you add shows up as its own column
eng = merged["eng_Latn"]
rows = []
for code in sorted(merged):
    v = merged[code]
    r = {"language": names.get(code, code), "flores_code": code, "script": code.split("_")[1],
         "sentences": v.get("sentences", ""), "characters": v.get("chars", "")}
    for c, k in cols:
        r[f"{c}_tokens"] = v.get(k, "")
    for c, k in cols:
        r[f"{c}_premium"] = round(v[k] / eng[k], 3) if k in v and k in eng else ""
    rows.append(r)

rows.sort(key=lambda r: r["chatgpt_o200k_premium"] if r["chatgpt_o200k_premium"] != "" else 99)
with open(out_f, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print("rows:", len(rows), "tokenizers:", [c for c, _ in cols])
