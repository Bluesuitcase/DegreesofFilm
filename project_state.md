# Project State — Degrees of Film

> **Running handoff doc. Read this first each session, and keep it updated** in place on `main`
> (no PR needed for this file). Division of labor: `CLAUDE.md` = how the code works (durable);
> **this file = where we are right now** (living). A mirror also lives in auto-memory
> (`degreesoffilm-status.md`).

_Last updated: 2026-07-11 (night). **v1 live, ALL v2 shipped, 18-skill library on `main`** (the
07-11 analysis added `degreesoffilm-worker-ops` + `degreesoffilm-graph-mode-campaign`; DESIGN §6
gained a v2.5 product-polish backlog; the roadmap below was rewritten). **v3 Phase 1 is
DEPLOYED and GATE 1 PASSED (2026-07-11)** — the `/match` Worker is live at
`https://dof-match.bluesuitcase.workers.dev` with all 11 puzzles' answers in KV; contract 9/9,
parity 25/25, p95 = 41 ms, fallback drill green (see the v3 section). **`MATCH_API` is ON since
2026-07-11 ([PR #21], owner-approved, §6 step 2 executed — live-verified both verdict paths from
the Pages origin).** Next v3 milestone: §6 step 5 (stop embedding answers in NEW puzzles), gated on
≥14 days' stability (~07-25) + owner sign-off. **⭐ MOVIE BUFF MODE SHIPPED same day** ([PR #22]
prototype + [PR #23] promotion → `6f199b9`, live-verified): `?play&mode=buff` = Cinephile rules +
film-rung autocomplete from the prebaked static top-5k title index (`curation/title_index.py` →
`docs/title-index.json`, 46 KB gz, ledger coverage asserted 21/21; `docs/buff.js` + buff.test.js
11 cases — 9 JS suites now). The last "coming soon" tile is lit; no server, no key exposure; buff
runs don't touch daily stats. **Buff autocomplete extended to EVERY rung later the same day**
([PR #25] → `f696282`): people suggestions on credit rungs from a **credits-harvested index**
(all 3,663 pool-floor films' top cast + five rung crew jobs → 29,692 names, 212 KB gz, 221/222
rung coverage — person-popularity measured 50% and was rejected; the sole miss is 001's pseudonym
editor). Harvest cached in gitignored `curation/people_harvest_cache.jsonl`; **rebuild the index
occasionally** as films cross the pool floor (re-runs fetch only new films). **⭐ SCORE HISTORY
also SHIPPED 2026-07-11** ([PR #24] → `00fbb0d`):
`?history` lists this device's Cinephile daily results (new `stats.history` per-day map in
recordResult, test-first 17→24, additive/R4-safe — old localStorage blobs gain it on their next
daily); rows link to `?id=N` replays; entry points on home + the end screen. Recording starts at
ship. The stay-static parking lot is now down to ONE item: true degrees-of-separation. **Content: 21 puzzles
(001–021), runway = 8 days** (012–021 pushed `89ccdbb` on 07-11; 012/013 are past-dated 07-09/07-10
archive backfill — see Key decisions; KV answers synced, 21 keys). LOAD THE RELEVANT SKILL FIRST
(v3 → `degreesoffilm-server-move-campaign`; curation → `degreesoffilm-run-and-operate`). Full v2/v3
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
- **v3 — Phase 1 DEPLOYED + GATE 1 PASSED (2026-07-11):** owner chose **Phase 1 only**
  (server-side matching, $0 ceiling); GATE 0 passed 07-04; spike merged via [PR #20] (`41fe9e8`);
  Worker deployed 07-11 and all GATE 1 checks green (evidence below). **§6 step 2 EXECUTED
  2026-07-11: `MATCH_API` = the Worker URL ([PR #21] → `98691bc`, rebase-merged)** — cinephile
  guesses are server-verified in production, with the 2 s local fallback + `?servermatch=0`
  override; rollback = one-line revert to `''`. Live-verified post-deploy: wrong guess → one POST
  /match → exactly `{"correct":false}` + reveal advances; correct guess → `correct:true` +
  canonical + rung advances. The rest of the parking lot stays parked.
- **Content:** 21 puzzles (001–021), dated **2026-06-28 .. 07-18**; **runway = 8 days as of
  2026-07-11** (batch 012–021 pushed `89ccdbb`, validator 8/8 clean, KV synced to 21 keys).
  012/013 are **past-dated backfill** (07-09/07-10 — published during the runway lapse before
  `next_date` was clamped; they never surface as a daily, only in the archive). NOTE: every
  publish/update refreshes `server/answers-bulk.json` (the KV artifact) — push it to KV after each
  batch (see "Keeping KV in sync" in the v3 section).
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

**⭐ v3 GATE 1 — PASSED 2026-07-11 (Worker deployed):**
- **Auth:** owner created the Cloudflare account and a scoped API token (Workers Scripts Edit +
  Workers KV Storage Edit + read scopes) — lives in gitignored `curation/.env` as
  `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID`. No interactive `wrangler login`; every wrangler
  command reads the env vars, so future sessions can deploy non-interactively.
- **Deployed:** `https://dof-match.bluesuitcase.workers.dev` (worker `dof-match`, version
  `a461aba5…`); KV namespace `ANSWERS` = `c6672c863072425f9b94d6b0501e2b03` (id committed in
  `server/wrangler.toml`); all 11 puzzles' answers bulk-loaded. The rate-limit binding WAS accepted
  on the free plan (a 429 was observed under load — it works).
- **TRAP found:** wrangler 4 defaults `kv bulk put` / `kv key list` to the LOCAL simulator — pass
  `--remote` or the write silently goes nowhere (`server/.wrangler/` is that simulator's state, now
  gitignored).
- **GATE 1 evidence (all checks green):** check 1 = flag-off local half verified 07-04, live app.js
  still ships `MATCH_API=''` + all 8 JS suites re-run green 07-11. Check 2 = contract 9/9: wrong
  guess body is EXACTLY `{"correct":false}`, correct → `correct:true`+`canonical`, 400/404/405,
  CORS pinned to the Pages origin and verified by real fetches from a browser AT
  `https://bluesuitcase.github.io` (both verdicts round-tripped). Check 3 = **25/25 parity** vs
  `match.cases.js`, replayed against the live endpoint via a synthetic KV entry `answers:9999`
  (deleted after the run). Check 4 = latency n=99 warm **p50=34 ms / p95=41 ms / max=88 ms**
  (target <300 ms), paced under the 60/min rate limit; fallback drill = local copy of `docs/` with
  `MATCH_API` set, served from a localhost origin the Worker's pinned CORS rejects → the client
  attempted the POST, got the rejection, and local matching accepted the guess in **55 ms** (play
  never blocked).

**Next v3 actions (in order):**
1. **Keeping KV in sync (new operational duty):** after every puzzle publish/update batch, the
   tool refreshes `server/answers-bulk.json` (gitignored); push it with
   `npx wrangler kv bulk put server/answers-bulk.json --namespace-id c6672c863072425f9b94d6b0501e2b03 --remote`
   (from `server/`, env vars from `curation/.env`). Until the flag is ON this is non-urgent (the
   endpoint 404s on unknown puzzles and clients don't call it anyway), but keep the habit.
2. **§6 step 2 — flip `MATCH_API` to the Worker URL (owner decision, player-facing PR).** The
   07-04 handoff recorded "only after GATE 1 is green ≥14 days" — owner may confirm or shorten
   that soak window. The flip itself is a one-line change in `docs/app.js` via branch → PR →
   rebase-merge; rollback is flipping it back.
3. Phases 2–3 stay parked per GATE 0 scope.

## Next phases — the roadmap (rewritten 2026-07-11 night, after the improvement analysis)
0. **Load the relevant skill first.** Curating → `degreesoffilm-run-and-operate`; Worker/KV
   anything → **`degreesoffilm-worker-ops` (NEW)**; degrees-of-separation →
   **`degreesoffilm-graph-mode-campaign` (NEW)**; committing → `degreesoffilm-change-control`.
   The library is now **18 skills**.
1. **Operational (before 07-19): curate the next batch** (runway = 8 days, stocked through
   07-18). Flow per run-and-operate — note its checklist gained **step 14 (KV sync after
   publish — MANDATORY now that server matching is live; `--remote` flag!)** and step 15
   (occasional people-index rebuild). Both curation bugs from 07-11 are fixed; the tool
   pre-targets today when the runway lapses.
2. **v3 §6 step 5 (earliest ~07-25): stop embedding answers in NEW puzzles.** Gates: flag-ON
   stable ≥14 days, zero fallback incidents, owner sign-off, rehearsed rollback. Execution
   runbook: `degreesoffilm-worker-ops` §4. Until then, nothing to do.
3. **Demand signal (passive — check before any Phase 2/3 discussion):** the live Worker's
   Cloudflare metrics ≈ engaged players (~36 calls/game) with zero client telemetry — the
   evidence GATE 0 said was missing for accounts/leaderboard now accrues by itself. Reading
   it: `degreesoffilm-worker-ops` §3. If numbers justify it, reopen Phases 2–3 via the
   server-move campaign (magic-link auth already recorded as the owner preference).
4. **IN PROGRESS — graph mode (degrees-of-separation), started 2026-07-13:**
   - **G0 PASSED** (owner answers): daily challenge · alternate film↔person hops ·
     par-based scoring (BFS shortest = par) · autocomplete on by default · spoilability
     accepted like the dig. **G1 PASSED** same day: `curation/graph_extract.py` (+11 pure
     tests) built the graph from the buff harvest cache + a films-metadata sweep
     (gitignored `films_cache.jsonl`) — 3,663 films / 29,774 people / 63,084 edges; corpus
     630 KB gz (over budget) → **per-challenge subgraphs** (median ~4 KB gz!); pair
     distances: 49% at 2 degrees, 34% at 3, median 4 edges, 2.3% unreachable.
   - **NEXT = Phase G2** (campaign skill §4): pure chain-validator module (docs-shaped,
     test-first) + challenge-generator CLI (pick A→B at target par, emit subgraph with
     decoy padding sized k≥par, filter unreachable pairs) + hand-author challenge 001.
     Then G3 client behind a route, G4 dailyization.
   - **v2.5 product polish** (DESIGN §6, new section): share card 2.0 (per-rung emoji grid),
     daily difficulty label/par, buff dropdown keyboard nav, PWA/offline (⚠ stale-cache
     trap), unified stats view, curation batch-draft flow, KV-sync button in the tool.
   - **Research-frontier items** (`degreesoffilm-research-frontier`): 1a auto-crop
     acceptance logging (a few lines, then data self-accrues during normal curation),
     1b difficulty calibration (feeds the par/label polish item), 1c decoy quality,
     3a offline replay validator (pre-work for any future leaderboard).
5. **Housekeeping (optional):** orphaned worktree dirs (`.claude/worktrees/*`) are
   git-deregistered + gitignored but Windows-locked; delete when their sessions close.
   Skill global mirrors under `~/.claude/skills/` are being kept in sync manually — the
   in-repo copies are the source of truth.

## Key decisions (why things are the way they are)
- **Backdated-publish incident + fix (2026-07-11):** with the runway lapsed, `publish.next_date`
  ("day after the latest puzzle") proposed PAST days, and the schedule strip's "targeted ✓" marker
  could drift from the date input approve actually sends (a stale async next-date overwrite
  clobbered click-set targets) — puzzles 012/013 published to 07-09/07-10 while the strip said
  today was targeted. Fixed in `10436aa`: `next_date` is clamped to today (test-first), and the
  marker is now DERIVED from the date input (`markTargeted`), which also survives reloads. Owner
  chose to keep 012/013 as past-dated archive backfill rather than reschedule (they're playable via
  `?archive`, never a daily). Also fixed same session: the crop tool's grid-blowout layout bug
  (`2d39b0c` — `min-width:0` on grid items; the 14-day strip was forcing the page ~1600px wide).
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
