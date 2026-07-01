# Degrees of Film

> **New session? Read [`project_state.md`](project_state.md) FIRST**, then keep it updated as you
> work. It's the running handoff — current task, decisions, next steps. This file (CLAUDE.md)
> explains how the code works; `project_state.md` tracks where we are right now.

A daily browser game testing film knowledge. You're shown a cropped frame from a film
(title hidden), name it, then dig down through its credits from famous to obscure. The
brag number is **depth** — how many rungs deep you got.

**`DESIGN.md` is the full spec and source of truth.** This file is the working summary;
when the two disagree, DESIGN.md wins. **Current status: Phase 3 complete — v1 (Cinephile) is
feature-complete.** Phase 1 (the game) and Phase 2 (the curation tool) are merged to `main`;
Phase 3 (the daily game) is built on `phase-3-daily` (PR #3): daily selection + an archive
browser, accent theming, the I Need Help lifeline, localStorage stats/streak, a home +
mode-select front door, the required TMDB attribution, and a copy-to-clipboard share card. The
client routes views by query string: `?` home, `?modes` mode-select, `?play` today's game,
`?id=N` an archived game, `?archive` the index, `?play&mode=poser` a Poser game. **Poser mode is
built** (v2 — all-MC, flat +1); still deferred: **Movie Buff** (needs the v2 server move) and the
rest of the DESIGN §6 parking lot.

> This is a *vertical dig into one film's credits*, not "six degrees of separation" (hopping
> between films). True degrees-of-separation is a deferred v2 mode.

## Run & test

- **Play it:** the game uses `fetch`, so it needs a server — `file://` won't work. Serve the
  `docs/` folder and open `index.html`, e.g. `python -m http.server` from inside `docs/`.
- **Tests:** plain Node, no framework or deps. Run `node match.test.js`, `node game.test.js`,
  `node daily.test.js`, `node theme.test.js`, and `node stats.test.js` from the repo root. Each prints PASS/FAIL lines and exits non-zero on any failure. There is
  no `npm test` script; `package.json` exists only to set `"type": "module"` so the `.test.js`
  files can `import` the ES modules under `docs/`.
- **Curation tests (Phase 2):** run the `python curation/*.test.py` files (`build_rungs`, `ledger`,
  `discover`, `decoys`, `manifest`) — pure-logic, no network or API key, same PASS/FAIL +
  non-zero-exit style. The CLI modules (`discover.py`, `build_rungs.py`, `decoys.py`) hit live TMDB
  and need the key in `curation/.env`.
- **Image tests (Pillow):** `.venv/Scripts/python curation/images.test.py` — needs the repo-root
  `.venv` with `pillow` (`pip install -r curation/requirements.txt`). The box/colour math is pure;
  the crop/sample tests use Pillow.
- **Curation crop tool:** `.venv/Scripts/python -m uvicorn app:app --app-dir curation --port 8001`,
  then open `http://localhost:8001` (or use the `curation` entry in `.claude/launch.json`). Needs
  `curation/.env`. Flow: discover an unused film → pick a still and drag a crop box → review the
  drafted rungs/decoys → **Approve**, which writes `docs/puzzles/NNN.json` + tier images, appends
  the ledger, and upserts the manifest. (FastAPI; the heavy logic lives in the modules above.)

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
DESIGN.md              Full v1 spec + build roadmap + v2/v3 parking lot.
CLAUDE.md              This file (how the code works).
project_state.md       Running session handoff — current task, decisions, next steps. Read FIRST.
package.json           Just { "type": "module" }.
match.test.js          Matcher tests (node match.test.js). Cases mirror puzzle 001's answers.
game.test.js           Rules/scoring tests (node game.test.js): scoring curve + scripted playthroughs.
daily.test.js          Daily-selection tests (node daily.test.js): pickPuzzle date logic.
theme.test.js          Accent-theming tests (node theme.test.js): parse/luminance/contrast.
stats.test.js          Stats/streak tests (node stats.test.js): recordResult streak + histogram.
docs/                  The entire static site = what gets hosted.
  index.html           Markup + element ids the JS binds to.
  style.css            Dark "ink/bone/amber" theme. CSS vars in :root. Mobile breakpoint at 600px.
  app.js               DOM glue ONLY. Fetches the puzzle, renders, wires buttons. No rules here.
  game.js              Game rules, scoring, run state. Pure logic, no DOM.
  match.js             Fuzzy answer matching. Pure logic, no DOM.
  daily.js             Daily/archive selection from the manifest (pickPuzzle/pickById). Pure, no DOM.
  theme.js             Accent theming colour math (luminance/contrast). Pure logic, no DOM.
  stats.js             localStorage stats + streak (recordResult is pure; load/save touch storage).
  puzzles/
    001.json           The one hand-authored Phase 0 puzzle (No Country for Old Men).
    images/001.jpg     Its frame image.
