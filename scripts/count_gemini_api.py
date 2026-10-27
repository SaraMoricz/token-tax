"""Count Gemini tokens for every FLORES-200 devtest language via the Gemini API's free countTokens endpoint
(no generation, so no token cost; rate-limited).

Usage:
    export GEMINI_API_KEY=...        # Google AI Studio, https://aistudio.google.com/apikey
    python3 -I count_gemini_api.py <flores_devtest_dir> <out.json> --model gemini-4-argon --key gemini4_argon

Each language is counted as ONE text, its sentences joined with newlines, like the other counting scripts.
The fixed per-request overhead is measured two independent ways, checked to agree (also on Thai and Amharic),
and subtracted once per language. Re-running resumes: languages already in the output file (for this key)
are skipped.
"""
import argparse
import json
import os
import time
import urllib.error
import urllib.request

p = argparse.ArgumentParser()
p.add_argument("flores_dir")
p.add_argument("out_file")
p.add_argument("--model", required=True)
p.add_argument("--key", required=True, help="key in the output JSON, e.g. gemini4_argon")
p.add_argument("--n", type=int, default=1012, help="sentences per language (FLORES devtest has 1012)")
a = p.parse_args()
api_key = os.environ["GEMINI_API_KEY"]


def count(text):
    body = json.dumps({"contents": [{"role": "user", "parts": [{"text": text}]}]}).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{a.model}:countTokens"
    for attempt in range(8):
        req = urllib.request.Request(url, body, {"x-goog-api-key": api_key, "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)["totalTokens"]
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise
        except urllib.error.URLError:
            pass
        time.sleep(2 ** attempt)
    raise RuntimeError("countTokens kept failing")


# Per-request overhead, two ways (same as count_claude.py).
# (a) Additivity: count(T) + count(U) - count(T + U); U starts with a newline, so the join is a natural boundary.
PAIRS = [("The cat sat on the mat.", "\nA dog ran past the house."),
         ("Stockholm is the capital of Sweden.", "\nIt has about a million inhabitants."),
         ("กรุงเทพฯ เป็นเมืองหลวงของประเทศไทย", "\nแมวนั่งอยู่บนเสื่อ"),
         ("አዲስ አበባ የኢትዮጵያ ዋና ከተማ ናት።", "\nድመቷ ምንጣፉ ላይ ተቀመጠች።")]
# (b) Intercept: count(X * k) for k = 1, 2, 3 is linear in k; the intercept is the overhead.
REPS = ["\nThe cat sat on the mat.", "\nกรุงเทพฯ เป็นเมืองหลวงของประเทศไทย", "\nአዲስ አበባ የኢትዮጵያ ዋና ከተማ ናት።"]
add = [count(t) + count(u) - count(t + u) for t, u in PAIRS]
icpt = []
for x in REPS:
    c = [count(x * k) for k in (1, 2, 3)]
    assert c[2] - c[1] == c[1] - c[0], f"not linear in k: {c}"
    icpt.append(c[0] - (c[1] - c[0]))
print(f"model={a.model} overhead additivity={add} intercept={icpt}")
assert len(set(add + icpt)) == 1, "overhead estimates disagree"
overhead = add[0]

out = json.load(open(a.out_file)) if os.path.exists(a.out_file) else {}
files = sorted(f for f in os.listdir(a.flores_dir) if f.endswith(".devtest"))
for i, f in enumerate(files, 1):
    code = f[: -len(".devtest")]
    if a.key in out.get(code, {}):
        continue
    with open(os.path.join(a.flores_dir, f), encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip()][: a.n]
    out.setdefault(code, {})[a.key] = count("\n".join(lines)) - overhead
    out[code][f"{a.key}_model"], out[code][f"{a.key}_overhead"] = a.model, overhead
    json.dump(out, open(a.out_file, "w"), indent=1)
    print(f"[{i}/{len(files)}] {code}: {out[code][a.key]}")
