---
name: degreesoffilm-research-frontier
description: >
  The open research problems where Degrees of Film could advance the state of the art, per the
  owner's chosen tracks (2026-07-02): AUTOMATED CURATION (auto-crop acceptance, difficulty
  calibration, decoy-quality scoring), NOVEL MODES (static-first degrees-of-separation graph
  play, Movie Buff via a prebaked title index), and SCALE & INTEGRITY (verifiable runs /
  anti-cheat for leaderboards). Load this when someone asks "what should we build next",
  "can this be state of the art?", wants research-grade improvements rather than maintenance,
  has ideas about auto-crop quality, puzzle difficulty, decoy plausibility, new game modes,
  autocomplete, or leaderboard/anti-cheat design. Every item here is OPEN/CANDIDATE — nothing
  is shipped or decided; promotions route through degreesoffilm-change-control. Explicitly NOT
  covered: matcher craft (owner excluded it) and executing the v3 server move itself
  (degreesoffilm-server-move-campaign).
---

# Degrees of Film — the research frontier

> **STATUS BANNER — read this first.** Every problem, step, milestone, and number in this file
> is **OPEN / CANDIDATE** as of 2026-07-03. NOTHING here is shipped, scheduled, or decided.
> This skill is a map of where the project could *advance the state of the art*, not a record
> of what it does. Before building anything from this file:
>
> 1. Route the change through **degreesoffilm-change-control** (classification, landing mode,
>    owner sign-off where required).
> 2. Anything needing a backend routes through **degreesoffilm-server-move-campaign** FIRST —
>    that campaign owns the v3 sequencing and its gates.
> 3. Turn the hunch into an accepted result using **degreesoffilm-research-methodology**
>    (predict numbers before running; name the falsifier; retire with a written why).

## Why this project can play at the frontier at all

Three structural assets, each verifiable in the repo today:

| Asset | Made real by | Why it matters |
|---|---|---|
| A human-in-the-loop curation pipeline that already touches every publish | `curation/app.py` + `curation/static/index.html` (Approve flow) | Every publish is a free labeling event — nobody instruments it yet |
| A pure-logic rules engine with zero DOM coupling | `docs/game.js` (imports only `./match.js`), `docs/match.js` (imports nothing) — verified 2026-07-03 | The SAME code that scores a player can replay/validate a run server-side with zero porting drift |
| Film↔person credit data flowing through the pipeline on every puzzle | `curation/build_rungs.py`, `curation/decoys.py`, `curation/used_films.json` | Graph raw material for new modes without any new data source |

The owner's chosen tracks (2026-07-02): **automated curation**, **novel modes**, **scale &
integrity**. Explicitly **NOT matcher craft** — do not propose Levenshtein/normalization
research; `docs/match.js` is maintained via its contract table (`match.test.js`), not advanced.

---

## Track 1 — AUTOMATED CURATION

### 1a. Auto-crop acceptance — turn every publish into labeled training data [STEP 1 DONE 2026-07-13 — data accruing]

> **Instrumented 2026-07-13:** `doAutocrop()` stores the suggestion (`state.autoBox` +
> scale + the face flag, now surfaced by `images.auto_crop_box`); approve/update bodies
> carry it; `app.py _log_autocrop` appends one row per publish to **gitignored**
> `curation/autocrop_log.jsonl` (spoiler-adjacent still URLs — local tuning data) with
> IoU precomputed via the new pure `images.box_iou` (tested). Rows with `suggested:
> null` measure adoption. Steps 2–3 (accumulate n≥20, then tune scale/deweight_bands
> against the log) remain OPEN — nothing to do but curate normally.

