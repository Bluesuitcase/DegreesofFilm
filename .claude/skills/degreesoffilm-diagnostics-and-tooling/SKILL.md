---
name: degreesoffilm-diagnostics-and-tooling
description: How to MEASURE the health of the Degrees of Film repo instead of eyeballing it. Load this when you need to verify content integrity before or after publishing a puzzle, check manifest/ledger/puzzle-file consistency, inspect one puzzle's decoded answers for curator review, measure the content runway (days until the daily repeats), gather evidence for a bug report ("is the data healthy?", "which commit broke it?"), decide which curation endpoint is safe to poke vs which one writes live files, or probe the live site / a local server without trusting a stale cache. Ships two working scripts — scripts/validate_content.py (read-only integrity validator) and scripts/puzzle_report.py (spoiler-revealing puzzle inspector) — plus the full test-suite inventory, endpoint safety table, and git forensics one-liners.
---

# Degrees of Film — diagnostics and tooling

## Philosophy: measure, don't eyeball

This project has no CI, no analytics, and one curator. The only thing standing between
"looks fine" and "the daily silently repeating tomorrow" is measurement you run yourself. Every claim
about health here reduces to a number you can print:

- **Content is healthy** when `scripts/validate_content.py` exits 0: manifest parses,
  sorted, dates+ids unique; every puzzle file exists, parses, and matches its manifest id;
  every referenced image exists; all 177 obfuscated strings (as of 2026-07-03) decode
  cleanly; every rung has ≥1 answer; rung 1 is the Film rung; ledger↔manifest is 1:1.
- **Code is healthy** when all 16 offline test suites are green (275 JS/Python-pure
  checks + 32 Pillow checks as of 2026-07-03; canonical per-suite counts:
  degreesoffilm-validation-and-qa §2). Counts drifting DOWN is suspicious; up is fine.
- **Operations are healthy** when the runway number (consecutive stocked days from
  today) is comfortably above 0. As of 2026-07-03 it is **2** — thin. Runway 0 means
  today has no puzzle and `pickPuzzle` silently serves the most recent one (a repeat,
  not a crash).

Never conclude from a screenshot or a glance at JSON what a script can assert. Decoded
answers are unreadable in the raw files by design (U+0001-sentinel XOR+base64 cipher) —
eyeballing the JSON literally cannot tell you if an answer is correct.

## Instrument 1 — the 16 offline test suites

All run from the repo root, print PASS/FAIL lines, and exit non-zero on any failure.
No framework, no network, no API key. All 16 run green on 2026-07-03. Expected: all suites
green; canonical per-suite counts live in degreesoffilm-validation-and-qa §2 — a count
LOWER than it states is a red flag.

| Suite (command) | What it measures |
|---|---|
| `node match.test.js` | Fuzzy matcher contract (typos, foreign titles, surname rule, rejections) |
| `node game.test.js` | Rules/scoring: curve, attempts, skips, helps, scripted playthroughs |
| `node daily.test.js` | `pickPuzzle`/`pickById` date selection + fallbacks |
| `node theme.test.js` | Accent parse/luminance/contrast math |
| `node stats.test.js` | `recordResult` streak + histogram logic |
| `node frame.test.js` | `pickCreditFrame` still selection + reveal tiers |
| `node cipher.test.js` | JS cipher decode/round-trip/passthrough + shared vector |
| `python curation/build_rungs.test.py` | Credits → ordered rung draft |
| `python curation/ledger.test.py` | Never-repeat ledger ops incl. `remove_by_puzzles` |
| `python curation/discover.test.py` | Pool-floor candidate filtering + random pick |
| `python curation/decoys.test.py` | Per-rung decoy generation logic |
| `python curation/manifest.test.py` | Upsert-by-date+id, sort, `clear_scheduled` split |
| `python curation/publish.test.py` | Assemble/publish, `next_date`, `upcoming_schedule`, `runway` |
| `python curation/credits_images.test.py` | Rung→person headshot mapping + finalize |
| `python curation/cipher.test.py` | Python cipher + the SAME fixed vector as cipher.test.js |
| `.venv/Scripts/python curation/images.test.py` | Crop tiers, color sampling, auto-crop (Pillow; degrades without cv2) |

Reverse map: cipher changes ⇒ run **both** cipher suites (cross-language parity is
asserted via a shared fixed vector). Matcher changes ⇒ add a `match.test.js` case FIRST
(contract-first rule; see degreesoffilm-validation-and-qa).

## Instrument 2 — `scripts/validate_content.py` (read-only integrity validator)

```
python .claude/skills/degreesoffilm-diagnostics-and-tooling/scripts/validate_content.py
```

