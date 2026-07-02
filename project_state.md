# Project State — Degrees of Film

> **Running handoff doc. Read this first each session, and keep it updated** in place on `main`
> (no PR needed for this file). Division of labor: `CLAUDE.md` = how the code works (durable);
> **this file = where we are right now** (living). A mirror also lives in auto-memory
> (`degreesoffilm-status.md`).

_Last updated: 2026-07-02. **v1 is live and ALL v2 features are shipped to `main`.** Working tree
clean, everything pushed, no open PRs. **Resume with: operational (curate more puzzles) and/or start
the v3 "server move."** Full v2/v3 backlog is in `DESIGN.md` §6._

## Status at a glance
- **v1 — COMPLETE + DEPLOYED LIVE:** https://bluesuitcase.github.io/DegreesofFilm/ (GitHub Pages,
  `main` `/docs`; pushes touching `docs/` auto-deploy).
- **v2 — COMPLETE:** every static-v2 feature is built, tested, and on `main` (list below).
- **v3 — NOT STARTED:** the parking lot; all of it needs the **server move** (a real backend).
- **Content:** 7 puzzles (001–007), dated **2026-06-28 .. 07-04**. **Pool is thin past 07-04** —
  `pickPuzzle` falls back to the most-recent so the daily won't 404, but it stops being *new*.
  Curating more is the main open operational task.
- **Tests:** 7 JS suites + 8 Python (pure) + `images` (Pillow) — **all green**. Details at the bottom.

## What's shipped in v2 (all on `main`)
**Player-facing (`docs/`, live):**
- **Poser mode** (`?play&mode=poser`) — all-MC, ladder trimmed to first 7 decoy-bearing rungs, flat +1.
- **Practice / endless mode** (`?practice` chooser → `?practice&mode=cinephile|poser`) — random past
  puzzles back-to-back, running tally, no daily-stat impact.
- **Reveal mechanic** — the film-rung crop widens one tier per wrong guess (`frame.js` `revealTier`).
- **Per-rung credit images** — automatic TMDB headshots (cast + crew); the manual character-still
  picker was removed.
- **Vibrant tooltips** — `data-tip` CSS bubbles (accent-colored, ~0.11s) replace native `title`.
- **Light answer obfuscation** — `docs/cipher.js` ↔ `curation/cipher.py` (XOR+base64, U+0001 sentinel,
  idempotent + plaintext-passthrough). Puzzle `answers`/`caption` + manifest `title` ship obfuscated;
  `app.js` `decodeRungs()` decodes at load. Interim anti-snoop only (key ships to client).

**Curation tool (`curation/`, private — never served):**
- **Week-ahead schedule** + **film search** + **edit-existing-puzzle** (`/api/schedule`, `/api/search`,
  `/api/puzzle/{id}` + `/api/update`).
- **Randomize** [`afec469`] — `/api/random` surfaces ONE random unused film as a *preview candidate*
  (does NOT auto-open the editor); Randomize-again / Use-this-film. Honors the sort dropdown.
  Pure `discover.pick_random_unused`.
- **Auto-crop** [`7957b19`, `4496c81`, `388e645`] — `/api/autocrop` suggests the tier-1 box; the curator
  approves or re-drags. **Face-first** (OpenCV Haar `images.detect_faces` → `images.box_around` the
  largest face); falls back to edge energy (`images.best_window` + `images.deweight_bands` to dodge
  title cards). A **size slider** (0.25–0.85) tunes tightness.
- **Clear scheduled** [`125c4a5`, `c0329a2`] — `/api/clear-schedule` (GET dry count, POST commit)
  unschedules all upcoming (strictly-future) puzzles AND frees their films (`ledger.remove_by_puzzles`)
  so Discover/Randomize can suggest them again. Keeps files; manifest+ledger git-reversible.

## Next steps (pick up here)
1. **Operational — curate more puzzles** (the one open v2 task). Run the crop tool
   (`.venv/Scripts/python -m uvicorn app:app --app-dir curation --port 8001`, needs `curation/.env`):
   Randomize → face-aware Auto-crop → review the drafted rungs → Approve (auto-fills the next free day,
   writes the puzzle + images + credit headshots, appends the ledger, upserts the manifest). Then
   `git commit`/push `docs/` to deploy.
2. **v3 parking lot** — all needs the server move. Two tracks (full list + complexity in DESIGN.md §6):
   - **Stay-static (no backend needed):** Score History (client-only), Movie Buff (prebaked popular-
     title index), true degrees-of-separation (prebaked film/person graph).
   - **Server-move track (needs backend, in dependency order):** **Accounts + DB** → **Server-side
     matching** → **Leaderboard** (sortable by mode/user/total, asterisk when a total is mostly
     easy-mode) + cross-device stats. Also: commercial TMDB agreement (only if it scales/monetizes).

## Key decisions (why things are the way they are)
- **Credit ordering:** cast by TMDB **billing order** (popularity only a tiebreaker), **director
  early**, technical crew deepest; a human reorders edge cases. Popularity-sort was **rejected** — it
  buried Heath Ledger's Joker at rung 13.
