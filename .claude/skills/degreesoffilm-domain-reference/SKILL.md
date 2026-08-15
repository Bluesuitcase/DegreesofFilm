---
name: degreesoffilm-domain-reference
description: >-
  Domain-theory reference for Degrees of Film — the concepts a mid-level engineer
  or model won't already know, grounded in this repo's code. Load it WHEN: any
  question about TMDB as this repo uses it (the two live endpoints, credit
  fields, billing order vs popularity, the vote_count/vote_average pool floor);
  why a player's guess matched or didn't (normalization, Levenshtein, typo
  tolerance, surname rule, contextual-vs-global resolution); BEFORE changing
  docs/match.js or docs/corpus.js resolution in any way; daily rollover, streak,
  replay, or share behavior; or when a project term (degree, hop, par, geodesic,
  obscurity, glyph trail, pool floor, runway, sidecar…) needs a definition — the
  canonical glossary lives here. NOT for landing changes
  (degreesoffilm-change-control), zone/layering invariants and schemas
  (degreesoffilm-architecture-contract), test inventory and QA
  (degreesoffilm-validation-and-qa), or TMDB terms/attribution/rights
  (degreesoffilm-external-positioning).
---

# Degrees of Film — domain reference

This skill teaches the *theory* behind the project's specialty domains — TMDB's
data model as harvested here, fuzzy string matching plus the corpus resolution
layer above it, the shipped graph's encoding, and daily-game conventions —
exactly as this repo uses them. Every behavioral claim is cited to a repo file;
worked examples were executed on the date shown. It explains *why the code is
the way it is*; for changing things see `degreesoffilm-change-control`, for the
architecture invariants see `degreesoffilm-architecture-contract`.

The game (since the 2026-08-11 rebuild): connect two films by alternating
person/film hops through shared credits; degrees vs par, golf-style. No images
anywhere. `CLAUDE.md` is the ruleset of record.

## 1. Glossary (canonical — other skills point here)

