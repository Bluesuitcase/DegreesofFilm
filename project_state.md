# Project State — Degrees of Film

> **Running handoff doc. Read this first each session, and keep it updated** as work
> progresses. **Update it in place on `main`; no PR needed for this doc.** Division of labor:
> `CLAUDE.md` = how the code works (durable); **this file = where we are right now** (living).
> A parallel copy of this status also lives in auto-memory (`degreesoffilm-status.md`).

_Last updated: 2026-07-01 (v1 live; v2: schedule+search+edit #16–#17, reveal mechanic #18, auto-headshot
credit images, Practice/endless mode, and **vibrant themed tooltips** all shipped to `main` + live. The
ONLY static-v2 feature left is **light answer obfuscation** (+ operational: curate more puzzles)._

## Where we are
- **v1 + polish + Poser + UX-polish batch merged** — PRs **#1–#11**.
- **Per-rung credit images — COMPLETE, MERGED to `main` (PRs #12–#15). This closes the last DESIGN
  §6 "UX polish" playtest item.**
  - **#12 (client + schema)** — `docs/frame.js` `pickCreditFrame()` picks the still per rung (tight
    crop → the answered credit's image + caption → full-frame fallback); app.js/index.html/style.css
    render the swap + caption overlay; optional per-rung `image`/`caption` schema. `frame.test.js`.
  - **#13 (curation authoring)** — `curation/credits_images.py` (maps rungs→people, finalizes
    image/caption + strips helper fields); `/api/film` + `/api/approve` wired; crop UI per-rung
    picker; client letterboxes credit images (`object-fit:contain`). `credits_images.test.py`.
  - **#14 + #15 (backfill)** — `curation/backfill_credit_images.py` (re-runnable CLI; `--ids`,
    `--dry-run`) filled **every credit rung** of all 6 puzzles with TMDB headshots. **62 images**
    (`docs/puzzles/images/NNN-rK.jpg`): 35 cast + 27 crew. People with no TMDB headshot (e.g. the
    Coens' "Roderick Jaynes") hold the full frame.
- **Design (as shipped):** ALL credit rungs → **TMDB headshot** (cast + crew, auto). We tried
  cast-specific *character stills* but TMDB tagged images are too sparse (mostly generic backdrops
  shared across the cast), so headshots are the uniform default. Missing headshot → **hold the full
  frame**. Caption = **"Name as Character"** for cast, name only for crew. The crop-tool picker still
  allows a manual in-character override (unused by default).
- **v2 curation started — MERGED to `main`:**
  - **#16 (week-ahead schedule)** — `publish.upcoming_schedule()`/`runway()` + `/api/schedule`; a
    14-day strip at the top of the crop tool (runway headline; empty days clickable to target a date).
  - **#17 (search + edit)** — `/api/search` free-text title search across all TMDB (used films badged
    → route to edit); **edit-existing-puzzle** flow (`/api/puzzle/{id}` load + `/api/update` rewrite):
    reschedule, re-edit rungs/credit images, optionally re-crop. Reachable from a filled schedule day
    or a used search hit. `manifest.upsert` now keys on id+date so reschedules don't leave stale entries.
  - **#18 (reveal mechanic) — BUILT, PR OPEN, NOT MERGED.** `frame.js` `pickCreditFrame` gains a
    `revealTier` param (= `game.attempts`); on the film rung each wrong guess widens the crop one tier
    toward the full frame (clamped; single-tier puzzles stay put). `app.js` passes `game.attempts` and
    cues it in the wrong-guess feedback ("More of the frame is showing."). `frame.test.js` extended.
    Client-only → **merging redeploys the live site.** Verified in-browser (004-1→2→3 across misses).
    **This branch's `frame.js`/`app.js`/`frame.test.js`/`CLAUDE.md` differ from `main` — they live on
    branch `reveal-mechanic`. Merge #18 before touching those files on main to avoid conflicts.**
- **7 puzzles live** (001–007): No Country, Interstellar, Forrest Gump, Dark Knight, Harry Potter,
  Toy Story, **Avatar** (007, 2026-07-04). Dated **2026-06-28 .. 07-04**, every credit rung imaged.
