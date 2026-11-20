"""Load data/graph.json and answer teammate-link questions.

    from links import Graph
    g = Graph.load()
    g.linked("Q615", "Q8023")      # -> [("Q7156", 2004.83, 2013.5), ...] shared team + overlap window
    g.neighbours("Q615")           # -> {pid: [(team, start, end), ...]}
"""
import bisect, collections, json, os

MIN_OVERLAP = 0.05  # years (~3 weeks): spells that merely touch at a transfer window don't count


class Graph:
    def __init__(self, data):
        self.meta = data["meta"]
        self.players = data["players"]
        self.teams = data["teams"]
        self.spells = data["spells"]
        # team -> spells sorted by start, for neighbour sweeps
        self.by_team = collections.defaultdict(list)
        for pid, ss in self.spells.items():
            for team, a, b in ss:
                self.by_team[team].append((a, b, pid))
        for v in self.by_team.values():
            v.sort()
        self._starts = {t: [s[0] for s in v] for t, v in self.by_team.items()}
        self._nbr_cache = {}

    @classmethod
    def load(cls, path=None):
        path = path or os.path.join(os.path.dirname(__file__), "data", "graph.json")
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f))

    def linked(self, p, q):
        """Shared teams with an overlap window, or [] if not teammates."""
        out = []
        for t1, a1, b1 in self.spells.get(p, []):
            for t2, a2, b2 in self.spells.get(q, []):
                if t1 == t2:
                    lo, hi = max(a1, a2), min(b1, b2)
                    if hi - lo > MIN_OVERLAP:
                        out.append((t1, lo, hi))
        return out

    def neighbours(self, p):
        """All teammates of p: {pid: [(team, lo, hi), ...]}."""
        if p in self._nbr_cache:
            return self._nbr_cache[p]
        out = collections.defaultdict(list)
        for team, a, b in self.spells.get(p, []):
            members, starts = self.by_team[team], self._starts[team]
            # Only spells that start before p's spell ends can overlap.
            for a2, b2, q in members[:bisect.bisect_left(starts, b)]:
                if q != p:
                    lo, hi = max(a, a2), min(b, b2)
                    if hi - lo > MIN_OVERLAP:
                        out[q].append((team, lo, hi))
        self._nbr_cache[p] = out = dict(out)
        return out

    def name(self, pid):
        return self.players[pid]["n"]

    def team_name(self, tid):
        return self.teams[tid]["n"] or tid

    def describe_link(self, p, q):
        parts = []
        for t, lo, hi in self.linked(p, q):
            parts.append(f"{self.team_name(t)} {int(lo)}–{int(hi)}")
        return "; ".join(parts) or "no link"
