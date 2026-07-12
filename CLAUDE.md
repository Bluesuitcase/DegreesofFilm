# Degrees of Film

> **New session? Read [`project_state.md`](project_state.md) FIRST**, then keep it updated as you
> work. It's the running handoff — current task, decisions, next steps. This file (CLAUDE.md)
> explains how the code works; `project_state.md` tracks where we are right now.
>
> **Then LOAD THE RELEVANT SKILL before working.** As of 2026-07-03 a 16-skill maintenance library
> lives in [`.claude/skills/`](.claude/skills/) (`degreesoffilm-*`), surfaced by trigger description.
> They encode the runbooks, invariants, config catalog, debugging playbook, and settled battles —
> e.g. `degreesoffilm-change-control` before committing, `degreesoffilm-run-and-operate` to publish a
> puzzle, `degreesoffilm-failure-archaeology` before "improving" anything. If a code change
> invalidates a fact a skill states, fix that skill in the same session (see `degreesoffilm-docs-and-writing`).

A daily browser game testing film knowledge. You're shown a cropped frame from a film
(title hidden), name it, then dig down through its credits from famous to obscure. The
brag number is **depth** — how many rungs deep you got.

**`DESIGN.md` is the full spec and source of truth.** This file is the working summary;
when the two disagree, DESIGN.md wins. **Current status: v1 COMPLETE and DEPLOYED LIVE** at
**https://bluesuitcase.github.io/DegreesofFilm/** (GitHub Pages, `main` `/docs`), and **ALL v2 features
are shipped to `main`.** Player-facing v2 (`docs/`, live): **Poser mode**, **Practice/endless mode**,
the **reveal mechanic** (widen the film-rung crop on wrong guesses), **per-rung credit images** (auto
TMDB headshots — the manual picker was removed), **vibrant themed tooltips** (`data-tip`, not native
`title`), and **light answer obfuscation** (a shared XOR+base64 cipher — `docs/cipher.js` /
`curation/cipher.py` — decoded in the client at load). Curation-tool v2 (`curation/`, private): the
**week-ahead schedule**, **film search**, **edit-existing-puzzle**, a **Randomize** film-picker
(`/api/random`), **Auto-crop** (`/api/autocrop`, face-first via OpenCV → edge-energy fallback, with a
size slider), and **Clear scheduled** (`/api/clear-schedule`, unschedule upcoming + free their films).
The client routes views by query string: `?` home, `?modes` mode-select, `?play` today's game, `?id=N`
an archived game, `?archive` the index, `?play&mode=poser` a Poser game, `?practice` the practice
chooser, `?practice&mode=cinephile|poser` an endless practice run. **The only open v2 task is
operational (curate more puzzles).** v3 status (2026-07-11): **Phase 1 server-side matching is
LIVE — deployed, GATE 1 passed, and the client default is ON** (`MATCH_API` in app.js points at
`https://dof-match.bluesuitcase.workers.dev`; Cloudflare Workers + KV, all puzzles' answers in KV).
Cinephile guesses are verified by POST /match with a 2 s local-match fallback (`?servermatch=0`
forces local); puzzle JSON still ships obfuscated answers as the fallback until §6 step 5 (gated on
≥14 days' stability). The rest of
the v3 parking lot — accounts/DB,
**Leaderboard**, degrees-of-separation — stays parked;
`degreesoffilm-server-move-campaign` is the decision-gated plan.
**Read `project_state.md` for exactly where we are and what's next.**

> This is a *vertical dig into one film's credits*, not "six degrees of separation" (hopping
> between films). True degrees-of-separation is a deferred v3-parking-lot mode.

## Run & test

- **Play it:** live at **https://bluesuitcase.github.io/DegreesofFilm/** (GitHub Pages serves `main`
  `/docs`; pushes to `main` touching `docs/` auto-deploy). Locally, the game uses `fetch`, so it needs
  a server — `file://` won't work. Serve the `docs/` folder and open `index.html`, e.g.
  `python -m http.server` from inside `docs/`.
