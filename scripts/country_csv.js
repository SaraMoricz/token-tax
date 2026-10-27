// Usage: node country_csv.js <premiums.csv> <country_language_map.json> <out.csv>
// One row per country (for Datawrapper choropleths etc.): country, ISO3/ISO2/numeric codes, language, premiums, tooltip text.
const fs = require('fs'), path = require('path');
const NM = path.join(__dirname, '..', 'node_modules');
const world = require(path.join(NM, 'world-atlas/countries-110m.json'));
const topojson = require(path.join(NM, 'topojson-client'));
const [csvF, mapF, outF] = process.argv.slice(2);
const lines = fs.readFileSync(csvF, 'utf8').trim().split('\n');
const parse = (l) => { const o = []; let c = '', q = false; for (const ch of l) { if (ch === '"') q = !q; else if (ch === ',' && !q) { o.push(c); c = ''; } else c += ch; } o.push(c); return o; };
const head = parse(lines[0]);
const prem = head.filter((h) => h.endsWith('_premium'));
const byCode = {};
for (const l of lines.slice(1)) { const r = Object.fromEntries(parse(l).map((v, i) => [head[i], v])); byCode[r.flores_code] = r; }
const cmap = JSON.parse(fs.readFileSync(mapF, 'utf8'));
const iso = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', 'iso_codes.json'), 'utf8')); // ISO numeric -> iso2/iso3 (Unicode CLDR)
const q = (s) => (/[",]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s);
const out = [['country', 'iso3', 'iso2', 'iso_numeric', 'language', 'flores_code', ...prem, 'tooltip_chatgpt'].join(',')];
for (const f of topojson.feature(world, world.objects.countries).features) {
  const code = cmap[f.properties.name]; if (!code) continue;
  const r = byCode[code];
  const ic = iso[f.id] || ({ Kosovo: { iso3: 'XKX', iso2: 'XK' } })[f.properties.name] || {};
  const tip = r.chatgpt_o200k_premium ? `${r.language}: ${(+r.chatgpt_o200k_premium).toFixed(2)}x tokens vs English on ChatGPT` : '';
  out.push([f.properties.name, ic.iso3 || '', ic.iso2 || '', f.id || '', r.language, code, ...prem.map((p) => r[p]), tip].map(q).join(','));
}
fs.writeFileSync(outF, out.join('\n') + '\n');
console.log(outF, out.length - 1, 'countries');
