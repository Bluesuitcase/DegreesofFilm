---
name: degreesoffilm-validation-and-qa
description: The evidence bar for the Degrees of Film repo — what "proven" means before any change lands. Load this when a change was just made and the question is "is this enough evidence?"; when asking "which tests do I run for file X?" or "how do I add a test here?"; before landing ANY change (there is no CI — green suites are a manual gate); after touching the matcher (docs/match.js — contract-first rule via match.cases.js), the chain rules (docs/chain.js), the corpus encoding (docs/corpus.js / curation/graph_build.py), or challenge generation (curation/challenge_gen.py); when doing pre-publish content QA on new dailies; or when tempted to weaken/delete a failing assertion. Contains the 9-suite inventory with the per-file reverse map, the house test-writing pattern (JS + Python skeletons), the golden inventory (the match.cases.js contract table, the frozen share line-1 grammar, the two --check validators), and the content-ops QA gate.
---

# Degrees of Film — validation and QA

**There is no CI.** Nothing runs the tests except you, and pushes to `main` touching
`docs/` deploy straight to live players. Discipline is the only enforcement layer, and
this skill defines it: what counts as evidence, which suites to run for which file,
how to add tests in the house style, and what content must pass before it publishes.

## 1. The evidence bar — when is a change proven?

A change is proven when ALL of the applicable lines below hold. Skipping one because
"it's a small change" is how repos like this accumulate silent breakage.