**Why current SOTA fails.** Generic saliency/smart-crop tools (CV saliency maps, cloud
"smart crop" APIs) optimize for "keep the interesting part". This game's crop has constraints
no generic tool knows: **title-safe** (must not include on-screen title text — the answer),
**spoiler-safe** (must not reveal the film too easily at tier 1), **face-first but not
face-only**, and **aspect-locked** so the three reveal tiers zoom out smoothly
(`expand_boxes` / `box_around` in `curation/images.py` keep the frame aspect). No public
benchmark or pretrained model encodes "crop so a film buff can *almost* name the film".

**This project's specific asset.** The approve/re-drag loop is a free labeling machine that
nobody has switched on. Verified 2026-07-03 in `curation/static/index.html`:

- `doAutocrop()` (~line 437) fetches `/api/autocrop` and sets `state.box` to the suggestion,
  with the caption `'auto — approve or re-drag'` (line 446).
- The curator either approves it unchanged or drags a new box — the drag **overwrites**
  `state.box` (line ~420); the `state` object (line 179) has **no field remembering the
  auto suggestion**.
- Approve POSTs only the final `box: [x,y,w,h]` (lines 476–479).

So every publish already produces a (suggested box, final box) pair — and then throws the
suggested half away. Logging it is a **curation-only** change (no player-facing surface, the
cheapest change class in degreesoffilm-change-control).

**First three steps in this repo:**

1. **Instrument the pair.** In `curation/static/index.html`'s `doAutocrop()`, also store the
   suggestion (e.g. `state.autoBox = b` plus the slider `scale`); include both boxes in the
   `/api/approve` and `/api/update` bodies; have `curation/app.py` append one JSON line per
   publish to a curation-side log (e.g. `curation/autocrop_log.jsonl` — owner decides
   committed vs gitignored). Record: still URL, scale, suggested box, final box, whether a
   face was detected (surface it from `auto_crop_box`).
2. **Accumulate ≥20 publishes** in normal operation (the open v2 task is "curate more puzzles"
   anyway — the data collects itself). Do nothing else until then; n<20 is anecdote.
3. **Measure, then tune.** A small offline script (pattern: `.claude/skills/degreesoffilm-diagnostics-and-tooling/scripts/`)
   computes per-publish: accepted-unmodified (boxes equal within ε), and IoU
   (intersection-over-union) otherwise. Tune against the log: the `scale` default (0.5 today,
   slider 0.25–0.85 — `index.html` line 148), and `deweight_bands` params (top 0.12 / bottom
   0.18 / factor 0.35 — `curation/images.py` line 78). Predict the improvement before changing
   a constant (research-methodology discipline).

**You have a result when:** over 20 consecutive publishes, the suggested box is accepted
unmodified in **≥ 70%** of them, OR median IoU(suggested, final) **≥ 0.8**. Either number,
measured from the log, is publishable-grade for this niche; below both, you have tuning
homework, not a result.

**Do not start here (fences):**
- **No custom model training** before exhausting (a) the logged-data tuning above and
  (b) `cv2.FaceDetectorYN` (YuNet), the sanctioned next detector step — as of training data it
  ships in opencv-python ≥ 4.5.4 with a separately-downloaded ONNX model and handles the
  angled/dark faces Haar misses (`curation/images.py` `detect_faces` docstring admits the
  gap). Verify the API and model-file story at execution time.
- **The `opencv-python-headless>=4.9,<5` pin is load-bearing** (`curation/requirements.txt`
  line 13): OpenCV 5.0 dropped the bundled Haar cascades. Moving to ≥5 is a deliberate,
  separate migration (Haar → YuNet), not a casual bump. See degreesoffilm-failure-archaeology.
- **Never remove the curator approve step.** Auto-crop is a *suggestion* by design
  (`auto_crop_box` docstring: "A STARTING POINT the curator reviews"); full automation is a
  milestone-gated future decision, not a starting assumption.

### 1b. Difficulty calibration — publish the first calibrated daily film puzzle [OPEN/CANDIDATE]

