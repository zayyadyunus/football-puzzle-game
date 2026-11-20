"""Sanity report on data/graph.json: coverage, fame ranking, spot checks."""
import collections, random, statistics, sys
from links import Graph

g = Graph.load()
P = g.players
print("META:", g.meta)


def era(b):
    if b is None:
        return "unknown"
    return "<1950" if b < 1950 else "1950-69" if b < 1970 else "1970-84" if b < 1985 else "1985-94" if b < 1995 else "1995+"


# ---- coverage by era
print("\nBY ERA            players  puzzle_ok  median teammates  w/ senior NT")
by_era = collections.defaultdict(list)
for pid, p in P.items():
    by_era[era(p["b"])].append(pid)
random.seed(0)
for e in ["<1950", "1950-69", "1970-84", "1985-94", "1995+", "unknown"]:
    pids = by_era.get(e, [])
    if not pids:
        continue
    sample = random.sample(pids, min(400, len(pids)))
    med = statistics.median(len(g.neighbours(x)) for x in sample)
    nt = sum(1 for x in pids if any(g.teams[t]["k"] == "nat_senior" for t, _, _ in g.spells[x]))
    ok = sum(1 for x in pids if P[x]["ok"])
    print(f"  {e:<14}{len(pids):>9}{ok:>11}{med:>18.0f}{100 * nt / len(pids):>13.0f}%")

# ---- position groups
print("\nPOSITION GROUPS (puzzle_ok):", dict(collections.Counter("/".join(P[x]["pos"]) for x in P if P[x]["ok"]).most_common(8)))
print("Puzzle exclusions:", dict(collections.Counter(r for p in P.values() for r in p.get("why", []))))

# ---- fame
ranked = sorted((x for x in P if P[x]["ok"]), key=lambda x: -P[x]["f"])
print(f"\nTOP 40 BY FAME (pageviews: {g.meta['has_pageviews']}):")
print("  " + ", ".join(P[x]["n"] for x in ranked[:40]))
for lo in (500, 2000, 5000, 10000):
    print(f"  around rank {lo}: " + ", ".join(f"{P[x]['n']} ({P[x]['nat']})" for x in ranked[lo:lo + 10]))
print("  famous legends (born <1960) in top 1000:",
      ", ".join(P[x]["n"] for x in ranked[:1000] if (P[x]["b"] or 9999) < 1960)[:600])

# ---- spot checks
by_name = collections.defaultdict(list)
for x, p in P.items():
    by_name[p["n"]].append(x)


def find(name):
    xs = by_name.get(name, [])
    return max(xs, key=lambda x: P[x]["f"]) if xs else None


CHECKS = [
    ("Lionel Messi", "Neymar", True), ("Lionel Messi", "Cristiano Ronaldo", False),
    ("Cristiano Ronaldo", "Wayne Rooney", True), ("Zinedine Zidane", "Ronaldo", True),
    ("Pelé", "Garrincha", True), ("Diego Maradona", "Careca", True),
    ("Johan Cruyff", "Johan Neeskens", True), ("Franz Beckenbauer", "Gerd Müller", True),
    ("Thierry Henry", "Dennis Bergkamp", True), ("Didier Drogba", "Frank Lampard", True),
    ("Mohamed Salah", "Sadio Mané", True), ("Erling Haaland", "Kevin De Bruyne", True),
    ("Jude Bellingham", "Harry Kane", True), ("Ferenc Puskás", "Alfredo Di Stéfano", True),
    ("Pelé", "Lionel Messi", False), ("Thierry Henry", "Lionel Messi", True),
    ("Paolo Maldini", "Andrea Pirlo", True), ("Bobby Charlton", "George Best", True),
    ("Steven Gerrard", "Fernando Torres", True), ("Andrés Iniesta", "Xavi Hernández", True),
    ("Eusébio", "Mário Coluna", True), ("Lev Yashin", "Valentin Ivanov", True),
    ("George Weah", "Paolo Maldini", True), ("Roberto Baggio", "Ronaldo", True),
    ("Didier Drogba", "Yaya Touré", True), ("Son Heung-min", "Harry Kane", True),
    ("Lamine Yamal", "Robert Lewandowski", True), ("Michael Owen", "Cristiano Ronaldo", False),  # Owen joined Utd as Ronaldo left, summer 2009
    ("Wayne Rooney", "Steven Gerrard", True), ("Kaká", "Andrea Pirlo", True),
    ("Gianluigi Buffon", "Cristiano Ronaldo", True), ("Thierry Henry", "Cristiano Ronaldo", False),
    ("Jamie Carragher", "Cristiano Ronaldo", False), ("Ryan Giggs", "Gareth Bale", True),
]
print("\nSPOT CHECKS:")
ok = 0
for a, b, expect in CHECKS:
    qa, qb = find(a), find(b)
    if not qa or not qb:
        print(f"  ?  {a} – {b}: missing {a if not qa else b}")
        continue
    got = bool(g.linked(qa, qb))
    ok += got == expect
    print(f"  {'✓' if got == expect else '✗'}  {a} – {b}: {g.describe_link(qa, qb)}")
print(f"  {ok}/{len(CHECKS)} as expected")