- **Tests:** plain Node, no framework or deps. Run `node match.test.js`, `node game.test.js`,
  `node daily.test.js`, `node theme.test.js`, `node stats.test.js`, `node frame.test.js`,
  `node cipher.test.js`, `node worker.test.js`, and `node buff.test.js` from the repo root. Each prints PASS/FAIL lines and exits non-zero on any failure. There is
  no `npm test` script; `package.json` exists only to set `"type": "module"` so the `.test.js`
  files can `import` the ES modules under `docs/`. The matcher's case table lives in
  `match.cases.js` (shared by match.test.js and worker.test.js) — add cases there.
- **Curation tests (Phase 2):** run the `python curation/*.test.py` files (`build_rungs`, `ledger`,
  `discover`, `decoys`, `manifest`, `publish`, `credits_images`, `cipher`, `push_answers`) — pure-logic, no network or API key,
  same PASS/FAIL + non-zero-exit style. The CLI modules (`discover.py`, `build_rungs.py`, `decoys.py`,
  `credits_images.py`) hit live TMDB and need the key in `curation/.env`.
- **Image tests (Pillow):** `.venv/Scripts/python curation/images.test.py` — needs the repo-root
  `.venv` with `pillow` (`pip install -r curation/requirements.txt`). The box/colour/window math is
  pure; the crop/sample tests use Pillow. Auto-crop's face detection uses **`opencv-python-headless`
  (pinned `<5`; 5.0 dropped the Haar cascades)** but it's optional — `detect_faces` degrades to the
  edge-energy path if cv2 is missing, so the test suite passes without it.
- **Curation crop tool:** `.venv/Scripts/python -m uvicorn app:app --app-dir curation --port 8001`,
  then open `http://localhost:8001` (or use the `curation` entry in `.claude/launch.json`). Needs
  `curation/.env`. Flow: find a film — **free-text title search** (`/api/search`, all of TMDB),
  **Discover** (unused shortlist), or **Randomize** (`/api/random`: one random unused film shown as a
  *preview candidate* — "Randomize again" re-rolls, "Use this film →" commits; it does NOT auto-open
  the editor) → pick a still and drag a crop box (or hit **✨ Auto-crop**, which suggests a tier-1 box
  over the busiest region via `/api/autocrop`; the curator approves or re-drags) → review the drafted
  rungs/decoys (**per-rung credit images are automatic** — every cast/crew rung uses that person's
  TMDB headshot; no manual picking) →
  **Approve**, which writes `docs/puzzles/NNN.json` + tier images + per-rung credit images, appends
  the ledger, and upserts the manifest. (FastAPI; the heavy logic lives in the modules above.) The
  top of the page shows a **week-ahead schedule** (`/api/schedule`): the coming 14 days flagged
  stocked/empty with a "runway" count (consecutive stocked days from today); clicking an empty day
  targets it in the approve date field, and clicking a **filled** day (or a search hit already made
  into a puzzle) opens it for **editing** (`/api/puzzle/{id}` → `/api/update`): reschedule, re-edit
  rungs/credit images, and optionally re-crop the frame; the update rewrites the puzzle in place and
  moves its manifest entry (the ledger is untouched). Publishing auto-fills the next free day. A
  **🗑 Clear scheduled** button (`/api/clear-schedule`, two-click confirm) unschedules every upcoming
  (strictly-future) puzzle and **frees their films** (removes their ledger records so Discover/Randomize
  can suggest them again), keeping today + past; puzzle files are kept (manifest + ledger are
  git-reversible).

## Architecture — three zones

The whole design turns on one fact: **the TMDB API key never reaches a player.** It lives only
in the curation tool on your machine (`curation/`, built). Players only ever fetch finished
static files.

1. **PRIVATE (your machine)** — *built (FastAPI).* The `curation/` tool holds the key, queries TMDB,
   crops images with Pillow, and writes puzzle files. Owns the used-films ledger (never repeat a
   film), the week-ahead schedule, film search, and the edit-existing-puzzle flow.
2. **STATIC HOSTING (GitHub Pages)** — the `docs/` folder. Per-day puzzle JSON + pre-cropped
   images + the game client (html/js/css). Past puzzles are just old files that still exist, so
   the archive is nearly free.
3. **PLAYER BROWSER** — no key, no backend. Vanilla ES-module JS runs the rules and the fuzzy
   matcher; daily stats/streak live in localStorage (`stats.js`).

