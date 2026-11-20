"""Stage 3: turn raw Wikidata CSVs (+ optional pageviews) into a clean teammate graph.

Usage: python3 build.py
Reads  data/raw/*.csv, data/raw/pageviews.csv (optional)
Writes data/graph.json

Graph model
-----------
Players are linked if they share a team (senior club first team, or senior men's national team)
with overlapping spells. We store spells rather than edges; `links.py` computes overlaps.
"""
import collections, csv, json, math, os, re

HERE = os.path.dirname(__file__)
RAW = os.path.join(HERE, "data", "raw")
NOW = 2026.9          # "today" as a fractional year, for ongoing spells
ACTIVE_BORN = 1984    # players born on/after this may still be active

def q(uri):
    return uri.rsplit("/", 1)[-1] if uri else ""

def rows(name):
    path = os.path.join(RAW, f"{name}.csv")
    with open(path, newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f)

LABEL = {q(r["x"]): r["label"] for r in rows("labels")}

# ---------------------------------------------------------------- dates
DATE_RE = re.compile(r"^(\d{4})-(\d\d)-(\d\d)")

def to_year(s):
    """Wikidata year-precision dates arrive as YYYY-01-01: treat as mid-year (summer window)."""
    m = DATE_RE.match(s or "")
    if not m:
        return None  # missing, BCE, or "unknown value"
    y, mo, d = (int(x) for x in m.groups())
    if mo == 1 and d == 1:
        return y + 0.5
    return round(y + (mo - 1) / 12 + (d - 1) / 365, 3)

# ---------------------------------------------------------------- teams
NAT_OTHER_NAME = re.compile(r"under-?\d|\bu-?\d\d\b|youth|olympic|\bB\b|amateur|beach|futsal|reserve|military|universiade|student", re.I)
NAT_OTHER_CLS = re.compile(r"under-|youth|olympic|secondary|amateur|beach|futsal|military|universit", re.I)
RESERVE_NAME = re.compile(r"\b(B|II|III|C|U\d\d)$|reserves?\b|youth|academy|juvenil|primavera|\bu-?\d\d\b|under-?\d\d|castilla|jong ", re.I)
CLUB_CLS = {"association football club", "defunct association football club", "sports club", "multi-sports club",
            "men's association football team", "association football team", "professional sports team",
            "amateur football club", "football club", "men's association football club", "sports team"}

teams = {}
for r in rows("teams"):
    t = teams.setdefault(q(r["team"]), {"name": r["en"] or r["mul"] or None, "classes": set(), "country": None})
    if r["cls"]:
        t["classes"].add(LABEL.get(q(r["cls"]), ""))
    if r["country"] and not t["country"]:
        t["country"] = LABEL.get(q(r["country"]))

def classify(t):
    cls, name = t["classes"], t["name"] or ""
    if any("women" in c for c in cls) or re.search(r"women|ladies|femen|frauen|feminin", name, re.I):
        return "women"
    is_nat = any(re.search(r"national.*(association football|football team|soccer)", c) for c in cls) \
        or re.search(r"national (football|soccer) team|national association football", name, re.I)
    if any(re.search(r"cricket|rugby|basketball|hockey|handball|volleyball|baseball|american football|futsal|beach", c) for c in cls) \
            and not any("association football" in c for c in cls):
        return "other"  # another sport's team
    if is_nat:
        if NAT_OTHER_NAME.search(name) or any(NAT_OTHER_CLS.search(c) for c in cls):
            return "nat_other"
        return "nat_senior"
    if "reserve team" in cls or RESERVE_NAME.search(name):
        return "reserve"
    if cls & CLUB_CLS:
        return "club"
    return "other"

for t in teams.values():
    t["kind"] = classify(t)

def nt_country(name):
    return re.sub(r"\s+(men's\s+)?national\b.*$", "", name or "", flags=re.I).strip() or None

