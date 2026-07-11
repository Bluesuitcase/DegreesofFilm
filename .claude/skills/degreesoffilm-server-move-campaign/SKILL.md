---
name: degreesoffilm-server-move-campaign
description: >
  The executable, decision-gated campaign for the v3 "server move" — the project's
  owner-designated hardest live problem. Load this when: starting v3 in any form;
  implementing server-side answer matching; retiring the plaintext/obfuscation wart
  ("answers readable in devtools", "the XOR cipher isn't security"); adding accounts,
  a database, or cross-device stats; building the leaderboard; unblocking Movie Buff
  mode's backend dependency; anyone says "move off static", "add a backend", or
  "validate scores server-side"; or someone proposes hashing/encrypting answers
  client-side (a fenced wrong path — see inside before agreeing). Status as of
  2026-07-11: Phase 1 DONE — the /match Worker is DEPLOYED (Cloudflare Workers + KV)
  and GATE 1 PASSED; the client default (MATCH_API) is still OFF, and flipping it on
  (§6 step 2) is the next owner-gated step; Phases 2–3 remain CANDIDATE and out of scope.
---

# Degrees of Film — the v3 server-move campaign

An executable campaign, not a vision doc. Numbered phases, each with entry criteria,
exact steps, expected observations, branch instructions ("if you see X instead → Y"),
and a **numeric exit gate**. Do not start phase N+1 until phase N's gate is green and
the promotion has gone through **degreesoffilm-change-control**.

**Status legend used throughout: everything below is CANDIDATE (unbuilt) or OPEN
(undecided) as of 2026-07-03.** When a phase ships, edit this file: mark it DONE with
the date and the evidence (gate numbers observed), same session as the change lands.

## 1. Campaign charter

### The problem (three heads, one root)

1. **Answers are enumerable client-side.** Every puzzle ships its accepted answers
   in static JSON under light XOR+base64 obfuscation (`docs/cipher.js`, key
   `'degrees-of-film'`, sentinel U+0001), whose own comments say "NOT security — the
   key ships to the client" (lines 3–5). DESIGN.md §6 names **server-side matching**
   as "the clean fix for the plaintext wart".
2. **No cross-device stats.** Stats live only in localStorage under `'dof-stats-v1'`
   (`docs/stats.js` line 4). New browser = blank history.
3. **No leaderboard is possible.** Depth/score are computed in the player's browser
   by `docs/game.js`; any client can claim any number. A leaderboard without
   server-validated runs is unvalidatable noise (fenced path W5).

The root: v1/v2 deliberately have **no backend for players** (DESIGN.md §2). v3 adds
one — carefully, without breaking what works.

### Hard requirements (owner constraints — violating any one fails the campaign)

| # | Requirement | How it's checked |
|---|---|---|
| R1 | **Static play keeps working end-to-end at every phase.** A player with no account, no flags, on the live GitHub Pages site, plays today's daily and the archive exactly as today. | Every phase gate includes a no-flag playthrough. |
| R2 | **The TMDB key never reaches a player — and never reaches the new server either unless a phase explicitly needs it (none below do).** The key stays in gitignored `curation/.env` on the owner's machine. | `grep -ri "TMDB_API_KEY\|api_key" docs/` stays empty; server repo/config audited per phase. |
| R3 | **The archive keeps working.** `?archive` and `?id=N` replay every past puzzle forever. | Gate playthroughs include an archived puzzle. |
| R4 | **Players' localStorage stats are never destroyed.** `'dof-stats-v1'` is never deleted or overwritten with less data. Migration is import, never move. | Phase 2 gate asserts the key survives login+sync byte-comparably. |
| R5 | **IMMUTABLE PAST.** Never delete or rewrite a published puzzle file dated ≤ today. Old puzzle JSON keeps its (obfuscated) answers on disk forever; the client supports both puzzle shapes indefinitely. | §6 migration protocol; any exception needs explicit owner sign-off recorded in project_state.md. |
| R6 | **Hobby-scale cost ceiling: ~$0–5/month.** ASSUMPTION as of 2026-07-03 — confirm the exact number with the owner in Phase 0 before choosing vendors. | Phase 0 step 3. |

### The repo's key asset (verified 2026-07-03 — feature this in every design decision)

`docs/match.js` **imports nothing** (zero `import` statements — read the file).
`docs/game.js` imports **only** `./match.js` (line 3). `docs/cipher.js` imports
nothing and uses only standard globals (`TextEncoder`, `atob`/`btoa`). All three are
pure ES modules with zero DOM. **Verified by execution** — this exact probe ran green
from the repo root on 2026-07-03:

