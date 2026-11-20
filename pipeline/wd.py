"""Minimal Wikidata SPARQL client (stdlib only)."""
import json, os, ssl, time, urllib.parse, urllib.request

# QLever (Uni Freiburg) mirrors Wikidata and is far faster than WDQS for bulk queries.
# WDQS was rate-limited during an outage when this was written (2026-11-19).
ENDPOINT = "https://qlever.dev/api/wikidata"

PREFIXES = """
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""
# Some python.org macOS builds lack a CA store; fall back to the system bundle.
_CTX = ssl.create_default_context(cafile="/etc/ssl/cert.pem" if os.path.exists("/etc/ssl/cert.pem") else None)
UA = "FootballXIPuzzle-DataPipeline/0.1 (research prototype)"

def sparql(query, retries=3):
    data = urllib.parse.urlencode({"query": PREFIXES + query, "format": "json"}).encode()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(ENDPOINT, data=data, headers={
                "User-Agent": UA, "Accept": "application/sparql-results+json"})
            with urllib.request.urlopen(req, timeout=300, context=_CTX) as r:
                return json.load(r)["results"]["bindings"]
        except Exception as e:
            print(f"  query failed ({e}); retry {attempt+1}/{retries}")
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("SPARQL query failed")