Runs from the repo root (or anywhere — it derives the repo root from its own path).
READ-ONLY: opens files for reading only; no network, no `.env`, no TMDB. Flags:
`--strict` (WARN-class findings fail the run), `--today YYYY-MM-DD` (deterministic
runway). Exit 0 = healthy (warnings allowed), 1 = any FAIL (or WARN under `--strict`).

Real output, captured 2026-07-03 against the live repo:

```
PASS  manifest-structure: 7 entries, sorted, dates+ids unique
PASS  puzzle-files: all 7 files exist and parse
PASS  id-consistency: every file id matches its manifest entry
PASS  images: all 92 referenced images exist on disk
PASS  decode: 177 obfuscated strings decode cleanly
PASS  rung-shape: every rung has answers; Film rung is first
PASS  ledger-crosscheck: 7 ledger records <-> 7 manifest entries, 1:1
PASS  quotes-vs-ledger: none of the 6 quote films are in the ledger
INFO  decoy-coverage: puzzle 1: 11/11 rungs have decoys
INFO  decoy-coverage: puzzle 2: 12/12 rungs have decoys
INFO  decoy-coverage: puzzle 3: 12/12 rungs have decoys
INFO  decoy-coverage: puzzle 4: 12/12 rungs have decoys
INFO  decoy-coverage: puzzle 5: 11/12 rungs have decoys
INFO  decoy-coverage: puzzle 6: 10/10 rungs have decoys
INFO  decoy-coverage: puzzle 7: 12/12 rungs have decoys
INFO  runway: 2 consecutive stocked day(s) from 2026-07-03

8 group(s) passed, 0 failed, 0 warning(s)
```

(Illustration — what a WARN looks like when it *does* fire: a `quotes-vs-ledger`
violation prints `WARN  quotes-vs-ledger: N problem(s)` with a `- QUOTES names 'X' — it
is puzzle N in the ledger (spoiler)` line each, and the summary reads `… , M warning(s)`;
exit stays 0 unless `--strict`.)

Note: 92 referenced images exactly equals the 92 files in `docs/puzzles/images/` — zero
orphans as of 2026-07-03.

### Interpretation guide (what each FAIL means, and where to go next)

| Line | Meaning | Next move |
|---|---|---|
| FAIL manifest-structure | Manifest corrupt / duplicate date or id / unsorted. Duplicate date = the 2026-06-30 collision class that orphaned puzzles 003/004. | `git log -p -1 -- docs/puzzles/manifest.json` to see what changed; degreesoffilm-failure-archaeology (manifest collision entry) |
| FAIL puzzle-files | Manifest points at a missing/corrupt `NNN.json` — orphaned entry or half-finished publish. | Was `/api/approve` interrupted? Restore: `git checkout -- docs/puzzles/manifest.json curation/used_films.json` (both git-tracked) |
| FAIL id-consistency | File's `"id"` ≠ manifest `"id"` — hand-edit or botched update. | `git log --oneline -- docs/puzzles/NNN.json` to find the touching commit |
| FAIL images | A tier (`NNN-K.jpg`) or headshot (`NNN-rK.jpg`) referenced but absent — broken image in the live game (client falls back to full frame for rung images, but tiers are load-bearing). | Check `docs/puzzles/images/`; if it never existed, the approve step's image save failed |
| FAIL decode | An obfuscated blob is corrupt (bad base64/UTF-8 after XOR) or decodes to empty — the puzzle is unwinnable on that rung. | Run both cipher suites; if green, the FILE is damaged, not the cipher — git-forensics the file |
| FAIL rung-shape | A rung with zero answers, or rung 1 isn't the Film rung. | Inspect with `puzzle_report.py <id>`; fix via the curation edit flow (future-dated only — IMMUTABLE PAST) |
| FAIL ledger-crosscheck | Manifest entry with no ledger record (film not marked used ⇒ Discover can re-suggest it ⇒ duplicate-film risk) or ledger record pointing at a vanished puzzle (film locked out for nothing). | `git log -p -1 -- curation/used_films.json`; a stray POST /api/clear-schedule is the usual suspect |
| WARN quotes-vs-ledger | A home-screen quote names a film that IS a puzzle answer — owner's spoiler-discipline violation. Exit stays 0 unless `--strict`. | Fix = swap the quote in `docs/app.js` QUOTES (player-facing change ⇒ PR path per degreesoffilm-change-control) |
| INFO decoy-coverage < total | Legal, but I-Need-Help (and Poser eligibility) is unavailable on decoyless rungs. | Curator judgment call; edit flow can add decoys |
| INFO runway low/0 | Days until the daily silently repeats. | Curate more puzzles — degreesoffilm-run-and-operate publishing runbook |

**Ledger reality (investigated 2026-07-03):** hand-authored puzzle 001 IS in the ledger
(`{"id": 6977, "puzzle": 1}`) and IS in the manifest, and its answers ARE obfuscated (the
migration ran). The crosscheck is therefore strict 1:1 with no 001 exception. Quirk: 001's
ledger `year` is the integer `2007` while later entries use strings ("2014"…) — harmless,
nothing compares years, but don't "normalize" it casually.

