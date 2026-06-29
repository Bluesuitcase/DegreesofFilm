# Degrees of Film

A daily browser game testing film knowledge. You're shown a cropped frame from a film
(title hidden), name it, then dig down through its credits from famous to obscure. The
brag number is **depth** — how many rungs deep you got.

**`DESIGN.md` is the full spec and source of truth.** This file is the working summary;
when the two disagree, DESIGN.md wins. **Current status: Phase 1** (prove the core loop is
fun against one hand-authored puzzle). Phases 2–3 (curation tool, daily/archive, lifelines,
theming) are not built yet.

> This is a *vertical dig into one film's credits*, not "six degrees of separation" (hopping
> between films). True degrees-of-separation is a deferred v2 mode.

## Run & test

- **Play it:** the game uses `fetch`, so it needs a server — `file://` won't work. Serve the
  `docs/` folder and open `index.html`, e.g. `python -m http.server` from inside `docs/`.
- **Tests:** plain Node, no framework or deps. Run `node match.test.js` and `node game.test.js`
  from the repo root. Each prints PASS/FAIL lines and exits non-zero on any failure. There is
  no `npm test` script; `package.json` exists only to set `"type": "module"` so the `.test.js`
  files can `import` the ES modules under `docs/`.
- **Curation tests (Phase 2):** `python curation/build_rungs.test.py` — pure-logic tests for the
  rung-ordering data layer (no network or API key needed), same PASS/FAIL + non-zero-exit style.

## Architecture — three zones

The whole design turns on one fact: **the TMDB API key never reaches a player.** It lives only
in the (future) curation tool on your machine. Players only ever fetch finished static files.

1. **PRIVATE (your machine)** — *Phase 2, not built.* Python (Flask/FastAPI) curation tool holds
   the key, queries TMDB, crops images with Pillow, and writes puzzle files. Owns the used-films
   ledger (never repeat a film).
2. **STATIC HOSTING (GitHub Pages)** — the `docs/` folder. Per-day puzzle JSON + pre-cropped
   images + the game client (html/js/css). Past puzzles are just old files that still exist, so
   the archive is nearly free.
3. **PLAYER BROWSER** — no key, no backend. Vanilla ES-module JS runs the rules and the fuzzy
   matcher; stats will live in localStorage (Phase 3).

Consequence: v1 needs **no backend for players**. v1 also ships answers in plaintext in the JSON
(readable in devtools) — accepted because there's no leaderboard yet.

## File layout

```
DESIGN.md              Full v1 spec + build roadmap + v2 parking lot. Read this first.
CLAUDE.md              This file.
package.json           Just { "type": "module" }.
match.test.js          Matcher tests (node match.test.js). Cases mirror puzzle 001's answers.
game.test.js           Rules/scoring tests (node game.test.js): scoring curve + scripted playthroughs.
docs/                  The entire static site = what gets hosted.
  index.html           Markup + element ids the JS binds to.
  style.css            Dark "ink/bone/amber" theme. CSS vars in :root. Mobile breakpoint at 600px.
  app.js               DOM glue ONLY. Fetches the puzzle, renders, wires buttons. No rules here.
  game.js              Game rules, scoring, run state. Pure logic, no DOM.
  match.js             Fuzzy answer matching. Pure logic, no DOM.
  puzzles/
    001.json           The one hand-authored Phase 0 puzzle (No Country for Old Men).
    images/001.jpg     Its frame image.
curation/              PRIVATE (Phase 2) — never served. Holds the TMDB key (.env, gitignored).
  tmdb.py              Tiny stdlib TMDB v3 client (load_key + get).
  build_rungs.py       Data layer: film+credits -> ordered rung draft (pure logic) + a thin CLI.
  build_rungs.test.py  Tests for the ordering rules (python curation/build_rungs.test.py).
  validate_ladder.py   Throwaway de-risk script (popularity-vs-billing comparison).
```

**Layering, keep it clean:** `match.js` has no imports. `game.js` imports only `match.js`.
`app.js` imports `game.js` and does all DOM work. Rules and matching stay DOM-free so the Node
tests can import them directly. Don't leak rendering into `game.js`/`match.js` or rules into `app.js`.

`app.js` currently hard-codes `fetch('puzzles/001.json')` — the daily/archive selection mechanism
is Phase 3. **Decided:** that mechanism is a `manifest.json` index (`{ date, id, file, title,
accent }` per puzzle); the client fetches the manifest, picks today's canonical date, then fetches
that puzzle. Archive = a render of the manifest. See DESIGN §4.

