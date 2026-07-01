# Project State — Degrees of Film

> **Running handoff doc. Read this first each session, and keep it updated** as work
> progresses (current task, decisions, next steps). Division of labor:
> `CLAUDE.md` = how the code works (durable); **this file = where we are right now** (living).
> A parallel copy of this status also lives in auto-memory (`degreesoffilm-status.md`).

_Last updated: 2026-06-30 (end of the Poser-mode session)._

## Where we are
- **v1 (Cinephile) is complete** and merged to `main`, plus a **polish round** — PRs **#1–#5 merged**.
- **v2 started: Poser mode is built.** Open as **PR #6** (`v2-poser` branch) — Poser mode +
  puzzle 006 (Toy Story). **Not yet merged.**
- **6 puzzles live** (001–006), dated **2026-06-28 .. 07-03** (No Country, Interstellar, Forrest
  Gump, The Dark Knight, Harry Potter, Toy Story).
- All tests green: 5 JS suites (`match/game/daily/theme/stats`) + 7 Python
  (`build_rungs/ledger/discover/decoys/manifest/publish/images`).

## Current task
Poser mode is done and in PR #6. **Decision pending: merge PR #6**, then choose the next v2 item.

## Next steps (pick up here)
1. **Merge PR #6** (`v2-poser`) into `main` — rebase merge like #1–#5, then sync `main` + delete branch.
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
