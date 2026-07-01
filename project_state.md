# Project State — Degrees of Film

> **Running handoff doc. Read this first each session, and keep it updated** as work
> progresses. **Update it in place on `main`; no PR needed for this doc.** Division of labor:
> `CLAUDE.md` = how the code works (durable); **this file = where we are right now** (living).
> A parallel copy of this status also lives in auto-memory (`degreesoffilm-status.md`).

_Last updated: 2026-07-01 (per-rung credit images MERGED — PRs #12–#14; crew headshots backfilled)._

## Where we are
- **v1 + polish + Poser + UX-polish batch merged** — PRs **#1–#11**.
- **Per-rung credit images — MERGED to `main` (PRs #12, #13, #14):**
  - **#12 (client + schema)** — `docs/frame.js` `pickCreditFrame()` picks the still per rung (tight
    crop → the answered credit's image + caption → full-frame fallback); app.js/index.html/style.css
    render the swap + caption overlay; optional per-rung `image`/`caption` schema. `frame.test.js`.
  - **#13 (curation authoring)** — `curation/credits_images.py` (maps rungs→people, offers candidate
    stills, finalizes picked image/caption + strips helper fields); `/api/film` + `/api/approve`
    wired; crop UI per-rung image picker; client letterboxes credit stills (`object-fit:contain`).
    `credits_images.test.py`.
  - **#14 (crew backfill)** — `curation/backfill_credit_images.py` filled all 6 puzzles' **crew**
    rungs with TMDB headshots (**27 images**, `docs/puzzles/images/NNN-rK.jpg`). Re-runnable CLI
    (`--ids`, `--dry-run`). No-headshot people (e.g. the Coens' "Roderick Jaynes") hold the full frame.
- **Design decisions:** cast rungs → **character still** (curator hand-picks); crew rungs → **TMDB
  headshot** (auto); missing image → **hold the full frame**; caption = **"Name as Character"**.
- **6 puzzles live** (001–006), dated **2026-06-28 .. 07-03**. **Crew rungs now have headshots;
  cast rungs still have NO images** (character stills = the remaining manual pass).
- All tests green: 6 JS suites (`match/game/daily/theme/stats/frame`) + 7 Python
  (`build_rungs/ledger/discover/decoys/manifest/publish/credits_images`).

## Current task
**Per-rung credit images shipped + crew backfilled.** The one piece left on this feature: **cast
character stills** — re-approve each of the 6 films through the crop tool and pick the still that
shows each actor (the new picker; needs TMDB key + your eye). Everything else is automatic and done.

## Next steps (pick up here)
1. **Finish credit images:** the manual **cast character-still** pass through the crop tool for the 6
   live puzzles (crew headshots already done via #14). Closes the last DESIGN §6 "UX polish" item.
2. **Continue v2** (see DESIGN §6). Remaining, roughly by closeness:
   - **Curate a week in advance** — scheduling view in the curation tool (see the coming week's
     slots, which dates are empty, stock ahead). `publish.next_date()` already queues onto the next
     free day; this makes the schedule visible. Curation-side only.
   - **Reveal mechanic** — spend image tiers 2–3 (e.g. a wider crop after a wrong guess). Cropper
     already authors all 3 tiers; client-only wiring.
   - **Practice / endless mode** · **Light answer obfuscation** (base64/cipher the in-JSON answers).
3. **Undone v1 finishing step:** deploy to **GitHub Pages** (serve `docs/`) so it's playable on the web.
4. **v3** (needs the *server move*): Movie Buff, accounts+DB, **Score History**, server-side
   matching, degrees-of-separation, commercial TMDB agreement.

## Key decisions (why things are the way they are)
- **Credit ordering:** cast by TMDB **billing order** (popularity only a tiebreaker), **director
  early**, technical crew deepest; a human reorders edge cases. Popularity-sort was de-risked and
  **rejected** — it buried Heath Ledger's Joker at rung 13.
- **Daily selection:** `manifest.json` index, single canonical-date rollover. **Archive hides film
  titles** (no spoilers). **Archived and Poser runs don't touch the daily streak/stats.**
- **I Need Help lifeline:** a wrong multiple-choice pick **burns an attempt** (not a guaranteed pass).
- **Image tiers:** cropper authors **3**; client shows only tier 1 (reveal mechanic deferred to v2).
- **Per-rung credit images:** shown *after* a rung is answered. **Cast → character still** (curator
  hand-picks; TMDB has no queryable actor-as-character image, so it's manual — candidates = tagged
  stills + movie backdrops + headshot); **crew → TMDB headshot** (auto). Missing image → **hold the
  full frame** (the film-rung reveal). Caption = **"Name as Character"** (name only for crew). Helper
  fields (person_id/profile/candidates/image_pick) ride the draft but are **stripped before publish**.
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
