---
name: degreesoffilm-research-frontier
description: >
  The open research problems for Degrees of Film — where the rebuilt degrees-of-separation
  game could still advance the state of the art. Load this when someone asks "what should we
  build next", wants research-grade improvements rather than maintenance, or has ideas about
  difficulty calibration (does the shipped weekly par arc match measured difficulty?), daily
  pair quality beyond par, verifiable runs / accountless league integrity / anti-cheat around
  the frozen share grammar, or new game modes. Every item is OPEN/CANDIDATE — nothing is
  scheduled or decided; the owner's original track list (2026-07-02) predates the 2026-08-14
  rebuild and the recast list here needs owner re-confirmation before anyone invests.
  Promotions route through degreesoffilm-change-control. Explicitly NOT covered: matcher
  craft (owner excluded it), how changes land (degreesoffilm-change-control), experiment
  discipline (degreesoffilm-research-methodology).
---

# Degrees of Film — the research frontier

> **STATUS BANNER — read this first.** Everything below is **OPEN / CANDIDATE** as of
> 2026-08-14. Nothing is shipped, scheduled, or decided. Two caveats bind harder than usual:
>
> 1. **The owner's track choices date from 2026-07-02 — before the rebuild.** The dig game
>    those tracks were chosen for is deleted. The list below is an honest recast of what
>    survives, **not owner intent**; re-confirm the tracks with the owner before investing
>    real effort in any of them.
> 2. Route anything that builds through **degreesoffilm-change-control**, and turn any hunch
>    into an accepted result via **degreesoffilm-research-methodology** (predict numbers
>    before running; name the falsifier; retire with a written why).

## What the 2026-08-14 rebuild settled

- **SHIPPED — no longer frontier:** *true degrees-of-separation graph play, static-first*
  (old track 2a) **is the product now** — whole corpus in `docs/graph.json` (190 KB gz),
  ~50-byte dailies, client-side validation, launched 2026-08-14. Its story lives in
  `project_state.md`; nothing about it belongs in this file anymore.
- **DELETED with the dig — problems gone because their assets are gone:** auto-crop
  acceptance (the crop tool, `images.py`, the approve loop), decoy-quality scoring
  (`decoys.py`, multiple-choice rungs), and the Movie Buff title index (the mode itself,
  `buff.js`, `title-index.json`). All deleted in the rebuild; history is in git. Do not
  resurrect these as research — there is no surface for them to improve.

## Open problems

### 1. Difficulty calibration — does measured difficulty match the arc? [OPEN/CANDIDATE]

**Why current SOTA fails.** No daily game publishes calibrated per-puzzle difficulty. Here
the shipped proxy is **par via the weekly arc** (`WEEKLY_ARC` Mon–Wed 2 → Sat 4,
`par_for_date` in `curation/challenge_gen.py`) — but par is crude: two par-3 pairs can
differ wildly in real difficulty depending on how hub-covered the routes are.

**This project's assets.** (1) `count_routes` / `par_closers` in `challenge_gen.py` — the
distinct-closers fairness count, already stored per daily as `"routes"` in the gitignored
solutions sidecar; (2) `obscurity()` and `countGeodesics()` in `docs/solve.js` — pure,
Node-importable, calibrated on the real corpus; (3) each player's own depth data in
`docs/stats.js` (histogram, handicap — device-local); (4) soon: **real shares** — the frozen
line-1 grammar makes every group-chat share a parseable result (degrees vs par, or `X`).

**First three steps in this repo:**

1. **A pure offline difficulty proxy per daily** — script over `graph.json` + the solutions
   sidecar: routes count, geodesic count, closer-set obscurity spread, endpoint hub-ness.
   No network, no key.
2. **Predict before observing:** rank all scheduled dailies by predicted difficulty and
   write the ranking down *first* (curator-only output — never committed; spoiler
   discipline).
3. **Compare against the first real signal:** shares collected by hand from the group chat
   (over-par rate, loss rate per daily). Spearman predicted rank vs observed.

**You have a result when:** predicted vs observed difficulty correlate at **ρ ≥ 0.6 over
≥ 15 played dailies** — the first calibrated daily film puzzle. Below that, the arc is
flying blind and the proxy is homework, not a result.

**Do not start here (fences):**
- **No client telemetry, ever** — no server, no accounts are owner decisions. The data
  source is shares and the owner's own play, full stop.
- **Don't retune `WEEKLY_ARC` on a hunch.** It shipped 2026-08-14 and players build
  schedule expectations around it; changes are evidence + owner sign-off.