```
node -e "import('./docs/game.js').then(async ({ Game }) => {
  const { matchGuess } = await import('./docs/match.js');
  const { decode } = await import('./docs/cipher.js');
  console.log(matchGuess('bardem', ['Javier Bardem']));            // true
  const g = new Game({ rungs: [{ answers: ['No Country for Old Men'] }] });
  console.log(g.guess('no country for old men').result);           // 'won'
  const p = JSON.parse((await import('node:fs')).readFileSync('docs/puzzles/004.json','utf8'));
  console.log(decode(p.rungs[0].answers[0]).length > 0); });"      // true
```

Consequence: **the SAME matcher and the SAME game rules can run server-side in Node
with zero porting.** Server and client can never disagree on matching semantics, and
Phase 3's replay validator is the same `Game` class re-running a transcript. Any
hosting choice that forfeits this (a Python or Go rewrite of `match.js`) must carry
the burden of proving parity forever — rank it accordingly.

### Baseline facts (captured 2026-07-03 — re-capture at Phase 0, commands given)

| Fact | Value as of 2026-07-03 | Re-capture command (repo root) |
|---|---|---|
| Published puzzles | 7 (ids 1–7, dates 2026-06-28..2026-07-04) + manifest | `node -e "const m=require('./docs/puzzles/manifest.json');console.log(m.length, m.map(e=>e.date))"` |
| Puzzle images | 92 files | `ls docs/puzzles/images | wc -l` |
| Cipher scheme | XOR key `'degrees-of-film'`, sentinel U+0001, base64, idempotent, plaintext-passthrough | read `docs/cipher.js` lines 7–8; `node cipher.test.js` (19 pass) |
| Stats schema | `{played, wins, bestDepth, currentStreak, maxStreak, lastDate, lastDepth, histogram}` under `'dof-stats-v1'` | read `docs/stats.js` lines 4–13 |
| Matcher contract | 25 cases, all pass | `node match.test.js` |
| Game rules suite | 34 cases, all pass (51 since 2026-07-04 — applyVerdict block added) | `node game.test.js` |
| Where a /match call slots | `docs/app.js` `onGuess()` (line ~334) calls `game.guess(v)` (line ~338); puzzle decode at `decodeRungs(puzzle.rungs)` (line ~83) | `grep -n "game.guess\|decodeRungs" docs/app.js` |
| What publishing writes | `curation/publish.py publish()`: puzzle JSON (answers encoded, line 99) + ledger append + manifest upsert | read `curation/publish.py` lines 103–133 |

## 2. Phase 0 — decision & baseline  [DONE 2026-07-04 — GATE 0 PASSED]

Evidence: all baselines re-captured and matched (suites 25/34/11/15/17/16/19, probe
`true / 'won' / true`, 7 puzzles, 92 images); owner answers + kill criteria recorded
in project_state.md (**Phase 1 only, $0 ceiling, magic-link if Phase 2 ever revives,
R5 intact**); hosting decision = **Cloudflare Workers + KV** (vendor facts
re-verified live that day, rejected alternatives recorded).

**Entry criteria:** owner has said "start v3" (or a v3 feature). Nothing else.

**Steps:**

1. Re-capture every baseline in the table above; record values + date in
   `project_state.md`. All 7 JS suites must be green first — if any fails, STOP and
   fix mainline (→ degreesoffilm-debugging-playbook).
2. Re-run the pure-module probe (§1). Expected: `true / 'won' / true`. **If you see
   an import error instead** → the layering law is broken; go to
   degreesoffilm-architecture-contract first — the campaign's core asset is gone
   until layering is restored.
3. Confirm with the owner, in writing (project_state.md): the **cost ceiling** (R6's
   ~$0–5/mo is an assumption); **auth preference** for Phase 2 (magic-link vs OAuth);
   whether stripping answers from PAST puzzle files is ever acceptable (default: NO —
   R5; §6 step 5); which phases are wanted — Phase 1 alone retires the wart;
   Phases 2–3 are separable.
