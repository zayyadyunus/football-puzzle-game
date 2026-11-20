"""Stage 1: bulk-export raw football data from Wikidata (via QLever) as CSV.

Usage: python3 fetch.py [MIN_SITELINKS]   (default 5)
Writes data/raw/{players,positions,occupations,spells,teams,labels}.csv
"""
import csv, io, os, sys, time, urllib.parse, urllib.request
from wd import ENDPOINT, PREFIXES, UA, _CTX

MIN_SITELINKS = int(sys.argv[1]) if len(sys.argv) > 1 else 5
RAW = os.path.join(os.path.dirname(__file__), "data", "raw")
os.makedirs(RAW, exist_ok=True)

# The player pool, reused as a sub-pattern in every query.
POOL = f"""
  ?p wdt:P106 wd:Q937857 ; wikibase:sitelinks ?sl .
  FILTER(?sl >= {MIN_SITELINKS})
  FILTER NOT EXISTS {{ ?p wdt:P21 wd:Q6581072 }}
"""

QUERIES = {
    "players": f"""
SELECT ?p ?sl ?en ?mul ?birth ?enwiki WHERE {{
  {POOL}
  OPTIONAL {{ ?p rdfs:label ?en FILTER(LANG(?en) = "en") }}
  OPTIONAL {{ ?p rdfs:label ?mul FILTER(LANG(?mul) = "mul") }}
  OPTIONAL {{ ?p wdt:P569 ?birth }}
  OPTIONAL {{ ?enwiki <http://schema.org/about> ?p ; <http://schema.org/isPartOf> <https://en.wikipedia.org/> }}
}}""",
    "positions": f"""
SELECT ?p ?pos WHERE {{ {POOL} ?p wdt:P413 ?pos . }}""",
    "occupations": f"""
SELECT ?p ?occ WHERE {{ {POOL} ?p wdt:P106 ?occ . }}""",
    "citizenship": f"""
SELECT ?p ?c WHERE {{ {POOL} ?p wdt:P27 ?c . }}""",
    "spells": f"""
SELECT ?p ?team ?start ?end ?apps WHERE {{
  {POOL}
  ?p p:P54 ?st . ?st ps:P54 ?team ; wikibase:rank ?rank .
  FILTER(?rank != wikibase:DeprecatedRank)
  OPTIONAL {{ ?st pq:P580 ?start }}
  OPTIONAL {{ ?st pq:P582 ?end }}
  OPTIONAL {{ ?st pq:P1350 ?apps }}
}}""",
    "teams": f"""
SELECT DISTINCT ?team ?en ?mul ?cls ?country WHERE {{
  {POOL}
  ?p wdt:P54 ?team .
  OPTIONAL {{ ?team rdfs:label ?en FILTER(LANG(?en) = "en") }}
  OPTIONAL {{ ?team rdfs:label ?mul FILTER(LANG(?mul) = "mul") }}
  OPTIONAL {{ ?team wdt:P31 ?cls }}
  OPTIONAL {{ ?team wdt:P17 ?country }}
}}""",
}


def fetch_csv(name, query):
    path = os.path.join(RAW, f"{name}.csv")
    data = urllib.parse.urlencode({"query": PREFIXES + query}).encode()
    req = urllib.request.Request(ENDPOINT, data=data, headers={"User-Agent": UA, "Accept": "text/csv"})
    t = time.time()
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=600, context=_CTX) as r, open(path, "wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            break
        except Exception as e:
            print(f"  {name}: failed ({e}), retry {attempt + 1}/3")
            time.sleep(10 * (attempt + 1))
    else:
        raise RuntimeError(f"fetch {name} failed")
    with open(path) as f:
        n = sum(1 for _ in f) - 1
    print(f"  {name}: {n:,} rows in {time.time() - t:.0f}s")


def fetch_labels():
    """English labels for every position / occupation / team-class / country QID referenced."""
    qids = set()
    for name, cols in [("positions", ["pos"]), ("occupations", ["occ"]), ("teams", ["cls", "country"]), ("citizenship", ["c"])]:
        with open(os.path.join(RAW, f"{name}.csv")) as f:
            for row in csv.DictReader(f):
                for c in cols:
                    if row.get(c, "").startswith("http://www.wikidata.org/entity/"):
                        qids.add(row[c].rsplit("/", 1)[-1])
    qids = sorted(qids)
    out = []
    for i in range(0, len(qids), 2000):
        values = " ".join(f"wd:{q}" for q in qids[i:i + 2000])
        query = f"""SELECT ?x ?label WHERE {{ VALUES ?x {{ {values} }}
          OPTIONAL {{ ?x rdfs:label ?en FILTER(LANG(?en) = "en") }}
          OPTIONAL {{ ?x rdfs:label ?mul FILTER(LANG(?mul) = "mul") }}
          BIND(COALESCE(?en, ?mul) AS ?label) }}"""
        data = urllib.parse.urlencode({"query": PREFIXES + query}).encode()
        req = urllib.request.Request(ENDPOINT, data=data, headers={"User-Agent": UA, "Accept": "text/csv"})
        with urllib.request.urlopen(req, timeout=300, context=_CTX) as r:
            out.extend(list(csv.DictReader(io.TextIOWrapper(r, encoding="utf-8"))))
    with open(os.path.join(RAW, "labels.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["x", "label"])
        w.writeheader()
        w.writerows(out)
    print(f"  labels: {len(out):,} rows")


if __name__ == "__main__":
    print(f"Fetching pool: male footballers with >= {MIN_SITELINKS} sitelinks")
    for name, q in QUERIES.items():
        fetch_csv(name, q)
    fetch_labels()
