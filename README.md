# XI (working title)

A daily football puzzle: complete a starting eleven where every linked pair of positions were teammates.
See `SPEC.md` for the design.

| dir | what |
|---|---|
| `pipeline/` | Python: Wikidata → teammate graph → daily puzzles → static web data (see `pipeline/README.md`) |
| `puzzles/` | generated daily puzzles (committed) |
| `web/` | Next.js static site: the game |

## Run locally
```sh
cd pipeline && python3 export_web.py   # needs pipeline/data/graph.json (see pipeline/README.md)
cd ../web && npm install && npm run dev  # http://localhost:3000, ?date=YYYY-MM-DD to open a specific puzzle
```
`npm run build` produces a static site in `web/out/`.
