// Usage: node count_openai.js <flores_devtest_dir> <out.json> [n_sentences]
// Counts tokens per language with OpenAI's o200k_base (GPT-4o / GPT-5.x) and cl100k_base (GPT-3.5/4).
const fs = require('fs');
const path = require('path');
const o200k = require(path.join(__dirname, '..', 'node_modules', 'gpt-tokenizer/cjs/encoding/o200k_base'));
const cl100k = require(path.join(__dirname, '..', 'node_modules', 'gpt-tokenizer/cjs/encoding/cl100k_base'));

const [dir, outFile, nArg] = process.argv.slice(2);
const n = nArg ? parseInt(nArg, 10) : Infinity;
const out = {};
for (const f of fs.readdirSync(dir).filter((x) => x.endsWith('.devtest')).sort()) {
  const code = f.replace('.devtest', '');
  const lines = fs.readFileSync(path.join(dir, f), 'utf8').split('\n').filter((l) => l.length).slice(0, n);
  let a = 0, b = 0;
  for (const l of lines) { a += o200k.encode(l).length; b += cl100k.encode(l).length; }
  const joined = lines.join('\n');
  out[code] = { sentences: lines.length, chars: [...joined].length, o200k_per_sentence: a, cl100k_per_sentence: b, o200k: o200k.encode(joined).length, cl100k: cl100k.encode(joined).length };
}
fs.writeFileSync(outFile, JSON.stringify(out, null, 1));
console.log('languages:', Object.keys(out).length);
