"""Usage: python3 -I count_more.py <flores_devtest_dir> <out.json> <config.json>
Counts tokens per language for extra open-weight tokenizers listed in config.json:
  {"name": {"kind": "hf_json" | "tiktoken" | "tekken", "path": "...", "pat_str": "..." (tiktoken only)}}
Each language's sentences are joined with newlines, matching the other counting scripts."""
import base64
import json
import os
import sys

d, out_file, cfg_file = sys.argv[1:4]
cfg = json.load(open(cfg_file))


def load(kind, path, pat_str=None):
    if kind == "hf_json":
        from tokenizers import Tokenizer
        t = Tokenizer.from_file(path)
        return lambda s: len(t.encode(s, add_special_tokens=False).ids)
    if kind == "tiktoken":
        import tiktoken
        ranks = {}
        for line in open(path, "rb"):
            if line.strip():
                tok, rank = line.split()
                ranks[base64.b64decode(tok)] = int(rank)
        enc = tiktoken.Encoding(name=os.path.basename(path), pat_str=pat_str, mergeable_ranks=ranks, special_tokens={})
        return lambda s: len(enc.encode_ordinary(s))
    if kind == "tekken":
        from mistral_common.tokens.tokenizers.tekken import Tekkenizer
        t = Tekkenizer.from_file(path)
        return lambda s: len(t.encode(s, bos=False, eos=False))
    raise ValueError(kind)


base = os.path.dirname(os.path.abspath(cfg_file))
encoders = {}
for name, c in cfg.items():
    c = dict(c)
    c["path"] = os.path.join(base, c["path"])  # paths in the config are relative to the config file
    encoders[name] = load(**c)
out = {}
for f in sorted(os.listdir(d)):
    if not f.endswith(".devtest"):
        continue
    with open(os.path.join(d, f), encoding="utf-8") as fh:
        text = "\n".join(l.rstrip("\n") for l in fh if l.strip())
    out[f[: -len(".devtest")]] = {name: enc(text) for name, enc in encoders.items()}
json.dump(out, open(out_file, "w"), indent=1)
print("languages:", len(out), "tokenizers:", list(encoders))