# ---------------------------------------------------------------- players
players = {}
for r in rows("players"):
    pid = q(r["p"])
    p = players.setdefault(pid, {"sitelinks": int(r["sl"]), "name": None, "birth": None, "enwiki": None})
    p["name"] = p["name"] or r["en"] or r["mul"] or None
    if not p["birth"]:
        m = DATE_RE.match(r["birth"] or "")
        p["birth"] = int(m.group(1)) if m else None
    if r["enwiki"] and not p["enwiki"]:
        p["enwiki"] = r["enwiki"].rsplit("/wiki/", 1)[-1]

POS_GROUPS = [
    ("GK", re.compile(r"^(goalkeeper|goaltender|gate)$")),
    ("DEF", re.compile(r"defender|full-back|centre-back|center-back|stopper|sweeper|libero|^back$|left[- ]back|right[- ]back|wing-back|centre-?half|centerhalf")),
    ("MID", re.compile(r"midfielder|wing half|half-back|playmaker|winger")),
    ("FWD", re.compile(r"forward|striker|attacker|winger")),
]
for r in rows("positions"):
    p = players.get(q(r["p"]))
    label = LABEL.get(q(r["pos"]), "").lower()
    for g, rx in POS_GROUPS:
        if p is not None and rx.search(label):
            p.setdefault("pos", set()).add(g)

FOOTBALL_OCC = re.compile(r"association football|football (player|coach|manager)|soccer|futsal|beach soccer|goalkeeper|"
                          r"^coach$|^manager$|sports (commentator|executive|agent|official|journalist|director)|"
                          r"color commentator|athlete|autobiographer|television presenter|pundit|^$", re.I)
for r in rows("occupations"):
    p = players.get(q(r["p"]))
    if p is None:
        continue
    label = LABEL.get(q(r["occ"]), "")
    if label == "association football coach" or label == "association football manager":
        p["coach"] = True
    elif not FOOTBALL_OCC.search(label):
        p.setdefault("other_occ", set()).add(label)

for r in rows("citizenship"):
    p = players.get(q(r["p"]))
    if p is not None and "citizen" not in p:
        p["citizen"] = LABEL.get(q(r["c"]))

# ---------------------------------------------------------------- spells
raw_spells = collections.defaultdict(list)
for r in rows("spells"):
    pid, tid = q(r["p"]), q(r["team"])
    if pid not in players:
        continue
    kind = teams.get(tid, {}).get("kind", "other")
    try:
        apps = int(float(r["apps"])) if r["apps"] else None
    except ValueError:
        apps = None
    raw_spells[pid].append({"team": tid, "kind": kind, "a": to_year(r["start"]), "b": to_year(r["end"]), "apps": apps})

stats = collections.Counter()
for pid, ss in raw_spells.items():
    by = players[pid]["birth"]
    active = by is not None and by >= ACTIVE_BORN
    club_starts = sorted({s["a"] for s in ss if s["kind"] == "club" and s["a"] is not None})
    # Dedupe identical statements (Wikidata sometimes duplicates them).
    seen = set()
    for s in ss:
        key = (s["team"], s["a"], s["b"])
        s["dup"] = key in seen
        seen.add(key)
        if s["dup"] or s["a"] is None or s["kind"] not in ("club", "nat_senior"):
            continue
        if s["b"] is None:
            later = [x for x in club_starts if x > s["a"]] if s["kind"] == "club" else []
            if later:
                s["b"], s["imp"] = later[0], "next-club"
            elif active:
                s["b"], s["imp"] = NOW, "ongoing"
        if s["b"] is not None and s["b"] < s["a"]:
            s["b"] = None
        if s["b"] is not None:
            stats[f"{s['kind']} usable" + (f" ({s['imp']})" if s.get("imp") else "")] += 1
        else:
            stats[f"{s['kind']} unusable (no end)"] += 1

# ---------------------------------------------------------------- pageviews (optional)
PV = {}
pv_path = os.path.join(RAW, "pageviews.csv")
if os.path.exists(pv_path):
    PV = {r["pid"]: int(r["views"]) for r in rows("pageviews") if r["views"]}

