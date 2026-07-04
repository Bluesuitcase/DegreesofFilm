---
name: degreesoffilm-validation-and-qa
description: The evidence bar for the Degrees of Film repo — what "proven" means before any change lands. Load this when you just made a change and must decide "is this enough evidence?", when asking "which tests do I run for file X?", "how do I add a test here?", or "is tests-pass sufficient?"; before landing ANY change (there is no CI — green suites are a manual gate); after touching the matcher (match.js — contract-first rule), game rules (game.js), or the cipher (docs/cipher.js / curation/cipher.py — BOTH languages' suites required); when doing pre-publish content QA on a new puzzle; or when tempted to weaken/delete a failing assertion. Contains the full 16-suite inventory with per-file reverse map, the house test-writing pattern (JS + Python skeletons), the golden/certified inventory (frozen cipher vector, puzzle 001, the scoring curve), and the per-puzzle content QA checklist.
---

# Degrees of Film — validation and QA

**There is no CI.** Nothing runs the tests except you, and pushes to `main` touching
`docs/` deploy straight to live players. Discipline is the only enforcement layer, and
this skill defines it: what counts as evidence, which suites to run for which file,
how to add tests in the house style, and what content must pass before it publishes.

## 1. The evidence bar — when is a change proven?

A change is proven when ALL of the applicable lines below hold. Skipping one because
"it's a small change" is how this repo's costliest incidents happened.

| # | Evidence | Applies to | How |
|---|---|---|---|
| E1 | **Relevant suites green** | every change | Reverse map in §2 — run the suites for each file you touched. When in doubt, run all 16 (they finish in seconds). |
| E2 | **New test, red→green** | any changed/new behavior | Write the test FIRST, watch it FAIL against the old code, then make it pass. A test that never failed proves nothing — it may be asserting the bug. State "failed before, passes after" in your handoff. |
| E3 | **Fresh-port browser check** | any player-visible change (`docs/`) | Serve `docs/` on a port you have NOT used this session (`python -m http.server 8010 --directory docs`) and exercise the change. The browser caches ES modules per origin:port; a stale port shows you the OLD code and produces false "it works"/"still broken" verdicts. This trap has a documented history — see degreesoffilm-debugging-playbook. |
| E4 | **Content validator green** | any content change (puzzle publish/edit, manifest, ledger) | `python .claude/skills/degreesoffilm-diagnostics-and-tooling/scripts/validate_content.py` — the read-only integrity instrument (see degreesoffilm-diagnostics-and-tooling for the interpretation guide). Run it before AND after. |

**"Tests pass" alone is NOT evidence for uncovered behavior.** The suites cover the
pure modules only. The following have **zero automated tests** — for them, E3-style
manual verification is the *only* gate (found by reading every suite, 2026-07-03):

- `docs/app.js` — all DOM glue: view routing (`?play`/`?archive`/`?practice`/…),
  `poserPuzzle` ladder trim, `renderChoices`, `applyTheme`, share text, ROASTS/QUOTES,
  the showEnd stat-isolation guards, the image `onerror` fallback chain.
- `docs/index.html`, `docs/style.css` — markup ids the JS binds to; the theme CSS vars.
- `curation/app.py` — every endpoint. The wiring from HTTP payload → `publish.publish()`
  is untested even though `publish()` itself is.
- `curation/static/index.html` — the entire curation UI (schedule strip, crop drag,
  Randomize preview flow, editor).
- `curation/tmdb.py` — no suite at all (it is the network client). `discover.test.py`
  and `decoys.test.py` import it transitively, so a *syntax* error fails them at import
  time, but its behavior (paging, error mapping, key loading) is only verified by
  running the live tool.
- `docs/stats.js` `loadStats`/`saveStats` — the localStorage halves; only the pure
  `defaultStats`/`recordResult` are covered by `stats.test.js`.
- The curation CLI entry points (`__main__` blocks) and the migration scripts
  `curation/backfill_credit_images.py`, `curation/obfuscate_puzzles.py`.
- `curation/images.py`'s network path (downloading a TMDB image) — only the pure
  box/energy/color math and local-Pillow crops are tested.

If your change lives in one of those, say so explicitly in your report and describe the
manual verification you did. Do not imply test coverage that does not exist.

## 2. Test inventory and reverse map

16 suites. No framework, no npm scripts (`package.json` is only `{"type":"module"}`),
no network, no API key. Every suite prints `PASS`/`FAIL` lines, ends with
`N passed, M failed`, and exits non-zero on any failure. All commands run from the
repo root. Counts below were measured by running all 16 on **2026-07-03** (all green);
counts drift as tests are added — a LOWER count than stated here is a red flag (§6).

| Suite | Module(s) under test | What it actually guards | Count | Command |
|---|---|---|---|---|
| `match.test.js` | `docs/match.js` | **The fairness contract**: 25 guess→match/reject rows (exact, typo tolerance, foreign titles ± diacritics, surname-only, wrong-surname rejection, empty/nonsense). Mirrors puzzle 001's real answers. | 25 | `node match.test.js` |
| `game.test.js` | `docs/game.js` | Scoring curve rungs 1–12 asserted verbatim; scripted playthroughs: strikeout at 3 wrong, skip cap (6th skip ends run), win state, I-Need-Help (score-0, attempt burn, no-decoy denial, MAX_HELPS cap), Poser flat +1. | 34 | `node game.test.js` |
| `daily.test.js` | `docs/daily.js` | `pickPuzzle` date logic (exact / most-recent-prior / earliest / gap-day / empty), `todayISO` zero-padding, `pickById` for the archive. | 11 | `node daily.test.js` |
| `theme.test.js` | `docs/theme.js` | `parseHex` (3/6-digit, garbage rejection), luminance ordering, `onAccentText` dark-ink-vs-bone contrast picks. | 15 | `node theme.test.js` |
| `stats.test.js` | `docs/stats.js` (pure part) | `recordResult`: streak extend/reset/max, same-day idempotence, histogram, input non-mutation. NOT load/save. | 17 | `node stats.test.js` |
| `frame.test.js` | `docs/frame.js` | `pickCreditFrame`: reveal tier widening + clamp (incl. single-tier 001 case), credit image + caption, full-frame fallback, overshoot clamp, no-frames edge. | 16 | `node frame.test.js` |
| `cipher.test.js` | `docs/cipher.js` | Decodes the **Python-produced fixed vector** (§4), round-trips ASCII/Unicode, sentinel prefix, plaintext passthrough, idempotence, `decodeRungs` scope (answers+caption yes, decoys/prompt no). | 19 | `node cipher.test.js` |
| `build_rungs.test.py` | `curation/build_rungs.py` | Ladder shape: cast by **billing not popularity** (a synthetic film where they disagree), director at rung 4, fixed deep-crew order, writer excluded, co-directors collapse to one rung, `max_cast` trim, original-title alternate. | 16 | `python curation/build_rungs.test.py` |
| `ledger.test.py` | `curation/ledger.py` | Never-repeat ledger: dedupe by film id, `remove_by_puzzles` free-the-films split, id-required, save/reload round-trip (temp dirs). | 12 | `python curation/ledger.test.py` |
| `discover.test.py` | `curation/discover.py` | Pool floor inclusive at ≥800 votes / ≥6.5 avg, used-film exclusion, `pick_random_unused` with an injected fake rng. | 11 | `python curation/discover.test.py` |
| `decoys.test.py` | `curation/decoys.py` | `pick_decoys` pure core: excludes the correct answer case-insensitively, dedupes, respects n/exclude-set, tolerates short pools + blank names. | 6 | `python curation/decoys.test.py` |
| `manifest.test.py` | `curation/manifest.py` | Upsert semantics: date-sorted, same-date REPLACE (one puzzle/day — the collision class), reschedule drops the stale entry, `clear_scheduled` keeps today+past, save/reload. | 13 | `python curation/manifest.test.py` |
| `publish.test.py` | `curation/publish.py` (+ `cipher`) | `next_id` scan, `assemble_puzzle` obfuscates answers but not decoys, full `publish()` into **temp dirs** (puzzle+ledger+manifest writes, obfuscated titles, dedupe), `next_date` collision avoidance, `upcoming_schedule`, `runway`. | 36 | `python curation/publish.test.py` |
| `credits_images.test.py` | `curation/credits_images.py` | `caption_for` (cast "Name as Character", crew name-only, Film blank), `NNN-rK.jpg` naming, `attach_person_meta` headshot mapping, `finalize_rung_images` with an **injected fake save** — helper fields stripped, headshot-less rungs skipped. | 22 | `python curation/credits_images.test.py` |
| `cipher.test.py` | `curation/cipher.py` | The SAME fixed vector as `cipher.test.js` (parity lock, §4), round-trips, sentinel, passthrough, idempotence, None handling, `encode_rungs`/`decode_rungs` non-mutation + scope. | 22 | `python curation/cipher.test.py` |
| `images.test.py` | `curation/images.py` | Tier expansion + clamping, `best_window` edge-energy (hot-block/tie/oversize), `box_around` clamps, `deweight_bands`, accent/background color clamps, Pillow `crop_tiers`/`auto_crop_box`/`sample_accent`, `detect_faces` no-face path (degrades to `[]` without cv2 — suite passes either way). | 32 | `.venv/Scripts/python curation/images.test.py` |

Run-everything one-liners (Git Bash, from repo root):

```bash
for t in match game daily theme stats frame cipher; do node $t.test.js || echo "** $t FAILED"; done
for t in build_rungs ledger discover decoys manifest publish credits_images cipher; do python curation/$t.test.py || echo "** $t FAILED"; done
.venv/Scripts/python curation/images.test.py    # .venv/bin/python on macOS/Linux
```

### Reverse map — changed file X ⇒ run suites Y

Derived from the actual import graph (verified 2026-07-03: `docs/game.js` imports only
`match.js`; `docs/app.js` imports game/daily/theme/stats/frame/cipher;
`curation/publish.py` imports cipher+ledger+manifest; `curation/credits_images.py`
imports build_rungs; `curation/discover.py` and `decoys.py` import tmdb).

| Changed file | Run | Also required |
|---|---|---|
| `docs/match.js` | `match.test.js` + `game.test.js` (game imports match) | **Contract-first rule, §3** |
| `docs/game.js` | `game.test.js` | Fresh-port browser check (E3) |
| `docs/daily.js` | `daily.test.js` | E3 |
| `docs/theme.js` | `theme.test.js` | E3 |
| `docs/stats.js` | `stats.test.js` | E3 — load/save halves are untested |
| `docs/frame.js` | `frame.test.js` | E3 |
| `docs/cipher.js` | `cipher.test.js` **AND** `python curation/cipher.test.py` | Parity is cross-language; one green side proves nothing |
| `curation/cipher.py` | `curation/cipher.test.py` **AND** `node cipher.test.js` **AND** `curation/publish.test.py` (imports cipher) | §4 — the vector is frozen |
| `docs/app.js` / `docs/index.html` / `docs/style.css` | — no suite exists — | **Manual gate only**: E3 fresh-port walk of every affected route; if QUOTES touched, run the content validator (it checks quotes-vs-ledger) |
| `docs/puzzles/*.json`, `docs/puzzles/manifest.json` | — | E4 content validator; content changes also gate on §5 + IMMUTABLE PAST |
| `curation/build_rungs.py` | `build_rungs.test.py` + `credits_images.test.py` (imports build_rungs) | |
| `curation/ledger.py` | `ledger.test.py` + `publish.test.py` | |
| `curation/manifest.py` | `manifest.test.py` + `publish.test.py` | |
| `curation/publish.py` | `publish.test.py` | |
| `curation/discover.py` | `discover.test.py` | |
| `curation/decoys.py` | `decoys.test.py` | |
| `curation/credits_images.py` | `credits_images.test.py` | |
| `curation/images.py` | `.venv/Scripts/python curation/images.test.py` | |
| `curation/tmdb.py` | `discover.test.py` + `decoys.test.py` (import-time smoke only) | **Manual gate**: run the live tool against one endpoint |
| `curation/app.py`, `curation/static/index.html` | — no suite exists — | **Manual gate only**: run the tool, poke SAFE-READ-ONLY endpoints (table in degreesoffilm-diagnostics-and-tooling); never point live-write endpoints at committed content |
| `curation/used_films.json` | — | E4 content validator (ledger↔manifest crosscheck) |

## 3. How to add a test

House style: **plain scripts, tiny `check` helper, PASS/FAIL lines, summary, non-zero
exit.** No framework, no test runner, no new dependencies. Copy an existing suite.

**JS skeleton** — this is the real `check` helper quoted from `game.test.js`:

```js
import { Game, scoreForRung, MAX_HELPS } from './docs/game.js';

let pass = 0, fail = 0;
function check(label, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  ok ? pass++ : fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${ok ? '' : `  (got ${JSON.stringify(got)}, want ${JSON.stringify(want)})`}`);
}