| Term | Meaning here |
|---|---|
| **hop** | One legal move: film → a person credited on it, or person → another film they worked on (`docs/chain.js` `legalMoves`). |
| **chain** | The alternating film/person path from the start film. It closes when you name a person who is *also credited on the goal film* — you never step into the goal (`docs/chain.js`). |
| **degree** | One person step taken. The brag number (`Chain#degrees`). |
| **par** | The fewest degrees any chain needs, BFS'd at build time over the same shipped corpus the player plays (`curation/challenge_gen.py` `degrees_between`); the end card re-derives it client-side (`docs/solve.js` `degreesBetween`). |
| **golf labels** | `relativeLabel` → `E` / `+n` / `−n` (U+2212 minus) and `verdictName` → Albatross…Double bogey (`docs/stats.js`). |
| **verdict** | `Chain#guess` results: `correct`, `won`, `wrong`, `unknown`, `over`, `ignored`, with `reason` ∈ `notCredited`, `used`, `wrongType`, `goalFilm`, `unrecognized`. Only `wrong` burns an attempt — typos and category slips are free (`docs/chain.js`). |
| **attempt / burn** | 3 attempts per step (`CHAIN_MAX_ATTEMPTS`); the third burn is verdict `over` and ends the run. |
| **back()** | Abandon the current person and return to the previous film. The degree stays spent and the person stays blocked — no refunds, like a golf stroke (`docs/chain.js` `back`). |
| **near-miss** | Temperature on a burned guess: graph distance d=1 (with a witness *year*, never a name) / d=2 / d=3+, depth-capped at 2 so three burns can't triangulate (`docs/chain.js` `nearMiss`). |
| **corpus** | `docs/graph.json` `{v, ids, films, people, cast}` — the *entire* pool in one cached download, so a challenge is ~50 bytes and the shipped data says nothing about today's answer. Built by `curation/graph_build.py`, loaded by `docs/corpus.js`. Current counts/size: `CLAUDE.md` or `python curation/graph_build.py --check`. |
| **pool floor** | Corpus admission bar: TMDB `vote_count >= 500 AND vote_average >= 6.0` (`curation/harvest.py` `POOL_MIN_VOTES` / `POOL_MIN_AVG`; widened from 800/6.5 on 2026-08-15). |
| **prune / connector** | A person credited on fewer than 2 distinct pool films can never be a hop, so they're dropped (~67% of harvested people) — `graph_build.py` `MIN_FILMS_PER_PERSON`, `connector_ids`. Films left with no connector drop too. |
| **delta-hex encoding** | Each film's cast ships as comma-separated hex gaps between ascending person indices (`"3,1,2b"`). Encoder `graph_build.encode_deltas`; the four-line decoder is mirrored in both languages (`graph_build.decode_deltas` ↔ `corpus.js` `decodeDeltas`). |
| **rank order** | Array index order *is* popularity order for both films and people, so "first hit wins" means "most famous wins" and no rank field ships (`corpus.js` header; `graph_build.rank_people`). |
| **contextual vs global resolution** | `corpus.resolve`: a guess is read first against the legal hops (scope `'here'`), then the whole pool (scope `'elsewhere'`), so the game can tell "not a real person" from "real, but not in this film". See §3.5. |
| **surname rule** | A single-token guess matches the *last* token of a multi-token name — "Bardem", never "Javier" (`docs/match.js`; `corpus.js` `lastTokenMatch`). |
| **daily / replay / archive** | `?play` = today via `daily.js` `pickPuzzle`; `?id=N` = replay a past daily; `?archive` lists them. Replays record only into the isolated `archive` channel (`stats.js` `recordArchive`, keyed by id, keep-better) — never the streak, histogram, or scorecard. |
| **streak / scorecard / handicap** | `stats.js`: `recordResult` is a pure, idempotent-per-date fold; `handicap` = rolling average vs par, losses count `LOSS_PENALTY = 3`, `null` under 10 recorded rounds. localStorage key `dof-degrees-v1`. |
| **obscurity** | 0–99 deep-cut score of a winning route's people; fame proxy = pool credit count, per-person score = geometric blend of midpoint-rank percentile and log-scale position (`docs/solve.js` `obscurity`; calibrated 2026-08-14: hubs 0, floor ≈ 88). |
| **glyph trail** | Share line 3: 🔗 completed degree · 🟥 burned attempt · ↩ back-up, in play order, names never included; >14 glyphs compress. Line 1 of the share is FROZEN — grammar lives in `CLAUDE.md` "Share grammar". |
| **curator's note** | Optional one-sentence `note` on a daily, shown only on the end card but shipped publicly in advance. Texture only — it must never name any possible closer or anything on the sidecar chain; `challenge_gen.py --check` enforces this (`note_violations` vs `par_closers`). |
| **geodesic** | A shortest (par-length) chain. `solve.js` `countGeodesics` counts distinct full sequences ("N distinct ways", capped at 1000); generation requires ≥ `MIN_ROUTES = 2` distinct *closing people* (`challenge_gen.count_routes`) so a daily is a game, not a needle. |
| **runway** | How many consecutive future dailies are already scheduled in `docs/challenges.json`. Restock with `challenge_gen.py --days N` before it empties; current runway is tracked in `project_state.md`. |
| **sidecar** | `curation/challenge_solutions.json` — gitignored solution chains keyed by daily id. This repo is public; the sidecar must never be committed. |

## 2. TMDB as used here

TMDB (The Movie Database) is a community film database with a free v3 REST API.
This repo calls it **only from the private curation pipeline** — never from the
player client. The key lives in gitignored `curation/.env`; `curation/tmdb.py`
(stdlib-only) passes it as an `api_key=` query parameter and **never logs a
URL** (URLs carry the key) — its 401 handler reports only
`HTTP 401 (check your TMDB_API_KEY) on {path}`.