Run the validator **before and after every publish/update/clear**, and before blaming
code for a content symptom.

## Instrument 3 — `scripts/puzzle_report.py <id>` (SPOILER-REVEALING, curator-only)

```
python .claude/skills/degreesoffilm-diagnostics-and-tooling/scripts/puzzle_report.py 1
```

Decodes and prints ONE puzzle in plaintext: manifest entry (date/decoded title/accent),
theme, tier images with `[ok]`/`[MISSING]` marks, then per rung: index, role, decoded
answers, decoded caption, decoy count, image + existence mark. **Never paste its output
anywhere player-visible** (commits, PR bodies, public issues). Exit 2 if the id doesn't
exist. Real excerpt, 2026-07-03, puzzle 1 (safe to show here — 001's answers are already
plaintext in `match.test.js` and CLAUDE.md):

```
========================================================================
SPOILERS BELOW — puzzle 1 (001.json) — curator eyes only
========================================================================
manifest : date 2026-06-28  title 'No Country for Old Men'  accent #734621
theme    : {'accent': '#734621', 'bg': '#241515', 'bg2': '#472820'}
images   : 1 tier(s)
           images/001.jpg [ok]
rungs    : 11

  r1  Film
      prompt : Name the film.
      answers: 'No Country for Old Men' | 'No es pais para viejos'
      decoys : 3
      image  : (none — client holds the full frame)

  r2  Cast
      prompt : Who played Sheriff Ed Tom Bell?
      answers: 'Tommy Lee Jones'
      caption: 'Tommy Lee Jones as Ed Tom Bell'
      decoys : 3
      image  : images/001-r2.jpg [ok]
  ...
  r10 Editor
      prompt : Who edited the film?
      answers: 'Roderick Jaynes' | 'Coen brothers' | 'The Coens' | 'Joel and Ethan Coen'
      decoys : 3
      image  : (none — client holds the full frame)
```