// ... check('label', actual, expected); ...

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
```

New JS suites live at the **repo root** as `<module>.test.js`, importing from
`./docs/<module>.js` (the root `package.json`'s `"type": "module"` exists solely to
make these imports work). Update CLAUDE.md's test list when you add one.

**Python skeleton** — the real header + `check` helper quoted from `build_rungs.test.py`
(identical helper across all eight suites):

```python
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_rungs import order_rungs, build_puzzle, order_cast  # noqa: E402

passed = failed = 0


def check(label, got, want):
    global passed, failed
    ok = got == want
    passed, failed = passed + (1 if ok else 0), failed + (0 if ok else 1)
    print(f"{'PASS' if ok else 'FAIL'}  {label}"
          + ("" if ok else f"\n        got:  {got!r}\n        want: {want!r}"))

# ... check("label", actual, expected) ...

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
```

New Python suites live in `curation/` as `<module>.test.py`. **They must stay
network-free and key-free** — everything must run with no `curation/.env` and no
TMDB. The established techniques, all visible in current suites:

- **Temp dirs for file I/O** — `publish.test.py` runs a full `publish()` into
  `tempfile.TemporaryDirectory()`; `ledger.test.py`/`manifest.test.py` do the same for
  round-trips. Never write into `docs/` or `curation/used_films.json` from a test.
- **Injected fakes for side effects** — `credits_images.test.py` passes a `fake_save`
  callable instead of downloading headshots; `discover.test.py` injects a fake `rng`.
- **Synthetic fixtures that make the property observable** — `build_rungs.test.py`
  builds a cast whose billing order *disagrees* with popularity, so a popularity-sort
  regression cannot pass silently.
- Pillow-dependent tests go in `images.test.py` (run under the venv); pure math stays
  runnable without it.

**Where new logic must live to be testable:** in a pure module — no DOM, no `fetch`,
no network, no localStorage in the logic path. That is the layering law
(degreesoffilm-architecture-contract): `docs/app.js` and `curation/app.py` are thin
glue precisely so everything decision-shaped is importable by these suites. If you
find yourself wanting to test something inside `app.js`/`app.py`, the fix is to
extract it into a pure module first, not to build a DOM/HTTP test harness.

> **NON-NEGOTIABLE — the matcher contract-first rule (from CLAUDE.md):**
> `match.test.js` IS the specification of what feels fair to a player. Before touching
> the algorithm in `docs/match.js`, add the new guess→should-match/should-reject row(s)
> to the `cases` table, run the suite, and watch the new rows FAIL. Only then change
> the algorithm, and land with the whole table green — the pre-existing rows are prior
> fairness decisions (foreign titles, typo tolerance, surname-only, wrong-surname
> rejection) and none of them may regress.

## 4. Golden inventory — frozen artifacts; changing them is change-control territory

**G1 — the shared cipher fixed vector (FROZEN).** Both cipher suites assert the exact
same payload so the two implementations cannot drift. From `cipher.test.js`:

```js
const S = String.fromCharCode(1);   // the U+0001 sentinel
check('decodes the Python-produced vector for "The Dark Knight"',
  decode(S + 'MA0CUiEEAUZPLUMPDgQZ'), 'The Dark Knight');
