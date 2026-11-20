import collections, sys
sys.argv = ["build"]
src = open("build.py").read().split("# ---------------------------------------------------------------- pageviews")[0]
exec(src)
dropped = []
for pid, p in players.items():
    ss = raw_spells.get(pid, [])
    if any(s["kind"] == "women" for s in ss): continue
    usable = [s for s in ss if not s["dup"] and s["kind"] == "club" and s["a"] is not None and s["b"] is not None]
    if not usable: dropped.append(pid)
why = collections.Counter()
for pid in dropped:
    ss = raw_spells.get(pid, [])
    if not ss: why["no P54 at all"] += 1
    elif not any(s["kind"] == "club" for s in ss): why["no team classified as club: " + "/".join(sorted({s['kind'] for s in ss}))] += 1
    elif all(s["a"] is None for s in ss if s["kind"] == "club"): why["club spells lack start date"] += 1
    else: why["club spells lack end, not imputable"] += 1
for k, v in why.most_common(12): print(v, k)
top = sorted(dropped, key=lambda pid: -players[pid]["sitelinks"])[:25]
print("\nMost famous dropped:")
for pid in top:
    p = players[pid]; ss = raw_spells.get(pid, [])
    print(f"  {p['name']} ({p['birth']}, sl={p['sitelinks']}): " + "; ".join(f"{teams.get(s['team'],{}).get('name')}[{s['kind']}] {s['a']}-{s['b']}" for s in ss[:4]))
other = collections.Counter(c for pid in dropped for s in raw_spells.get(pid, []) if s["kind"] in ("other","reserve") for c in teams.get(s["team"],{}).get("classes", []))
print("\nClasses of 'other'/'reserve' teams among dropped:", other.most_common(15))