| # | Evidence | Applies to | How |
|---|---|---|---|
| E1 | **Relevant suites green** | every change | Reverse map in §2 — run the suites for each file you touched. When in doubt, run all 9 (they finish in seconds, offline, no key). |
| E2 | **New test, red→green** | any changed/new behavior | Write the test FIRST, watch it FAIL against the old code, then make it pass. A test that never failed proves nothing — it may be asserting the bug. State "failed before, passes after" in your handoff. |
| E3 | **Browser check** | any player-visible change (`docs/`) | Serve `docs/` (the `docs` entry in `.claude/launch.json`, port 8010, or `python -m http.server 8010 --directory docs` — `file://` won't work, the game uses `fetch`) and exercise the change. Beware ES-module caching per origin:port — a stale tab can show OLD code and produce false verdicts; hard-reload or use a fresh port. |
| E4 | **Content validators green** | any content change (corpus rebuild, daily publish/edit, note) | `python curation/challenge_gen.py --check` (and `python curation/graph_build.py --check` after a corpus rebuild). §4–5. |

**"Tests pass" alone is NOT evidence for uncovered behavior.** The suites cover the
pure modules only. The following have **zero automated tests** — for them, E3-style
manual verification is the *only* gate (found by listing `docs/*.js` against the
suites, re-verified 2026-08-14):

- `docs/app.js` — ALL DOM glue: routes (`?play`/`?id=N`/`?archive`/`?history`),
  rendering, `shareText()` (the frozen grammar's implementation, §4), animations,
  the localStorage wiring for run persistence.
- `docs/index.html`, `docs/style.css` — markup ids the JS binds to; the theme vars.
- `docs/stats.js` `loadStats`/`saveStats` — the localStorage halves. Only the pure
  functions (`recordResult`, `recordArchive`, `exportRecord`/`importRecord`, …) are
  covered by `stats.test.js`.
- `curation/tmdb.py` — the network client, no suite. `harvest.test.py` imports it
  transitively (via `harvest`), so a *syntax* error fails at import time, but its
  behavior (paging, key loading) is only verified by a live harvest.
- The curation `__main__` blocks' network paths (`harvest.py`'s TMDB sweep).

Every other `docs/*.js` module has a dedicated suite: match, corpus, chain, solve,
daily, stats. If your change lives in an untested surface, say so explicitly in your
report and describe the manual verification you did. Do not imply coverage that does
not exist.

## 2. Test inventory and reverse map

**9 suites.** No framework, no npm scripts (`package.json` is only `{"type":"module"}`),
no network, no API key, no venv. Every suite prints `PASS`/`FAIL` lines, ends with
`N passed, M failed`, and exits non-zero on any failure. All commands run from the
repo root. **Do not trust cached counts — run them; each suite prints its own count**
(CLAUDE.md and the suites own the numbers; they drift every wave).

| Suite | Module(s) guarded | Command |
|---|---|---|
| `match.test.js` | `docs/match.js` — the fairness contract; **the case table lives in `match.cases.js`** | `node match.test.js` |
| `daily.test.js` | `docs/daily.js` — `pickPuzzle` date logic, `pickById` | `node daily.test.js` |
| `stats.test.js` | `docs/stats.js` (pure half) — streak, scorecard, golf labels, handicap, backup codes | `node stats.test.js` |
| `corpus.test.js` | `docs/corpus.js` — decoding, resolution, suggestions; **plus real-asset invariants against the shipped `docs/graph.json`** (structural only, never a specific title, so a rebuild can't break it) | `node corpus.test.js` |
| `chain.test.js` | `docs/chain.js` — verdicts, forged chains, `back()`, par (against a synthetic Corpus) | `node chain.test.js` |
| `solve.test.js` | `docs/solve.js` — shortest route, geodesic count, obscurity | `node solve.test.js` |
| `harvest.test.py` | `curation/harvest.py` (pure parts) | `python curation/harvest.test.py` |
| `graph_build.test.py` | `curation/graph_build.py` — prune, rank, encode, validate | `python curation/graph_build.test.py` |
| `challenge_gen.test.py` | `curation/challenge_gen.py` — BFS path, pair picking, par arc, note rule | `python curation/challenge_gen.test.py` |

Plus two shipped-artifact validators (not suites, same green-required standing):
`python curation/graph_build.py --check` and `python curation/challenge_gen.py --check` (§4).

Run-everything one-liners (Git Bash, repo root):

```bash
for t in match daily stats corpus chain solve; do node $t.test.js || echo "** $t FAILED"; done
for t in harvest graph_build challenge_gen; do python curation/$t.test.py || echo "** $t FAILED"; done
```

### Reverse map — changed file X ⇒ run suites Y

Derived from the actual import graph (re-read 2026-08-14: `docs/match.js` imports
nothing; `docs/corpus.js` imports only `match.js`; `docs/chain.js` and `docs/solve.js`
import nothing and take a corpus; `chain.test.js`/`solve.test.js` build fixtures via
`Corpus`, so they load corpus.js and match.js transitively;
`curation/challenge_gen.py` imports `graph_build`; `curation/harvest.py` imports `tmdb`).

| Changed file | Run | Also required |
|---|---|---|
| `docs/match.js` | `match.test.js` + `corpus.test.js` (`corpus.resolve` builds on normalize/levenshtein); `chain.test.js` + `solve.test.js` load it transitively — run all four | **Contract-first rule, §3** |
| `match.cases.js` | `match.test.js` | Adding rows is the §3 rule working; editing existing rows is change-control |
| `docs/corpus.js` | `corpus.test.js` + `chain.test.js` + `solve.test.js` (both fixture through `Corpus`) | E3 |
| `docs/chain.js` | `chain.test.js` (solve.js does NOT import chain) | E3 — rules changes are owner-sign-off territory |
| `docs/solve.js` | `solve.test.js` | E3 (end-card reveal is player-visible) |
| `docs/daily.js` | `daily.test.js` | E3 |
| `docs/stats.js` | `stats.test.js` | E3 — the load/save localStorage halves are untested |
| `docs/app.js` / `index.html` / `style.css` | — no suite exists — | **Manual gate only**: E3 walk of every affected route; if `shareText()` touched, §4 G2 |
| `docs/graph.json` (rebuilt) | `python curation/graph_build.py --check` + `node corpus.test.js` (real-asset invariants) | `python curation/challenge_gen.py --check` — a rebuild can drop a daily's endpoint from the pool |
| `docs/challenges.json` | `python curation/challenge_gen.py --check` | Spoiler-safe commit (§5) |
| `curation/harvest.py` | `harvest.test.py` | Network path: manual (one live harvest) |
| `curation/graph_build.py` | `graph_build.test.py` + `challenge_gen.test.py` (imports graph_build) + `graph_build.py --check` | If you rebuilt graph.json: the `docs/graph.json` row above |
| `curation/challenge_gen.py` | `challenge_gen.test.py` + `challenge_gen.py --check` | |
| `curation/tmdb.py` | `harvest.test.py` (import-time smoke only) | **Manual gate**: run a live harvest against one endpoint |

## 3. How to add a test

House style: **plain scripts, tiny `check` helper, PASS/FAIL lines, summary, non-zero
exit.** No framework, no test runner, no new dependencies. Copy an existing suite.

**JS skeleton** — the real `check` helper quoted from `chain.test.js`:

```js
import { Corpus } from './docs/corpus.js';
import { Chain, CHAIN_MAX_ATTEMPTS } from './docs/chain.js';

let pass = 0, fail = 0;
function check(label, got, want) {
  const g = JSON.stringify(got), w = JSON.stringify(want);
  const ok = g === w;
  ok ? pass++ : fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${ok ? '' : `  (got ${g}, want ${w})`}`);
}
```

New JS suites live at the **repo root** as `<module>.test.js`, importing from
`./docs/<module>.js` (the root `package.json`'s `"type": "module"` exists solely to
make these imports work). Update CLAUDE.md's test list when you add one.

**Python skeleton** — the real header + `check` helper quoted from
`curation/graph_build.test.py`:

```python
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graph_build as gb  # noqa: E402