- **Daily selection:** `manifest.json` index, single canonical-date rollover. **Archive hides film
  titles** (no spoilers). **Archived / Poser / Practice runs don't touch the daily streak/stats.**
- **I Need Help lifeline:** a wrong multiple-choice pick **burns an attempt** (not a guaranteed pass).
- **Reveal mechanic (shipped):** the cropper authors **3** tiers (tight → wider → full); on the film
  rung each wrong guess widens the crop one tier (`frame.js` `revealTier` = `game.attempts`). Credit
  rungs unaffected; single-tier puzzles (001) stay put.
- **Per-rung credit images:** shown *after* a rung is answered. **ALL credit rungs → TMDB headshot**
  (cast + crew, automatic — the manual character-still picker was **removed**). We tried character
  stills but TMDB tagged images are too sparse (mostly generic backdrops shared across the cast).
  Missing headshot → hold the full frame. Caption = "Name as Character" for cast, name only for crew.
- **Answer obfuscation (shipped):** a shared XOR+base64 cipher, decoded client-side at load. It's an
  interim anti-snoop stopgap — the key ships to the client, so **v3 server-side matching is the real
  fix**. Decoys/prompts stay plaintext (player-facing, not the answer).
- **Auto-crop:** **face-first, then edge-energy** — Haar misses angled/dark faces, so it's a *starting
  point* the curator approves. Pinned **`opencv-python-headless>=4.9,<5`**: OpenCV **5.0 dropped the
  bundled Haar cascades** (only ships DNN `FaceDetectorYN`, which needs a downloaded model file); 4.13
  has a Python-3.14 wheel and keeps the classic cascade. cv2 is **optional at runtime** (degrades to
  edge-energy if absent).
- **Randomize:** shows a *preview candidate* and does NOT auto-load the editor (unlike search/Discover,
  whose clicks call `loadFilm`). "Use this film →" is the explicit commit.
- **Clear-scheduled:** unschedules future puzzles AND frees their films from the ledger (so they can be
  re-picked). Keeps the puzzle files on disk; manifest + ledger are git-tracked, so it's reversible.
- **Theming:** per-puzzle `theme {accent, bg, bg2}` sampled from the still; page tints the background
  (bg2→bg gradient) but **bone text stays fixed** for legibility.
- **Poser mode:** `Game(puzzle,{mode})` changes only scoring; the ladder trim + all-MC rendering live
  in `app.js`. Share tagged `(Poser)`; no streak/stats/roast.
- **Curation publish date** auto-assigns the **next free day** (`publish.next_date`) — fixes the
  manifest-collision footgun (multiple same-day publishes silently overwrote each other).

## Workflow / gotchas
- **Shipping this session:** curation-only changes (no `docs/` change) were committed **direct to
  `main`** per the user's repeated choice — they don't deploy the live game (Pages rebuilds but
  produces byte-identical `docs/`). Earlier player-facing work went via **branch → PR → rebase-merge →
  delete branch**. Confirm with the user how they want each change to land (they've been choosing
  commit-direct for curation-only).
- **`gh` CLI:** works **directly in the Bash tool** this session (the tool environment supplies auth) —
  no manual token dance was needed. If it ever shows logged-out, fall back to the `GH_TOKEN`-from-cached-
  credential trick (see the `gh-auth-via-cached-token` memory).
- **Verifying destructive curation endpoints** (`/api/clear-schedule`): they modify the real
  `manifest.json` / `used_films.json`. Test via the tool, verify, then **restore with
  `git checkout -- docs/puzzles/manifest.json curation/used_films.json`**. Both are git-tracked.
- **Dev cache gotcha:** the browser caches `docs/` CSS/JS per origin:port. After edits, force a fresh
  stylesheet/module (cache-bust the `<link>`/`import`, or use a fresh port) when verifying UI in preview.
- **Curation tool deps:** repo-root `.venv` with **Pillow + FastAPI/uvicorn + opencv-python-headless**
  (`pip install -r curation/requirements.txt`), plus `curation/.env` (TMDB key, gitignored).
- **Preview `screenshot`** often times out on the heavy curation page — fall back to `preview_eval`
  DOM/computed-style checks (they're more reliable anyway).

## Run & test (quick — full details in CLAUDE.md)
- **Play:** serve `docs/` (`python -m http.server` inside `docs/`), open `localhost:8000`.
  Views: `?` home · `?play` today · `?play&mode=poser` Poser · `?practice` · `?modes` · `?archive` ·
  `?id=N`.
- **Curation tool:** `.venv/Scripts/python -m uvicorn app:app --app-dir curation --port 8001` (or the
  `curation` entry in `.claude/launch.json`). Needs `curation/.env`.
- **JS tests (repo root):** `node match.test.js game.test.js daily.test.js theme.test.js stats.test.js
  frame.test.js cipher.test.js`.
- **Python tests:** `python curation/{build_rungs,ledger,discover,decoys,manifest,publish,credits_images,
  cipher}.test.py` (pure); `.venv/Scripts/python curation/images.test.py` (Pillow; the `detect_faces`
  test degrades gracefully without cv2).
