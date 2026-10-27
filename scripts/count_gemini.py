"""Usage: python3 -I count_gemini.py <flores_devtest_dir> <sentencepiece_model> <out.json> [n_sentences]
Counts tokens per language with the Gemma 3 SentencePiece model, which Google's
google-genai SDK uses as the local tokenizer for Gemini 2.0-3.0 models."""
import json
import os
import sys

import sentencepiece as spm

d, model, out_file = sys.argv[1:4]
n = int(sys.argv[4]) if len(sys.argv) > 4 else None
sp = spm.SentencePieceProcessor(model_file=model)
out = {}
for f in sorted(os.listdir(d)):
    if not f.endswith(".devtest"):
        continue
    with open(os.path.join(d, f), encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip()][:n]
    out[f[: -len(".devtest")]] = {"gemma3_per_sentence": sum(len(sp.encode(l)) for l in lines), "gemma3": len(sp.encode("\n".join(lines)))}
json.dump(out, open(out_file, "w"), indent=1)
print("languages:", len(out))
