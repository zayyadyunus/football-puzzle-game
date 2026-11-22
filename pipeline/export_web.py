"""Export graph + puzzles as small static files for the web app.

Usage: python3 export_web.py
Writes web/public/data/
  search/<xxx>.json  players with a name word starting with <xxx> (normalised a–z, 3 chars;
                     2-letter words get their own 2-char file), fame-sorted
  p/<n>.json         career spells for players whose numeric QID % SHARDS == n
  puzzles/<date>.json + puzzles/index.json
"""
import collections, glob, json, os, re, shutil, unicodedata
from links import Graph

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "web", "public", "data")
SHARDS = 512  # keep in sync with web/src/lib/data.ts


def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("ø", "o").replace("Ø", "O").replace("ł", "l").replace("Ł", "L").replace("đ", "d").replace("ß", "ss")
    return s.lower()


def tokens(name):
    return [t for t in re.split(r"[^a-z0-9]+", norm(name)) if len(t) >= 2]


def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def main():
    g = Graph.load()
    if os.path.exists(OUT):
        shutil.rmtree(OUT)

    # ---- search index
    buckets = collections.defaultdict(list)
    for pid, p in g.players.items():
        years = [x for _, a, b in g.spells[pid] for x in (a, b)]
        entry = [pid, p["n"], p["nat"] or "", "/".join(p["pos"]), p["b"] or 0,
                 int(min(years)) if years else 0, int(max(years)) if years else 0, round(p["f"], 2)]
        for prefix in {t[:3] for t in tokens(p["n"])}:
            buckets[prefix].append(entry)
    sizes = []
    for prefix, entries in buckets.items():
        entries.sort(key=lambda e: -e[7])
        write(os.path.join(OUT, "search", f"{prefix}.json"), entries)
        sizes.append(len(entries))
    print(f"search: {len(buckets)} files, median {sorted(sizes)[len(sizes) // 2]} entries, max {max(sizes)}")

    # ---- career shards
    shards = collections.defaultdict(dict)
    for pid, ss in g.spells.items():
        shards[int(pid[1:]) % SHARDS][pid] = [[g.team_name(t), g.teams[t]["k"] == "nat_senior", a, b] for t, a, b in ss]
        # team id is needed for exact matching (two clubs can share a name)
        for row, (t, _, _) in zip(shards[int(pid[1:]) % SHARDS][pid], ss):
            row.insert(0, t)
    for n, players in shards.items():
        write(os.path.join(OUT, "p", f"{n}.json"), players)
    print(f"careers: {len(shards)} shards")

    # ---- puzzles (strip nothing for now; the reference solution is revealed after solving)
    dates = []
    for path in sorted(glob.glob(os.path.join(HERE, "..", "puzzles", "*.json"))):
        pz = json.load(open(path, encoding="utf-8"))
        write(os.path.join(OUT, "puzzles", os.path.basename(path)), pz)
        dates.append(pz["date"])
    write(os.path.join(OUT, "puzzles", "index.json"), {"dates": dates, "min_overlap": 0.05})
    print(f"puzzles: {len(dates)} ({dates[0]} … {dates[-1]})")

    total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT) for f in fs)
    print(f"total {total / 1e6:.1f} MB raw")


if __name__ == "__main__":
    main()