4. Write the **kill criteria** into project_state.md. Default kill list — abandon or
   pause v3 if any becomes true: no hosting option meets the cost ceiling; any phase
   cannot pass R1 (static play breaks and can't be restored); the design ends up
   needing the TMDB key on the server (violates R2 — redesign or stop); a phase
   stalls >1 month mid-migration (roll it back rather than leave a half-state); for
   Phases 2–3: no evidence of player demand — NOTE the project has **no analytics**
   (nothing in `docs/` phones home), so player count is unknowable today; the
   leaderboard's value is an assumption — say so to the owner.

**Exit gate (GATE 0):** baselines recorded; owner answers to all four questions
written in project_state.md; kill criteria written. All 7 suites green
(25/34/11/15/17/16/19 or higher). No code written yet.

## 3. Phase 1 — server-side matching spike  [DONE 2026-07-11 — DEPLOYED, GATE 1 PASSED]

Built on branch `v3-phase1-server-match`: `server/worker.js` (+ `wrangler.toml`),
`worker.test.js` (17 cases incl. the full 25-case parity run in-process),
`Game.applyVerdict` (test-first, game.test.js 34→51), `MATCH_API` + 2 s fallback in
app.js, `publish.py answers_sink` (publish.test.py 36→39), `curation/push_answers.py`
+ `backfill_answers.py` (+17-case suite), the matcher case table extracted to
`match.cases.js` (shared client/server). `MATCH_API = ''` — ships OFF (§6 step 1).
GATE 1 check 1's local half verified in-browser 2026-07-04. **DEPLOYED 2026-07-11**
(auth = a scoped API token in gitignored `curation/.env`: `CLOUDFLARE_API_TOKEN` +
`CLOUDFLARE_ACCOUNT_ID` — no interactive `wrangler login` needed): Worker at
`https://dof-match.bluesuitcase.workers.dev`, KV namespace ANSWERS
`c6672c863072425f9b94d6b0501e2b03`, all 11 puzzles' answers bulk-loaded. TRAP:
wrangler 4 defaults `kv bulk put` to the LOCAL simulator — pass `--remote`.
**GATE 1 checks 2–4 PASSED 2026-07-11:** contract 9/9 (wrong guess is EXACTLY
`{"correct":false}`; 400/404/405; CORS pinned, also verified in-browser from the
live Pages origin); parity **25/25** vs `match.cases.js` (replayed via a synthetic
KV puzzle `answers:9999`, deleted afterwards); latency n=99 warm **p50=34 ms,
p95=41 ms, max=88 ms** (target <300 ms); one 429 during the run = the rate-limit
binding works on the free plan; fallback drill: CORS-blocked origin → guess
accepted by local matching in **55 ms**. `MATCH_API` remains `''` (OFF) — flipping
the default on is §6 step 2, a separate owner-gated, player-facing PR.

The smallest slice that retires the plaintext wart. No accounts, no DB, no writes —
one stateless endpoint.

### 3.1 The endpoint contract

```
POST /match
Request:  { "puzzleId": 4, "rungIndex": 1, "guess": "bale" }
Response: { "correct": true,  "canonical": "Christian Bale" }   // canonical ONLY when correct
          { "correct": false }                                   // NEVER canonical, NEVER answers
```

- Answers live **only server-side** (a private artifact — see 3.4). The response for
  a wrong guess contains no answer material of any kind.
- `canonical` on a correct guess is deliberate and safe: the player just proved they
  know it; the client may use it for display.
- The server imports `docs/match.js` **unchanged** and calls
  `matchGuess(guess, answers[puzzleId][rungIndex])`.
- Stateless. No cookies, no user identity in Phase 1.
- Abuse surface: /match is a guess oracle. The answer space was always enumerable
  (see W1), so the oracle adds little, but rate-limit anyway: legitimate play needs
  ≤ 3 guesses/rung × ~12 rungs ≈ 36 calls/game. A limit of **60 req/min/IP** is
  generous for humans and hostile to scripts. (Mechanism per hosting option below.)

### 3.2 The client gate (feature flag)

This project has **no flag system** — configuration is module constants and query
params (see degreesoffilm-config-and-flags). Follow that convention:

- One module constant in `docs/app.js`: `const MATCH_API = '';` — empty = OFF
  (today's behavior). Query-param override for testing before flipping the default:
  `?servermatch=1` forces on, `?servermatch=0` forces off.
- **Fallback is mandatory (availability gate):** when on, `onGuess()` tries
  `POST /match` with a **2000 ms timeout**; on timeout/network error/non-200 it
  falls back to local `game.guess(text)` against the decoded answers — which still
  ship in the static JSON until §6 step 5. A player must never be unable to play
  because the endpoint is down.
- Register the new axis in degreesoffilm-config-and-flags' catalog when it lands.

Implementation note: `game.js` must NOT gain a network call (layering law —
degreesoffilm-architecture-contract). Clean shape: `app.js` asks the server
"correct?" then drives the existing `Game` state machine with the verdict (e.g. a
test-first `Game.applyVerdict(correct)` method, or `game.guess(canonical)` on
server-confirmed correct — decide via change control; add game.test.js cases FIRST).

### 3.3 Hosting menu — RANKED, with theory obligations

Vendor specifics below (free tiers, cold starts, product names) are **as of training
data (early 2026) — verify at execution time**; the gate tests observable outcomes,
so a drifted vendor fact changes your choice, not the campaign.

**Option A — Cloudflare Workers (or Pages Functions) + KV.  RANK 1.**
- *Why first:* JS runtime runs `match.js` unchanged (Workers supports ES modules,
  `TextEncoder` — verify at execution via GATE 1 check 3); isolate model ≈ no cold
  start; free tier historically ~100k req/day (verify); KV fits per-puzzle answer
  blobs.
- *Obligations:* answers in KV keyed `answers:<puzzleId>`; publish pushes via
  Wrangler/API (3.4). CORS: GitHub Pages (`bluesuitcase.github.io`) is a different
  origin → `Access-Control-Allow-Origin` pinned to the Pages origin (not `*`) +
  preflight `OPTIONS`. Rate limiting: Cloudflare rules or a KV/Durable-Object
  counter (verify free-tier coverage). Cost: $0 expected at hobby traffic (verify).
**Option B — small FastAPI service (Fly.io / cheap VPS).  RANK 3.**
- *Why listed:* the team already runs FastAPI (`curation/app.py`) — familiarity.
- *Why ranked below A/C:* **it forfeits the key asset.** Python can't import
  `match.js`; you'd port the matcher and prove parity forever (every future matcher
  change lands twice, with a cross-language vector like the cipher's — see
  degreesoffilm-validation-and-qa). Also: Fly free machines auto-stop → cold starts
  of seconds (verify); a VPS is ~$4–6/mo, at the ceiling. CORS: CORSMiddleware
  pinned to the Pages origin. Answers: JSON baked into the image or a volume. Rate
  limiting: slowapi or nginx (self-managed).
**Option C — Vercel / Netlify serverless functions.  RANK 2.**
- *Why second:* Node runtime → `match.js` unchanged; simple deploy; free tiers
  historically generous for this traffic (verify limits and whether functions sleep).
- *Obligations:* cold starts of 100s of ms are normal (still inside the 300 ms p95
  only when warm — measure honestly; if p95 fails on cold starts, that's a real gate
  failure for C). Answers: bundle a private `answers/` dir into the function (NOT in
  any public/static dir — verify the platform doesn't serve it). CORS: separate
  origin → same pinned-origin obligation. Rate limiting: platform add-ons or an
  in-function token bucket (weak across instances — note it).
**Option D — keep the static site as-is + any separate API origin.  (posture, not a vendor)**
- All of A–C are deployments of D: the static site stays on GitHub Pages untouched,
  the API lives elsewhere. The alternative — moving the whole site to the API's host
  to get same-origin and drop CORS — is a bigger change (deploy pipeline, DNS) for a
  small win; keep Pages unless CORS proves painful. Obligation either way: the API
  origin is a second thing that can be down, hence the mandatory fallback (3.2).

**Decision step:** pick one option, write the choice + rejected alternatives + the
verified-today vendor facts into project_state.md, route through
degreesoffilm-change-control (player-facing code changes ship via PR).

### 3.4 The publishing pipeline change

`curation/publish.py publish()` currently writes three things: puzzle JSON (answers
encoded via `cipher.encode_rungs`, line 99), ledger append, manifest upsert
(lines 103–133). Phase 1 adds a **fourth artifact**: the new puzzle's plaintext
answers, pushed to the server's private store (KV push, private-repo file, or deploy
bundle — per the option chosen). Rules:

- Curation **stays on the owner's machine** (W6). The artifact step pushes FROM
  curation TO the server store, authenticated by a deploy credential that is NOT the
  TMDB key and also lives in gitignored `curation/.env`.
- Derive the artifact from the same `rungs` list passed to `assemble_puzzle`; add
  the step behind a keyword arg (e.g. `answers_sink=None`, default off) so
  `publish.test.py` (36 cases) passes unchanged and the new behavior gets its own
  temp-dir tests. Test-first.
- Write a **backfill CLI** (pattern: `curation/backfill_credit_images.py`) that
  pushes answers for all existing puzzles by decoding them with `curation/cipher.py`
  — needed once at cutover, and again in any rollback.

### 3.5 GATE 1 (all four numeric checks, in order)

1. **Flag off = today.** With `MATCH_API = ''`: all 7 JS suites green, counts ≥
   baseline; devtools Network on `?play` and on `?id=1` (archive) shows exactly
   today's request set (manifest + puzzle JSON + images; **zero** calls to the API
   origin); a scripted playthrough of puzzle 001 reproduces the same depth/score as
   against live. Any API-origin request with the flag off → gate failed; the
   constant isn't gating the code path.