# ---------------------------------------------------------------- assemble
out_players, out_spells, used_teams = {}, {}, set()
drop = collections.Counter()
for pid, p in players.items():
    ss = raw_spells.get(pid, [])
    if any(s["kind"] == "women" for s in ss):
        drop["women's team spell"] += 1; continue
    usable = [s for s in ss if not s["dup"] and s["kind"] in ("club", "nat_senior") and s["a"] is not None and s["b"] is not None]
    clubs = [s for s in usable if s["kind"] == "club"]
    nts = [s for s in usable if s["kind"] == "nat_senior"]
    if not clubs:
        drop["no dated senior club spell"] += 1; continue
    if not p["name"]:
        drop["no name"] += 1; continue

    club_apps = sum(s["apps"] or 0 for s in clubs)
    nat = nt_country(teams[nts[0]["team"]]["name"]) if nts else p.get("citizen")

    # Can this player be used in a puzzle's seed / reference solution?
    reasons = []
    if not p.get("pos"):
        reasons.append("no position")
    if p.get("other_occ") and not nts:
        reasons.append("mainly known for something else")
    if not nts and len(clubs) < 3 and club_apps < 50:
        reasons.append("thin career data")
    puzzle_ok = not reasons

    # Fame: log10 of monthly English Wikipedia pageviews. Sitelinks are a weak fallback, used only
    # when there are no views (no enwiki article, or the title didn't match, e.g. after a rename).
    # Blend with sitelinks (stable over time, global rather than English-only) to damp one-month
    # news spikes. 3*log10(sitelinks) is on roughly the same scale as log10(monthly views).
    views = PV.get(pid)
    sl_score = 3 * math.log10(p["sitelinks"])
    fame = 0.6 * math.log10(views + 1) + 0.4 * sl_score if views else sl_score - 0.5
    if p.get("coach"):
        fame -= 0.3  # pageviews partly reflect a managerial career
        if not nts and club_apps < 200:
            fame -= 0.7  # famous as a manager, not as a player (e.g. Mourinho)
    if p.get("other_occ") and not nts:
        fame -= 1.5

    out_players[pid] = {
        "n": p["name"], "b": p["birth"], "nat": nat, "pos": sorted(p.get("pos", [])),
        "f": round(fame, 3), "sl": p["sitelinks"], "pv": views, "ok": puzzle_ok,
        **({"why": reasons} if reasons else {}), **({"w": p["enwiki"]} if p["enwiki"] else {}),
    }
    out_spells[pid] = sorted([[s["team"], s["a"], round(s["b"], 3)] for s in usable], key=lambda x: x[1])
    used_teams.update(s["team"] for s in usable)

out_teams = {tid: {"n": teams[tid]["name"], "k": teams[tid]["kind"], **({"c": teams[tid]["country"]} if teams[tid]["country"] else {})}
             for tid in used_teams}

graph = {
    "meta": {"built": "2026-11-19", "source": "Wikidata via QLever", "now": NOW,
             "players": len(out_players), "puzzle_ok": sum(p["ok"] for p in out_players.values()),
             "teams": len(out_teams), "spells": sum(len(v) for v in out_spells.values()),
             "has_pageviews": bool(PV)},
    "players": out_players, "teams": out_teams, "spells": out_spells,
}
with open(os.path.join(HERE, "data", "graph.json"), "w", encoding="utf-8") as f:
    json.dump(graph, f, ensure_ascii=False, separators=(",", ":"))

print("Players fetched:", len(players))
print("Dropped:", dict(drop))
print("Spell date handling:", dict(stats))
print("Meta:", graph["meta"])
print("Team kinds used:", dict(collections.Counter(t["k"] for t in out_teams.values())))
print("Size:", round(os.path.getsize(os.path.join(HERE, "data", "graph.json")) / 1e6, 1), "MB")