- All tests green: 6 JS suites (`match/game/daily/theme/stats/frame`) + 7 Python
  (`build_rungs/ledger/discover/decoys/manifest/publish/credits_images`).

## Current task — DONE this session (both shipped to `main`):
1. **PR #18 (reveal mechanic) MERGED** — rebased to `main` (commit `995c01e`), branch deleted, Pages
   built + confirmed live (deployed `frame.js` byte-matches `main`).
2. **Practice/endless mode BUILT + committed direct to `main`** (client-only: `docs/index.html`,
   `docs/app.js`; no server, no new puzzle data). Decisions taken this session:
   - **Shape:** *endless run + session tally* — finish a random past puzzle → **"Next film →"** loads
     the next; running tally = films / cleared / total depth / avg depth. No daily-stat impact.
   - **Ruleset:** **player chooses** Cinephile or Poser at the start (a Practice chooser screen).
   - **Pool/spoilers:** random from the manifest, **excluding today's daily**; avoids an immediate
     repeat when >1 puzzle. (Only ~7 puzzles, so it will repeat — fine.)
   - **Wiring:** `#modes` has a **Practice** card → `?practice` (chooser, `renderPractice`) → the two
     ruleset links `?practice&mode=cinephile|poser` start the run. `app.js`: `isPractice`/`playedIds`/
     `practiceTally` state; `practicePool()`/`nextPracticeEntry()`; the puzzle-load body was extracted
     into `loadAndStart(entry)` so "Next film" re-runs it without a full reload. `showEnd` guards stats
     with `!isPractice` (alongside `isArchive`/`poser`), shows `practiceHtml()` tally + Next/End
     buttons, and hides the share for practice. Verified in preview; 6 node suites green.
3. **Removed the manual cast-photo picker from the curation tool** (curation-only; no `docs/` change,
   so no live deploy). Per-rung credit images are now **fully automatic** — every cast/crew rung uses
   that person's TMDB headshot, no manual character-still choice. Ripped out `candidate_stills`/
   `tagged_still_urls`/`image_pick`/`candidates` and the crop-tool `#pickers` UI + its JS/CSS.
   `credits_images.attach_person_meta` now stamps just `character`/`profile`/`caption`;
   `finalize_rung_images` saves from `profile` (headshot); `app.py` calls `attach_person_meta`
   directly (dropped `_attach_image_options`); `backfill` reads `profile`. Tests + docs updated;
   verified end-to-end against live TMDB (`/api/film/155` returns headshot+caption, no picker fields).
4. **Vibrant themed tooltips** (client-only, `docs/`) — replaced the plain, slow native `title`
   hover hints with custom CSS tooltips: any element with `data-tip="…"` gets an accent-colored
   bubble + pointer above it, ~0.11s fade (vs native ~500ms), shown on hover AND `:focus-visible`.
   In-game the bubble uses the puzzle's accent (`var(--amber)`) with auto-contrasting text. Applied
   to Play today / Modes / Skip / I Need Help (the `#help-btn` tip is new); `title` attrs removed to
   avoid double tooltips. Pure CSS (`[data-tip]::after/::before` in `style.css`) — no JS. Verified in
   preview (computed styles + screenshot); no console errors.

**Live site:** https://bluesuitcase.github.io/DegreesofFilm/ (Pages serves `main` `/docs`).

## Deploy notes (how the live site is wired)
- **GitHub Pages**, source = `main` branch `/docs` folder (set via `gh api ... /pages`). Every push to
  `main` that touches `docs/` re-deploys automatically. Check builds: `gh api repos/Bluesuitcase/
  DegreesofFilm/pages/builds/latest`.
- `docs/.nojekyll` present (raw static serve). No custom domain; URL is the default `*.github.io`.
- **Content treadmill:** 7 puzzles now (through 2026-07-04). Past the last date `pickPuzzle` falls
  back to the most-recent puzzle, so the daily won't 404 — but it stops being *new*. Keep curating
  (the schedule strip + edit flow make stocking + fixing days easy now).

## Next steps (pick up here)
1. **Remaining v2** (DESIGN §6): **light answer obfuscation** (base64/cipher the in-JSON answers);
   **curate more puzzles** (operational; the live daily needs a steady supply — the schedule + edit
   flow make this easy now).