curation/              PRIVATE (Phase 2) — never served. Holds the TMDB key (.env, gitignored).
  app.py               FastAPI crop tool: backend endpoints + serves the crop page. The capstone.
  static/index.html    Localhost crop UI (discover -> crop a still -> review rungs/decoys -> approve).
  tmdb.py              Tiny stdlib TMDB v3 client (load_key + get).
  discover.py          Find an unused film clearing the pool floor (vote_count/avg) + a CLI.
  build_rungs.py       Data layer: film+credits -> ordered rung draft (pure logic) + a thin CLI.
  decoys.py            Per-rung decoys (~3 same-category wrong answers) from neighbour films + CLI.
  images.py            Reveal-tier cropping + theme accent/palette-background sampling (Pillow) + CLI.
  publish.py           Approve step: assemble the puzzle file + append ledger + upsert manifest;
                       next_date() defaults publish dates to the next free day (no manifest collisions).
  ledger.py            Used-films ledger (never repeat); reads/writes used_films.json.
  manifest.py          Writer for docs/puzzles/manifest.json (the daily index the client reads).
  requirements.txt     Curation pip deps (Pillow + FastAPI/uvicorn) for the repo-root .venv.
  used_films.json      Version-controlled ledger of films already turned into puzzles.
  *.test.py            Tests (build_rungs/ledger/discover/decoys/manifest/publish pure; images=Pillow).
  validate_ladder.py   Throwaway de-risk script (popularity-vs-billing comparison).
```

**Layering, keep it clean:** `match.js` has no imports. `game.js` imports only `match.js`.
`app.js` imports `game.js` and does all DOM work. Rules and matching stay DOM-free so the Node
tests can import them directly. Don't leak rendering into `game.js`/`match.js` or rules into `app.js`.

`app.js` fetches `puzzles/manifest.json` (date-keyed to dodge stale caches), picks today's entry
via `daily.js`'s `pickPuzzle`, then fetches that puzzle file. The manifest is the `{ date, id,
file, title, accent }` daily index (DESIGN §4). `pickPuzzle` takes the exact-date entry, else the
most recent on/before today, else the earliest. The **archive browser** is a render of the
manifest: `?archive` lists past dailies (date + number + accent swatch, **titles hidden** so the
film rung stays a challenge), `?id=N` replays one (`pickById`), and archived runs don't touch the
daily streak/stats.

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
- **I Need Help:** 3 per game (`MAX_HELPS`). `useHelp()` converts the current rung to multiple
  choice (the answer + its `decoys`) and caps that rung's value at **0**; a wrong pick still
  **burns an attempt** (can strike you out). A rung with no `decoys` can't be helped. `app.js`
  shuffles the returned choices for display.
- **Win:** solving the last rung sets status `won`.
- **State machine:** `status` is `'playing' | 'over' | 'won'`. `guess()`/`skip()` no-op unless playing.
- **Stats:** `depth` = rungs passed = the hero/brag number. `score` = the tiebreaker (how cleanly
  you dug). Two players both 10 deep can have different scores.
- **Scoring (`scoreForRung(n)`):** rung N is worth N points, plus a deep-dig bonus that starts at
  rung 6, climbs +1/rung, and caps at +5 from rung 10 on. Curve for rungs 1–12:
  `1,2,3,4,5,7,9,11,13,15,16,17`. (Skips subtract 1 each.)

**Modes (in `app.js`, via the `?mode=` query):**
- **Cinephile** (default) — the full dig described above.
- **Poser** (v2, built) — `?play&mode=poser`. Every rung is multiple choice (answer + its
  `decoys`, shuffled), the ladder is trimmed to the first `POSER_RUNGS` (7) decoy-bearing rungs,
  and scoring is a flat **+1** per correct (no curve). No I-Need-Help (it's already all-MC) and no
  text input. Poser runs **don't** touch the daily streak/stats and skip the savage end roast; the
  share is tagged `(Poser)`. `game.js`'s `Game(puzzle, { mode })` only changes the scoring; the
  trim + all-MC rendering live in `app.js` (`poserPuzzle` / `renderChoices`).

**Still deferred (DESIGN §6 parking lot), don't assume these exist:**
- **Movie Buff** mode — TMDB title autocomplete on the film rung; needs the **v2 server move**
  (a live browser TMDB call would leak the key), so it stays "coming soon" on the mode-select.
- The rest of the v2/v3 parking lot (curate-a-week-ahead, practice/endless, reveal mechanic,
  accounts/DB, Score History, server-side matching, degrees-of-separation, …).

## Puzzle file schema

Each day is one self-contained JSON plus its images, under `docs/puzzles/`.

**As implemented today** (`001.json`): `id`, `images` (array of pre-cropped reveal tiers,
most-zoomed first — though 001 ships only one; **decided:** the curation tool authors 3 tiers,
but the v1 client renders only `images[0]` — tiers 2–3 are authored-ahead for a future reveal
mechanic), and `rungs[]` where each rung is
`{ role, prompt, answers[] }`. `answers` is the list of accepted strings (alternate titles,
language variants, name forms); the matcher accepts any of them.

**Full spec adds two fields (DESIGN §4), required once the curation tool exists:**
- `theme` — `{ accent, bg, bg2 }` sampled from the still. `accent` recolors the highlights (the
  guess-button text auto-contrasts via `theme.js`); `bg`/`bg2` are deep, film-hued tones that tint
  the surfaces and a top→bottom background gradient (`applyTheme` in app.js). Only **bone text stays
  fixed** for legibility; the dark base now leans into the film's palette. Curator can override the
  accent. (Sampled by `images.py` `derive_background`/`sample_accent`.)
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