**Why current SOTA fails.** As of training data, no daily guessing game (Wordle-likes, Framed,
Cine2Nerdle) publishes a *calibrated* per-puzzle difficulty — they eyeball it or say nothing.
Here, rung difficulty is implicitly "billing order ≈ fame" (`curation/build_rungs.py`
`order_rungs`) and nobody checks whether players' actual depth distribution matches.

**This project's specific asset.** Two halves of a calibration loop already exist, unconnected:
(1) rung-level structure flows through the pipeline on every publish (`build_rungs.py` — rung
index, role class, billing order; TMDB person stats are *fetched* at draft time but not
persisted); (2) the client already records a **depth histogram** — `docs/stats.js`
`recordResult` keeps `histogram: {depth → times reached}` under localStorage key
`'dof-stats-v1'`. It is **device-local only** today; aggregating it across players is gated on
the server move, but a single curator's own histogram is readable right now.

**First three steps in this repo:**

1. **Define a difficulty proxy per rung, offline.** v0 uses only what's on disk: rung index,
   role class (Film / Cast / Director / deep crew), and decoy-pool presence. Write the proxy as
   a pure function in a scratch script; document the intended v1 upgrade (person
   `popularity` / film `vote_count` captured at publish time — a curation-side, key-gated
   addition to the approve flow, logged like 1a's boxes, NOT shipped in player JSON).
2. **Compute it retroactively for puzzles 001–007** from `docs/puzzles/NNN.json` (decode
   answers via `curation/cipher.py` — spoiler-revealing, curator-only output) plus
   `curation/used_films.json` for film ids. Entirely offline; no key, no network.
3. **Predict before observing.** From the proxy, write down the expected depth distribution
   per puzzle (e.g. "median strike-out at rung 7±1; puzzle 006 easiest — 10 rungs, all
   decoy-covered") **before** looking at any real depth data. Committing the prediction first
   is what makes the eventual comparison evidence rather than curve-fitting
   (degreesoffilm-research-methodology).

**You have a result when:** predicted vs observed per-puzzle depth distributions correlate at
**Spearman ρ ≥ 0.6** once any aggregate data exists (server-move Phase 2+), or — interim,
weaker — the proxy correctly rank-orders the curator's own playtest depths on ≥ 5 puzzles.
State which evidence tier you hit.

**Do not start here (fences):**
- **Don't block on the server move** — steps 1–3 are offline-now. Aggregation is the gated
  part, and it routes through degreesoffilm-server-move-campaign (Phase 2 accounts/DB).
- **Don't resurrect popularity as the ladder sort.** SETTLED-REJECTED (failure-archaeology
  entry 1: rolling popularity buried Heath Ledger's Joker at rung 13; evidence
  `curation/validate_ladder.py`). Popularity may *score* difficulty; it may not *order* rungs.
- **Don't add telemetry to the client** to get data faster — that's an accounts/privacy
  decision owned by the server-move campaign, not a research shortcut.

### 1c. Decoy quality — score plausibility instead of trusting popularity order [OPEN/CANDIDATE]

**Why current SOTA fails.** Multiple-choice distractor generation is studied for education
(where wrongness must be unambiguous) but not for trivia *plausibility* — "would a film buff
hesitate?". Here decoys are simply the popularity-sorted heads of neighbour-film pools
(`curation/decoys.py`: `gather_pools` sorts each pool by TMDB popularity, `pick_decoys`
preserves that order and takes the first 3). Popularity ≈ recognizable, but not ≈ plausible
*for this film*: a 2020s star is a weak decoy for a 1970s DP rung.

**This project's specific asset.** The raw material for a plausibility score is already
computed and then discarded: `gather_pools` walks neighbour films (recommendations→similar,
`min_votes=400`, `source_limit=8`, `cast_per_film=5`), sees each candidate's popularity and
source film (hence era/genre), and keeps only the name. The distance structure exists at
publish time for free.

**First three steps in this repo:**

1. **Define a plausibility score**: same-era (decoy's source-film release year within ±k of
   the puzzle film's), popularity-band match (decoy popularity within a ×/÷ band of the rung
   answer's), role already guaranteed by pool construction. Pure function, unit-tested in the
   house style (see degreesoffilm-validation-and-qa), no network.
2. **Audit the 7 existing puzzles offline** for the structural failures visible without TMDB:
   zero-decoy rungs, decoys duplicated across rungs, a decoy that equals another rung's
   answer in the same puzzle. Real gap already found this way (2026-07-03, verified by
   decoding all 7 puzzle files): **puzzle 005 rung 12 (Production Designer) has ZERO decoys**
   — it can never be helped in Cinephile and is silently dropped from Poser's decoy-bearing
   trim. The diagnostics skill's validator reports decoy coverage; extend it, don't duplicate it.
3. **Score full candidate pools** (key-gated, curation-side: re-run `gather_pools` for the 7
   ledger films, keep the metadata this time) and produce, per rung, the score-ranked top-3
   beside the current popularity-ranked top-3.

**You have a result when:** in a **blind curator A/B over ≥ 10 rungs** (current pick vs
scored re-rank, unlabeled), the scored set is preferred on a majority — and the zero-decoy
class of defect is impossible by construction (the score surfaces empty/thin pools at draft
time instead of at the player's expense).

**Do not start here (fences):**
- Don't "fix" puzzle 005 rung 12 by editing the file — **IMMUTABLE PAST** (owner rule: never
  modify a published puzzle dated ≤ today; 005's date has passed). It's evidence, not a bug
  to hotfix.
- Don't reach for an LLM-generated decoy pipeline first — the same-category pools are the
  asset; exhaust scoring/re-ranking them before adding a new generation source (which would
  also need its own accidentally-correct exclusion, which `gather_pools` already solves via
  `_people_in`).

---

## Track 2 — NOVEL MODES

### 2a. True degrees-of-separation, static-first [OPEN/CANDIDATE — campaign skill exists]

> **2026-07-11 updates:** (1) the raw graph material now EXISTS ON DISK — the Movie Buff
> people harvest (`curation/people_harvest_cache.jsonl`) maps all 3,663 pool-floor films
> to their top cast + key crew; extractor v0 needs ZERO new TMDB calls. (2) The executable,
> decision-gated plan (phases G0–G4, gates, fenced paths) now lives in
> **degreesoffilm-graph-mode-campaign** — start there; this entry remains the research
> framing.

**Why current SOTA fails.** Connect-the-films games (as of training data: Cine2Nerdle and
kin) run live backends — the graph queries happen server-side per guess. Nobody ships a
credible film-connection game as **pure static files**, because nobody prebakes the graph.
DESIGN §6 already spots the opening: the v3 parking-lot entry for degrees-of-separation says
"(Doable static with prebaked data, but a big mode — slotted here.)" — the "doable static"
half has never been de-risked.

**This project's specific asset.** The curation pipeline already fetches full credits for
every puzzle film (`curation/build_rungs.py` via `tmdb.movie_with_credits`) and for its
neighbour films (`curation/decoys.py` `gather_pools`). Film↔person edges are computed on
every publish and discarded. The zone model (key stays in `curation/`, players fetch static
files — CLAUDE.md "Architecture") is exactly the shape a prebaked-graph mode needs.

**First three steps in this repo:**

1. **A graph-extractor CLI in `curation/`** (house pattern: pure core + thin CLI, like
   `build_rungs.py`). Input: a seed film list (start with the 7 ledger films). Output: a
   nodes/edges JSON (films, people, appeared-in edges). First run can be structure-only from
   decoded puzzle JSONs (offline, no key); the real corpus needs key-gated credit fetches —
   batch them, respect the modest-usage posture (degreesoffilm-external-positioning).
2. **Measure the size budget before designing the mode.** Bytes per film (≈ cast trim × edge
   cost) → project N films at raw / minified / gzip. State the target against GitHub Pages
   limits (as of training data: ~1 GB site soft limit, keep individual files ≪ 100 MB —
   verify at execution time). Write the measured curve down; it decides whether the mode ships
   a whole-corpus graph or a per-challenge subgraph (likely the latter — a puzzle file that
   contains only the neighborhood needed for one A→B challenge, matching the "each day is one
   self-contained JSON" convention).
3. **An offline pathfinding prototype + one hand-authored challenge.** Node script, BFS over
   the extracted graph, verifying an A→B path exists within d hops; then hand-author one
   challenge JSON and render it behind a new query route (the client already routes by query
   string — `docs/app.js`). Prototype stays off `main`'s `docs/` until change-control review.

**You have a result when:** a playable A→B challenge is served **purely static** — no key in
the client (grep-verifiable, the architecture-contract invariant), graph payload **≤ your
measured budget from step 2** (state the number; if the per-challenge subgraph is ≤ 100 KB gz,
say so) — and one person who isn't you completes it.

**Do not start here (fences):**
- **Answer enumerability is worse here**: shipping the graph ships the solution space. The
  cipher is anti-snoop only (CLAUDE.md); accept spoilability like the current game does, or
  route validation server-side — the latter is a server-move dependency, so it goes through
  that campaign. Decide which posture *before* building the client.
- Don't confuse this with the existing game — CLAUDE.md's banner note: the shipped game is a
  vertical dig, NOT six-degrees. This is a second mode, new route, new schema; it must not
  touch `game.js`'s rules.
- Don't bulk-crawl TMDB to build a huge graph speculatively — measure the per-challenge
  subgraph option first; it may need only the credits the pipeline already pulls.

### 2b. Movie Buff via a prebaked title index [SHIPPED 2026-07-11 — record only]

> **PROMOTED AND SHIPPED 2026-07-11.** All three steps executed (curation/title_index.py,
> docs/buff.js + docs/title-index.json, PRs #22/#23); milestone met and beaten: 5k titles =
> 124.4 KB raw / 45.9 KB gzip, ledger coverage 21/21 asserted at build time, 0.05 ms/keystroke
> filter via the shipped normalize(), index fetched only in buff mode, `?play&mode=buff` live.
> Story in project_state.md. The section below is kept as the design record — nothing open here.

**Why current SOTA fails / why the gate is softer than believed.** Movie Buff (title
autocomplete on the film rung) is parked in DESIGN §6 v3 — but read the entry: "Needs a
prebaked popular-title index **or** a backend search proxy; a live TMDB call from the browser
would expose the API key." The ban is on the *live call*; DESIGN itself names the static
escape hatch, and nobody has costed it. A static top-N index sidesteps the server move
entirely — IF it doesn't leak which titles are eligible answers.

**This project's specific asset.** `docs/match.js` exports `normalize()` (verified
2026-07-03) — the exact normalization the matcher applies to guesses. Building the index keys
with the same function guarantees autocomplete-selected titles survive matching, with zero
new matching logic (and zero matcher changes — the track excludes matcher craft; this only
*calls* it).

**First three steps in this repo:**

1. **A curation CLI emitting a normalized top-N title index** (key-gated, `curation/`,
   discover-endpoint paging — note `curation/tmdb.py`'s paging cap of 500). Emit
   `{normalizedKey → display title}` (or a sorted array), N configurable.
2. **Measure size/latency for N ∈ {5k, 10k, 20k}**: raw / gzip bytes, client filter latency on
   keystroke (a Node micro-benchmark is fine first). Write the numbers into the proposal.
   Ballpark expectation ~15–35 bytes/title raw — but the measured number is the deliverable.
3. **A client autocomplete prototype behind a query flag** (e.g. `&buff=1` on a branch —
   query-string routing is the house flag mechanism, see degreesoffilm-config-and-flags),
   index fetched lazily ONLY when the flag is on, so default players pay zero bytes.

**You have a result when:** with the flag on, autocomplete on the film rung works fully
offline-static; the index adds **≤ your measured budget** (state it — e.g. "10k titles,
X KB gz"); and it **provably does not reveal eligible answers**: the index must be a strict
superset built from TMDB-wide popularity, NEVER from the ledger or manifest — eligibility
(pool floor `vote_count≥800 & vote_average≥6.5`, `curation/discover.py`) selects a small
subset of any top-10k list, so index membership carries ~no signal. Add a build-time
assertion: every ledger film's title is present in the index (absence would be the leak in
reverse — and would break autocomplete on a puzzle day).

**Do not start here (fences):**
- **NO live TMDB call from the browser, ever** — the key-leak ban (DESIGN §6, CLAUDE.md's one
  load-bearing fact). This includes "temporary" dev shortcuts.
- Don't modify `docs/match.js` — the index adapts to the matcher, never the reverse
  (matcher changes are contract-gated via `match.test.js` and out of this skill's scope).
- Mode promotion (mode-select tile, DESIGN §1 wording says Movie Buff is Cinephile-rules +
  autocomplete) is a change-control decision with owner sign-off; the prototype proves
  feasibility only.

---

## Track 3 — SCALE & INTEGRITY

### 3a. Verifiable runs — replay-validated scores from the unmodified rules engine [OPEN/CANDIDATE]

**Why current SOTA fails.** Client-computed leaderboard scores are junk — a POST with a
forged `depth` is indistinguishable from a real one, so small games either skip leaderboards
or ship gameable ones. Validated replay (server re-runs the player's inputs through the real
rules) is what serious competitive games do; nobody at daily-puzzle scale does it, usually
because their rules engine is welded to their UI and a server port would drift.

**THE asset.** This repo's rules engine cannot drift, because there is nothing to port:
`docs/game.js` is a pure ES module importing only `docs/match.js`, which imports nothing
(verified 2026-07-03 — and `game.test.js` already runs the engine in Node, 34 checks). The
SAME file a player's browser executes replays a transcript server-side. Depth, score, skips,
help usage all fall out of `new Game(puzzle, { mode })` + the `guess()` / `skip()` /
`useHelp()` API deterministically.

**First three steps in this repo (all offline, today):**

1. **Define a run-transcript format.** Candidate: `{ puzzleId, mode, events: [...] }` where
   each event is `{t:'guess', text}` | `{t:'skip'}` | `{t:'help'}` | `{t:'pick', text}` (help
   then MC pick), in order. Write it down as a short spec in the prototype dir; the claimed
   `depth`/`score` are *outputs*, never inputs.
2. **An offline Node replay validator.** Script that loads a puzzle JSON, decodes rungs via
   `docs/cipher.js` `decodeRungs` (exactly as `docs/app.js` does), feeds the transcript through
   the unmodified `Game`, and asserts the recomputed `{depth, score, status}` equals the claim.
   House test style: PASS/FAIL lines, non-zero exit (degreesoffilm-validation-and-qa).
3. **Tamper tests.** Legit transcript (record one by hand from a real playthrough) → accepted.
   Then forge: bump claimed depth (+1) → mismatch; delete a wrong guess (hiding a strike-out)
   → mismatch; replay a Poser transcript claiming Cinephile scoring → mismatch; out-of-order /
   post-terminal events → rejected (the engine's status guards no-op them — assert the
   recomputation therefore diverges from the inflated claim).

**You have a result when:** the validator, **offline, using unmodified `docs/game.js` and
`docs/match.js`**, accepts a recorded legitimate transcript and rejects all forged variants
above — binary, demonstrable in one terminal session. That artifact IS the integrity core of
a future leaderboard.

**Do not start here (fences):**
- **Do not build the leaderboard itself.** This work *feeds*
  degreesoffilm-server-move-campaign **Phase 3** (which also owns the DESIGN §6 asterisk rule
  for easy-mode-heavy totals, rate limiting, and accounts). Don't start Phase-3 surface work
  before that campaign's Phase 1–2 gates pass.
- Don't harden by obfuscating the client or the transcript — enumerable-domain analysis
  (see degreesoffilm-proof-and-analysis-toolkit) applies: replay validation is the mechanism;
  client-side secrecy is not.
- Residual threat to state honestly in any writeup: replay proves *consistency*, not
  *humanity* — a bot can generate a valid transcript. That's a separate (rate-limit/
  statistical) problem; don't claim replay solves it.

---

## Priority and dependencies map (as of 2026-07-03)

| Problem | Startable today, fully offline? | Needs curation key (private, owner-run)? | Gated on server move? |
|---|---|---|---|
| 1a auto-crop logging → tuning | Step 1 is a curation-only code change; analysis offline | Data accrues via normal publishing | No |
| 1b difficulty proxy | **Yes — steps 1–3 now** | v1 proxy enrichment only | Only the *aggregation* endgame |
| 1c decoy scoring | Structural audit now (005 r12 gap already found) | Step 3 pool re-fetch | No |
| 2a static graph mode | Extractor v0 + pathfinding now | Full corpus fetch | Only if server-validated answers chosen |
| 2b Movie Buff index | Benchmarks + client prototype vs a stub index now | Index build | **No — that's the finding** |
| 3a replay validator | **Yes — entirely, today** | No | Leaderboard *use* of it, yes (campaign Phase 3) |

Cheapest first results: **3a** (one Node script, binary outcome) and **1b steps 1–3** (pure
analysis). Highest leverage per effort: **1a step 1** (a few lines now; the data then collects
itself during the already-open "curate more puzzles" task). Most novel if it lands: **2a**.

**How any of these becomes an accepted result:** degreesoffilm-research-methodology (predict
numbers first, name the falsifier, adversarial pass, retire-with-a-written-why into
degreesoffilm-failure-archaeology if it dies). **How any of these ships:**
degreesoffilm-change-control, without exception.

**Demand-signal unlock (2026-07-11):** the /match Worker is live and ON, so Cloudflare's
free request metrics ≈ engaged players (≈36 calls/game) — the project's first
privacy-preserving usage signal, with **no client telemetry added**. Phases 2–3 of the
server-move campaign were parked for lack of demand evidence; that evidence now accrues
by itself. Reading it → **degreesoffilm-worker-ops** §3.

## Settled battles this file must not re-open

Cross-reference degreesoffilm-failure-archaeology before proposing anything adjacent:

- **Popularity-ordered ladder — SETTLED-REJECTED** (Joker at rung 13). 1b may use popularity
  as a difficulty *feature*, never as the rung *sort*.
- **Character-stills picker — SETTLED-REJECTED** (built via PRs #12/#13, removed 3e2cfbb;
  TMDB tagged images too sparse). No frontier item may quietly rebuild per-rung character
  imagery; credit rungs are auto TMDB headshots, full stop.
- **Live browser TMDB call — BANNED** (key leak; DESIGN). 2b exists precisely to route
  around it.
- **IMMUTABLE PAST + SPOILER DISCIPLINE** (owner rules): no experiment edits published
  puzzles dated ≤ today; no experiment writeup, commit message, or logged artifact names a
  future puzzle's film.

## When NOT to use this skill

- Executing the v3 backend migration (hosting menus, phases, gates) →
  **degreesoffilm-server-move-campaign** (3a feeds its Phase 3; the campaign owns sequencing).
- Deciding how a change lands, what needs sign-off → **degreesoffilm-change-control**.
- The discipline for running any experiment here (evidence bar, hypothesis cards) →
  **degreesoffilm-research-methodology**.
- Analysis recipes (de-risk scripts, parity vectors, enumerability arguments) →
  **degreesoffilm-proof-and-analysis-toolkit**.
- What was already tried and killed → **degreesoffilm-failure-archaeology**.
- Understanding current behavior (rules, matcher, TMDB model) →
  **degreesoffilm-domain-reference**; invariants → **degreesoffilm-architecture-contract**.
- Running/publishing today's pipeline → **degreesoffilm-run-and-operate**; measuring current
  content health → **degreesoffilm-diagnostics-and-tooling**; test standards →
  **degreesoffilm-validation-and-qa**; env setup → **degreesoffilm-build-and-env**;
  config values → **degreesoffilm-config-and-flags**; debugging symptoms →
  **degreesoffilm-debugging-playbook**; docs/writing → **degreesoffilm-docs-and-writing**;
  external claims/attribution → **degreesoffilm-external-positioning**.

## Reusing this pattern beyond this project

The transferable template: a **research-frontier register** — each entry pinned to
(why-SOTA-fails, a *file-cited* local asset, three steps startable in-repo, a falsifiable
milestone with a number or binary observable, and fences honoring settled battles). The
project-specific content (crop constraints, TMDB shapes, the pure-engine replay trick) does
not transfer; the two load-bearing habits do: **instrument the human loop you already have**
(1a's approve flow) and **exploit purity you already paid for** (3a's replay). Any project
with a human review step or a DOM-free core has the same free assets waiting.

## Provenance and maintenance

- **Written 2026-07-03.** All asset claims verified against the working tree that day:
  `curation/images.py` (auto_crop_box/detect_faces/deweight_bands/box_around, defaults),
  `curation/decoys.py` (gather_pools/pick_decoys, popularity sort, min_votes=400),
  `curation/build_rungs.py` (order_rungs), `curation/requirements.txt` (opencv `<5` pin),
  `curation/static/index.html` (state object line 179, doAutocrop ~437, approve body 476–479,
  slider 0.25–0.85), `docs/stats.js` (histogram, 'dof-stats-v1'), `docs/game.js` /
  `docs/match.js` import graph and exports, DESIGN.md §6 quotes ("Doable static with prebaked
  data"; "prebaked popular-title index or a backend search proxy").
- **Decoy audit executed 2026-07-03**: decoded all 7 puzzle files; sole zero-decoy rung =
  puzzle 005 rung 12 (Production Designer).
- External/SOTA claims (competitor backends, FaceDetectorYN availability, GitHub Pages
  limits, byte-per-title ballpark) are **as of training data — verify at execution time**.
- Re-verify one-liners:
  - Import purity: `grep -n "^import" docs/game.js docs/match.js` (expect: game.js only `./match.js`; match.js none)
  - OpenCV pin: `grep -n opencv curation/requirements.txt`
  - Approve payload / no autoBox field: `grep -n "state = {" curation/static/index.html` and `grep -n "api/approve" curation/static/index.html`
  - Decoy coverage: `python -c "import json;[print(i,[k+1 for k,r in enumerate(json.load(open(f'docs/puzzles/{i:03d}.json',encoding='utf-8'))['rungs']) if not r.get('decoys')]) for i in range(1,8)]"` (run from repo root; extend the range as puzzles land)
  - Parking-lot gates still as quoted: `grep -n "prebaked" DESIGN.md`
- **2026-07-11 sweep:** 2b PROMOTED AND SHIPPED (marked above); 2a gained the harvest-cache
  asset + its executable campaign skill (degreesoffilm-graph-mode-campaign); demand-signal
  note added (Worker metrics via degreesoffilm-worker-ops). Product-polish ideas from the
  same night's analysis went to DESIGN §6 (they're product backlog, not research).
- **Maintenance rule:** when any item here is promoted (built) or retired (killed), move its
  story to project_state.md / degreesoffilm-failure-archaeology, relabel or delete the entry
  here, and update this date — this file must only ever contain OPEN/CANDIDATE work.
