"""Coverage + link-graph report for data/sample_raw.json."""
import collections, itertools, json, os, re

D = json.load(open(os.path.join(os.path.dirname(__file__), "data", "sample_raw.json")))
players, spells, teams = D["players"], D["spells"], D["teams"]
NOW = 2026.9

# ---------- team classification ----------
NAT_OTHER_RE = re.compile(r"under-?\d|u-?\d\d|youth|olympic|\bb\b|amateur|beach|futsal|reserve", re.I)
RESERVE_RE = re.compile(r"\b(B|II|III|C)$|reserves?\b|youth|academy|juvenil|primavera|u-?\d\d|under-?\d\d|castilla|atlètic|jong ", re.I)

def classify(t):
    cls, name = set(t["classes"]), t["name"] or ""
    if any("women" in c for c in cls) or re.search(r"women|ladies|femen|frauen|feminin", name, re.I):
        return "women"
    is_nat = any("national" in c for c in cls) or re.search(r"national (football|soccer|team)", name, re.I)
    if is_nat:
        if NAT_OTHER_RE.search(name) or any(re.search(r"under-|youth|olympic|secondary|amateur|beach", c) for c in cls):
            return "nat_other"
        return "nat_senior"
    if "reserve team" in cls or RESERVE_RE.search(name):
        return "reserve"
    if cls & {"association football club", "defunct association football club", "sports club", "multi-sports club",
              "men's association football team", "association football team", "professional sports team",
              "amateur football club", "football club", "men's association football club"}:
        return "club"
    return "other"

for t in teams.values():
    t["kind"] = classify(t)

# ---------- date handling ----------
def to_year(date, end=False):
    """Year-precision dates come back as YYYY-01-01; treat them as mid-year (transfer window)."""
    if not date or not re.match(r"^\d{4}-\d\d-\d\d$", date):  # missing, BCE, or "unknown value" URI
        return None
    y, m, d = (int(x) for x in date.split("-"))
    if m == 1 and d == 1:
        return y + 0.5
    return y + (m - 1) / 12 + (d - 1) / 365

def interval(s):
    a, b = to_year(s["start"]), to_year(s["end"], end=True)
    if a is None:
        return None
    if b is None:
        # Open-ended: only trust it as "current" if it started recently.
        b = NOW if a >= 2017 else None
    if b is None or b < a:
        return None
    return (a, b)

def era(p):
    b = p.get("birth")
    if not b or not re.match(r"^\d{4}-", b):
        return "unknown"
    y = int(b[:4])
    return "born <1950" if y < 1950 else "1950-69" if y < 1970 else "1970-84" if y < 1985 else "1985-94" if y < 1995 else "1995+"

ERAS = ["born <1950", "1950-69", "1970-84", "1985-94", "1995+", "unknown"]

def birth_year(p):
    b = p.get("birth")
    return int(b[:4]) if b and re.match(r"^\d{4}-", b) else None

by_player = collections.defaultdict(list)
for s in spells:
    s["kind"] = teams.get(s["team"], {}).get("kind", "other")
    by_player[s["player"]].append(s)

# Impute missing end dates:
#  - club spell: ends when the next club spell starts; if it's the last one and the player
#    could still be active (born >= 1984), it's ongoing.
#  - senior NT spell: ongoing if the player could still be active.
for q, ss in by_player.items():
    by = birth_year(players.get(q, {}))
    could_be_active = by is not None and by >= 1984
    clubs = sorted((s for s in ss if s["kind"] == "club" and to_year(s["start"]) is not None),
                   key=lambda s: to_year(s["start"]))
    for i, s in enumerate(ss):
        s["iv"] = interval(s)
        if s["iv"] or to_year(s["start"]) is None or to_year(s["end"]) is not None:
            continue
        a = to_year(s["start"])
        if s["kind"] == "club":
            later = [to_year(c["start"]) for c in clubs if to_year(c["start"]) > a]
            if later:
                s["iv"] = (a, later[0]); s["imputed"] = "next-club"
            elif could_be_active:
                s["iv"] = (a, NOW); s["imputed"] = "ongoing"
        elif s["kind"] == "nat_senior" and could_be_active:
            s["iv"] = (a, NOW); s["imputed"] = "ongoing"

# ---------- 1. coverage ----------
def pct(a, b):
    return f"{100 * a / b:5.1f}%" if b else "   - "

print("=" * 78)
print("TEAM KINDS:", dict(collections.Counter(t["kind"] for t in teams.values())))
print("SPELL KINDS:", dict(collections.Counter(s["kind"] for s in spells)))
women = {q for q, ss in by_player.items() if any(s["kind"] == "women" for s in ss)}
print(f"Players with women's-team spells: {len(women)} (excluded from graph below)")

