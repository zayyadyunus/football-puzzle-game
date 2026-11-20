"""Constraint solver for XI puzzles.

A *pool* is "the top-K players by fame": a proxy for how deep a solver's football knowledge goes.
  - random_xi(): a random valid XI drawn from a pool (the puzzle's reference solution)
  - count():     number of ways to complete a partial XI from a pool (capped)
  - depth():     smallest pool in which a completion exists = how much you need to know
"""
import random
from formations import neighbours as slot_neighbours

OUTFIELD = {"DEF", "MID", "FWD"}


def era_adjusted_fame(graph, weight=0.5, ref_decade=1990):
    """Pageviews favour current players heavily: a 1950s top-100 player scores like a 1990s ~500th.
    Close `weight` of each birth decade's gap (median fame of its top 100) to the reference decade,
    so legends are eligible for puzzles without pretending they're as widely known as today's stars."""
    import collections, statistics
    by = collections.defaultdict(list)
    for p in graph.players.values():
        if p["b"] and p["ok"]:
            by[(p["b"] // 10) * 10].append(p["f"])
    med = {d: statistics.median(sorted(v, reverse=True)[:100]) for d, v in by.items() if len(v) >= 100}
    ref = med[ref_decade]
    adj = {}
    for pid, p in graph.players.items():
        d = (p["b"] // 10) * 10 if p["b"] else None
        gap = max(0.0, ref - med[d]) if d in med else 0.0
        adj[pid] = p["f"] + weight * gap
    return adj


class Solver:
    def __init__(self, graph, era_weight=0.5):
        self.g = graph
        self.fame = era_adjusted_fame(graph, era_weight) if era_weight else {p: v["f"] for p, v in graph.players.items()}
        ranked = sorted(graph.players, key=lambda p: -self.fame[p])
        self.rank = {p: i for i, p in enumerate(ranked)}
        self.ranked = ranked
        self._nbrs = {}

    # ---- player helpers
    def groups(self, p):
        pos = self.g.players[p]["pos"]
        return set(pos) if pos else OUTFIELD  # unknown position: any outfield slot

    def fits(self, p, slot):
        return bool(self.groups(p) & set(slot["accepts"]))

    def nbrs(self, p):
        s = self._nbrs.get(p)
        if s is None:
            s = self._nbrs[p] = frozenset(self.g.neighbours(p))
        return s

    # ---- core search
    def _candidates(self, slot, assign, nb, K, used, pool_filter=None):
        sets = [self.nbrs(assign[n]) for n in nb[slot["id"]] if n in assign]
        if not sets:
            return None  # unconstrained
        sets.sort(key=len)
        cands = set(sets[0])
        for s in sets[1:]:
            cands &= s
            if not cands:
                return []
        out = [p for p in cands if self.rank[p] < K and p not in used and self.fits(p, slot)
               and (pool_filter is None or pool_filter(p))]
        return out

    def count(self, formation, seeds, K, cap=200, node_limit=200_000):
        """Count completions of `seeds` ({slot_id: pid}) using players ranked < K.
        Returns (count, complete) where complete=False means the cap or node limit was hit."""
        nb = slot_neighbours(formation)
        slots = {s["id"]: s for s in formation["slots"]}
        assign = dict(seeds)
        used = set(seeds.values())
        state = {"n": 0, "nodes": 0, "aborted": False}

        def rec():
            if state["n"] >= cap or state["nodes"] >= node_limit:
                state["aborted"] = True
                return
            empty = [s for s in slots if s not in assign]
            if not empty:
                state["n"] += 1
                return
            # MRV: most-constrained empty slot that touches an assigned one
            best, best_c = None, None
            for sid in empty:
                c = self._candidates(slots[sid], assign, nb, K, used)
                if c is None:
                    continue
                if best_c is None or len(c) < len(best_c):
                    best, best_c = sid, c
                    if not c:
                        return  # dead end
            if best is None:
                raise ValueError("unconstrained slot with no assigned neighbours; give at least one seed")
            for p in best_c:
                state["nodes"] += 1
                assign[best] = p; used.add(p)
                rec()
                del assign[best]; used.discard(p)
                if state["aborted"]:
                    return

        rec()
        return state["n"], not state["aborted"]

    def depth(self, formation, seeds, ladder=(500, 1000, 2000, 4000, 8000, 16000, 10**9)):
        """Smallest K on the ladder with at least one completion (None if unsolvable)."""
        for K in ladder:
            n, _ = self.count(formation, seeds, K, cap=1)
            if n:
                return K
        return None

    def random_xi(self, formation, K, rng, ok_only=True, start=None, tries=200, node_limit=20_000):
        """A random complete XI using players ranked < K (and puzzle-usable if ok_only)."""
        nb = slot_neighbours(formation)
        slots = {s["id"]: s for s in formation["slots"]}
        pool = [p for p in self.ranked[:K] if not ok_only or self.g.players[p]["ok"]]
        flt = (lambda p: self.g.players[p]["ok"]) if ok_only else None

        for _ in range(tries):
            sid0 = rng.choice(list(slots))
            p0 = start or rng.choice([p for p in pool if self.fits(p, slots[sid0])])
            if not self.fits(p0, slots[sid0]):
                continue
            assign, used = {sid0: p0}, {p0}
            nodes = [0]

            def rec():
                empty = [s for s in slots if s not in assign]
                if not empty:
                    return True
                best, best_c = None, None
                for sid in empty:
                    c = self._candidates(slots[sid], assign, nb, K, used, flt)
                    if c is None:
                        continue
                    if best_c is None or len(c) < len(best_c):
                        best, best_c = sid, c
                if not best_c:
                    return False
                rng.shuffle(best_c)
                for p in best_c[:12]:
                    nodes[0] += 1
                    if nodes[0] > node_limit:
                        return False
                    assign[best] = p; used.add(p)
                    if rec():
                        return True
                    del assign[best]; used.discard(p)
                return False

            if rec():
                return assign
        return None