3. **v3** (needs the *server move*): Movie Buff, accounts+DB, **Score History**, server-side
   matching, degrees-of-separation, commercial TMDB agreement.

_Shipped so far this v2 push: week-ahead schedule (#16), film search + edit-existing-puzzle (#17),
reveal mechanic (#18, awaiting merge)._

## Key decisions (why things are the way they are)
- **Credit ordering:** cast by TMDB **billing order** (popularity only a tiebreaker), **director
  early**, technical crew deepest; a human reorders edge cases. Popularity-sort was de-risked and
  **rejected** — it buried Heath Ledger's Joker at rung 13.
- **Daily selection:** `manifest.json` index, single canonical-date rollover. **Archive hides film
  titles** (no spoilers). **Archived and Poser runs don't touch the daily streak/stats.**
- **I Need Help lifeline:** a wrong multiple-choice pick **burns an attempt** (not a guaranteed pass).
- **Image tiers / reveal mechanic:** cropper authors **3** tiers (tight → wider → full). The reveal
  mechanic (PR #18, built/unmerged) spends them on the film rung: each wrong guess widens the crop one
  tier toward the full frame (`frame.js` `revealTier` = `game.attempts`). Credit rungs are unaffected;
  single-tier puzzles (001) stay put.
- **Per-rung credit images:** shown *after* a rung is answered. **ALL credit rungs → TMDB headshot**
  (cast + crew, auto). We tried cast-specific *character stills* but TMDB tagged images proved too
  sparse (mostly generic backdrops shared across the whole cast — 13 of 14 identical between two Dark
  Knight actors), so headshots became the uniform default. Missing headshot → **hold the full frame**
  (the film-rung reveal). Caption = **"Name as Character"** for cast, name only for crew. The crop-tool
  picker still *offers* candidate stills for a manual override, but that override flow is **parked**.
  Helper fields (person_id/profile/candidates/image_pick) ride the draft but are **stripped before publish**.
- **Theming:** per-puzzle `theme {accent, bg, bg2}` sampled from the still's palette; page tints the
  background (bg2→bg gradient) but **bone text stays fixed** for legibility.
- **Poser mode:** all-MC, ladder trimmed to first **7** decoy-bearing rungs, flat **+1**; reuses
  `decoys`; no streak/stats/roast; share tagged `(Poser)`. `Game(puzzle,{mode})` changes scoring;
  trim + all-MC rendering live in `app.js`.
- **Curation publish date** auto-assigns the **next free day** (`publish.next_date`) — fixed the
  manifest-collision footgun (multiple same-day publishes silently overwrote each other).
- **Answers ship in plaintext** in v1 (accepted; no leaderboard). v2 obfuscation / v3 server-side
  matching are parked.

## Workflow / gotchas
- **Branch → PR → merge (rebase) → delete branch** for each chunk. `main` is the default branch.
- **gh CLI is installed but NOT logged in** — auth per-command via `GH_TOKEN` pulled from the cached
  git credential (`git credential fill` → password). See the `gh-auth-via-cached-token` memory.
- **Dev cache gotcha:** `python http.server` serves **stale ES modules / CSS** after edits. To verify
  UI changes, use a **fresh port** (temporarily add a `docsN` config to `.claude/launch.json`, use it,
  then `git checkout .claude/launch.json`).
- **Curation tool** needs the repo-root `.venv` (Pillow + FastAPI) and `curation/.env` (TMDB key,
  gitignored). Run: `.venv/Scripts/python -m uvicorn app:app --app-dir curation --port 8001`.
- The preview **screenshot** tool sometimes times out on the renderer — fall back to `preview_eval`
  DOM checks to verify.

## Run & test (quick)
- **Play:** serve `docs/` (`python -m http.server` inside `docs/`), open `localhost:8000`.
  Views: `?` home · `?play` today · `?play&mode=poser` Poser · `?modes` · `?archive` · `?id=N`.
- **Tests:** `node match.test.js game.test.js daily.test.js theme.test.js stats.test.js` (repo root);
  `python curation/{build_rungs,ledger,discover,decoys,manifest,publish}.test.py`;
  `.venv/Scripts/python curation/images.test.py`. (Full details in CLAUDE.md.)
