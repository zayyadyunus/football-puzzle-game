# Wikidata sample — findings (2026-11-19)

Sample: top 2,000 people with occupation "association football player" (Q937857), ranked by Wikidata sitelink count. Scripts: `sample.py` (fetch) and `analyze.py` (report).

## Verdict
**Wikidata is good enough to be the primary source**, including for legends. The weak point is the fame ranking, not the career data.

## Coverage (men, by birth era)
| era | n | has club spell | club spells dated | has senior NT | NT spells dated | has position |
|---|---|---|---|---|---|---|
| born <1950 | 254 | 72%* | 92% | 91% | 99% | 98% |
| 1950–69 | 335 | 99% | 97% | 93% | 99% | 99% |
| 1970–84 | 575 | 100% | 98% | 98% | 99% | 100% |
| 1985–94 | 552 | 100% | 97% | 98% | 100% | 100% |
| 1995+ | 234 | 99% | 98% | 98% | 99% | 100% |

\*The pre-1950 gap is mostly noise: celebrities who played as youths (Camus, Sean Connery…) and 1930s Japanese internationals with bot-generated articles. It's not a hole in the data for real legends.

## Link quality
- 19/19 spot checks were correct. These included legends (Pelé–Garrincha, Puskás–Di Stéfano, Cruyff–Neeskens, Charlton–Best), modern pairs, and negatives (Messi–Ronaldo, Pelé–Messi). The 20th check was skipped because "Xavi" is labelled "Xavi Hernández".
- 15 random links all looked correct.
- Graph (club + senior NT), 2,000-player pool: about 56k links, median 54 teammates per player. The national-team rule adds about 50% more links.

## Issues to handle in the real pipeline
1. **Fame metric:** sitelinks over-rank 1930s Japanese players heavily (120 of ranks 500–1000, 202 of ranks 1500–2000) because bots created their articles in many languages. → Use **Wikipedia pageviews** instead, possibly blended with sitelinks.
2. **Non-footballers:** people tagged as footballers who are famous for something else (Camus, Orbán, Bohr) and managers whose playing data is thin. → Require at least one dated senior club spell, and down-weight people whose main occupation isn't football.
3. **Pool size:** pre-1950 legends have a median of only 4 links within this pool. Their teammates (e.g. Eusébio's Benfica sides) aren't famous enough to make the top 2,000. → Build the full graph from a much larger pool (~50k+). The fame score should limit which players the *puzzle* uses, not which links exist.
4. **Missing end dates:** handled by inference. A club spell ends when the next club spell starts. An open spell counts as ongoing if the player was born in 1984 or later.
5. **Labels:** many items only have a `mul` (language-neutral) label, e.g. Cristiano Ronaldo. → Fall back from `en` to `mul`.
6. **Women:** 18 of the 2,000 have women's-team spells. They are excluded for now (see open question).

## Infra notes
- The Wikidata Query Service was rate-limited to 1 request/min during an outage. **QLever** (`qlever.dev/api/wikidata`) is much faster: the full sample takes about 2 minutes, with each query finishing in under 2 seconds. We use QLever as the primary endpoint.
- The python.org build of Python 3.8 on this machine lacks a CA store, so `wd.py` uses `/etc/ssl/cert.pem`.

---

# Full build (2026-11-20)

Pool: 111,639 male footballers with ≥5 sitelinks → **84,692 in the graph** (74,472 usable in puzzles), 15,014 teams (14,749 clubs, 265 senior national teams), 514k dated spells. `graph.json` is 27 MB.

| era | players | puzzle-usable | median teammates | has senior NT |
|---|---|---|---|---|
| born <1950 | 13,339 | 11,967 | 31 | 61% |
| 1950–69 | 10,821 | 10,078 | 58 | 55% |
| 1970–84 | 24,311 | 23,142 | 105 | 42% |
| 1985–94 | 27,844 | 24,678 | 92 | 31% |
| 1995+ | 8,341 | 4,583 | 70 | 24% |

- **Spot checks: 34/34**, including the legend pairs that failed in the small sample (Eusébio–Coluna, Yashin–Ivanov).
- **Dropped:** 26,467 players with no dated senior club spell. Most are lower-league players born in the 1990s with undated spells, plus the non-footballers. Nobody well known was lost.
- **Pageviews:** October 2026 enwiki dump, with 83,465/83,482 titles matched.
- **Fame ranking:** pageviews alone reflected October news spikes and managerial fame. Blending in 40% sitelinks plus a manager penalty fixed most of it. The top 10 is now Ronaldo, Messi, Kane, Mbappé, Neymar, Yamal, Pelé, Beckham, Haaland, Ronaldo Nazário. Legends are well represented in the top 1,000.
- **Bug fixed:** "England cricket team" was classified as a national football team (it linked Ian Botham to cricketers). National teams must now be association-football teams, and other sports' teams are excluded.

## Known rough edges
- A few names still rank above their footballing fame because of news (Shaun Wright-Phillips) or fame outside football (Vinnie Jones). Using 12 months of dumps would smooth this, at about 40 minutes per month streamed.
- The "1995+" era has the lowest puzzle-usable share (55%). Young players often have thin data (fewer than 3 clubs, no caps). This is acceptable because the puzzle prefers famous players anyway.
- Managers whose playing careers were modest still appear (Ancelotti, Clough). They are real players, just best known as managers. Revisit if they show up as seeds too often.
- Players with the same name exist (e.g. several "Ronaldo"s), so search must show nationality, position and years.
