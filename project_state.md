# Project State — Degrees of Film

> **Running handoff doc. Read this first each session, and keep it updated** as work
> progresses. **Update it in place on `main`; no PR needed for this doc.** Division of labor:
> `CLAUDE.md` = how the code works (durable); **this file = where we are right now** (living).
> A parallel copy of this status also lives in auto-memory (`degreesoffilm-status.md`).

_Last updated: 2026-07-02. v1 live; ALL static-v2 features shipped. Curation-only tools built recently:
**Randomize** (`afec469`), **Auto-crop** (`7957b19`), and **Clear scheduled puzzles** (this session,
uncommitted at time of writing — see below). v3 parking lot recorded incl. **Leaderboard**. Curation-only
commits trigger a Pages build but produce byte-identical `docs/`, so the live game is unchanged. **Resume:
operational curate-more / v2 leftovers (see ranking below) / v3 parking lot (Movie Buff, accounts/DB,
Leaderboard, Score History, server-side matching, degrees-of-separation — all need the server move).**_

## DONE — Clear scheduled puzzles (curation)
A **🗑 Clear scheduled** button in the crop tool's schedule section unschedules every upcoming
(strictly-future) puzzle at once, keeping today's daily + all past days. Two-click arm/confirm
(previews the count → commits; no native modal, so it's testable). Curation-only.
- **Backend:** pure `manifest.clear_scheduled(manifest, today)` → (kept, removed) split; tested in
  `manifest.test.py`. `GET /api/clear-schedule` = dry count preview, `POST` = commit (save kept).
- **Frontend (`curation/static/index.html`):** `#clearsched` button + `.btn.danger` style;
  `doClearSchedule()` arms on first click (shows "⚠ Clear N upcoming — click again", 5s timeout),
  commits on second, then `loadSchedule()` refreshes.
- **Design choice — UNSCHEDULE ONLY:** drops manifest entries; **keeps puzzle files + the ledger**
  (reversible; films stay "used" so they won't be re-suggested). A future "also delete files / free
  the films" variant could be added if wanted.
- **Verified live:** dry `GET` → `{scheduled:2, dates:[07-03,07-04]}`; UI arms correctly; `POST`
  removed exactly those 2 (kept through today), then the manifest was restored from git. 16 suites green.

### v2 ranking (updated — ordered by build complexity, low→high)
Operational (not a build item): **curate more puzzles** (ongoing content). Build items, simplest first:
1. Auto-crop **scale slider** — S · **DONE** (`?scale=` slider 0.25–0.85, live label, re-crops on release).
2. Randomize **honor sort** — S · **DONE** (`/api/random?sort=` from the sort dropdown). *(Floor has no
   UI — still the `POOL_MIN_*` constants; add a floor control only if wanted.)*
3. **Clear scheduled puzzles** — S–M · **DONE.**
4. ~~Randomize/Discover exclude scheduled-but-unpublished~~ — **DROPPED as a non-issue** (investigated:
   the ledger already excludes every approved film immediately + locally; there's no such gap). Instead,
   the user chose **"free films on Clear-scheduled"** — **DONE**: clearing now also removes the cleared
   puzzles' ledger records (`ledger.remove_by_puzzles`), re-opening those films for Discover/Randomize.
   Puzzle files kept; manifest+ledger git-reversible. Verified live (freed Toy Story + Avatar, restored).
5. Auto-crop **face/saliency detection** *(not built)* — M · smarter placement, avoid title cards.

**Only v2 build item left: #5 (auto-crop face/saliency).**

## DONE this session — Auto-crop (curation)
An **✨ Auto-crop** button in the crop tool suggests the tier-1 box instead of hand-dragging it; the
curator approves or re-drags (nothing is written until Approve). Curation-only, Pillow-only (no new deps).
- **Backend:** `images.auto_crop_box(image, *, scale=0.5)` places a `scale`-sized window (frame aspect)
  over the busiest region of the still, found from an edge-energy (`FIND_EDGES`) map via the pure
  `images.best_window` (summed-area table). `GET /api/autocrop?url=` returns the normalized box.
  Tests: `best_window` + `auto_crop_box` in `images.test.py` (now 25).
- **Frontend (`curation/static/index.html`):** Auto-crop button under the stage (enabled once a still
  is selected); `doAutocrop()` fetches the box, `drawBox()` renders the `#selbox` overlay, sets
  `state.box`, updates `#boxinfo`. Curator can then Approve or drag a new box (drag overrides).
- **Verified live (TMDB):** `/api/autocrop` returns e.g. `{x:0.46,y:0.37,w:0.5,h:0.5}` for a Dark Knight
  still; UI draws the overlay pixel-accurately (408.8px ≈ expected 409). All 16 suites green; no console
  errors. (Preview screenshot timed out on the heavy page — box verified via computed geometry instead.)
- **Follow-ups (not done):** face/saliency detection for smarter placement; a scale slider; auto-avoid
  title-card/subtitle regions (edge-energy can be drawn to text).

## DONE this session — curation "Randomize" button
A third way to find a film on the curation page (beside **search** and **Discover**): a **Randomize**
button that surfaces ONE random unused film as a **preview candidate** — it does NOT auto-open the
crop editor. From the preview the curator can **Randomize again** (re-roll) or **Use this film →**
(then and only then does it call `loadFilm(id)` to start authoring). Curation-only, no `docs/` change.
- **Backend:** `GET /api/random` (`curation/app.py`) — pulls a *random* `/discover` page (across the
  eligible catalog, for variety) and returns one random unused film summary `{id,title,year,
  vote_average,vote_count,backdrop}`; retries a few pages if one is all-used; 404 if none. New pure
  helper `discover.pick_random_unused(results, used, *, rng=…)` (rng injectable) — tested in
  `discover.test.py`.
- **Frontend (`curation/static/index.html`):** Randomize button by Discover; `doRandomize()` +
  `renderRandom(f)` show a `.randcard` preview (`#randombox`) with Use/Reroll buttons; `state.random`
  holds the candidate. `renderCards`/`fillPanel` clear the preview so it never lingers.
- **Verified live (TMDB):** varied unused picks (Yojimbo→Odd Thomas→House of Flying Daggers), all
  ledger-excluded; preview shows without opening the editor; reroll swaps; "Use this film" opens the
  editor (13 stills, 12 rungs) + clears the preview. 16 suites green; no console errors.
- **Possible follow-ups (not done):** exclude already-scheduled-but-unpublished films (only the ledger
  = published is excluded today); let the Randomize honour the sort dropdown / floor sliders.

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
5. **Light answer obfuscation** (both zones + migration) — answers/captions in puzzle files and the
   manifest `title` now ship lightly obfuscated so they're not readable in devtools. Shared cipher:
   `docs/cipher.js` + `curation/cipher.py` (XOR w/ key `degrees-of-film` + base64, U+0001 sentinel
   prefix → idempotent + plaintext-passthrough; a fixed cross-language vector is asserted in both
   `cipher.test.js` and `cipher.test.py`). Client: `app.js` `decodeRungs()` after fetch, so
   game.js/match.js see plaintext; decoys/prompts stay plaintext. Curation: `publish.assemble_puzzle`
   encodes rungs, `publish()`/`api_update` encode the manifest title, `upcoming_schedule` + `api_puzzle`
   (edit-load) + `backfill` decode. Migration CLI `curation/obfuscate_puzzles.py` encoded the 7 existing
   puzzles (170 strings) + 7 manifest titles (idempotent — re-run is a no-op). Verified end-to-end:
   Cinephile correct-guess + surname match + decoded caption, Poser MC choices, curation schedule +
   edit-load all round-trip; 16 suites green; no console errors. **NOT NECESSARILY DECISIVE:** it's a
   snoop stopgap, the key is in the client (v3 server-side matching is the real fix).

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
