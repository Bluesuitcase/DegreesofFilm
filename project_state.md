# Project State — Degrees of Film

> **Running handoff doc. Read this first each session, and keep it updated** in place on `main`
> (no PR needed for this file). Division of labor: `CLAUDE.md` = how the code works (durable);
> **this file = where we are right now** (living). A mirror also lives in auto-memory
> (`degreesoffilm-status.md`).

_Last updated: 2026-07-04. **v1 live, ALL v2 shipped, 16-skill library on `main`.** **v3 GATE 0
passed + hosting decided (Cloudflare Workers + KV) + the ENTIRE Phase 1 spike is MERGED to `main`**
([PR #20], flag OFF — zero player-facing change; Worker + client flag + publish artifact +
backfill; all 18 suites green; see the v3 section below). **GATE 1 checks 2–4 are blocked on the
owner creating a Cloudflare account** (+ `wrangler login`) — that is the ONLY thing standing
between the spike and the gate. **Content runway = 5 days** (008–011 published 2026-07-04, stocked
through 07-08 — keep curating to extend it). LOAD THE RELEVANT SKILL FIRST (v3 →
`degreesoffilm-server-move-campaign`; curation → `degreesoffilm-run-and-operate`). Full v2/v3
backlog is in `DESIGN.md` §6._

## ⭐ NEW 2026-07-03 — the skill library (read this if nothing else)
- **`.claude/skills/degreesoffilm-*` — 16 skills + 2 diagnostic scripts, committed + pushed.** Built by
  multi-agent authoring, then a 3-reviewer (factual/doctrine/usability) + fixer pass; every command,
  constant, hash, and worked example was verified against the repo. **Before any task, load the
  matching skill** — the harness lists them by trigger description. Highlights:
  `change-control` (what may land where — READ before committing), `run-and-operate` (the publishing
  runbook), `failure-archaeology` (settled battles — don't re-fight them), `architecture-contract`
  (invariants), `debugging-playbook` (symptom→fix), `diagnostics-and-tooling` (ships
  `scripts/validate_content.py` — run it before/after any content change), `server-move-campaign`
  (the decision-gated v3 plan), `research-frontier` (where to advance SOTA).
- **The build record** is `.claude/skills/_BUILD-STATE.md` (marked BUILD COMPLETE; safe to delete —
  it's not a skill and nothing references it).
- **Four repo issues found + FIXED during the build** (all on `main` now): home-page QUOTES named two
  puzzle films → swapped for unused films (`ee4ec54`, spoiler fix); curation approve message printed
  "accent undefined" → reads `j.theme?.accent` (`44b044d`); TMDB footer wording aligned to TMDB's
  current terms (`c5b86d2`); stale `frame.js` header comment corrected (`d23c52a`). The content
  validator now passes fully clean (8 groups, 0 warnings).
- **Maintenance rule going forward:** when a code change invalidates a fact a skill states, update
  that skill + its Provenance date in the SAME session (this session did exactly that for all four
  fixes). See `docs-and-writing`.

## Status at a glance
- **v1 — COMPLETE + DEPLOYED LIVE:** https://bluesuitcase.github.io/DegreesofFilm/ (GitHub Pages,
  `main` `/docs`; pushes touching `docs/` auto-deploy).
- **v2 — COMPLETE:** every static-v2 feature is built, tested, and on `main` (list below).
- **v3 — Phase 1 spike MERGED, shipped OFF (2026-07-04):** owner chose **Phase 1 only**
  (server-side matching, $0 ceiling); GATE 0 passed; hosting = Cloudflare Workers + KV; the spike
  landed via [PR #20] (`41fe9e8`) with `MATCH_API=''`. **GATE 1 blocked on the owner's Cloudflare
  account.** See the v3 sections below. The rest of the parking lot stays parked.
- **Content:** 11 puzzles (001–011), dated **2026-06-28 .. 07-08**. **Runway = 5 days** (stocked
  through 2026-07-08) after the 2026-07-04 curation batch (008–011 — pushed `bd20e79`; titles omitted
  here, they're future-dated = spoilers). 009 was trimmed to 9 rungs (dropped three unquizzable
  bit-part cast rungs). Keep curating to extend the runway.
- **Tests:** 8 JS suites + 9 Python (pure) + `images` (Pillow) — **all green as of 2026-07-04**
  (JS: match 25, game 51, daily 11, theme 15, stats 17, frame 16, cipher 19, worker 17). Details at
  the bottom.

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

## ⭐ v3 GATE 0 — PASSED 2026-07-04 (server-move campaign scoped)

Per `degreesoffilm-server-move-campaign` Phase 0. (The hosting decision and the Phase 1 spike
both followed the same day — see below.)

**Owner answers (recorded in writing, 2026-07-04):**
1. **Scope: Phase 1 ONLY** — the server-side `/match` endpoint that retires the plaintext-answers
   wart. Phases 2 (accounts/DB) and 3 (leaderboard) are NOT in scope; revisit after GATE 1 has been
   green a while and there's evidence of demand.
2. **Cost ceiling (R6): $0/month — free tiers only.** Kill the phase if it can't stay free.
3. **Auth (future Phase 2, recorded now): magic-link email.** Moot until Phase 2 is ever green-lit.
4. **Stripping answers from PAST puzzle files: NO — R5 stays as-is.** Archive playable forever
   without the server. Only NEW post-cutover puzzles would ever be server-only (§6 step 5, itself
   gated on ≥14 days stability + separate owner sign-off).
- Latency target: **p95 < 300 ms** accepted as the campaign default (owner did not override).

**GATE 0 baselines (re-captured 2026-07-04 — all match the 2026-07-03 capture):**
- 7 JS suites green: match 25, game 34, daily 11, theme 15, stats 17, frame 16, cipher 19.
- Pure-module probe: `true / 'won' / true` — `match.js`/`game.js`/`cipher.js` run in Node unchanged
  (the campaign's key asset: zero-port server reuse).
- Content: 7 puzzles (ids 1–7, 2026-06-28..07-04), 92 images, manifest consistent. Tip `ea5e70c`.

**Kill criteria (abandon/pause Phase 1 if any becomes true):**
- No hosting option runs `/match` within the **$0** ceiling (rate limiting included).
- GATE 1 check 1 can't pass — i.e. static play breaks with the flag off and can't be restored (R1).
- The design ends up needing the TMDB key on the server (R2 violation — redesign or stop).
- The phase stalls **>1 month** mid-migration — roll back (`MATCH_API=''`) rather than leave a
  half-state.
- Note: the project has **no analytics**, so player demand is unknowable; Phase 1 is justified by
  the wart alone, not by demand claims.

**Phase 1 hosting decision — MADE 2026-07-04: Cloudflare Workers + KV.** Vendor facts re-verified
live that day (developers.cloudflare.com pricing/limits pages + 2026 roundups):
- **Workers free: 100k requests/day, 10 ms CPU/invocation.** A legit game ≈ 36 `/match` calls →
  even ~500 players/day ≈ 18k req/day, 5× headroom. `matchGuess` is microseconds — 10 ms is ample.
- **KV free: 100k reads/day, 1k writes/day, 1 GB.** One read per request worst case (answers blob
  keyed `answers:<puzzleId>`; cacheable in isolate memory); writes only at publish (~1/day).
- **Rate limiting:** Workers Rate Limiting binding — `period` must be 10 or 60 s, so the campaign's
  60 req/min/IP is literally `{period: 60, limit: 60}` keyed by IP. Docs state no plan restriction
  (verify at `wrangler deploy`; fallback if gated: in-Worker token bucket — acceptable, the answer
  space was always enumerable so the oracle adds little).
- Isolate model → no cold starts → p95 < 300 ms realistic. Free `*.workers.dev` origin; CORS pinned
  to `https://bluesuitcase.github.io`.
**Rejected:** Vercel Hobby (1M invocations/mo but a **4 h active-CPU/mo cap that hard-pauses the
deployment** when hit — an availability cliff — plus non-commercial-only terms); Netlify free
(125k invocations/mo ≈ 4k/day — thin headroom, plus cold starts); FastAPI/VPS (forfeits the
zero-port `match.js` asset + ~$6/mo breaks the $0 ceiling).
**Owner dependency before the spike can deploy:** a Cloudflare account + `wrangler` login, and a
scoped API token for the publish push (lives in gitignored `curation/.env`, NOT the TMDB key).

**Phase 1 spike — BUILT + MERGED 2026-07-04 ([PR #20] → `41fe9e8`, rebase-merge, branch deleted;
Pages redeploy confirmed, live app.js carries the flag OFF):**
- `server/worker.js` — POST /match, imports `docs/match.js` UNCHANGED; KV answers
  (`answers:<id>`), 5-min isolate cache, CORS pinned to the Pages origin, 60/min/IP rate limit
  (binding optional — degrades to unlimited). `server/wrangler.toml` carries the deploy runbook.
- `worker.test.js` (17) — in-process vs a stub KV env: **full 25-case match.cases.js parity**,
  wrong-guess body is EXACTLY `{correct:false}`, canonical on correct, 400/404/405, CORS, 429.
- `match.cases.js` — the matcher contract extracted as data (match.test.js + worker.test.js both
  consume it; the GATE 1 live parity check will too). match.test.js still 25/25.
- `docs/game.js applyVerdict(correct)` — test-first (game.test.js 34→51 incl. a guess-vs-verdict
  parity run); `guess()` now delegates to it, so both paths are provably the same machine.
- `docs/app.js` — `MATCH_API = ''` (**OFF — shipped state, §6 step 1**), `?servermatch=0` override,
  async `onGuess` with in-flight guard, `resolveGuess()`: POST /match with a 2 s abort → ANY failure
  falls back to local matching. Cinephile-only (poser's trimmed ladder re-indexes rungs).
- `curation/publish.py answers_sink=None` kwarg (publish.test.py 36→39) +
  `curation/push_answers.py` (KV-bulk artifact, `file_sink` upserts) + `curation/backfill_answers.py`
  (rebuild-all CLI; dry-run verified against the real 7 puzzles) + push_answers.test.py (17).
  app.py approve/update wired to the sink. **`server/answers-bulk.json` is GITIGNORED (plaintext).**
- Verified: all 18 suites green (8 JS: 25/51/11/15/17/16/19/17 + 10 Py incl. images 32); content
  validator 8 groups clean; in-browser flag-off playthrough = exact static request set, wrong-guess
  reveal + correct-guess advance both work, `?id=1` archive route fine (GATE 1 check 1 local half).

**Next v3 actions (in order — spike PR already landed):**
1. **OWNER: create a Cloudflare account + `wrangler login`** — the only blocker for GATE 1.
2. Deploy per `server/wrangler.toml` header (KV namespace create → paste id →
   `python curation/backfill_answers.py` → `wrangler kv bulk put` → `wrangler deploy`), set
   `MATCH_API` to the Worker URL locally, run GATE 1 checks 2–4 (no answer material, 25/25 live
   parity via match.cases.js, p95 < 300 ms + fallback drill). Only after GATE 1 is green ≥14 days
   consider §6 step 2 (flip the default on).

## Next steps (pick up here)
0. **Load the relevant skill first** (new this session). For curating puzzles →
   `degreesoffilm-run-and-operate` + `degreesoffilm-validation-and-qa`'s content-QA checklist; for v3
   → `degreesoffilm-server-move-campaign`; before committing anything → `degreesoffilm-change-control`.
1. **v3 GATE 1 — OWNER ACTION: create a Cloudflare account + `wrangler login`**, then deploy per
   `server/wrangler.toml`'s header and run GATE 1 checks 2–4 (see "Next v3 actions" above). This is
   the single thing standing between the merged spike and retiring the plaintext wart.
2. **Operational — keep curating** (**runway = 5 days as of 2026-07-04**, stocked through 07-08).
   Run the crop tool (`.venv/Scripts/python -m uvicorn app:app --app-dir curation --port 8001`,
   needs `curation/.env`): Randomize → face-aware Auto-crop → review the drafted rungs → Approve
   (auto-fills the next free day). **Then run `scripts/validate_content.py` (diagnostics skill)
   before committing**, use a spoiler-safe commit message ("Add puzzle NNN (YYYY-MM-DD)" — no film
   title until the date passes), and push `docs/`. NOTE from the 07-04 batch: check the QA flags
   below (bit-part rungs; don't let the editor touch today's/past puzzles).
3. **v3 parking lot (everything else — out of the owner's chosen scope for now).** Two tracks
   (full list in DESIGN.md §6, research angles in `degreesoffilm-research-frontier`):
   - **Stay-static (no backend):** Score History (client-only), **Movie Buff** (prebaked popular-title
     index — the frontier skill found this is static-possible, NOT strictly server-gated), true
     degrees-of-separation (prebaked film/person graph).
   - **Server-move track (needs backend, in campaign order):** server-side matching (Phase 1 —
     spike DONE, gate pending) → **Accounts + DB** (Phase 2) → **Leaderboard** (Phase 3; sortable by
     mode/user/total, asterisk when a total is mostly easy-mode) + cross-device stats. Also:
     commercial TMDB agreement (only if it scales/monetizes).
3. **Housekeeping (optional):** two orphaned worktree dirs (`.claude/worktrees/adoring-blackburn-*`,
   `loving-maxwell-*`) are git-deregistered + gitignored but Windows-locked; delete them once the
   sessions holding them close (`rm -rf .claude/worktrees/*`). Also consider copying the skills to the
   user-global `~/.claude/skills/` if you want them in every project's Customize→Skills (treat the
   in-repo copy as source of truth).

## Key decisions (why things are the way they are)
- **v3 scope = Phase 1 only, $0 ceiling, R5 intact (2026-07-04, GATE 0):** full owner answers +
  kill criteria in the GATE 0 section above. **Rejected:** Phases 2–3 now (no demand evidence —
  the project has no analytics), Vercel/Netlify/VPS hosting (reasons recorded above).
- **007 mid-day re-crop REVERTED (2026-07-04):** the curation editor re-cropped puzzle 007 (that
  day's LIVE daily) as a side effect of an edit-session; owner chose revert per IMMUTABLE PAST —
  players keep the frame they'd already seen. **Rule confirmed: the tool happily edits any id;
  the discipline is ours.** Watch for this whenever the editor was opened on a filled past/today slot.
- **009 trimmed to 9 rungs before publish (2026-07-04):** dropped three unquizzable bit-part cast
  rungs (umpire/physio/security guard — a three-hander's billing order falls off a cliff). Quality
  rule of thumb: if nobody could be quizzed on the credit, cut the rung. Trimming via `/api/update`
  leaves **orphaned `NNN-rK.jpg` files** — delete the ones no longer referenced before staging.
- **Skill library is project-scoped (2026-07-03):** it lives in the repo at `.claude/skills/`, NOT the
  user-global `~/.claude/skills/` — so it travels with the repo and every session/collaborator here
  gets it. **Why:** the skills describe *this* project; they should be versioned with it. Trade-off:
  they don't show in the global Customize→Skills UI unless also copied there (deferred).
- **Skills cite past incidents by hash + puzzle number, never film title, until the puzzle date has
  passed (2026-07-03):** the library is public once committed, so naming a future-dated puzzle's film
  in a skill would itself be a spoiler leak. This rule is written into `failure-archaeology` and
  `docs-and-writing`; the doctrine reviewer caught the library violating it and the fixer scrubbed it.
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
- **Shipping 2026-07-04:** the v3 spike went **branch → PR #20 → rebase-merge** (player-facing
  docs/ changes, per change-control); the puzzle batch + doc updates went **direct to `main`**
  (content/docs precedent). All pushed; tip at session end: see `git log`.
- **Live-site cache after a content push:** the `bluesuitcase.github.io` Fastly edge can serve a
  stale `manifest.json` for a while even after the Pages build succeeds. **Harmless by design** —
  the client's fetch is date-keyed (`?d=<todayISO>`), so the next day's request is a fresh cache
  key. Verify pushes against `raw.githubusercontent.com` (bypasses the edge), not the Pages URL.
- **Reusable project templates (2026-07-04):** a starter kit distilled from this project's doc
  system lives at `C:\Claude\_templates\` (CLAUDE.md + project_state.md + SETUP.md) — machine-local,
  not in this repo.
- **Shipping this session (2026-07-03):** the skill library + all four fixes landed **direct to
  `main`** per the user's choice (the library/docs are curation-adjacent; the two player-facing fixes
  — QUOTES, footer — were small and pre-verified). **Linear history is required** (the repo has no
  merge commits): when a parallel worktree session had independently pushed the same QUOTES fix,
  integration was done by **`git rebase origin/main`** (which auto-dropped the duplicate cherry-pick),
  NOT `git merge`. Confirm landing mode per change; player-facing work still normally goes
  branch → PR → rebase-merge (see `degreesoffilm-change-control`).
- **Parallel worktree sessions:** the two "fix" chips ran in `.claude/worktrees/*` and could push to
  `main` independently — expect possible divergence; `git fetch` + rebase before pushing.
- **Shipping earlier:** curation-only changes (no `docs/` change) were committed direct to `main`;
  earlier player-facing work went via branch → PR → rebase-merge → delete branch.
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
- **JS tests (repo root):** `for t in match game daily theme stats frame cipher worker; do node
  $t.test.js; done` (matcher case table lives in `match.cases.js` — add cases there).
- **Python tests:** `python curation/{build_rungs,ledger,discover,decoys,manifest,publish,credits_images,
  cipher,push_answers}.test.py` (pure); `.venv/Scripts/python curation/images.test.py` (Pillow; the
  `detect_faces` test degrades gracefully without cv2).