The surviving pipeline uses exactly **two endpoints**, both from
`curation/harvest.py`:

| Endpoint | Used for | Fields consumed |
|---|---|---|
| `GET /discover/movie` | Sweep every film clearing the pool floor (`vote_count.gte=500`, `vote_average.gte=6.0`, `sort_by=popularity.desc`, `include_adult=false`), paging to at most 500 pages | `results[].{id, title, release_date}`, `total_pages` |
| `GET /movie/{id}?append_to_response=credits` | One call per new film for its key credits | `credits.cast[:12].{id, name, popularity}`; `credits.crew[].{id, name, popularity}` where `job` ∈ Director, Director of Photography, Original Music Composer, Editor, Production Design |

"Key credits" = the **top 12 billed cast** (the cast array's own order is
billing order; the slice `[:cast_top]` trusts it) plus those five exact-string
crew jobs (`harvest.py` `CAST_TOP`, `CREW_JOBS`, `extract_people`). Per-credit
`popularity` is kept only to become the corpus **rank** — a person's rank is
their max across credits (`graph_build.rank_people`). **No image fields are
fetched or stored** — the rebuilt game ships no images at all.

Both caches (`films_cache.jsonl`, `people_harvest_cache.jsonl`) are append-only
and gitignored: a refresh fetches only films it hasn't seen.

Per-endpoint parameter detail: [`references/tmdb.md`](references/tmdb.md).
Attribution obligations, terms, and the commercial line:
`degreesoffilm-external-positioning`.

## 3. Fuzzy matching theory (`docs/match.js` + `docs/corpus.js`)

`match.js` decides whether the game *feels fair*. It has **no imports** (bottom
of the layering law) and survived the rebuild **unchanged**; its contract lives
as data in `match.cases.js` (25 rows), run by `match.test.js`.
**Rule: add a failing case to `match.cases.js` before touching the algorithm.**

### 3.1 Normalization pipeline

`normalize(s)` canonicalizes both the guess and every candidate before any
comparison, so film knowledge is tested, not orthography. The stages, in order
(`docs/match.js` lines 4–13), with an executed trace (re-verified 2026-08-14):

| Stage | Operation | `"Amélie"` | `"The Lord of the Rings: The Return of the King"` | `"Joel & Ethan Coen"` |
|---|---|---|---|---|
| 1 | lowercase | `amélie` | `the lord of the rings: the return…` | `joel & ethan coen` |
| 2 | NFD-decompose, strip combining marks U+0300–U+036F (removes diacritics) | `amelie` | *(unchanged)* | *(unchanged)* |
| 3 | `&` → `" and "` | — | — | `joel  and  ethan coen` |
| 4 | non-`[a-z0-9\s]` → space (punctuation gone; note the colon) | — | `the lord of the rings  the return…` | — |
| 5 | collapse whitespace, trim | — | `the lord of the rings the return of the king` | `joel and ethan coen` |
| 6 | drop ONE leading article (`the`/`a`/`an`) | — | `lord of the rings the return of the king` | — |

Stage 2 works because Unicode NFD splits `é` into `e` + a combining accent, and
combining accents live in U+0300–U+036F — deleting them leaves the base letter.
Stage 6 removes only a *leading* article, once: interior "the"s survive (see the
LOTR trace). Non-Latin scripts normalize to empty (every char is punctuation to
stage 4); `matchGuess` skips empty candidates, so a non-Latin alternate is
inert, not harmful.

### 3.2 Levenshtein distance and `maxDist`

**Levenshtein distance** = the minimum number of single-character insertions,
deletions, or substitutions to turn one string into another (each costs 1 —
no transposition operation, so `teh`→`the` costs 2, not 1). `docs/match.js`
implements the classic DP with the **two-row optimization** — O(m·n) time,
O(n) memory.