passed = failed = 0


def check(label, got, want):
    global passed, failed
    ok = got == want
    passed, failed = passed + (1 if ok else 0), failed + (0 if ok else 1)
    print(f"{'PASS' if ok else 'FAIL'}  {label}"
          + ("" if ok else f"\n        got:  {got!r}\n        want: {want!r}"))
```

New Python suites live in `curation/` as `<module>.test.py`. **They must stay
network-free and key-free** — everything must run with no `curation/.env` and no
TMDB. Established techniques, all visible in current suites: synthetic corpora built
inline (`chain.test.js` hand-writes a 7-film `Corpus` whose comment explains why par
really is 2); temp dirs for file I/O; never write into `docs/` from a test.

**Where new logic must live to be testable:** in a pure module — no DOM, no `fetch`,
no localStorage in the logic path. That is the layering law (CLAUDE.md +
degreesoffilm-architecture-contract): `docs/app.js` is thin glue precisely so
everything decision-shaped is importable by these suites. If you want to test
something inside `app.js`, extract it into a pure module first — do not build a DOM
harness.

> **NON-NEGOTIABLE — the matcher contract-first rule (from CLAUDE.md):**
> `match.cases.js` IS the specification of what feels fair to a player
> (`[guess, answers, expected, label]` rows; `match.test.js` replays them). Before
> touching the algorithm in `docs/match.js`, add the new row(s) to the table, run the
> suite, watch them FAIL, then change the algorithm and land with the whole table
> green. The pre-existing rows are prior fairness decisions (foreign titles, typo
> tolerance, surname-only, wrong-surname rejection) and none may regress.

## 4. Golden inventory — frozen artifacts; changing them is change-control territory

**G1 — the `match.cases.js` contract table.** The matcher contract as data. Rows are
add-only in normal work; editing or deleting an existing row is a fairness-rules
change (owner sign-off per degreesoffilm-change-control). The table survived the
rebuild verbatim from the dig game — its answer fixtures still reference the retired
puzzle 001, which is fine: they are test data, not live content.

**G2 — the FROZEN share line-1 grammar** (CLAUDE.md "Share grammar"; implemented by
`shareText()` in `docs/app.js`). Accountless leagues — Discord bots parsing
group-chat shares — depend on line 1; changing it breaks every parser silently.
Frozen 2026-08-14: line 1 may only ever GAIN content after the final `)`. **No suite
guards this** (`app.js` is untested) — any `shareText()` edit gets a manual
before/after diff of the emitted string against the grammar block in CLAUDE.md.

**G3 — `python curation/challenge_gen.py --check`, the content golden.** Re-derives
every published daily's par by BFS against the shipped corpus, confirms the cached
titles still resolve, and HARD-enforces the curator's-note rule (a note must never
name anything on any geodesic — checked against every possible closer plus the
solutions sidecar). Green output ends `N dailies, 0 broken`. Run it after ANY corpus
rebuild and before ANY content commit.

**G4 — `python curation/graph_build.py --check`.** Re-validates the shipped
`docs/graph.json` (decode round-trip, counts, structure) and prints the corpus line
(films/people/size). Pairs with `corpus.test.js`'s real-asset invariants, which
assert structure from the JS side without pinning any title.

## 5. Content QA — the gate before dailies publish

The commands and their order live in CLAUDE.md "Content operations" — don't duplicate
them; this section is the *gate*:

1. **Generate:** `python curation/challenge_gen.py --days N` (the weekly par arc is
   the default; solutions go to the gitignored sidecar).
2. **Verify:** `python curation/challenge_gen.py --check` green — every daily's par
   re-derived, titles resolve, any curator's notes pass the never-name-a-connector
   rule. Write notes by hand; `--check` is the enforcement, not a substitute for
   reading your own note.
3. **Spoiler-safe commit:** this repo is PUBLIC. Never name a future daily's chain in
   a commit message; `curation/challenge_solutions.json` is gitignored and must stay
   that way. (Shipping future *pairs* in `challenges.json` is accepted posture — the
   pair is the prompt, not the answer.)
4. **After any corpus rebuild** (`graph_build.py`), re-run `--check` — film ids are
   stable, but this catches a daily whose endpoint fell out of the pool.

## 6. Acceptance thresholds

- **All 9 suites green, always, before landing anything.** No "unrelated failure"
  exemption — with no CI, a tolerated red suite is indistinguishable from a broken
  repo. If a suite is red for a reason you didn't cause, STOP and fix or escalate
  before landing; never land on top of red.
- **Never weaken or delete an assertion to get to green** without explicit sign-off
  through degreesoffilm-change-control. Existing assertions encode prior decisions
  (fairness rows, verdict semantics, `back()`'s no-refund rule, the note rule). A red
  assertion is a question — "did you mean to change this behavior?" — and the answer
  belongs to the owner for anything player-facing.
- **Count drift: up is fine, down is suspicious.** Each suite prints its own count;
  the last-known total lives in project_state.md. A count LOWER than last session's
  means tests were deleted or silently not running (an import error swallowed) —
  investigate before anything else.
- **Content thresholds:** both `--check` commands exit 0; `challenge_gen --check`
  reports `0 broken`.
- **Evidence in handoffs:** when reporting a change done (project_state.md, PR body),
  name which suites you ran and the red→green fact for new tests. "All tests pass"
  without naming them is below the bar here.

## When NOT to use this skill

- Whether/how a change may land, commit/PR conventions, rollback → **degreesoffilm-change-control**
- What an invariant is and why (layering law, key confinement, zone boundaries) → **degreesoffilm-architecture-contract**
- Session handoffs, doc ownership, spoiler-safe writing conventions → **degreesoffilm-docs-and-writing**
- Matching/TMDB theory behind the tested behavior, glossary → **degreesoffilm-domain-reference**
- Public claims, attribution, share-string external posture → **degreesoffilm-external-positioning**
- Why a past approach was rejected → **degreesoffilm-failure-archaeology**
- How to PROVE a design claim from first principles → **degreesoffilm-proof-and-analysis-toolkit**
- What to build next / research-grade ideas → **degreesoffilm-research-frontier**
- Turning a hunch into an accepted result → **degreesoffilm-research-methodology**

## Provenance and maintenance

- Written 2026-07-03 for the dig game (16 suites). **Rewritten 2026-08-14, re-verified
  after the degrees rebuild:** all 9 suites RUN that day from the repo root (268
  assertions, all green), both `--check` validators RUN green (`graph_build --check`:
  3,682 films / 9,791 people / 190 KB gz; `challenge_gen --check`: 64 dailies, 0
  broken). Import graph re-read from the source files; skeletons quoted verbatim from
  `chain.test.js` and `curation/graph_build.test.py`; untested-surface list rebuilt by
  listing `docs/*.js` against the suites.
- Re-verify: the two run-everything one-liners in §2 + both `--check` commands.
- If you add a suite or extract logic from `app.js` into a tested module, update §2
  (and §1's gap list) plus this date in the same session. Per-suite assertion counts
  are deliberately NOT cached here — the suites print them.