Reading it: `answers` lists every accepted form (the matcher takes any); a missing
`image` is fine (client holds the full frame — 001's r10 above is real); `[MISSING]`
next to a listed image is a bug (the validator's images group will also FAIL); a
`WARNING: puzzle file date != manifest date` line means a half-applied reschedule.
Use it for pre-publish review, verifying an edit landed, and confirming decoys aren't
accidentally correct answers.

## Instrument 4 — curation endpoints: what's safe to poke

Classified from `curation/app.py` (verified 2026-07-03). Server:
`.venv/Scripts/python -m uvicorn app:app --app-dir curation --port 8001`.

**SAFE-READ-ONLY** (write nothing to the repo):

| Endpoint | Needs TMDB key? | Notes |
|---|---|---|
| `GET /` | no | Serves the crop page |
| `GET /api/next-date` | no | Next free publish date |
| `GET /api/schedule?days=14` | no | Slots + runway — the quickest health probe |
| `GET /api/clear-schedule` | no | **DRY count** of what a clear WOULD remove; changes nothing |
| `GET /api/autocrop?url=&scale=` | no | Suggests a box; downloads the TMDB image (network) |
| `GET /api/discover`, `GET /api/random`, `GET /api/search?q=` | yes | Live TMDB calls; 500 without a key |
| `GET /api/film/{id}`, `GET /api/puzzle/{pid}` | yes | Draft / edit-load; no repo writes |

**LIVE-WRITE** (mutate `docs/` and/or `curation/used_films.json` — never point these at
committed content during an experiment; the puzzle-004 incident is the lesson):

| Endpoint | Writes |
|---|---|
| `POST /api/approve` | puzzle JSON + tier images + headshots + ledger append + manifest upsert |
| `POST /api/update` | rewrites the puzzle file in place, optional re-crop, moves the manifest entry (ledger untouched) |
| `POST /api/clear-schedule` | drops strictly-future manifest entries AND frees their ledger films |

Restore after any live-write experiment:
`git checkout -- docs/puzzles/manifest.json curation/used_films.json` (verify with the
validator afterwards).

## Instrument 5 — browser-side probes

- **Live manifest** (is the deploy actually out?):
  `curl -s https://bluesuitcase.github.io/DegreesofFilm/puzzles/manifest.json` — compare
  entry count/dates to the local file. Differs after a push = Pages lag (minutes) or you
  never pushed; `git status` + `git log origin/main..main` discriminates.
- **Decoded-in-memory vs obfuscated-on-disk** is NORMAL: fetching `puzzles/NNN.json`
  shows U+0001-prefixed base64 blobs; the running page shows plaintext because `app.js` decodes at
  load. Plaintext IN the JSON file is also legal (passthrough) but means an unmigrated
  file. Gibberish ON the page = someone bypassed `decodeRungs` — a code bug, not data.
- **Fresh-port cache trick**: `python -m http.server 8010 --directory docs` on a NEW
  port before declaring a UI fix broken/working — the browser caches ES modules per
  origin:port and stale-cache false alarms are a documented recurring trap here. Only
  the manifest fetch is cache-busted (`?d=<todayISO>`); JS/CSS are not.
- **Curation page**: automated screenshot tooling times out on this page — assert via
  the browser devtools console / computed styles instead. They're more precise anyway:
  assert numbers, not pixels.

## Instrument 6 — git forensics one-liners

All read-only; all verified working 2026-07-03.

| Question | Command |
|---|---|
| Which commits touched puzzle N? | `git log --oneline -- docs/puzzles/004.json` |
| When was puzzle N first added? | `git log --diff-filter=A --oneline -- docs/puzzles/005.json` |
| What changed in the manifest last? | `git log -p -1 -- docs/puzzles/manifest.json` |
| Who freed/added ledger films? | `git log -p -1 -- curation/used_films.json` |
| Manifest as of an old commit | `git show <hash>:docs/puzzles/manifest.json` |
| Uncommitted content drift right now | `git status --short docs/puzzles curation/used_films.json` |

## Evidence-before-conclusions protocol

1. **Reproduce with a number**, not an impression: validator output, a failing suite
   line, a curl of the live manifest, a git diff.
2. **Localize the zone** (content data / player client / curation tool / deploy) —
   the validator settles "is it the data?" in seconds; run it before reading any code.
3. **Run the discriminating experiment** (fresh port for cache-vs-regression; `--today`
   for date logic; both cipher suites for parity-vs-file-damage) before proposing a fix.
4. **Only then hypothesize.** The evidence bar for "fixed" lives in
   degreesoffilm-validation-and-qa (relevant suites green + new red→green test + fresh-
   port verification); the discipline for turning a hunch into an accepted result lives
   in degreesoffilm-research-methodology. Fixes land per degreesoffilm-change-control.

## Known findings as of 2026-07-03

1. **quotes-vs-ledger — FIXED (`ee4ec54`, 2026-07-03).** `docs/app.js` QUOTES had quoted
   two films that were puzzle answers; the two quotes were swapped for films outside the
   puzzle set, and the validator's quotes-vs-ledger group now PASSES. (Full account:
   degreesoffilm-failure-archaeology entry 12.) The check is permanent — it will re-fire
   if a future QUOTES edit or a newly-published film re-introduces an overlap, so keep
   running it.
2. **Runway = 2** (2026-07-03): puzzles run out after 2026-07-04. Operational, not a bug.
3. **Puzzle 5 rung 12 (Production Designer) has 0 decoys** — I-Need-Help unavailable
   there. Legal per the schema; curator judgment call.
4. **Ledger year-type quirk:** entry for puzzle 1 has integer `2007`; the rest are
   strings. Harmless today; noted so nobody "discovers" it as corruption.

## When NOT to use this skill

- Setting up Node/Python/venv or fixing environment breakage → **degreesoffilm-build-and-env**
- Actually running the game/curation tool, or publishing a puzzle end-to-end → **degreesoffilm-run-and-operate**
- A symptom→cause triage walk ("blank page", "wrong daily") → **degreesoffilm-debugging-playbook**
- The evidence bar, adding tests, content QA checklist → **degreesoffilm-validation-and-qa**
- Whether/how a change may land → **degreesoffilm-change-control**
- What an invariant IS and why → **degreesoffilm-architecture-contract**
- Past investigations and settled battles → **degreesoffilm-failure-archaeology**
- Looking up a constant/config value → **degreesoffilm-config-and-flags**

## Reusing this pattern beyond this project

The transferable template: (1) a single read-only content validator that derives its
repo root from its own file path, checks every cross-file invariant (index↔files↔assets↔
registry), and separates FAIL / WARN / INFO with a `--strict` promotion flag; (2) a
spoiler/PII-marked single-record inspector for human review; (3) an instrument inventory
that classifies every endpoint SAFE vs LIVE-WRITE with a git-restore command. Project-
specific: the cipher import, the rung/manifest/ledger schemas, and the quotes rule.

## Provenance and maintenance

- Written 2026-07-03. Every fact verified against the live repo that day: both scripts
  written AND run from the repo root with the exact invocations above (outputs pasted
  verbatim/excerpted); all 16 test suites run green;
  endpoint classification read from `curation/app.py`; git one-liners executed.
- Re-verify (from the repo root):
  `python .claude/skills/degreesoffilm-diagnostics-and-tooling/scripts/validate_content.py`
  and `... puzzle_report.py 1`, plus the 16-suite commands in the table. If validator
  groups or `curation/app.py` endpoints change, update this file and this
  date in the same session.
