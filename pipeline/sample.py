"""Pull a sample of well-known footballers from Wikidata with their team spells.

Usage: python3 sample.py [N]   (default N=2000)
Writes data/sample_raw.json
"""
import json, os, sys, time
from wd import sparql

N = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
OUT = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUT, exist_ok=True)

def qid(uri):
    return uri.rsplit("/", 1)[-1]

def val(row, key):
    return row[key]["value"] if key in row else None

def batched(xs, n):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]

# 1. Top N association football players by sitelink count (proxy for fame).
print(f"Fetching top {N} players…")
rows = sparql(f"""
SELECT ?p ?links WHERE {{
  ?p wdt:P106 wd:Q937857; wikibase:sitelinks ?links .
  FILTER(?links >= 15)
}} ORDER BY DESC(?links) LIMIT {N}""")
players = {qid(r["p"]["value"]): {"sitelinks": int(r["links"]["value"])} for r in rows}
print(f"  got {len(players)}")

# 2. Player details: label, birth, positions.
print("Fetching player details…")
for chunk in batched(list(players), 250):
    values = " ".join(f"wd:{q}" for q in chunk)
    for r in sparql(f"""
    SELECT ?p ?pLabel ?birth ?posLabel WHERE {{
      VALUES ?p {{ {values} }}
      OPTIONAL {{ ?p rdfs:label ?pEn FILTER(LANG(?pEn) = "en") }}
      OPTIONAL {{ ?p rdfs:label ?pMul FILTER(LANG(?pMul) = "mul") }}
      BIND(COALESCE(?pEn, ?pMul) AS ?pLabel)
      OPTIONAL {{ ?p wdt:P569 ?birth }}
      OPTIONAL {{ ?p wdt:P413 ?pos . ?pos rdfs:label ?posLabel FILTER(LANG(?posLabel) = "en") }}
    }}"""):
        p = players[qid(r["p"]["value"])]
        p["name"] = val(r, "pLabel")
        if val(r, "birth"):
            p["birth"] = val(r, "birth")[:10]
        if val(r, "posLabel"):
            p.setdefault("positions", set()).add(val(r, "posLabel"))
    time.sleep(0.5)

# 3. Team spells (P54) with qualifiers.
print("Fetching team spells…")
spells = []
for chunk in batched(list(players), 100):
    values = " ".join(f"wd:{q}" for q in chunk)
    for r in sparql(f"""
    SELECT ?p ?team ?start ?end ?apps WHERE {{
      VALUES ?p {{ {values} }}
      ?p p:P54 ?st . ?st ps:P54 ?team ; wikibase:rank ?rank .
      FILTER(?rank != wikibase:DeprecatedRank)
      OPTIONAL {{ ?st pq:P580 ?start }}
      OPTIONAL {{ ?st pq:P582 ?end }}
      OPTIONAL {{ ?st pq:P1350 ?apps }}
    }}"""):
        spells.append({
            "player": qid(r["p"]["value"]),
            "team": qid(r["team"]["value"]),
            "start": (val(r, "start") or "")[:10] or None,
            "end": (val(r, "end") or "")[:10] or None,
            "apps": int(float(val(r, "apps"))) if val(r, "apps") else None,
        })
    time.sleep(0.5)
print(f"  got {len(spells)} spells")

# 4. Team metadata: label + instance-of classes, to separate clubs from national teams.
print("Fetching team metadata…")
teams = {}
for chunk in batched(sorted({s["team"] for s in spells}), 250):
    values = " ".join(f"wd:{q}" for q in chunk)
    for r in sparql(f"""
    SELECT ?t ?tLabel ?clsLabel WHERE {{
      VALUES ?t {{ {values} }}
      OPTIONAL {{ ?t rdfs:label ?tEn FILTER(LANG(?tEn) = "en") }}
      OPTIONAL {{ ?t rdfs:label ?tMul FILTER(LANG(?tMul) = "mul") }}
      BIND(COALESCE(?tEn, ?tMul) AS ?tLabel)
      OPTIONAL {{ ?t wdt:P31 ?cls . ?cls rdfs:label ?clsLabel FILTER(LANG(?clsLabel) = "en") }}
    }}"""):
        t = teams.setdefault(qid(r["t"]["value"]), {"name": val(r, "tLabel"), "classes": set()})
        if val(r, "clsLabel"):
            t["classes"].add(val(r, "clsLabel"))
    time.sleep(0.5)
print(f"  got {len(teams)} teams")

def to_json(o):
    if isinstance(o, set):
        return sorted(o)
    raise TypeError(o)

with open(os.path.join(OUT, "sample_raw.json"), "w") as f:
    json.dump({"players": players, "spells": spells, "teams": teams}, f, default=to_json)
print("Wrote data/sample_raw.json")