print("\nCOVERAGE BY ERA (men only)")
hdr = f"{'era':<11}{'n':>5} {'club≥1':>7} {'club dated':>11} {'senior NT':>10} {'NT dated':>9} {'position':>9} {'apps qual':>10}"
print(hdr); print("-" * len(hdr))
rows = collections.defaultdict(lambda: collections.Counter())
for q, p in players.items():
    if q in women:
        continue
    e = era(p); r = rows[e]; ss = by_player[q]
    clubs = [s for s in ss if s["kind"] == "club"]
    nts = [s for s in ss if s["kind"] == "nat_senior"]
    r["n"] += 1
    r["club≥1"] += bool(clubs)
    r["club_spells"] += len(clubs); r["club_dated"] += sum(1 for s in clubs if s["iv"])
    r["nt≥1"] += bool(nts)
    r["nt_spells"] += len(nts); r["nt_dated"] += sum(1 for s in nts if s["iv"])
    r["pos"] += bool(p.get("positions"))
    r["apps_spells"] += sum(1 for s in clubs if s["apps"] is not None)
for e in ERAS:
    r = rows[e]
    if not r["n"]:
        continue
    print(f"{e:<11}{r['n']:>5} {pct(r['club≥1'], r['n']):>7} {pct(r['club_dated'], r['club_spells']):>11} "
          f"{pct(r['nt≥1'], r['n']):>10} {pct(r['nt_dated'], r['nt_spells']):>9} {pct(r['pos'], r['n']):>9} "
          f"{pct(r['apps_spells'], r['club_spells']):>10}")
print("(club dated / NT dated = % of spells with a usable start+end interval)")
imp = collections.Counter((s["kind"], s.get("imputed")) for s in spells if s.get("imputed"))
print("Imputed end dates:", dict(imp))

# ---------- positions ----------
POS_GROUP = [("GK", r"goalkeeper"), ("DEF", r"back|defender|sweeper|libero|stopper"),
             ("MID", r"midfield|playmaker|winger|wing half|half-back|regista|mezzala|trequartista"),
             ("FWD", r"forward|striker|centre-forward|inside forward|attacker|second striker|false 9")]
def groups(p):
    g = set()
    for pos in p.get("positions", []):
        for k, rx in POS_GROUP:
            if re.search(rx, pos, re.I):
                g.add(k)
    return g
unmapped = collections.Counter(pos for p in players.values() for pos in p.get("positions", []) if not groups({"positions": [pos]}))
print("\nPOSITION GROUPS:", dict(collections.Counter(len(groups(p)) for p in players.values())), "(#groups per player)")
print("Unmapped position labels:", unmapped.most_common(10))

# ---------- 2. link graph ----------
def team_ivs(q, kinds):
    out = collections.defaultdict(list)
    for s in by_player[q]:
        if s["kind"] in kinds and s["iv"]:
            out[s["team"]].append(s["iv"])
    return out

def build_graph(kinds):
    by_team = collections.defaultdict(list)
    for q in players:
        if q in women:
            continue
        for t, ivs in team_ivs(q, kinds).items():
            for iv in ivs:
                by_team[t].append((q, iv))
    adj = collections.defaultdict(dict)
    for t, members in by_team.items():
        for (a, ia), (b, ib) in itertools.combinations(members, 2):
            if a != b and min(ia[1], ib[1]) - max(ia[0], ib[0]) > 0.05:  # >~3 weeks overlap
                adj[a].setdefault(b, set()).add(t); adj[b].setdefault(a, set()).add(t)
    return adj

men = [q for q in players if q not in women]
for label, kinds in [("CLUB ONLY", {"club"}), ("CLUB + SENIOR NT", {"club", "nat_senior"})]:
    adj = build_graph(kinds)
    degs = sorted(len(adj.get(q, {})) for q in men)
    iso = sum(1 for d in degs if d == 0)
    print(f"\nGRAPH ({label}) over {len(men)} men: {sum(degs)//2} edges, "
          f"median degree {degs[len(degs)//2]}, isolated {iso} ({pct(iso, len(men)).strip()})")
    by_era = collections.defaultdict(list)
    for q in men:
        by_era[era(players[q])].append(len(adj.get(q, {})))
    print("  median degree by era:", {e: sorted(v)[len(v)//2] for e, v in by_era.items() if v})

# ---------- 3. spot checks ----------
name_to_q = {}
for q, p in players.items():
    if p.get("name"):
        name_to_q.setdefault(p["name"], q)
adj = build_graph({"club", "nat_senior"})
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
    ("Steven Gerrard", "Fernando Torres", True), ("Andrés Iniesta", "Xavi", True),
]
print("\nSPOT CHECKS (club + senior NT):")
ok = 0
for a, b, expect in CHECKS:
    qa, qb = name_to_q.get(a), name_to_q.get(b)
    if not qa or not qb:
        print(f"  ?  {a} – {b}: not in sample ({'missing ' + (a if not qa else b)})"); continue
    via = adj.get(qa, {}).get(qb)
    got = bool(via)
    ok += got == expect
    mark = "✓" if got == expect else "✗"
    teamnames = ", ".join(teams[t]["name"] or t for t in via) if via else "-"
    print(f"  {mark}  {a} – {b}: expected {expect}, got {got} [{teamnames}]")
print(f"  {ok}/{len(CHECKS)} as expected")
