"""Puzzle generator.

    python3 generate.py 2026-12-01 14     # write puzzles/2026-12-01.json … for 14 days
    python3 generate.py experiment        # calibration: difficulty vs number of seeds

Difficulty = "knowledge needed": the smallest top-N pool (by era-adjusted fame) in which the puzzle
has at least 3 distinct completions. The seed subset is chosen to hit the day's target.
"""
import collections, datetime as dt, json, os, random, statistics, sys, time
from links import Graph
from solver import Solver
from formations import FORMATIONS

HERE = os.path.dirname(__file__)
PUZZLES = os.path.join(HERE, "..", "puzzles")

SOLUTION_POOL = 3000   # reference XIs are drawn from the top-N (era-adjusted fame)
SEED_POOL = 1500       # pre-placed players must be at least this recognisable
LADDER = (250, 500, 1000, 2000, 4000, 8000, 16000)
MIN_SOLUTIONS = 3
SEED_COOLDOWN_DAYS = 30

# weekday (Mon=0) -> (label, seeds, target knowledge)
SCHEDULE = {
    0: ("Easy", 4, 500),
    1: ("Easy", 4, 1000),
    2: ("Medium", 5, 1000),
    3: ("Medium", 5, 2000),
    4: ("Medium", 5, 2000),
    5: ("Hard", 6, 4000),
    6: ("Hard", 6, 4000),
}


# ------------------------------------------------------------------ scoring
def diversity(g, xi, formation):
    """Higher = more varied: distinct teams needed to explain the links, plus era spread."""
    teams_per_link = [{t for t, _, _ in g.linked(xi[a], xi[b])} for a, b in formation["links"]]
    left, used = list(range(len(teams_per_link))), 0
    while left:  # greedy set cover
        best = collections.Counter(t for i in left for t in teams_per_link[i]).most_common(1)[0][0]
        left = [i for i in left if best not in teams_per_link[i]]
        used += 1
    births = [g.players[p]["b"] for p in xi.values() if g.players[p]["b"]]
    return used + (statistics.pstdev(births) if len(births) > 1 else 0) / 4


def candidate_xis(s, formation, rng, n=30):
    out = []
    for _ in range(n):
        xi = s.random_xi(formation, SOLUTION_POOL, rng)
        if xi:
            out.append((diversity(s.g, xi, formation), xi))
    out.sort(key=lambda x: -x[0])
    return out


def knowledge(s, formation, seeds):
    for K in LADDER:
        if s.count(formation, seeds, K, cap=MIN_SOLUTIONS)[0] >= MIN_SOLUTIONS:
            return K
    return None


# ------------------------------------------------------------------ output
def card(g, s, pid):
    p = g.players[pid]
    years = [x for _, a, b in g.spells[pid] for x in (a, b)]
    return {"id": pid, "name": p["n"], "nat": p["nat"], "pos": p["pos"], "born": p["b"],
            "career": [int(min(years)), int(max(years))] if years else None}


def link_note(g, a, b):
    out = []
    for t, lo, hi in sorted(g.linked(a, b), key=lambda x: x[1]):
        out.append({"team": g.team_name(t), "kind": g.teams[t]["k"], "from": int(lo), "to": int(hi)})
    return out


def puzzle_json(g, s, date, label, formation, xi, seeds, k_needed, div):
    return {
        "date": date.isoformat(),
        "difficulty": {"label": label, "knowledge": k_needed,
                       "solutions": {str(K): s.count(formation, seeds, K, cap=1000)[0] for K in (500, 1000, 2000, 4000)}},
        "formation": formation,
        "seeds": {sid: card(g, s, pid) for sid, pid in seeds.items()},
        "solution": {sid: card(g, s, pid) for sid, pid in xi.items()},
        "solution_links": [{"a": a, "b": b, "via": link_note(g, xi[a], xi[b])} for a, b in formation["links"]],
        "meta": {"diversity": round(div, 1), "generator": "v1", "data_built": g.meta["built"]},
    }