Consequence: v1 needs **no backend for players**. v1 shipped answers in plaintext in the JSON;
**v2 added light obfuscation** (`cipher.js`/`cipher.py`) so they're not readable at a glance in
devtools — still not real security (the key ships to the client), just an interim anti-snoop
stopgap until v3's server-side matching.

## File layout

```
.claude/skills/        16-skill maintenance library (degreesoffilm-*, 2026-07-03) — runbooks,
                       invariants, config catalog, debugging, failure archaeology, v3 campaign,
                       research frontier + methodology. Load the relevant one before working.
                       Ships scripts/validate_content.py (content integrity) + puzzle_report.py.
                       _BUILD-STATE.md there is the (deletable) build record, not a skill.
DESIGN.md              Full v1 spec + build roadmap + v2/v3 parking lot.
CLAUDE.md              This file (how the code works).
project_state.md       Running session handoff — current task, decisions, next steps. Read FIRST.
package.json           Just { "type": "module" }.
match.cases.js         The matcher contract as data: [guess, answers, expected, label] rows.
                       Shared by match.test.js + worker.test.js (+ the GATE 1 live parity check).
match.test.js          Matcher tests (node match.test.js). Cases mirror puzzle 001's answers.
game.test.js           Rules/scoring tests (node game.test.js): scoring curve + scripted playthroughs
                       + applyVerdict (server-verdict path) semantics/parity.
worker.test.js         /match Worker tests (node worker.test.js): in-process against a stub KV env —
                       full match.cases.js parity, no-answer-leak contract, CORS, rate limit.
daily.test.js          Daily-selection tests (node daily.test.js): pickPuzzle date logic.
theme.test.js          Accent-theming tests (node theme.test.js): parse/luminance/contrast.
stats.test.js          Stats/streak tests (node stats.test.js): recordResult streak + histogram.
frame.test.js          Credit-image tests (node frame.test.js): pickCreditFrame still selection.
cipher.test.js         Answer-obfuscation tests (node cipher.test.js): decode/round-trip/passthrough
                       + a fixed vector shared with curation/cipher.test.py (cross-language parity).
buff.test.js           Movie Buff autocomplete tests (node buff.test.js): indexKeys/suggest ranking.
docs/                  The entire static site = what gets hosted.
  index.html           Markup + element ids the JS binds to.
  style.css            Dark "ink/bone/amber" theme. CSS vars in :root. Mobile breakpoint at 600px.
  app.js               DOM glue ONLY. Fetches the puzzle, renders, wires buttons. No rules here.
  game.js              Game rules, scoring, run state. Pure logic, no DOM.
  match.js             Fuzzy answer matching. Pure logic, no DOM.
  daily.js             Daily/archive selection from the manifest (pickPuzzle/pickById). Pure, no DOM.
  theme.js             Accent theming colour math (luminance/contrast). Pure logic, no DOM.
  stats.js             localStorage stats + streak + per-day score history (recordResult is pure;
                       load/save touch storage). ?history renders the history map.
  frame.js             Which still to show per rung (pickCreditFrame): film-rung crop that widens
                       one tier per wrong guess (reveal) -> credit image + caption -> full-frame
                       fallback. Pure logic, no DOM.
  cipher.js            Light answer de-obfuscation (decode/decodeRungs). Mirrors curation/cipher.py;
                       app.js decodes each puzzle's rungs at load. Pure logic, no DOM.
  buff.js              Movie Buff autocomplete core (indexKeys/suggest over title-index.json,
                       keyed via match.js normalize). Pure logic, no DOM.
  title-index.json     Prebaked top-5k TMDB title index [[title,year],...] for Movie Buff
                       (built by curation/title_index.py; fetched only in buff mode).
  people-index.json    Prebaked people index ["Name",...] for Movie Buff credit rungs
                       (credits-harvested by curation/people_index.py --source credits;
                       fetched only in buff mode).
  puzzles/
    001.json           The hand-authored Phase 0 puzzle (No Country for Old Men); 002+ are
                       tool-published. manifest.json is the daily index.
    images/001.jpg     Its frame image (tool-published puzzles add NNN-{1,2,3}.jpg tiers + NNN-rK.jpg headshots).
curation/              PRIVATE (Phase 2) — never served. Holds the TMDB key (.env, gitignored).
  app.py               FastAPI crop tool: backend endpoints + serves the crop page. The capstone.
  static/index.html    Localhost crop UI (discover -> crop a still -> review rungs/decoys -> approve).
  tmdb.py              Tiny stdlib TMDB v3 client (load_key + get).
  discover.py          Find an unused film clearing the pool floor (vote_count/avg): candidates/
                       pick_unused/pick_random_unused (Randomize) + a CLI.
  build_rungs.py       Data layer: film+credits -> ordered rung draft (pure logic) + a thin CLI.
  decoys.py            Per-rung decoys (~3 same-category wrong answers) from neighbour films + CLI.
  credits_images.py    Per-rung credit images: map rungs->people, stamp each with its TMDB headshot
                       + caption (auto, cast + crew alike), finalize image/caption + strip helper
                       fields at approve (pure core) + CLI.
  images.py            Reveal-tier cropping + theme accent/palette-background sampling + auto-crop
                       (auto_crop_box: face-first via detect_faces/box_around, else edge-energy via
                       best_window/deweight_bands) (Pillow; face detection uses optional OpenCV) + CLI.
  cipher.py            Light answer obfuscation (obfuscate/deobfuscate + encode_rungs/decode_rungs):
                       XOR+base64 with a sentinel prefix, idempotent + plaintext-passthrough. Mirrors
                       docs/cipher.js. publish encodes on write; app.py decodes on edit-load.
  publish.py           Approve step: assemble the puzzle file (answers/captions obfuscated via cipher)
                       + append ledger + upsert manifest (title obfuscated); next_date() defaults
                       publish dates to the next free day (no manifest collisions); upcoming_schedule()
                       (decodes titles) / runway() power the week-ahead scheduling view.
  ledger.py            Used-films ledger (never repeat); reads/writes used_films.json. remove_by_puzzles
                       frees films when their scheduled puzzle is cleared.
  manifest.py          Writer for docs/puzzles/manifest.json (the daily index the client reads).
                       clear_scheduled splits kept/removed for the Clear-scheduled button.
  requirements.txt     Curation pip deps (Pillow + FastAPI/uvicorn + opencv-python-headless<5, the last
                       optional for auto-crop face detection) for the repo-root .venv.
  used_films.json      Version-controlled ledger of films already turned into puzzles.
  *.test.py            Tests (build_rungs/ledger/discover/decoys/manifest/publish/credits_images/cipher/
                       push_answers pure; images=Pillow).
  backfill_credit_images.py  Re-runnable CLI: fill existing puzzles' credit rungs (cast + crew) with
                       TMDB headshots (maps puzzle->film via the ledger).
  obfuscate_puzzles.py Re-runnable migration CLI: obfuscate answers/captions in existing puzzle files
                       + manifest titles (idempotent). New publishes are encoded automatically.
  push_answers.py      v3 Phase 1: builds the /match Worker's PLAINTEXT answers artifact
                       (server/answers-bulk.json, GITIGNORED) as a `wrangler kv bulk put` file;
                       file_sink() is publish()'s answers_sink so approve/update keep it current.
  backfill_answers.py  Re-runnable CLI: rebuild the whole answers artifact from the published
                       puzzles (decodes via cipher). Needed at Phase 1 cutover + rollback.
  validate_ladder.py   Throwaway de-risk script (popularity-vs-billing comparison).
server/                v3 Phase 1 (LIVE since 2026-07-11, client flag ON) — the /match Cloudflare Worker.
  worker.js            POST /match {puzzleId, rungIndex, guess} -> {correct[, canonical]}.
                       Imports docs/match.js UNCHANGED (parity by reuse). Answers in KV,
                       pinned CORS, 60/min/IP rate limit. ON in the client since 2026-07-11.
  wrangler.toml        Worker config + the deploy runbook in its header comment.
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
- **Movie Buff** (shipped 2026-07-11) — `?play&mode=buff`. Cinephile rules and scoring on the
  full ladder, plus **autocomplete on every rung**: titles on the film rung
  (`title-index.json`, top-5k TMDB-wide) and people on credit rungs (`people-index.json`,
  credits-harvested from all ~3.7k pool-floor films — 221/222 rung coverage; person-popularity
  was measured at 50% and rejected). Both via `docs/buff.js` suggest, fetched only in this
  mode. Server matching active (untrimmed ladder). Buff runs **don't** touch the daily
  streak/stats, skip the roast, and share as `(Movie Buff)`. Rebuild the people index
  occasionally (`curation/people_index.py --source credits`, cached) as films cross the pool floor.

**Still deferred (DESIGN §6 parking lot), don't assume these exist:**
- ~~Movie Buff mode~~ — **SHIPPED 2026-07-11** (`?play&mode=buff`, mode-select tile lit):
  Cinephile rules + film-rung title autocomplete from a **prebaked static top-5k title index**
  (`docs/title-index.json`, built TMDB-wide by `curation/title_index.py` so membership leaks
  nothing; build asserts every ledger film present). `docs/buff.js` is the pure suggest core
  (keys via the shipped `normalize()`); other modes never fetch the index. Buff runs don't touch
  daily streak/stats and share as "(Movie Buff)". No live TMDB call — the key-leak ban holds.
- ~~Server-side matching~~ — **SHIPPED AND ON (2026-07-11)**: the v3 Phase 1 Worker at
  `https://dof-match.bluesuitcase.workers.dev` verifies cinephile guesses (2 s local fallback;
  `?servermatch=0` forces local). Still pending: §6 step 5 (stop embedding answers in NEW puzzle
  files) — gated on ≥14 days' stability + owner sign-off.
