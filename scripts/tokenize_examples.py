"""Usage: python3 -I tokenize_examples.py <out.json>
Splits one example sentence per language into tokens with each tokenizer on the web page, to show readers what
tokenization does. The sentence is Petrov et al.'s example 0 (flores/assets/examples/<code>.json), a FLORES-200
dev-split sentence they already publish; FLORES-200 is CC BY-SA 4.0. The output is NOT committed (see .gitignore)
and the page serves it from a file robots.txt keeps crawlers away from, so the text isn't re-hosted for crawlers.

Per tokenizer: n (token count) and spans ([start, end) character offsets per token; tokens inside one character
share its span). Claude and Gemini publish no tokenizer and their APIs (with an AI Studio key) return counts only,
so they have n but no spans. Gemma 4 gives the same Gemini 3.x counts on all 204 example sentences, but equal
counts don't prove equal cuts, so its pieces are not shown as Gemini's.
"""
import base64
import glob
import json
import os
import re
import sys

import tiktoken
from tokenizers import Tokenizer

out_file = sys.argv[1]
root = os.path.join(os.path.dirname(__file__), "..")
T = os.path.join(root, "tokenizers")


def hf(name):
    t = Tokenizer.from_file(os.path.join(T, name))
    return lambda s: [list(o) for o in t.encode(s, add_special_tokens=False).offsets]


def tik(enc):
    def spans(s):
        _, starts = enc.decode_with_offsets(enc.encode_ordinary(s))
        return [[a, b] for a, b in zip(starts, starts[1:] + [len(s)])]
    return spans


def llama4():
    pat = re.search(r'O200K_PATTERN = r"""(.*?)"""', open(os.path.join(T, "llama4_tokenizer.py")).read()).group(1)
    ranks = {base64.b64decode(a): int(b) for a, b in (l.split() for l in open(os.path.join(T, "llama4.tiktoken"), "rb") if l.strip())}
    return tik(tiktoken.Encoding(name="llama4", pat_str=pat, mergeable_ranks=ranks, special_tokens={}))


SPLIT = {   # the tokenizers behind the page's buttons
    "chatgpt_o200k": tik(tiktoken.get_encoding("o200k_base")),
    "llama4_muse": llama4(),
    "deepseek_v4": hf("deepseek_v4.json"),
    "qwen35": hf("qwen35.json"),
}

claude = None
if os.environ.get("ANTHROPIC_API_KEY"):
    import anthropic
    client = anthropic.Anthropic()
    count = lambda s: client.messages.count_tokens(model="claude-opus-5-5", messages=[{"role": "user", "content": s}]).input_tokens
    overhead = count("a") + count("\nb") - count("a\nb")   # same additivity check as count_claude.py (8 on Opus 5.5)
    claude = lambda s: count(s) - overhead

gemini = None
if os.environ.get("GEMINI_API_KEY"):
    import urllib.request
    def gemini(s):   # Gemini API countTokens on gemini-3.8-flash, minus its 1-token request overhead (see count_gemini_api.py)
        req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:countTokens",
                                     json.dumps({"contents": [{"role": "user", "parts": [{"text": s}]}]}).encode(),
                                     {"x-goog-api-key": os.environ["GEMINI_API_KEY"], "content-type": "application/json"})
        return json.load(urllib.request.urlopen(req, timeout=60))["totalTokens"] - 1

out = {"_source": "Example sentence 0 per language from Petrov et al., github.com/AleksandarPetrov/tokenization-fairness "
                  "(assets/examples, commit 365c3f8); FLORES-200 dev split, CC BY-SA 4.0. Do not re-host for crawlers."}
for f in sorted(glob.glob(os.path.join(root, "flores", "assets", "examples", "*.json"))):
    code = os.path.basename(f)[:-5]
    text = json.load(open(f, encoding="utf-8"))["cl100k_base"]["0"]["text"]
    toks = {k: {"n": len(sp), "spans": sp} for k, fn in SPLIT.items() for sp in [fn(text)]}
    if claude:
        toks["claude"] = {"n": claude(text)}
    if gemini:
        toks["gemini_3x_flash"] = {"n": gemini(text)}
    out[code] = {"text": text, "tokens": toks}
json.dump(out, open(out_file, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
e = out["eng_Latn"]["tokens"]; s = out["swe_Latn"]["tokens"]
print(out_file, len(out) - 1, "languages | English vs Swedish tokens:", {k: (e[k]["n"], s[k]["n"]) for k in e})