### 2. Verifiable runs — integrity for accountless leagues [OPEN/CANDIDATE]

**Why current SOTA fails.** Everything here is client-side; a share string is just text, so
a claimed score is forgeable by typing. Serious games validate by server replay — but this
game has **no server and no accounts by owner decision**, and the frozen share line 1
exists precisely so Discord bots can run leagues with neither. Nobody does *verifiable*
accountless daily-game leagues.

**THE asset.** The rules engine cannot drift from a validator because there is nothing to
port: `docs/chain.js` (pure, `Chain` + `toJSON`/`fromJSON`, imports nothing) and
`docs/corpus.js` already run in Node — `chain.test.js` replays runs today, including forged
ones. The same file a player's browser executes can replay a transcript offline.

**First three steps in this repo (all offline, today):**

1. **Define a run-transcript format.** Candidate: `{challengeId, events: [...]}` where each
   event is `{t:'guess', text}` | `{t:'back'}`, in order, keyed by TMDB ids/names like
   `toJSON` (never corpus indices). Claimed degrees/won/glyph-trail are *outputs*, never
   inputs.
2. **An offline Node replay validator:** load `graph.json` + `challenges.json`, feed the
   transcript through the **unmodified** `Chain`, assert the recomputed
   `{degrees, won, glyph trail}` matches the claimed share line 1/3.
3. **Tamper tests:** a recorded legitimate run → accepted. Forge: degrees−1, a deleted burn
   (hiding a 🟥), a swapped challenge id, events after the win → each rejected.

**You have a result when:** the validator, using unmodified `docs/chain.js` +
`docs/corpus.js`, accepts the real transcript and rejects every forgery class above —
binary, one terminal session. That artifact is the integrity core of any future league bot.

**Do not start here (fences):**
- **No server, no accounts** — owner decisions, not open questions. A league bot consuming
  transcripts is a community artifact, not a repo feature, until the owner says otherwise.
- **Share line 1 is FROZEN** (CLAUDE.md "Share grammar"). A transcript may only ride after
  the final `)` or live outside the share entirely.
- State the residual threat honestly: replay proves *consistency*, not *humanity* — a BFS
  bot produces valid transcripts. That's a separate problem; don't claim replay solves it.

### 3. Pair quality — grading a daily beyond par [OPEN/CANDIDATE]

**Why current SOTA fails / current state.** The generator's quality bar is minimal and
structural: exact par, endpoints in the top 900 films, franchise rejection (`too_similar`),
and `min_routes=2` (`pick_pair`, `curation/challenge_gen.py`). What makes a pair *good* —
hub-avoidance (no "one famous person solves it instantly"), obscurity spread across routes,
genuine route diversity — is computed nowhere. No daily game grades its puzzles before
players see them.

**This project's assets.** `count_routes`/`par_closers` (Python, curation side) and
`countGeodesics`/`obscurity` (`docs/solve.js`, Node-importable) already measure the raw
ingredients; the sidecar stores route counts for every scheduled daily.

**First three steps in this repo:**

1. **Define a pair-quality score** — pure Python beside `pick_pair`: hub penalty (fame of
   the most-credited closer), diversity bonus (routes, geodesic count), obscurity spread of
   the closer set. Unit-tested in the house stdlib style.
2. **Grade every scheduled daily retroactively, offline.** Compare the worst-scored few
   against curator judgment (spoiler-safe: the discussion never enters a commit).
3. **If the score discriminates,** wire it into `pick_pair` as a rejection threshold behind
   a flag and generate one week with/without, comparing the drawn pairs blind.

**You have a result when:** in a blind ranking of **≥ 10 pairs** (score vs curator), the
score's bottom quartile matches the curator's — and the "one obvious hub closes it" defect
becomes impossible by construction at generation time.

**Do not start here (fences):**
- **Never regenerate or edit a published daily dated ≤ today** — immutable past.
- Grading output and the sidecar stay gitignored/uncommitted — public repo, spoiler
  discipline; commit messages never name a chain.
- The curator's-note rule is already hard-enforced by `challenge_gen.py --check`; a quality
  score extends the generator, it doesn't relax `--check`.

### 4. Soft-fail caddy — evidence-gated; DO NOT BUILD NOW [GATED]

