# Data pipeline

Builds the teammate graph (`data/graph.json`) from Wikidata, with Wikipedia pageviews as the fame signal.
Stdlib-only Python 3.8+. Nothing needs installing.

## Run order
```sh
python3 fetch.py 5          # 1. bulk export from Wikidata via QLever (~1 min) → data/raw/*.csv
python3 build.py            # 2. first build (needed to know which enwiki titles to look up)
curl -s https://dumps.wikimedia.org/other/pageview_complete/monthly/2026/2026-10/pageviews-202610-user.bz2 \
  | bzcat | LC_ALL=C awk '/^en\.wikipedia /{print; seen=1; next} seen{exit}' \
  | python3 pageviews_dump.py   # 3. stream a monthly pageview dump (~40 min, ~6 GB download, nothing stored)
python3 build.py            # 4. rebuild with fame scores
python3 report.py           # 5. coverage, fame ranking, spot checks
```
The argument to `fetch.py` (default 5) is the minimum number of Wikipedia language editions with an article on the player, i.e. the size of the pool. `pageviews.py` is an API-based alternative to step 3, but Wikimedia rate-limits it too heavily for bulk use.

## Files
| file | role |
|---|---|
| `wd.py` | SPARQL client (QLever endpoint, prefixes, SSL fallback) |
| `fetch.py` | raw export: players, positions, occupations, citizenship, spells, teams, labels |
| `pageviews_dump.py` | extracts English Wikipedia monthly views for graph players from a streamed dump |
| `build.py` | team classification, date inference, filters, positions, fame → `graph.json` |
| `links.py` | `Graph` loader: `linked(a, b)`, `neighbours(p)` (used by the puzzle generator) |
| `report.py` | sanity report |
| `sample.py`, `analyze.py` | the original 2k-player feasibility sample (see `FINDINGS.md`) |

## graph.json
```jsonc
{
  "meta": {...},
  "players": { "Q615": { "n": "Lionel Messi", "b": 1987, "nat": "Argentina", "pos": ["FWD"],
                         "f": 6.94, "sl": 228, "pv": 1234567, "ok": true, "w": "Lionel_Messi" } },
  "teams":   { "Q7156": { "n": "FC Barcelona", "k": "club", "c": "Spain" } },   // k: club | nat_senior
  "spells":  { "Q615": [["Q7156", 2004.83, 2021.6], ...] }                      // fractional years
}
```
- `f` (fame) = 0.6 × log10(monthly enwiki views) + 0.4 × 3·log10(sitelinks), minus a penalty for managers.
- `ok` = usable as a puzzle seed or reference solution (if false, `why` gives the reason). Every player can still be *entered* by solvers.
- Two players are linked when they share a team with more than ~3 weeks of overlap (`links.MIN_OVERLAP`).

## Key rules in build.py
- Senior men's national football teams only. Youth, Olympic, B, women's and other sports' teams are excluded.
- Reserve/B/youth club sides don't count as clubs.
- Year-only dates are treated as mid-year (summer transfer window).
- A missing club end date is inferred as the start of the player's next club spell. An open spell counts as ongoing if the player was born in 1984 or later.
- Players need at least one dated senior club spell. This also drops non-footballers tagged as footballers (Camus, Connery…).