# ------------------------------------------------------------------ generation
def generate_day(g, s, date, recent_seeds, prev_formation, max_xis=60, subsets_per_xi=40):
    rng = random.Random(f"xi-puzzle-{date.isoformat()}")
    label, k, target = SCHEDULE[date.weekday()]
    names = [n for n in FORMATIONS if n != prev_formation]
    fname = rng.choice(names)
    formation = FORMATIONS[fname]

    best = None  # fallback: closest miss
    for div, xi in candidate_xis(s, formation, rng, n=max_xis):
        seedable = [sid for sid, p in xi.items() if s.rank[p] < SEED_POOL and p not in recent_seeds]
        if len(seedable) < k:
            continue
        tried = set()
        for _ in range(subsets_per_xi):
            sids = tuple(sorted(rng.sample(seedable, k)))
            if sids in tried:
                continue
            tried.add(sids)
            seeds = {sid: xi[sid] for sid in sids}
            kn = knowledge(s, formation, seeds)
            if kn is None:
                continue
            miss = abs(LADDER.index(kn) - LADDER.index(target))
            if miss == 0:
                return puzzle_json(g, s, date, label, formation, xi, seeds, kn, div)
            if best is None or miss < best[0]:
                best = (miss, xi, seeds, kn, div)
    if best is None:
        raise RuntimeError(f"no puzzle found for {date}")
    _, xi, seeds, kn, div = best
    return puzzle_json(g, s, date, label, formation, xi, seeds, kn, div)


def generate(start, days):
    g = Graph.load()
    s = Solver(g)
    os.makedirs(PUZZLES, exist_ok=True)
    recent = collections.deque()  # (date, seed pids)
    prev_formation = None
    # Respect seeds already used in existing puzzles shortly before `start`.
    for back in range(SEED_COOLDOWN_DAYS, 0, -1):
        path = os.path.join(PUZZLES, f"{start - dt.timedelta(days=back)}.json")
        if os.path.exists(path):
            pz = json.load(open(path))
            recent.append((start - dt.timedelta(days=back), {c["id"] for c in pz["seeds"].values()}))
            prev_formation = pz["formation"]["name"]
    for i in range(days):
        date = start + dt.timedelta(days=i)
        while recent and (date - recent[0][0]).days > SEED_COOLDOWN_DAYS:
            recent.popleft()
        t = time.time()
        pz = generate_day(g, s, date, set().union(*(x[1] for x in recent)) if recent else set(), prev_formation)
        with open(os.path.join(PUZZLES, f"{date}.json"), "w", encoding="utf-8") as f:
            json.dump(pz, f, ensure_ascii=False, indent=1)
        recent.append((date, {c["id"] for c in pz["seeds"].values()}))
        prev_formation = pz["formation"]["name"]
        d = pz["difficulty"]
        hit = "" if d["knowledge"] == SCHEDULE[date.weekday()][2] else f" (target {SCHEDULE[date.weekday()][2]})"
        print(f"{date} {date.strftime('%a')} {pz['formation']['name']:<8} {d['label']:<6} "
              f"knowledge {d['knowledge']}{hit}  solutions {d['solutions']}  [{time.time() - t:.1f}s]")
        print("    seeds: " + ", ".join(f"{sid} {c['name']}" for sid, c in pz["seeds"].items()))


# ------------------------------------------------------------------ calibration
def experiment():
    g = Graph.load()
    s = Solver(g)
    rng = random.Random(7)
    res = collections.defaultdict(collections.Counter)
    for fname, f in FORMATIONS.items():
        for div, xi in candidate_xis(s, f, rng, n=12)[:4]:
            seedable = [sid for sid, p in xi.items() if s.rank[p] < SEED_POOL]
            for k in (3, 4, 5, 6):
                if len(seedable) < k:
                    continue
                for _ in range(10):
                    sids = rng.sample(seedable, k)
                    res[k][knowledge(s, f, {x: xi[x] for x in sids})] += 1
    print(f"seeds | knowledge needed for ≥{MIN_SOLUTIONS} solutions (top-N pool)")
    for k in sorted(res):
        print(f"  {k}  ", "  ".join(f"{K or '>16k'}:{res[k][K]}" for K in list(LADDER) + [None] if res[k][K]))


if __name__ == "__main__":
    if sys.argv[1:2] == ["experiment"]:
        experiment()
    else:
        start = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today()
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        generate(start, days)