The one unbuilt Comeback Loop item (project_state.md): a graceful assist when a player is
about to DNF. Its own gate requires **measured DNF rates from real players** — if DNF is
below ~10%, skip it forever — plus owner sign-off (it's a rules change). It stays in this
file as the house example of *evidence-gated product research*: the buildable research task
today is not the caddy but the **DNF measurement pipeline**, which is problem 1's share
parsing. Anyone proposing to build the caddy before the number exists is skipping the gate.

### Parked — real, but not research-shaped yet

- **Role glyphs in shares** (🎭🎬🎼): needs a harvest schema change + corpus rebuild.
  Engineering with a known design, not an open question — route through change-control
  when the owner wants it.
- **Community-pulse features:** KILLED 2026-08-14. Revival trigger = organic strangers
  sharing + a min-N gate + owner sign-off. Do not reopen without the trigger.

## Priority map (as of 2026-08-14)

| Problem | Startable today, fully offline? | Needs real players? |
|---|---|---|
| 1 difficulty calibration | Steps 1–2 now | Step 3's shares — yes |
| 2 replay validator | **Yes — entirely, today; binary outcome** | No |
| 3 pair-quality score | Steps 1–2 now | Optional judgment calibration |
| 4 soft-fail caddy | **No — gated on measured DNF** | Yes, by definition |

Cheapest first result: **2** (one Node script over modules that already run in Node).
Everything above assumes the owner re-confirms the tracks — the 2026-07-02 choices
(automated curation / novel modes / scale & integrity) were made for a game that no longer
exists, even though all four problems above are their honest descendants.

## Settled decisions this file must not re-open

- **No accounts, no leaderboards, no server** — owner decisions from the 2026-08-14
  Comeback Loop plan. Problem 2 exists *because* of them, not despite them.
- **Matcher craft is excluded** (owner, 2026-07-02, still honored): `docs/match.js` is
  maintained via its contract table (`match.cases.js` + `match.test.js`), not advanced.
- **Per-challenge subgraphs — REJECTED** (July prototype): shipping the subgraph handed the
  player the answer via autocomplete. The whole-corpus ship is the fix; don't propose
  subgraphs for payload reasons. See degreesoffilm-failure-archaeology.
- **Spoiler discipline + immutable past:** no experiment edits a published daily dated
  ≤ today; no writeup, commit, or committed artifact names a future daily's chain.

## When NOT to use this skill

- How a change lands, sign-off, branch-vs-main → **degreesoffilm-change-control**.
- Running an experiment properly (evidence bar, hypothesis cards) →
  **degreesoffilm-research-methodology**.
- Proof recipes (parity, enumerability, replay arguments) →
  **degreesoffilm-proof-and-analysis-toolkit**.
- What was tried and killed → **degreesoffilm-failure-archaeology**.
- Current behavior and vocabulary → **degreesoffilm-domain-reference**; invariants and
  zones → **degreesoffilm-architecture-contract**.
- Test standards and the suite inventory → **degreesoffilm-validation-and-qa**.
- Public claims, TMDB attribution, competitor comparisons →
  **degreesoffilm-external-positioning**.
- Where to document results → **degreesoffilm-docs-and-writing**.

## Provenance and maintenance

- **Written 2026-07-03; rewritten 2026-08-14, re-verified after the degrees rebuild.** The
  dig-era tracks (auto-crop, decoys, Movie Buff index) were deleted with their assets;
  static degrees-of-separation shipped as the product. Asset claims verified against the
  working tree 2026-08-14: `curation/challenge_gen.py` (`par_for_date`/`WEEKLY_ARC`,
  `pick_pair` with `DEFAULT_TOP=900`/`MIN_ROUTES=2`, `too_similar`, `count_routes`,
  `par_closers`, `note_violations`, sidecar `"routes"` field), `docs/solve.js`
  (`obscurity` 0–99, `countGeodesics`, `shortestChain`), `docs/chain.js` (pure `Chain`,
  `toJSON`/`fromJSON`, `nearMiss`), `docs/stats.js` (histogram/handicap/`recordArchive`),
  `docs/app.js` `shareText` (frozen line 1), CLAUDE.md "Share grammar",
  project_state.md open items (caddy gate, role glyphs, community-pulse trigger).
- Owner-intent caveat: the recast problem list is a reconciliation, **not re-confirmed
  owner tracks** — get that confirmation before major investment.
- **Maintenance rule:** when an item is promoted (built) or retired (killed), move its story
  to project_state.md / degreesoffilm-failure-archaeology, delete or relabel the entry
  here, and update this date — this file must only ever contain OPEN/CANDIDATE work.
