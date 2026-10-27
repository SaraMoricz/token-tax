"""Usage: python3 -I country_population.py <out.json> [year]
Population per country (World Bank, indicator SP.POP.TOTL), keyed by the same world-atlas country names as
data/country_language_map.json. The token-tax page uses it to list a language's biggest countries first.
Countries the World Bank doesn't cover (e.g. Taiwan, Western Sahara) are left out and listed."""
import json
import os
import sys
import urllib.request

out_file = sys.argv[1]
year = sys.argv[2] if len(sys.argv) > 2 else "2025"
root = os.path.join(os.path.dirname(__file__), "..")

world = json.load(open(os.path.join(root, "node_modules", "world-atlas", "countries-110m.json")))
iso = json.load(open(os.path.join(root, "data", "iso_codes.json")))   # ISO numeric -> iso2/iso3 (Unicode CLDR)
names = {g["properties"]["name"]: g.get("id") for g in world["objects"]["countries"]["geometries"]}
iso3 = {n: (iso.get(i) or {}).get("iso3") for n, i in names.items()}
iso3["Kosovo"] = "XKX"   # no ISO numeric code; same special case as country_csv.js

url = f"https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?format=json&per_page=20000&date={year}"
meta, rows = json.load(urllib.request.urlopen(url))
pop = {r["countryiso3code"]: int(r["value"]) for r in rows if r["value"] is not None and r["countryiso3code"]}

out = {n: pop[c] for n, c in sorted(iso3.items()) if c in pop}
missing = sorted(n for n in iso3 if n not in out)
json.dump({"_source": f"World Bank SP.POP.TOTL, {year} (data updated {meta.get('lastupdated')})", **out},
          open(out_file, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(out_file, len(out), "countries; no World Bank population:", ", ".join(missing))