A guess is accepted when `levenshtein(guess, answer) <= maxDist(answer.length)`
(both post-normalization). Tolerance scales with the target's length because a
fixed budget would be useless for long titles or catastrophic for short ones:

| normalized length | `maxDist` | intuition |
|---|---|---|
| ≤ 3 | 0 | `Up`, `Her`: any edit is a different word |
| ≤ 6 | 1 | one typo in a short name |
| ≤ 10 | 2 | `deakins`-scale names |
| > 10 | `floor(len * 0.2)` | ~1 typo per 5 chars |

Executed (re-verified 2026-08-14): `levenshtein("javier bardum","javier
bardem")` = **1**, `maxDist(13)` = **2** → "Javier Bardum" matches.
`maxDist(23)` = **4**, so "No Country for Old Man" (distance 1) matches the
full title. The generous 20% band is deliberate: candidates are proper nouns
from a closed pool, so near-misses are almost always the intended name.

### 3.3 The surname rule

If the guess is a **single token** and equals the **last token** of a
multi-token candidate, it matches (`docs/match.js` lines 49–52): players say
"Bardem", not "Javier Bardem". Executed (re-verified 2026-08-14):

- `matchGuess("Bardem", ["Javier Bardem"])` → `true`
- `matchGuess("Joel", ["Joel Coen"])` → **`false`** — first names do NOT match;
  "Joel" is not the *last* token.
- `matchGuess("Roger Moore", ["Roger Deakins"])` → `false` — two tokens, so the
  rule never fires; `match.cases.js` pins "right first name wrong surname" as a
  rejection.

