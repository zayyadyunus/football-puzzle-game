"""Formations: slots (with pitch coordinates and accepted position groups) and link lines.

Coordinates: x 0 (left touchline) → 100 (right), y 0 (own goal line) → 100 (opponent's).
Link lines join neighbouring positions; a puzzle is solved when every line joins teammates.
"""

GK = ("GK",)
DEF = ("DEF",)
WB = ("DEF", "MID")      # wing-back
MID = ("MID",)
WIDE = ("MID", "FWD")    # wide midfielder / attacking mid / winger
FWD = ("FWD",)


def _f(name, slots, links):
    ids = {s[0] for s in slots}
    for a, b in links:
        assert a in ids and b in ids, (name, a, b)
    return {
        "name": name,
        "slots": [{"id": i, "label": lbl, "x": x, "y": y, "accepts": list(acc)} for i, lbl, x, y, acc in slots],
        "links": [list(l) for l in links],
    }


FORMATIONS = {
    "4-4-2": _f("4-4-2", [
        ("GK", "GK", 50, 6, GK),
        ("LB", "LB", 12, 26, DEF), ("LCB", "CB", 37, 22, DEF), ("RCB", "CB", 63, 22, DEF), ("RB", "RB", 88, 26, DEF),
        ("LM", "LM", 12, 54, WIDE), ("LCM", "CM", 37, 50, MID), ("RCM", "CM", 63, 50, MID), ("RM", "RM", 88, 54, WIDE),
        ("LST", "ST", 37, 80, FWD), ("RST", "ST", 63, 80, FWD),
    ], [
        ("GK", "LCB"), ("GK", "RCB"),
        ("LB", "LCB"), ("LCB", "RCB"), ("RCB", "RB"),
        ("LB", "LM"), ("LCB", "LCM"), ("RCB", "RCM"), ("RB", "RM"),
        ("LM", "LCM"), ("LCM", "RCM"), ("RCM", "RM"),
        ("LM", "LST"), ("LCM", "LST"), ("RCM", "RST"), ("RM", "RST"),
        ("LST", "RST"),
    ]),
    "4-3-3": _f("4-3-3", [
        ("GK", "GK", 50, 6, GK),
        ("LB", "LB", 12, 26, DEF), ("LCB", "CB", 37, 22, DEF), ("RCB", "CB", 63, 22, DEF), ("RB", "RB", 88, 26, DEF),
        ("LCM", "CM", 28, 50, MID), ("CM", "CM", 50, 46, MID), ("RCM", "CM", 72, 50, MID),
        ("LW", "LW", 15, 78, WIDE), ("ST", "ST", 50, 84, FWD), ("RW", "RW", 85, 78, WIDE),
    ], [
        ("GK", "LCB"), ("GK", "RCB"),
        ("LB", "LCB"), ("LCB", "RCB"), ("RCB", "RB"),
        ("LB", "LCM"), ("LCB", "CM"), ("RCB", "CM"), ("RB", "RCM"),
        ("LCM", "CM"), ("CM", "RCM"),
        ("LB", "LW"), ("RB", "RW"),
        ("LCM", "LW"), ("CM", "ST"), ("RCM", "RW"),
        ("LW", "ST"), ("ST", "RW"),
    ]),
    "4-2-3-1": _f("4-2-3-1", [
        ("GK", "GK", 50, 6, GK),
        ("LB", "LB", 12, 26, DEF), ("LCB", "CB", 37, 22, DEF), ("RCB", "CB", 63, 22, DEF), ("RB", "RB", 88, 26, DEF),
        ("LDM", "DM", 37, 44, MID), ("RDM", "DM", 63, 44, MID),
        ("LAM", "LM", 15, 66, WIDE), ("CAM", "AM", 50, 64, WIDE), ("RAM", "RM", 85, 66, WIDE),
        ("ST", "ST", 50, 86, FWD),
    ], [
        ("GK", "LCB"), ("GK", "RCB"),
        ("LB", "LCB"), ("LCB", "RCB"), ("RCB", "RB"),
        ("LCB", "LDM"), ("RCB", "RDM"), ("LDM", "RDM"),
        ("LB", "LAM"), ("RB", "RAM"),
        ("LDM", "LAM"), ("LDM", "CAM"), ("RDM", "CAM"), ("RDM", "RAM"),
        ("LAM", "CAM"), ("CAM", "RAM"),
        ("LAM", "ST"), ("CAM", "ST"), ("RAM", "ST"),
    ]),
    "3-5-2": _f("3-5-2", [
        ("GK", "GK", 50, 6, GK),
        ("LCB", "CB", 28, 22, DEF), ("CB", "CB", 50, 20, DEF), ("RCB", "CB", 72, 22, DEF),
        ("LWB", "LWB", 10, 48, WB), ("LCM", "CM", 32, 50, MID), ("CM", "CM", 50, 44, MID), ("RCM", "CM", 68, 50, MID),
        ("RWB", "RWB", 90, 48, WB),
        ("LST", "ST", 37, 80, FWD), ("RST", "ST", 63, 80, FWD),
    ], [
        ("GK", "LCB"), ("GK", "CB"), ("GK", "RCB"),
        ("LCB", "CB"), ("CB", "RCB"),
        ("LCB", "LWB"), ("RCB", "RWB"), ("LCB", "LCM"), ("CB", "CM"), ("RCB", "RCM"),
        ("LWB", "LCM"), ("LCM", "CM"), ("CM", "RCM"), ("RCM", "RWB"),
        ("LWB", "LST"), ("LCM", "LST"), ("RCM", "RST"), ("RWB", "RST"),
        ("LST", "RST"),
    ]),
    "3-4-3": _f("3-4-3", [
        ("GK", "GK", 50, 6, GK),
        ("LCB", "CB", 28, 22, DEF), ("CB", "CB", 50, 20, DEF), ("RCB", "CB", 72, 22, DEF),
        ("LM", "LM", 12, 50, WB), ("LCM", "CM", 37, 48, MID), ("RCM", "CM", 63, 48, MID), ("RM", "RM", 88, 50, WB),
        ("LW", "LW", 18, 78, WIDE), ("ST", "ST", 50, 84, FWD), ("RW", "RW", 82, 78, WIDE),
    ], [
        ("GK", "LCB"), ("GK", "CB"), ("GK", "RCB"),
        ("LCB", "CB"), ("CB", "RCB"),
        ("LCB", "LM"), ("LCB", "LCM"), ("CB", "LCM"), ("CB", "RCM"), ("RCB", "RCM"), ("RCB", "RM"),
        ("LM", "LCM"), ("LCM", "RCM"), ("RCM", "RM"),
        ("LM", "LW"), ("LCM", "ST"), ("RCM", "ST"), ("RM", "RW"),
        ("LW", "ST"), ("ST", "RW"),
    ]),
}


def neighbours(formation):
    nb = {s["id"]: set() for s in formation["slots"]}
    for a, b in formation["links"]:
        nb[a].add(b)
        nb[b].add(a)
    return nb


if __name__ == "__main__":
    for name, f in FORMATIONS.items():
        nb = neighbours(f)
        print(f"{name}: {len(f['links'])} links; degrees " + ", ".join(f"{k}:{len(v)}" for k, v in nb.items()))
