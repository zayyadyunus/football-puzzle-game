"""Stage 2: English Wikipedia pageviews as the fame signal.

Usage: python3 pageviews.py [N]   (default 30000: top-N graph players by sitelinks)
Reads data/graph.json (run build.py first), appends to data/raw/pageviews.csv (resumable).
Then re-run build.py to fold the views into fame scores.

Uses the MediaWiki Action API (prop=pageviews), which returns the last 60 days of daily views
for 50 titles per request. The per-article REST API is rate-limited too hard for bulk use.
"""
import csv, json, os, sys, time, urllib.error, urllib.parse, urllib.request
from wd import UA, _CTX

N = int(sys.argv[1]) if len(sys.argv) > 1 else 30000
HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "data", "raw", "pageviews.csv")
API = "https://en.wikipedia.org/w/api.php"

graph = json.load(open(os.path.join(HERE, "data", "graph.json"), encoding="utf-8"))
cands = sorted((pid for pid, p in graph["players"].items() if p.get("w")),
               key=lambda pid: -graph["players"][pid]["sl"])[:N]

done = set()
if os.path.exists(OUT):
    with open(OUT) as f:
        done = {r["pid"] for r in csv.DictReader(f)}
todo = [pid for pid in cands if pid not in done]
print(f"{len(cands)} candidates, {len(done)} already fetched, {len(todo)} to go", flush=True)


def get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60, context=_CTX) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            wait = int(e.headers.get("retry-after") or 0) or 2 ** attempt * 5
            print(f"  HTTP {e.code}, waiting {wait}s", flush=True)
            time.sleep(wait)
        except Exception as e:
            print(f"  {type(e).__name__}: {e}", flush=True)
            time.sleep(2 ** attempt)
    raise RuntimeError("API keeps failing")


def fetch_batch(pids):
    title_of = {pid: urllib.parse.unquote(graph["players"][pid]["w"]).replace("_", " ") for pid in pids}
    params = {"action": "query", "prop": "pageviews", "pvipdays": 60, "format": "json", "formatversion": 2,
              "redirects": 1, "titles": "|".join(title_of.values())}
    views, alias = {}, {}
    while True:
        d = get(params)
        q = d.get("query", {})
        for m in q.get("normalized", []) + q.get("redirects", []):
            alias[m["from"]] = m["to"]
        for page in q.get("pages", []):
            pv = page.get("pageviews")
            if pv is not None:
                views[page["title"]] = views.get(page["title"], 0) + sum(v or 0 for v in pv.values())
        if "continue" not in d:
            break
        params.update(d["continue"])
    out = []
    for pid, t in title_of.items():
        while t in alias:
            t = alias[t]
        out.append((pid, views.get(t, "")))
    return out


new_file = not os.path.exists(OUT)
t0 = time.time()
with open(OUT, "a", newline="") as fh:
    w = csv.writer(fh)
    if new_file:
        w.writerow(["pid", "views"])
    for i in range(0, len(todo), 50):
        w.writerows(fetch_batch(todo[i:i + 50]))
        fh.flush()
        if (i // 50) % 40 == 0:
            print(f"  {i + 50}/{len(todo)}  {time.time() - t0:.0f}s", flush=True)
        time.sleep(0.5)
print(f"Done in {time.time() - t0:.0f}s", flush=True)