Last-token-only means double surnames credit only the final token ("García
Bernal" → only "Bernal" works solo); the matcher gets no special cases for
this — alternate forms are a data problem (extra `answers[]` strings in the
contract table), never new matcher branches.

### 3.4 What the matcher deliberately does NOT do

No phonetic matching (Soundex/Metaphone), no token reordering ("Bardem Javier"
fails), no substring/containment matching, no per-context thresholds. Each
would widen false-accepts in hard-to-reason-about ways. That keeps the
algorithm small, testable, and shared by every caller — in the shipped game
`corpus.resolve` (below) supplies the context-awareness instead.

### 3.5 The resolution layer (`docs/corpus.js` `resolve`) — new since the rebuild

`corpus.resolve` sits above the matcher and its **asymmetry is deliberate**
(`corpus.js` `resolve`, `lastTokenMatch`, `fuzzy`):

- **In context** (`within` = the handful of legal hops): exact → typo →
  last-word with mode `'any'`. "Bardem" or "Fiction" is unambiguous among a
  dozen candidates, and the best-ranked hit wins.
- **Globally** (the whole pool of ~10k names): exact → typo → last-word
  **only if exactly one pool name ends that way** (mode `'unique'` refuses on
  ambiguity). Executed 2026-08-14: `resolvePerson('smith', null)` → `null` —
  55 pool names end in "smith", so a bare "smith" resolves to nothing rather
  than silently to whichever Smith ranks highest.
- Returns `{index, scope}` with scope `'here'` (a legal hop) or `'elsewhere'`
  (real, but not playable from here), or `null` — which is what lets `chain.js`
  distinguish a burn (`wrong`/`notCredited`) from a free miss
  (`unknown`/`unrecognized`).
- Index order is rank order, so "first hit wins" = "most famous wins" — that is
  how duplicate titles like *Heat (1995)* vs *Heat (1986)* resolve, and why
  context beats rank when the lower-ranked one is the legal hop.
- The fuzzy scan uses a cheap length-difference prefilter before computing
  Levenshtein; worst case (a guess matching nothing, scanning every name)
  measures **~5 ms** — asserted in `corpus.test.js`.
- **Suggestions are global, resolution is contextual**: autocomplete
  (`Corpus.suggest*`) always draws from the whole pool — suggesting only valid
  hops would hand the player the answer.

## 4. Daily-game conventions

**Daily selection** (`docs/daily.js`, pure): `pickPuzzle` takes the entries in
`docs/challenges.json` and picks an exact date match → else the most recent
entry on or before today → else the earliest. An empty day re-shows the latest
daily rather than erroring. `todayISO()` uses the **device-local date** — the
rollover is per-device, not global. `?id=N` replays via `pickById`.

**Streak honesty** (`docs/stats.js`, pure): `recordResult` folds one finished
daily in, idempotent per date (`lastDate === date` → no-op); day gaps use
UTC-parsed dates (DST-proof); gap of exactly 1 extends the streak, else reset.
`recomputeStreak` settles the number at load so missed days can't show a stale
streak, and `streakState` drives the at-risk nudge. Replays and backups merge
through `recordArchive` / `importRecord` + `rebuildStats` (derived fields are
always recomputed from history, never patched).

**Share discipline**: the share string's **line 1 is frozen** — external
parsers (Discord-bot leagues) depend on it; the grammar of record is in
`CLAUDE.md` "Share grammar", implemented by `shareText()` in `docs/app.js`.
Names never appear in the glyph trail.

**Spoiler posture**: the shipped corpus is *everything*, so nothing about
today's answer ships beyond the pair itself; solutions live only in the
gitignored sidecar; curator's notes are machine-checked against every possible
closer; commit messages never name a future daily's chain.

## When NOT to use this skill

| You actually need | Go to |
|---|---|
| The zone/layering invariants and data contracts | `degreesoffilm-architecture-contract` |
| How to land a change (gates, branches, rollback) | `degreesoffilm-change-control` |
| Which doc owns a fact; commit/PR style | `degreesoffilm-docs-and-writing` |
| TMDB terms, attribution wording, rights posture | `degreesoffilm-external-positioning` |
| Why past ideas were rejected (full stories) | `degreesoffilm-failure-archaeology` |
| How to prove a claim before building on it | `degreesoffilm-proof-and-analysis-toolkit` |
| What to build next / research-grade ideas | `degreesoffilm-research-frontier` |
| Turning a hunch into an accepted result | `degreesoffilm-research-methodology` |
| Test inventory, adding tests, QA checklists | `degreesoffilm-validation-and-qa` |

## Provenance and maintenance

- **Written 2026-07-03**; **rewritten and re-verified 2026-08-14** after the
  degrees-of-separation rebuild (the dig game, its image/color tooling, cipher,
  and manifest are deleted — sections covering them were removed). All quoted
  behavior read directly from the cited files that day; `match.test.js` (25)
  and `corpus.test.js` (35) run green; the §3 probes (surname rule, typo
  distances, LOTR normalize, global-"smith" refusal) executed against
  `docs/match.js` / `docs/corpus.js` + the shipped `docs/graph.json`.
- Corpus counts, sizes, and runway drift by design — read them from `CLAUDE.md`
  / `project_state.md` or run `python curation/graph_build.py --check` and
  `python curation/challenge_gen.py --check`; this skill deliberately avoids
  caching them.
- **Re-verify drift-prone facts** (repo root):
  - Matcher + resolution: `node match.test.js && node corpus.test.js`
  - Surname/first-name rule: `node -e "import('node:url').then(u => import(u.pathToFileURL('docs/match.js').href)).then(m => console.log(m.matchGuess('Joel', ['Joel Coen']), m.matchGuess('Coen', ['Joel Coen'])))"` → expect `false true` (the `pathToFileURL` form avoids Windows backslash traps)
  - Chain verdicts / stats / dailies: `node chain.test.js && node stats.test.js && node daily.test.js`
  - Pool floor + harvest shape: `grep -n "POOL_MIN\|CAST_TOP\|CREW_JOBS" curation/harvest.py`
  - Prune + encoding: `grep -n "MIN_FILMS_PER_PERSON\|encode_deltas" curation/graph_build.py`
- If any cited file changes behavior, update the matching section AND this date.