2. **Flag on = no answer material.** With `?servermatch=1`, play a full game with
   devtools open. Expected: every guess produces one `POST /match`; **zero** response
   bodies contain answers, decoys-marked-correct, or obfuscated blobs; wrong-guess
   responses are exactly `{"correct":false}`. `canonical` on a wrong guess → server
   bug, fix first. (The puzzle JSON still carries obfuscated answers at this stage —
   expected and correct until §6 step 5.)
3. **Parity 25/25.** Replay the entire `match.test.js` table against the live
   endpoint (for each case, POST the guess against a rung holding that case's answer
   list; compare booleans). Expected **25/25**. N<25 on option B → the porting-
   divergence risk materializing; fix the port or switch to a Node host. N<25 on a
   Node host → the server isn't actually running `docs/match.js` unchanged; find the
   fork.
4. **Latency + fallback drill.** ≥100 timed requests from a residential connection:
   **p95 < 300 ms** (TARGET — confirm with the owner at Phase 0). Measure warm and
   cold (wait 15+ min) separately. Then block the API origin (devtools request
   blocking) and guess again — expected: answer accepted locally within ~2 s (the
   timeout), play continues. Play hangs or errors → fallback broken; gate failed.

**Rollback:** flip `MATCH_API` back to `''` (one-line PR). Static play was never
dependent on the server. Leave the endpoint up or tear it down freely.

