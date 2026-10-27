"""Count Claude tokens for every FLORES-200 devtest language via Anthropic's free
token-counting endpoint (no generation, so no token cost; it is rate-limited).

Usage:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 count_claude.py <flores_devtest_dir> claude.json [--model claude-opus-5-5] [--n 1012]

Each language is counted as ONE text: its sentences joined with newlines, exactly
like count_more.py / count_gemini.py / count_openai.js. One request per language
(~40k tokens). The fixed per-message overhead is measured two independent ways,
checked to agree (also on Thai and Amharic text), and subtracted once per
language. Re-running resumes: languages already in the output file are skipped.
"""
import argparse
import json
import os
import time

import anthropic

p = argparse.ArgumentParser()
p.add_argument("flores_dir")
p.add_argument("out_file")
p.add_argument("--model", default="claude-opus-5-5")
p.add_argument("--n", type=int, default=1012, help="sentences per language (FLORES devtest has 1012)")
a = p.parse_args()

client = anthropic.Anthropic()


def count(text):
    for attempt in range(8):
        try:
            r = client.messages.count_tokens(model=a.model, messages=[{"role": "user", "content": text}])
            return r.input_tokens
        except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.InternalServerError):
            time.sleep(2 ** attempt)
    raise RuntimeError("count_tokens kept failing")


# Per-message overhead, two ways.
# (a) Additivity: count(T) + count(U) - count(T + U) = overhead, if no token spans the join.
#     U starts with a newline after T's final full stop, so the join is a natural token boundary.
PAIRS = [("The cat sat on the mat.", "\nA dog ran past the house."),
         ("Stockholm is the capital of Sweden.", "\nIt has about a million inhabitants."),
         ("กรุงเทพฯ เป็นเมืองหลวงของประเทศไทย", "\nแมวนั่งอยู่บนเสื่อ"),
         ("አዲስ አበባ የኢትዮጵያ ዋና ከተማ ናት።", "\nድመቷ ምንጣፉ ላይ ተቀመጠች።")]
# (b) Intercept: count(X * k) for k = 1, 2, 3 is linear in k; the intercept is the overhead.
#     X starts (not ends) with its newline: the endpoint ignores trailing whitespace, so a
#     trailing "\n" would be dropped once and bias the intercept down by one.
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
    if code in out:
        continue
    with open(os.path.join(a.flores_dir, f), encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip()][: a.n]
    total = count("\n".join(lines)) - overhead
    out[code] = {"claude": total, "sentences": len(lines), "model": a.model, "overhead": overhead}
    json.dump(out, open(a.out_file, "w"), indent=1)
    print(f"[{i}/{len(files)}] {code}: {total}")