## v1 ruleset (as implemented in `game.js`)

- **The ladder:** rung 1 names the **film** from the cropped frame; rungs 2+ are credits ordered
  famous → obscure. **Cast by TMDB billing order** (lead first; popularity only as a tiebreaker —
  rolling popularity buries posthumous legends, e.g. it put the Joker at rung 13). **Director
  floats early** (≈ rung 3–4, after the top lead cast); technical crew (DP/composer/editor/PD) are
  the deepest rungs. The curation tool emits this as a draft; a human reorders edge cases. The
  ordering was de-risked in `curation/validate_ladder.py`; see DESIGN §1 / §5.
- **Attempts:** 3 per rung (`MAX_ATTEMPTS`). The 3rd wrong guess is a strike-out and **ends the
  run**; score and depth freeze where they are.
- **Skip:** advances a rung for **−1 point**, max 5 per game (`MAX_SKIPS`). A skip *beyond* the
  5th ends the run (`out_of_skips`).
- **Win:** solving the last rung sets status `won`.
- **State machine:** `status` is `'playing' | 'over' | 'won'`. `guess()`/`skip()` no-op unless playing.
- **Stats:** `depth` = rungs passed = the hero/brag number. `score` = the tiebreaker (how cleanly
  you dug). Two players both 10 deep can have different scores.
- **Scoring (`scoreForRung(n)`):** rung N is worth N points, plus a deep-dig bonus that starts at
  rung 6, climbs +1/rung, and caps at +5 from rung 10 on. Curve for rungs 1–12:
  `1,2,3,4,5,7,9,11,13,15,16,17`. (Skips subtract 1 each.)

**Not yet built (DESIGN Phase 3 / fast-follows), don't assume these exist:**
- **I Need Help** lifeline (3×): converts a rung to multiple choice from `decoys`, caps its value at 0.
  A wrong pick **burns an attempt** (can still strike you out) — decided, not a guaranteed pass.
- **Mode select:** v1 is **Cinephile** only. *Poser* (all-MC, flat +1) and *Movie Buff* (TMDB title
  autocomplete; needs the v2 server move) are deferred.
- Daily mechanism + archive browser, localStorage stats/streak, dynamic accent theming, home page,
  TMDB attribution UI (mandatory before any real ship), share card.

## Puzzle file schema

Each day is one self-contained JSON plus its images, under `docs/puzzles/`.

**As implemented today** (`001.json`): `id`, `images` (array of pre-cropped reveal tiers,
most-zoomed first — though 001 ships only one; **decided:** the curation tool authors 3 tiers,
but the v1 client renders only `images[0]` — tiers 2–3 are authored-ahead for a future reveal
mechanic), and `rungs[]` where each rung is
`{ role, prompt, answers[] }`. `answers` is the list of accepted strings (alternate titles,
language variants, name forms); the matcher accepts any of them.

**Full spec adds two fields (DESIGN §4), required once the curation tool exists:**
- `theme.accent` — a hex colour sampled from the still, used as the page accent (ink base + bone
  text stay fixed for legibility). Clamped to a saturation/contrast floor; curator can override.
- `decoys[]` per rung — ~3 plausible same-category wrong answers, generated at curation. Feeds the
  I-Need-Help multiple choice (and all of Poser later). It's a v1 *schema* requirement even though
  the hand-authored 001 puzzle omits it.

## Matching module (`match.js`) — the part that decides if the game feels fair

This is where the real engineering is; change it only with the test table green.

- `normalize(s)`: lowercase → strip diacritics → `&`→`and` → punctuation to spaces → collapse
  whitespace → drop a single leading article (`the`/`a`/`an`).
- `matchGuess(guess, answers)` accepts a guess if, against any normalized answer, it: matches
  exactly; is within `maxDist()` Levenshtein edits (typo tolerance scaled to answer length:
  0 for ≤3 chars, 1 for ≤6, 2 for ≤10, else 20%); or is a single token equal to the answer's
  **last** token (surname-only: "Bardem" → "Javier Bardem").
- Multi-name credits (e.g. the Coens) are handled by listing every acceptable form in `answers`,
  not by matcher logic.
- `match.test.js` is the contract: it encodes what should match vs. reject (foreign titles, typos,
  surname-only, wrong-surname rejections). Add a case there before touching the algorithm.