## 4. Phase 2 — accounts + DB  [CANDIDATE]

**Entry criteria:** GATE 1 green ≥14 days with no fallback-path incidents; owner
confirmed they want cross-device stats/leaderboard (not just the wart fix).

### 4.1 Menu (vendor facts as of training data — verify at execution)

| Option | For | Against / obligations |
|---|---|---|
| **Supabase** (RANK 1) | Postgres + built-in auth (magic-link AND OAuth) + row-level security; free tier historically fits hobby scale (verify) | A second vendor; RLS policies must be written and tested (a missing policy = public table) |
| **Firebase** (RANK 2) | Mature auth; generous free tier (verify) | Firestore's model fits documents, not the relational leaderboard queries of Phase 3; Google account coupling |
| **Self-hosted Postgres** (RANK 3) | Full control; pairs with option B's VPS | You own backups, upgrades, auth implementation — the most engineer-hours for the same gate |

Auth flow: default **magic-link** (no passwords stored, minimal PII — one email),
offer OAuth only if the owner asked for it in Phase 0.

**Data minimalism (privacy note, and a spec obligation):** store exactly one row per
user: `user_id, email, stats_json` where `stats_json` is the `'dof-stats-v1'` shape
(`docs/stats.js` `defaultStats()`), plus Phase 3's per-day results table later.
Nothing else — no guesses, no IPs beyond what the platform logs, no analytics
smuggled in. The stats schema **is the contract**: the server stores what the client
already computes; `recordResult` (pure, `docs/stats.js` line 22) remains the single
place streak math lives.

### 4.2 localStorage migration protocol (R4 — the never-destroy rule)

1. Anonymous players: **zero change** — no DB-origin calls, localStorage exactly as
   today.
2. First login, **empty** server record: read `'dof-stats-v1'`, upload it as the
   server record. Do NOT delete or modify the local copy.
3. Login where **both** exist: keep the server record; never merge automatically
   (summing `played` double-counts; field-wise max lies about `histogram`). An
   explicit one-time "import this device's history" only if the owner asks.
4. localStorage keeps being written on every run even when logged in (offline
   resilience). Server sync is additive.

### 4.3 GATE 2 (numeric/observable)

1. **Round-trip:** play a daily on browser A (logged in); open browser B (different
   profile/device), log in — identical `played/wins/bestDepth/streak` figures within
   **one** page load. Blanks on B → sync read broken.
