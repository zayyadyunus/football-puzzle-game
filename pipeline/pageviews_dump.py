"""Stage 2 (preferred): pageviews from a Wikimedia monthly dump, streamed — nothing large touches disk.

Usage:
  curl -s https://dumps.wikimedia.org/other/pageview_complete/monthly/2026/2026-10/pageviews-202610-user.bz2 \
    | bzcat | LC_ALL=C awk '/^en\\.wikipedia /{print; seen=1; next} seen{exit}' | python3 pageviews_dump.py
  (awk exits once the en.wikipedia block ends — the dump is sorted by wiki — which stops the download early.)

Reads data/graph.json for player enwiki titles; writes data/raw/pageviews.csv (pid,views) for every
graph player with an English Wikipedia article. Then re-run build.py.
Dump line format: "<wiki> <title> <page_id> <access> <monthly_total> <daily_counts>"
"""
import collections, csv, json, os, sys, time, urllib.parse

HERE = os.path.dirname(__file__)
graph = json.load(open(os.path.join(HERE, "data", "graph.json"), encoding="utf-8"))
pid_of = {}
for pid, p in graph["players"].items():
    if p.get("w"):
        pid_of[urllib.parse.unquote(p["w"]).replace(" ", "_")] = pid
print(f"Matching {len(pid_of):,} titles", file=sys.stderr, flush=True)

OUT = os.path.join(HERE, "data", "raw", "pageviews.csv")


def write():
    tmp = OUT + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pid", "views"])
        for pid in pid_of.values():
            w.writerow([pid, views.get(pid, 0)])
    os.replace(tmp, OUT)


views = collections.Counter()
t0, n = time.time(), 0
for line in sys.stdin:
    n += 1
    parts = line.split(" ", 5)
    if len(parts) >= 5:
        pid = pid_of.get(parts[1])
        if pid:
            views[pid] += int(parts[4])
    if n % 20_000_000 == 0:
        write()
        print(f"  {n / 1e6:.0f}M en lines, {len(views):,} players matched, {time.time() - t0:.0f}s", file=sys.stderr, flush=True)

write()
print(f"Done: {n:,} en lines, {len(views):,}/{len(pid_of):,} players with views, {time.time() - t0:.0f}s",
      file=sys.stderr, flush=True)