```

From `curation/cipher.test.py`:

```python
check("obfuscate('The Dark Knight') is the shared vector",
      obfuscate("The Dark Knight"), SENTINEL + "MA0CUiEEAUZPLUMPDgQZ")
check("deobfuscate reverses the vector",
      deobfuscate(SENTINEL + "MA0CUiEEAUZPLUMPDgQZ"), "The Dark Knight")
```

(`cipher.test.js` additionally asserts a JS-only Unicode vector,
`S + 'JQik2wkMFg=='` → `'Amélie'`.) The vector pins KEY `'degrees-of-film'` +
SENTINEL U+0001 + the XOR/base64 scheme. **Every published puzzle file and every
manifest title on disk is encoded with this exact scheme** — change the key or scheme
and all live content becomes gibberish to the client. Treat the vector as effectively
frozen; if these checks ever fail, the bug is on whichever side you just edited, not
in the vector. (The real fix for the cipher's weakness is v3 server-side matching, not
a stronger key — see degreesoffilm-architecture-contract.)

**G2 — puzzle 001, the hand-authored golden** (`docs/puzzles/001.json`, No Country for
Old Men — its answers are already public in `match.test.js` and CLAUDE.md, so naming
it here is spoiler-safe). Verified on disk 2026-07-03:

- Born plaintext in Phase 0; **now fully obfuscated** (the migration ran) and it IS in
  the ledger (`{"id": 6977, "puzzle": 1}`) and the manifest — do not code
  "001 is special" exceptions.
- Still **single image tier** (`images/001.jpg` only) — the live exercise of frame.js's
  reveal clamp ("single-tier puzzles stay put"; asserted in `frame.test.js`).
- Its Editor rung has **no `image`/`caption`** ("Roderick Jaynes" is a Coen pseudonym
  with no TMDB headshot) — the live exercise of the hold-the-full-frame fallback.
- `match.test.js`'s answer sets mirror its rungs — the matcher contract and the golden
  puzzle validate each other.

**G3 — the scoring curve.** `game.test.js` asserts the exact sequence:

```js
const curve = [1,2,3,4,5,6,7,8,9,10,11,12].map(scoreForRung);
check('score curve rungs 1-12', curve, [1,2,3,4,5,7,9,11,13,15,16,17]);
```

`1,2,3,4,5,7,9,11,13,15,16,17` = rung value n plus a deep-dig bonus starting at rung 6,
capped at +5 from rung 10. Any scoring change makes this row red — that is the alarm
working, not an obstacle; rebalancing the curve is a player-facing rules change
(owner sign-off per degreesoffilm-change-control).

**G4 — the `validate_ladder.py` 5-film stress set** (describe only — it hits live TMDB
and needs the key; do NOT run it as a QA step). `curation/validate_ladder.py` is the
kept throwaway de-risk script whose `FILMS` list stresses the ladder premise across
ensemble / blockbuster / two foreign-language: *No Country for Old Men* (2007),
*Pulp Fiction* (1994), *The Dark Knight* (2008), *Parasite* (2019), *Pan's Labyrinth*
(2006). Its historical verdict — popularity sort buried Heath Ledger's Joker at rung
13 → **billing order adopted** — is why `build_rungs.test.py` has an explicit
billing-beats-popularity fixture. Re-run it only if the ordering rule itself is being
reconsidered (settled battle: degreesoffilm-failure-archaeology).

## 5. Content QA checklist — per puzzle, before publish

Run this during the review step of the publishing runbook (the runbook itself, with
the point-of-no-return marked, lives in degreesoffilm-run-and-operate). All rungs and
answers are curator-eyes-only — inspect with
`python .claude/skills/degreesoffilm-diagnostics-and-tooling/scripts/puzzle_report.py <id>`
(SPOILER-REVEALING; never paste output anywhere public).

1. **Rung order is sane** — lead cast at the top, director ≈ rung 3–4, technical crew
   (DP/composer/editor/PD) deepest. The tool drafts by billing order; **a human MUST
   review edge cases** — star cameos billed low, ensemble oddities, posthumous-legend
   billing. The draft is a starting point, not a verdict.
2. **Every rung has ≥1 answer, with the variants a fair player would type** — foreign/
   original titles for the film rung, name forms (e.g. "Josh"/"Joshua Brolin"),
   pseudonyms plus real names (001's Editor rung accepts both "Roderick Jaynes" and
   the Coens). Variants live in `answers[]`, never in matcher logic.
3. **Decoys are plausible, same-category, and NOT accidentally correct** — check each
   decoy against the rung's full `answers` list (an alternate name form sneaking into
   the decoys makes the rung unwinnable-feeling). Zero decoys on a rung is *legal* —
   I-Need-Help is simply unavailable there (real example: puzzle 5 rung 12, Production
   Designer, has 0 decoys — verified 2026-07-03) — but it should be a decision, not
   an oversight.
4. **The tier-1 crop reveals no title, credit text, or watermark.** Auto-crop
   de-weights top/bottom bands but does not read text — eyeball it.
5. **Tiers 2–3 don't spoil** — the widened crops appear after wrong guesses; if the
   full frame contains the title card, the reveal hands over the answer.
6. **Headshots present-or-fallback** — every cast/crew rung either has its `NNN-rK.jpg`
   on disk or intentionally holds the full frame (missing TMDB headshot). `[MISSING]`
   in puzzle_report = broken; `(none)` = the fallback, fine.
7. **The date is the intended free day** — publish auto-fills the next free day;
   confirm it matches your plan, and that you are not editing anything dated ≤ today
   (**IMMUTABLE PAST** — players played it; the tooling won't stop you, discipline must).
8. **A spoiler-safe commit message is planned** — puzzle number + date only
   ("Add puzzle NNN (YYYY-MM-DD)"), never the film title until its date has passed.
   Commit history is public (two historical commits violated this; see
   degreesoffilm-change-control).
9. **Validator green** — `validate_content.py` passes before you push (E4).

Known open violation to be aware of (not per-puzzle, but this checklist's spirit): a
known OPEN spoiler issue in the home-page QUOTES as of 2026-07-03 (puzzle 4's and
puzzle 6's films quoted) — check current state with the validator's quotes-vs-ledger
group (`validate_content.py`, E4); full account: degreesoffilm-failure-archaeology
entry 12. If it's fixed by the time you read this, the WARN disappears — trust the
validator, not this note.

## 6. Acceptance thresholds

- **All 16 suites green, always, before landing anything.** There is no "unrelated
  failure" exemption — with no CI, a tolerated red suite is indistinguishable from a
  broken repo, and the next person cannot tell your pre-existing failure from their
  new one. If a suite is red for a reason you didn't cause, STOP and fix or escalate
  before landing; never land on top of red.
- **Never weaken or delete an assertion to get to green** without explicit sign-off
  through degreesoffilm-change-control. Existing assertions encode prior decisions
  (fairness rows in match.test.js, the scoring curve, billing-beats-popularity,
  same-date-upsert). A red assertion is a question — "did you mean to change this
  behavior?" — and the answer belongs to the owner for anything player-facing.
- **Count drift: up is fine, down is suspicious.** New tests raise the `N passed`
  numbers past the table in §2 — good; update the table's date when you notice.
  A count LOWER than the table means tests were deleted or are silently not running
  (e.g. an import error swallowed) — investigate before anything else.
- **Content thresholds:** validator exit 0 (WARNs are visible-but-allowed unless
  `--strict`); every manifest entry ↔ ledger record 1:1; zero missing referenced
  images; every obfuscated string decodes.
- **Evidence in handoffs:** when you report a change as done (project_state.md, PR
  body), state which suites you ran and the red→green fact for new tests. "All tests
  pass" without naming them is below the bar here.

## When NOT to use this skill

- Running the game/curation tool, or the publish runbook itself → **degreesoffilm-run-and-operate**
- The validator/report scripts' interpretation guides, endpoint safety, git forensics → **degreesoffilm-diagnostics-and-tooling**
- A live bug to triage (symptom → cause) → **degreesoffilm-debugging-playbook**
- Whether/how a change may land, commit/PR conventions → **degreesoffilm-change-control**
- What an invariant is and why (layering law, cipher parity, key confinement) → **degreesoffilm-architecture-contract**
- Environment setup (Node/venv/pins) → **degreesoffilm-build-and-env**
- Matching/TMDB/image-math theory behind the tested behavior → **degreesoffilm-domain-reference**
- Looking up a constant's value/location → **degreesoffilm-config-and-flags**
- Why a past approach was rejected → **degreesoffilm-failure-archaeology**

## Reusing this pattern beyond this project

Transferable as a template: the evidence-bar table (suites + red→green + fresh-runtime
manual gate + content validator); a per-source-file reverse map derived from the import
graph; framework-free PASS/FAIL test scripts with a shared `check` helper; cross-language
parity locked by a shared fixed vector; a golden-artifact inventory with an explicit
FROZEN list; and "count down = suspicious" as a CI-less tripwire. Project-specific: the
suite names/counts, the cipher scheme, puzzle 001, and the content checklist items.

## Provenance and maintenance

- Written 2026-07-03. All 16 suites RUN that day from the repo root — every count in §2
  is from those runs (all green, 0 failed). Skeletons and golden quotes copied verbatim
  from `game.test.js`, `build_rungs.test.py`, `cipher.test.js`, `curation/cipher.test.py`,
  `curation/validate_ladder.py`. Import graph, coverage gaps, puzzle-001 state,
  puzzle-5-rung-12 zero decoys, and the live QUOTES violation (HEAD `10668ca`) verified
  by direct reads/greps the same day.
- Re-verify counts: the three run-everything one-liners in §2. Re-verify the vector:
  `node cipher.test.js && python curation/cipher.test.py`. Re-verify the QUOTES note:
  `python .claude/skills/degreesoffilm-diagnostics-and-tooling/scripts/validate_content.py`.
- If you add a suite, change a count, or extract logic from app.js/app.py into a tested
  module, update §2 (and §1's gap list) plus this date in the same session.