2. **Anonymous unaffected:** fresh profile, no login, full daily with devtools open:
   **zero** requests to the DB/auth origin, and afterwards
   `JSON.parse(localStorage.getItem('dof-stats-v1'))` equals
   `recordResult(before, {date, depth, won})` computed by hand, field for field. Any
   DB-origin request while anonymous fails the gate.
3. **Never destroyed:** snapshot `'dof-stats-v1'` before login; after login + sync +
   one game, the key still exists and `played` has not decreased. Key gone → R4
   violated; gate failed; revert.

**Rollback:** accounts are additive. Disable the login UI (one constant), leave the
DB dormant. Local play never depended on it.

## 5. Phase 3 — leaderboard + integrity  [CANDIDATE]

**Entry criteria:** GATE 2 green; Phase 1 endpoint in production (a leaderboard
without server matching is fenced — W5).

### 5.1 The integrity reality

Depth is client-computed (`docs/game.js` runs in the player's browser). Therefore a
leaderboard entry is a **claim**, and the server must be able to re-derive it. Design:

**Run transcript** (submitted once at game end, logged-in users only):

```json
{ "puzzleId": 6, "date": "2026-07-03", "mode": "cinephile",
  "events": [
    { "rung": 0, "action": "guess", "text": "heat" },
    { "rung": 1, "action": "help" },
    { "rung": 1, "action": "guess", "text": "Al Pacino" },
    { "rung": 2, "action": "skip" } ] }
```

**Replay validator (the key-asset payoff):** the server constructs
`new Game(puzzle, { mode })` from the SAME `docs/game.js`, feeds the events in order
(`guess(text)` / `skip()` / `useHelp()` then `guess(text)`), and reads
`depth/score/status` off the finished object. The client doesn't even send claimed
numbers — it sends the transcript; the server computes the truth. Phase 1's answer
artifact supplies `rungs[].answers` for the replay. Zero porting; forging a result
requires forging a transcript that actually plays that well, i.e. knowing the
answers, i.e. playing well.
- **One submission per (user, date, mode):** DB unique constraint — second POST 409.
- **Rate limit** submissions (e.g. 10/day/user — covers modes + retries).
- **The asterisk rule is a spec obligation** (DESIGN.md §6, Leaderboard bullet):
  totals sortable by mode/user/total; a total gets an asterisk when the **majority**
  came from the easier modes (Movie Buff / Poser): `easy_points > 0.5 * total_points`
  at query time, asterisk shown in UI and share text.
- Practice runs and archived replays are **not** submittable (mirrors the client
  rule that they don't touch daily stats — `docs/app.js` showEnd guards).

### 5.2 GATE 3 (numeric/observable)

1. **Forged transcript rejected:** swap a legit transcript's correct guess text for
   gibberish — expected: the server stores the REPLAYED (lower) depth, never a
   claimed one. A transcript with an impossible event sequence (guess after
   strikeout, 4th attempt on a rung, help with 0 decoys) returns **HTTP 4xx** and
   stores nothing. Test all three tamper shapes.
2. **Legit accepted:** an honest transcript from a real playthrough round-trips:
   stored depth/score equal the client's displayed depth/score exactly.
3. **Cohort ranks correctly:** submit a synthetic cohort of ≥5 users with
   hand-computed expected scores (reuse game.test.js's scripted playthroughs as the
   generator). Expected: the leaderboard endpoint returns them in exact expected
   order, and the one cohort member with >50% Poser points carries the asterisk;
   the one with exactly 50% does NOT (majority means strictly more than half).
4. **Duplicate rejected:** the same user re-POSTs the same day/mode — HTTP 409, row
   count unchanged.

**Rollback:** hide the board UI (constant), stop accepting submissions (410). Stats
and matching are unaffected.

## 6. Migration & compatibility protocol (ordered, least-reversible LAST)

| Step | Action | Reversal |
|---|---|---|
| 1 | Ship /match behind `MATCH_API=''` (off) | delete the dead code |
| 2 | Flip the default on (fallback still coded) | flip back — one line |
| 3 | Accounts/DB (additive) | disable login UI |
| 4 | Leaderboard (additive) | hide board, 410 submissions |
| 5 | **FINAL: stop embedding answers in NEW puzzle files** (`publish.py` writes `answers: []` or omits it for future puzzles; server artifact becomes the only home) | re-enable embedding + re-publish affected future puzzles (backfill CLI, 3.4) |

Step 5 gates — ALL required before executing:
- server matching **stable ≥14 days**: measured as zero client-fallback activations
  you know of and endpoint error rate <0.1% over the window (log it — you can't gate
  on a number you don't collect);
- **owner sign-off** recorded in project_state.md;
- a written **rollback plan** (the re-publish path above, rehearsed once on a
  future-dated puzzle).

Consequences to accept explicitly:
- **Past puzzle files keep their obfuscated answers forever (R5).** Pre-cutover
  puzzles are matched locally forever; the client supports both shapes
  (answers-present → local fallback allowed; answers-absent → server required, and
  if the server is down a post-cutover puzzle is unplayable — the one place R1
  softens, which is exactly why step 5 is last and gated). Stripping answers from
  past files is an R5 exception requiring explicit owner sign-off — default: DON'T.
- Old cached clients keep working through step 4 (their JSON is unchanged); step 5
  only affects puzzles published after it, by which time the flagged client has been
  live ≥14 days.

## 7. FENCED WRONG PATHS — do not walk these; derivations included

**W1 — Client-side answer hashing ("just SHA-256 the answers").**
Derivation: hashing protects a secret only when the preimage space is large and
private. Here it is small and public: the film pool is TMDB films with
`vote_count≥800 AND vote_average≥6.5` (DESIGN.md §1) — a few thousand titles anyone
can list from public TMDB — and every credit answer is on the film's public credits
page. Attack: fetch the candidate pool, run the SHIPPED `normalize()` (in
`docs/match.js`, delivered to every client) over each candidate, hash, compare —
minutes of offline work, total break. Independent second killer: fuzzy matching
cannot run on hashes — `levenshtein(g, a)` needs plaintext `a` — so you'd hash every
typo variant (combinatorial, still enumerable) or delete typo tolerance (destroys
the fairness contract, `match.test.js`). Verdict: strictly worse than the current
cipher. The only real fix is the answers not being present — Phase 1.

**W2 — Hardening the XOR cipher (AES, per-puzzle keys, WASM obfuscation).**
Derivation: the client must decode to play, so the key and decoder ship to the
attacker by definition — `docs/cipher.js` lines 3–5 say exactly this. And even an
unbreakable cipher falls to W1's enumeration: the attacker never decrypts, only
tests candidates against the shipped matcher. An arms race with no win condition.
The cipher's job is "not readable at a glance"; it already does that.

**W3 — A naive TMDB proxy for Movie Buff autocomplete.**
Derivation: Movie Buff wants title autocomplete over ALL of TMDB (DESIGN.md §6).
Proxying every keystroke means: (a) an open proxy anyone can script against your
quota/key standing — abuse cost scales with attacker enthusiasm, not player count;
(b) per-keystroke round-trip latency on the hot input path; (c) key-adjacent risk —
one proxy bug (SSRF, permissive routes, verbose errors) and R2 is in question. The
static alternative — a prebaked top-N title index, no key, no server — is designed
in **degreesoffilm-research-frontier**; route Movie Buff there first, and only fall
back to a rate-limited, allowlisted, cached proxy if the index measurably can't work.

**W4 — Rewriting the client in a framework "while we're at it".**
Derivation: the vanilla client is load-bearing three times over: (1) the pure
modules ARE this campaign's server code — a rewrite that entangles rules with
components forfeits Phases 1 and 3's zero-port replay; (2) no build step means
GATE 1's "flag off = today's exact request set" is actually checkable; (3) the Node
suites import the shipped files directly. No gate here needs a framework. Any
rewrite proposal is its own change-control item, not a rider on v3.

**W5 — Building the leaderboard BEFORE server-side matching/validation.**
Derivation: depth is computed by `docs/game.js` in the player's browser; a board fed
by client-claimed numbers accepts `{depth: 99}` from anyone with curl. You'd launch
it, it gets poisoned, and you build Phases 1+3 anyway — now with a public trust
problem and a table of garbage to migrate. The dependency is real, not procedural:
the replay validator (5.1) cannot verify a transcript without server-side answers,
which is Phase 1's artifact. Order: matching → accounts → board. Always.

**W6 — Putting the curation tool on the server.**
Derivation: curation is deliberately private — the one zone holding the TMDB key
(DESIGN.md §2: "the API key never leaves your machine"). The server needs only
published artifacts; nothing in Phases 1–3 needs TMDB at all. Hosting curation
online adds an admin auth surface, key exfiltration risk, and uptime obligations for
zero player value. The key-holder stays on the owner's machine; publishing PUSHES
artifacts out (3.4).

## 8. Sequencing map — what this campaign unlocks (DESIGN.md §6)

| §6 item | Unblocked by | One line |
|---|---|---|
| Movie Buff | Phase 1 origin exists (rate limiting home) — but try the static prebaked-title-index first | route to **degreesoffilm-research-frontier** |
| Server-side matching | IS Phase 1 | the wart fix DESIGN names |
| Accounts + database | IS Phase 2 | cross-device stats |
| Score History | Phase 2 (durable, cross-device); a client-only localStorage version needs nothing from this campaign | small follow-on after GATE 2 |
| Leaderboard (+ asterisk rule) | IS Phase 3 | requires Phases 1+2 |
| True degrees-of-separation | NOT this campaign — static-possible with a prebaked graph | route to **degreesoffilm-research-frontier** |
| Commercial TMDB agreement | independent; triggered by monetization, not by v3 | route to **degreesoffilm-external-positioning** |

## When NOT to use this skill

- Deciding **how to land** a change (PR vs direct, sign-offs, rollback conventions)
  → **degreesoffilm-change-control** (every promotion in this campaign routes there).
- Understanding the current three-zone architecture and its invariants
  → **degreesoffilm-architecture-contract**.
- Adding/locating a config axis (like `MATCH_API`) → **degreesoffilm-config-and-flags**.
- Movie Buff's static title index, the degrees-of-separation graph, anti-cheat as a
  research topic → **degreesoffilm-research-frontier**.
- Running or publishing today's static game/curation flow → **degreesoffilm-run-and-operate**.
- Test-writing standards for the new test-first pieces → **degreesoffilm-validation-and-qa**.
- Debugging today's live behavior → **degreesoffilm-debugging-playbook**.
- The enumerable-domain security argument as a reusable analysis recipe
  → **degreesoffilm-proof-and-analysis-toolkit**.

## Reusing this pattern beyond this project

The transferable template: (1) state owner constraints as numbered hard requirements
with per-phase checks; (2) phase by reversibility — least-reversible step last, each
phase additive with a one-line rollback; (3) gate on observable numbers, never vendor
promises; (4) fence wrong paths with derivations so they stay settled; (5) hunt for a
"pure core" you can run on both sides — client/server logic parity by reuse beats
parity by discipline. Project-specific: the exact endpoints, the cipher, TMDB
enumerability, and every vendor fact.

## Provenance and maintenance

- Written 2026-07-03. All in-repo facts verified against the working tree that day:
  file reads of `docs/{cipher,game,match,stats,app}.js`, `curation/publish.py`,
  `docs/puzzles/004.json`, `DESIGN.md` §6; the pure-module probe in §1 **executed**
  (output: `true / 'won' / true`); all 7 JS suites run: match 25, game 34, daily 11,
  theme 15, stats 17, frame 16, cipher 19 — all pass; baselines: 7 manifest entries
  (2026-06-28..07-04), 92 images.
- **Status 2026-07-11:** Phase 1 DONE — Worker deployed + GATE 1 PASSED (evidence in
  the §3 status note); the client default is still OFF pending §6 step 2 (owner-gated).
  Phases 2–3 remain CANDIDATE and OUT of the chosen scope.
- **Status 2026-07-04:** Phase 0 DONE (GATE 0 passed — owner scope: Phase 1 only,
  $0 ceiling, R5 intact); hosting = Cloudflare Workers + KV; Phase 1 spike BUILT
  (GATE 1 pending deploy). Phases 2–3 remain CANDIDATE and OUT of the chosen scope.
- Previously: nothing built, all phases CANDIDATE as of 2026-07-03. When
  one ships, update its status header + this section in the same session.
- Vendor facts (Cloudflare/Vercel/Netlify/Fly/Supabase/Firebase tiers, cold starts)
  are **as of training data (early 2026)** — RE-VERIFY EVERY VENDOR FACT BEFORE
  EXECUTING ANY PHASE (pricing pages + a live probe), and re-confirm R6's ceiling.
- Re-verify one-liners: pure modules → the §1 probe; suite counts →
  `node match.test.js && node game.test.js && node cipher.test.js && node stats.test.js`;
  baseline content → the commands in §1's table; stats key →
  `grep -n "dof-stats-v1" docs/stats.js`; cipher key/sentinel →
  `grep -n "SENTINEL\|KEY" docs/cipher.js`.
