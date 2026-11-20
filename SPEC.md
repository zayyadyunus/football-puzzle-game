# Football XI Puzzle — Spec (draft)

_Working title: TBD_

## Concept
A daily puzzle. You're given a formation with some players already placed. Fill the remaining slots so that **every pair of adjacent positions on the pitch** is made of players who were teammates.

## Core rules
- **Link:** two players are linked if they were at the **same club at the same time** (overlapping spells) **or** in the **same senior men's national team at the same time** (overlapping international careers). Youth, Olympic and B national teams don't count.
- **Adjacency:** each formation defines a fixed set of link lines between neighbouring positions (e.g. LB–LCB, LB–LM). The puzzle is solved when every line is valid.
- **Positions:** players must fit the slot's broad group: GK / DEF / MID / FWD.
- **Uniqueness:** each player can be used once. Pre-placed players are locked.
- **Multiple solutions:** any valid XI is accepted. The generator guarantees at least one solution exists.
- **No mistake limit** at launch. Link lines show valid/invalid live as players are placed.
- **Hints:** deferred, design still open (see below).

## Player pool
- Many leagues, not just the top five, and all eras including legends.
- Each player gets a **recognisability score** based mainly on Wikipedia pageviews. Sitelinks alone over-rank players with bot-generated articles (see `pipeline/FINDINGS.md`). Seeded players and generator solutions favour well-known players. Solvers can enter anyone in the database.
- Search results show nationality, primary position and career years so players with the same name can be told apart.

## Difficulty levers
- Number and position of pre-placed players
- Formation (number of link lines, central vs wide slots)
- Recognisability of seeded players
- Weekly ramp: easy Monday → hard weekend

## Daily-game features (launch)
- One puzzle per day for everyone; resets at 00:00 UK time
- Streaks and stats stored in localStorage (no accounts)
- Spoiler-free share text (emoji pitch)

## Later
- Hint system
- Optional mistake limit / scoring mode
- Rarity score (needs a backend)
- Archive of past puzzles
- Accounts

## UI direction
Mobile-first and clean: an FPL-style pitch with shirt cards and NYT Games restraint. Tap a slot → autocomplete search. Link lines turn green/red.

## Tech
- **Data pipeline (Python, offline):** Wikidata → players, club spells, national-team spells, positions, recognisability → precomputed teammate graph
- **Puzzle generator (offline):** picks a formation, finds a valid well-known XI, removes players according to difficulty, verifies solvable → `puzzles/YYYY-MM-DD.json`
- **Web app:** Next.js + TypeScript + Tailwind, deployed on Vercel; static puzzle JSON plus a link-check data/API

## Open questions
- Name
- Hint design
- Shirt visuals: club kit colours vs neutral shirts