- The rest of the v3 parking lot: accounts/DB, Leaderboard, true
  degrees-of-separation. *(Formerly parked but since shipped in v2: practice/endless, light answer
  obfuscation, the week-ahead schedule, film search + edit-existing-puzzle, the reveal mechanic.)*

## Puzzle file schema

Each day is one self-contained JSON plus its images, under `docs/puzzles/`.

**As implemented today** (`001.json`): `id`, `images` (array of pre-cropped reveal tiers,
most-zoomed first — though 001 ships only one; the curation tool authors 3 tiers). The **reveal
mechanic** now spends them on the film rung: `frame.js` `pickCreditFrame` takes a `revealTier` =
`game.attempts` (wrong guesses on the current rung), so each miss on rung 1 widens the crop one tier
toward the full frame (clamped to `images[last]`; single-tier puzzles just stay put). Then
`rungs[]` where each rung is
`{ role, prompt, answers[] }`. `answers` is the list of accepted strings (alternate titles,
language variants, name forms); the matcher accepts any of them. **On disk the `answers` (and each
rung's `caption`, and the manifest `title`) are lightly obfuscated** — a U+0001-sentinel-prefixed
XOR+base64 blob (see `cipher.js`/`cipher.py`) so they aren't readable in devtools; `app.js` decodes
the rungs at load, so `game.js`/`match.js` still see plaintext. `decoys`/`prompt` stay plaintext
(they're player-facing and aren't the answer). Decoding is a passthrough for any un-prefixed string,
so hand-authored plaintext puzzles still work.

**Full spec adds these fields (DESIGN §4), required once the curation tool exists:**
- `theme` — `{ accent, bg, bg2 }` sampled from the still. `accent` recolors the highlights (the
  guess-button text auto-contrasts via `theme.js`); `bg`/`bg2` are deep, film-hued tones that tint
  the surfaces and a top→bottom background gradient (`applyTheme` in app.js). Only **bone text stays
  fixed** for legibility; the dark base now leans into the film's palette. Curator can override the
  accent. (Sampled by `images.py` `derive_background`/`sample_accent`.)
- `decoys[]` per rung — ~3 plausible same-category wrong answers, generated at curation. Feeds the
  I-Need-Help multiple choice (and all of Poser later). It's a v1 *schema* requirement even though
  the hand-authored 001 puzzle omits it.
- `image` + `caption` per rung (**both optional**) — the credit image shown *after* you answer that
  rung: the person's TMDB headshot (cast and crew alike, chosen automatically), with `caption` =
  "Name as Character" for cast, name only for crew. `image` is a filename under `puzzles/` (e.g.
  `images/004-r2.jpg`). The film
  rung carries neither — passing it reveals the full frame. Any rung missing `image` holds the full
  frame (`frame.js` `pickCreditFrame`). Authored by the curation tool; puzzles without them just
  keep the old tight-crop → full-frame reveal.

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
