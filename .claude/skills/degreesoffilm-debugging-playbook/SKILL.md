---
name: degreesoffilm-debugging-playbook
description: >
  Symptom-first triage for anything broken in Degrees of Film. Load this when you see:
  a blank page or "Could not load" in the game; the wrong / old / yesterday's / earliest
  puzzle showing as the daily; gibberish or ^A/U+0001 garbage text where answers or
  captions should be; answers visible in plaintext in devtools; broken / missing / wrong
  credit images or headshots; the reveal crop not widening on wrong guesses; wrong theme
  colors; streak or stats not counting; curation tool 500s / 401s / won't start; empty
  Discover or search results; Randomize 404; auto-crop box off-center or on a title card;
  Approve wrote an unexpected date; edit view shows stale data; manifest / ledger / puzzle
  file drift or duplicate dates; "I pushed but the live site didn't change"; deploy or
  cache confusion; or a failing test suite you need to map to a subsystem. Contains the
  project's three costliest traps (stale ES-module cache, manifest date-collision,
  character-stills dead end) and paired experiments that separate look-alike causes.
---

# Degrees of Film — debugging playbook

Symptom-first triage for this repo's real failure modes. Jargon (rung, tier, manifest,
ledger, runway, sentinel…) is defined in **degreesoffilm-domain-reference**. All paths are
repo-relative (run from the repo root). Volatile facts date-stamped **as of 2026-07-03**.

The one architectural fact that shapes all debugging: three zones — player client
(`docs/*.js`, static, no backend), curation tool (`curation/`, FastAPI on localhost:8001,
holds the TMDB key), and static content (`docs/puzzles/`). First question is always:
**which zone is the symptom in?** A player-client symptom can never be a TMDB/key problem
(the client never calls TMDB); a curation 500 can never be a player-cache problem.

## 1. First five minutes — universal triage

1. **What changed last?** `git status` + `git log --oneline -10`. A clean tree with no
   recent commits touching the failing zone strongly suggests environment/cache/data, not code.
2. **Which zone?** Player browser symptom → `docs/*.js` + `docs/puzzles/`. Curation UI/500 →
   `curation/`. Content looks wrong but code untouched → `docs/puzzles/` data.
3. **Is it cache?** For ANY "my fix didn't work" or "the page ignores my edit" in the player
   client: serve `docs/` on a **fresh port** before debugging further (see trap #1):
   `python -m http.server 8010 --directory docs` → open `http://localhost:8010/?play`.
   The browser caches ES modules per origin:port; a fresh port is a guaranteed clean slate.
4. **Run the relevant suite** (all offline, PASS/FAIL lines, non-zero exit on failure). Map:

   | Changed / suspect | Run (from repo root) | Guards |
   |---|---|---|
   | `docs/match.js` | `node match.test.js` | matcher contract (typos, surnames, foreign titles) |
   | `docs/game.js` | `node game.test.js` | rules, scoring curve, playthroughs |
   | `docs/daily.js` | `node daily.test.js` | date-pick fallback logic |
   | `docs/theme.js` | `node theme.test.js` | luminance/contrast math |
   | `docs/stats.js` | `node stats.test.js` | streak + histogram + idempotence |
   | `docs/frame.js` | `node frame.test.js` | still selection + reveal tiers |
   | `docs/cipher.js` | `node cipher.test.js` **and** `python curation/cipher.test.py` | cross-language parity (shared fixed vector) |
   | `curation/build_rungs.py` | `python curation/build_rungs.test.py` | ladder ordering |
   | `curation/publish.py` | `python curation/publish.test.py` | assembly, obfuscation, next_date |
   | `curation/manifest.py` | `python curation/manifest.test.py` | upsert, clear_scheduled |
   | `curation/ledger.py` / `discover.py` / `decoys.py` / `credits_images.py` | `python curation/<name>.test.py` | as named |
   | `curation/images.py` | `.venv/Scripts/python curation/images.test.py` | crop/auto-crop/color math (needs Pillow) |

   `docs/app.js`, `curation/app.py`, and `curation/static/index.html` have **no automated
   tests** — DOM glue and endpoints are verified manually (see degreesoffilm-validation-and-qa).
5. **If it's a test failure**, believe the test first. One cipher suite failing the shared
   vector while the other passes = cross-language drift, not a flaky test (§4.4).

## 2. Symptom → triage tables

### 2a. Player client (`docs/`)

Every error string below is quoted verbatim from `docs/app.js` (verified 2026-07-03).

| Symptom | First probe | Likely causes (ranked) | Fix | Ref |
|---|---|---|---|---|
| Blank page, nothing renders | Browser console for module errors | 1. Opened via `file://` (fetch + ES modules fail) 2. JS syntax error in a `docs/*.js` edit 3. Stale cached module masking a fix | Serve `docs/` over HTTP; fix the console error; fresh port | §3.1 |
| `Could not load — are you running a local server?` | Network tab: is `puzzles/manifest.json?d=...` 404/failed? | 1. `file://` or wrong served directory (must serve `docs/`, not repo root) 2. `manifest.json` missing/unparseable JSON | Serve the `docs/` folder itself; validate the manifest (probe in §2c) | `docs/app.js` init catch |
| `Could not load the puzzle.` | Network tab: which `puzzles/NNN.json` failed? | 1. Manifest entry points at a file that doesn't exist (orphan/drift) 2. Puzzle file is invalid JSON | Cross-check manifest↔files (§2c); restore or re-publish the file | §3.2 |
| `No such puzzle.` on `?id=N` | Is `N` in the manifest? `python -c "import json; print([e['id'] for e in json.load(open('docs/puzzles/manifest.json',encoding='utf-8'))])"` | 1. Typo'd/never-published id 2. Entry removed (e.g. by Clear-scheduled, which drops manifest entries but keeps files) | Use a listed id; if the entry should exist, `git log -- docs/puzzles/manifest.json` to see what removed it | `docs/app.js` |
| `No puzzles to practice yet.` | Same manifest listing as above | Practice pool = manifest minus today's daily (`practicePool()` in app.js) — with ≤1 entry the pool is empty. Not a bug with a thin manifest. | Publish more puzzles | design |
| Daily shows **yesterday's** (or an older recent) puzzle | Runway probe: `python -c "import sys; sys.path.insert(0,'curation'); import publish, manifest; print('runway', publish.runway(manifest.load()))"` (printed `runway 2` as of 2026-07-03) | 1. **Pool ran dry** — `pickPuzzle` falls back to the most recent entry on/before today. Working as designed, silent. 2. Device clock behind | Curate more puzzles (see degreesoffilm-run-and-operate). Not a code bug. | `docs/daily.js` |
| Daily shows the **earliest** puzzle (#1) | `node -e "import('./docs/daily.js').then(d=>console.log(d.todayISO()))"` vs the manifest's date range | `pickPuzzle`'s last fallback fires only when **every** manifest date is in the future relative to the device — device clock wrong, or manifest dates corrupted | Fix the clock; inspect manifest dates. `todayISO` is **device-local**, an accepted DESIGN divergence — don't "fix" it | §4.2 |
| **Gibberish text** shown to players (base64-ish, may start with an invisible U+0001) | Is it an answer/caption surface? Which code path renders it? | A path forgot to decode. Known decode points: `decodeRungs(puzzle.rungs)` in app.js `loadAndStart`; `publish.upcoming_schedule` decodes manifest titles for the schedule view; `app.py api_puzzle` decodes for edit-load. A NEW surface that reads `answers`/`caption`/manifest `title` must call `cipher` decode | Add the decode call at the new surface | §4.4 |
| **Plaintext answers visible in devtools** JSON | Does the on-disk string start with the U+0001 sentinel? | Hand-authored or unmigrated puzzle — decode is a passthrough for un-prefixed strings **by design** (puzzle 001 is plaintext, intentionally). Obfuscation is anti-snoop only, not security | If it should be encoded: `curation/obfuscate_puzzles.py` (idempotent). Often: no action | `docs/cipher.js` |
| Credit image broken/missing after answering a rung | Network tab: 404 on `puzzles/images/NNN-rK.jpg`? | 1. Headshot file never written / deleted → onerror swaps in the **full frame** (caption hidden); if even that fails the img is hidden — so a "full frame instead of headshot" display IS the fallback working 2. Rung's `image` field names the wrong file | Backfill via `curation/backfill_credit_images.py`, or edit the puzzle in the curation tool | `docs/app.js` onerror + `docs/frame.js` |
| Reveal doesn't widen on wrong film guesses | How many entries in the puzzle's `images[]`? | Single-tier puzzle (001 has one image) — `frame.js` clamps the tier to `images.length - 1`, so it **correctly stays put**. Only a bug if a 3-tier puzzle doesn't widen | Nothing for single-tier. For 3-tier: check `game.attempts` is passed as `revealTier` in app.js `updateFrame` | `docs/frame.js` |
| Theme colors wrong / page stays default dark | Does the puzzle JSON have a `theme` object? | 1. `applyTheme` returns silently if `theme` is falsy (hand-authored puzzles may omit it) 2. Bad accent → run `node theme.test.js` | Re-publish/edit to regenerate theme; `theme.bg`/`bg2` drive the gradient | `docs/app.js` applyTheme |
| Streak didn't increment / played-count stuck | Did you already finish **today's daily** today? | `recordResult` is **idempotent per date**: `if (s.lastDate === date) return s;` — a same-day replay ("Play again") changes nothing. By design | Not a bug. Streak resets when the day gap ≠ 1 | `docs/stats.js` |
| Poser / Practice / archive run didn't count toward stats | — | By design: `showEnd` guards with `!isArchive && !poser && !isPractice` before `recordResult` | Not a bug | `docs/app.js` showEnd |

### 2b. Curation tool (`curation/`, localhost:8001)

Start: `.venv/Scripts/python -m uvicorn app:app --app-dir curation --port 8001`.
Key fact: the key is loaded **per-request** (`_key()` in `curation/app.py`), so the server
always starts fine key-less; failures appear per endpoint. Exactly 7 endpoints need the key:
`/api/discover`, `/api/random`, `/api/search`, `/api/film/{id}`, `/api/puzzle/{pid}`,
`/api/approve`, `/api/update`. `/api/autocrop`, `/api/schedule`, `/api/next-date`, and
`/api/clear-schedule` work without it.

| Symptom | First probe | Likely causes (ranked) | Fix | Ref |
|---|---|---|---|---|
| Server won't start | Read the uvicorn traceback | 1. Ran with system python (no fastapi) — must use `.venv/Scripts/python` 2. `--app-dir curation` missing 3. Port 8001 busy | `pip install -r curation/requirements.txt` into `.venv`; correct command above | degreesoffilm-build-and-env |
| Page loads but Discover/Search/Randomize all 500, response detail readable: `TMDB_API_KEY not set — put your key in curation/.env (gitignored; do not paste it in chat).` | The 500 body's `detail` field | Missing/placeholder key: `tmdb.load_key()` raises SystemExit, `_key()` re-raises it as `HTTPException(500, str(e))` | Put the key in `curation/.env` (`TMDB_API_KEY=...`). Never print/commit it | `curation/tmdb.py`, `curation/app.py` `_key` |
| 500 with **opaque** "Internal Server Error"; uvicorn console traceback shows `HTTP 401 (check your TMDB_API_KEY) on /...` | The server console, not the browser | Key present but **wrong/revoked**: `tmdb.get` raises RuntimeError (not HTTPException), so FastAPI returns a generic 500 and the real message lands only in the server log | Fix the key in `curation/.env` | `curation/tmdb.py` get() |
| Discover returns few/no films | Try `/api/search?q=<known title>` — does search work? | 1. Ledger has consumed the top of the sorted pool (Discover scans only 3 pages of the floor `vote_count≥800 & vote_average≥6.5`) 2. Key problem (see above) | Change the sort dropdown, use Search or Randomize; not a bug when the used ledger overlaps the shortlist | `curation/app.py` api_discover, `curation/discover.py` |
| Randomize → 404 `couldn't find an unused film — try Randomize again` | Just retry | The random page draw found only used films 6 times running — expected occasionally, near-certain only if the eligible pool is nearly exhausted for that sort | Re-roll; switch sort | `curation/app.py` api_random |
| 400 `image must be a TMDB image URL` (autocrop/crop/headshot save) or 400 `image_url must be a TMDB image URL` (approve) | What URL did the UI send? | `_download_rgb` / `api_approve` reject any non-`https://image.tmdb.org/` URL — key-hygiene guard, not a network error | Use a still from the tool's own picker | `curation/app.py` |
| 400 `box must be [x, y, w, h]` | Payload's `box` field | Malformed crop box from the UI (or a hand-rolled request) | Re-drag the crop; send 4 normalized floats | `curation/app.py` _crop_and_theme |
| Auto-crop box off-center / on a title card / ignores an obvious face | `.venv/Scripts/python -c "import cv2; print(cv2.__version__, cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml').empty())"` (prints `4.13.0 False` when healthy, as of 2026-07-03) | 1. cv2 missing or cascade empty → `detect_faces` returns `[]` **silently** and the edge-energy fallback runs 2. cv2 fine but Haar missed (angled/dark/profile face — Haar is frontal-only) 3. Genuinely faceless frame — edge energy picks the busiest region, de-weighted at the top/bottom bands to dodge title cards | Auto-crop is a *starting point by design* — re-drag. If cv2 is broken: reinstall `opencv-python-headless>=4.9,<5` (the `<5` pin is load-bearing: OpenCV 5.0 dropped the bundled Haar cascades) | §4.3, `curation/images.py` |
| Approve wrote an unexpected date | `GET /api/next-date` — or offline: the runway probe in §2a prints `next free date` | The date field pre-fills with `publish.next_date()` = **day after the latest manifest date** (not "today") so back-to-back publishes queue instead of colliding. If you wanted a specific day, you must set the field (or click an empty schedule slot) before Approve | Move it: click the filled day in the schedule strip → edit → change the date → update | §3.2, `curation/publish.py` next_date |
| Edit view shows stale/odd data, or 404 `no ledger entry for puzzle {pid}` / `puzzle file {pid} not found` | `python -c "import sys; sys.path.insert(0,'curation'); from ledger import load; print([(e['puzzle'],e['id']) for e in load()])"` | 1. Puzzle's ledger record was removed (Clear-scheduled frees films by deleting ledger rows) — edit-load maps puzzle→film **via the ledger** 2. Puzzle file deleted/renamed 3. Browser cached an old curation page (same fresh-port logic applies to :8001) | Restore ledger/manifest from git if a clear went wrong: `git checkout -- docs/puzzles/manifest.json curation/used_films.json` | `curation/app.py` api_puzzle |

### 2c. Content / data (`docs/puzzles/` ↔ `curation/used_films.json`)

The three records must agree: **manifest** (`docs/puzzles/manifest.json`, the daily index),
**puzzle files** (`docs/puzzles/NNN.json` + images), **ledger** (`curation/used_films.json`,
never-repeat). For a full mechanical check use **degreesoffilm-diagnostics-and-tooling**'s
`validate_content.py`. Quick offline probe (verified, prints `entries 7 | dates unique: True |
all titles decode: True` as of 2026-07-03):

```
python -c "import json,sys; sys.path.insert(0,'curation'); import cipher; man=json.load(open('docs/puzzles/manifest.json',encoding='utf-8')); print('entries', len(man), '| dates unique:', len({e['date'] for e in man})==len(man), '| all titles decode:', all(not cipher.deobfuscate(e['title']).startswith(chr(1)) for e in man))"
```

| Symptom | First probe | Likely causes (ranked) | Fix | Ref |
|---|---|---|---|---|
| Puzzle file exists but never appears in the game (**orphan**) | Compare `ls docs/puzzles/*.json` against manifest ids (probe above) | Its manifest entry was replaced: `manifest.upsert` drops any prior entry sharing the **same date OR same id**. Historically: two same-day publishes → second silently evicted the first | Re-add the entry via the edit flow (`/api/update` re-upserts), or hand-edit the manifest + validate | §3.2 |
| Duplicate dates in the manifest | Probe above (`dates unique: False`) | Hand-edit gone wrong — `upsert` itself can't produce duplicates | Fix by hand; `pickPuzzle` with duplicate dates picks the `sort`-stable first, which is undefined behavior you don't want | `curation/manifest.py` |
| Film re-suggested by Discover/Randomize that was already used | Ledger probe in §2b | 1. Clear-scheduled **intentionally** freed it (`remove_by_puzzles`) 2. Ledger row lost | Intentional after a clear. Otherwise restore: `git checkout -- curation/used_films.json` | `curation/ledger.py` |
| Manifest/ledger mysteriously changed on disk | `git diff docs/puzzles/manifest.json curation/used_films.json` | A live-write endpoint ran (`/api/approve`, `/api/update`, POST `/api/clear-schedule`) — including "just testing" one | Both files are git-tracked: `git checkout -- docs/puzzles/manifest.json curation/used_films.json` (this exact restore recovered the puzzle-004 reschedule incident — recorded account in project_state.md). Rule: never point live-write tests at committed content | project_state.md |

### 2d. Deploy / end-to-end (GitHub Pages)

| Symptom | First probe | Likely causes (ranked) | Fix | Ref |
|---|---|---|---|---|
| Pushed, but the live site is unchanged | `curl.exe -s "https://bluesuitcase.github.io/DegreesofFilm/puzzles/manifest.json"` — is the new content there at the source? | 1. **Never actually pushed** (`git log origin/main..main` shows unpushed commits) 2. Commit didn't touch `docs/` (Pages only serves `docs/`; curation-only commits deploy nothing visible) 3. Pages build still running (minutes) 4. **Browser cache**: the client cache-busts ONLY the manifest fetch (`?d=<todayISO>` in app.js) — puzzle JSON, images, JS, CSS use normal HTTP caching, so a hard reload (Ctrl+F5) may be needed to see them refresh | Push; wait a few minutes; hard reload. Checking the raw manifest URL bypasses the app entirely and isolates "deployed?" from "cached?" | §4.5 |
| Live daily differs from local daily | Compare live manifest (probe above) with local `docs/puzzles/manifest.json` | Local publishes not yet committed/pushed — Approve writes to the working tree only; deploy requires a git push | Commit + push `docs/` (spoiler-safe message: "Add puzzle NNN (YYYY-MM-DD)" — never the film title before its date) | degreesoffilm-change-control |

## 3. The trap hall of fame

The three costliest time-sinks in this project's history (owner-ranked). Full chronicle with
evidence in **degreesoffilm-failure-archaeology**.

### 3.1 The stale ES-module cache (the #1 "my fix didn't work" sink — recurring)

**What it looked like:** you edit `docs/app.js` (or CSS), reload — even hard-reload — and the
behavior doesn't change. You conclude the fix is wrong, "fix" it again, spiral into debugging
code that was already correct.
**What it actually was:** the browser caches ES modules and stylesheets per **origin:port**,
and `python -m http.server` sends no cache-busting headers. Hard reload does not reliably
re-fetch imported submodules.
**The experiment that finds it in minutes:** serve on a **fresh port** —
`python -m http.server 8010 --directory docs` — and retest there. Fresh port = fresh cache
key = guaranteed current code. If the fix works on 8010, it always worked.
**The rule:** any player-visible verification happens on a fresh port (or with a cache-busted
import). This is written into project_state.md "Workflow / gotchas". Corollary for content:
the *deployed* client cache-busts only the manifest, so the same trap exists in production
for JS/images (§2d).

### 3.2 The manifest date-collision (orphaned puzzles 003/004, 2026-06-30)

**What it looked like:** three puzzles published in one session (two orphaned); later, the
orphans simply didn't exist as far as the game was concerned — files on disk, absent from
the daily rotation and the archive.
**What it actually was:** `manifest.upsert` (`curation/manifest.py`) replaces any entry with
the same **date** (one-puzzle-per-day is enforced by eviction, not by error). Both publishes
defaulted to "today", so the second upsert silently dropped the first entry, orphaning its
file. Recovered in commit `772f4f7` ("Add curated puzzles 004/005 + recover the manifest");
prevented by `257bcff` ("Curation: auto-assign the next free publish date (fix manifest
collisions)"), which makes
`publish.next_date()` default every publish to the day **after** the latest manifest date.
**The experiment that would have found it in minutes:** after every publish, list the
manifest (probe in §2c) and diff entry count vs puzzle-file count. An orphan shows instantly.
**The rules that now exist:** the date field auto-fills with `next_date`; don't hand-set the
same date twice; and know that the eviction-by-date behavior is still there — it's what makes
*reschedules* clean, so it is a feature with a sharp edge, not a bug to remove.

### 3.3 The character-stills dead end (a data-reality lesson, not a code bug)

**What it looked like:** a whole feature — per-rung *character stills* with a manual picker
(built across PRs #12/#13) — that kept producing wrong-looking results: generic backdrops,
the same crowd shot for multiple cast members. Looked like a matching/picker bug worth
debugging.
**What it actually was:** reality. TMDB's person-tagged images are **sparse** — most films
have few or no per-character stills, and what exists is mostly shared backdrops. No amount of
code fixes absent data. The feature was removed in `3e2cfbb` ("Curation: drop the manual
cast-photo picker — headshots are automatic"); ALL credit rungs now use the person's TMDB
headshot automatically.
**The experiment that would have found it in minutes:** before building, sample the tagged-
image counts for 10 representative films and eyeball what comes back — a 20-minute throwaway
probe (the same de-risk pattern that validated ladder ordering in `curation/validate_ladder.py`).
**The rule:** when output quality looks wrong, first ask "is the *source data* capable of
being right?" — and **do not rebuild character stills** (settled; see
degreesoffilm-failure-archaeology).

## 4. Discriminating experiments — separating look-alike causes

1. **Stale cache vs real regression** (player client). Serve `docs/` on a fresh port and
   reproduce there. Fresh port → bug gone = cache; bug persists = regression → run the suite
   for the file you changed (§1 table) and bisect with `git stash` / `git log -p -- docs/<file>.js`.
2. **Pool-dry repeat vs date bug** (wrong daily). Run the runway probe (§2a). Runway 0 and
   the shown puzzle is the manifest's **latest** entry = pool dry, by design. Shown puzzle is
   the **earliest** entry = every manifest date is in the device's future → clock or manifest
   dates. Anything else → `node daily.test.js` and inspect the manifest ordering.
3. **cv2-missing vs Haar-miss vs genuinely faceless** (auto-crop). Run the cv2 probe (§2b).
   Import fails or `cascade empty: True` → environment: reinstall `opencv-python-headless>=4.9,<5`.
   cv2 healthy + the face is angled/profile/dark → Haar-miss (frontal-only classifier),
   expected: re-drag. cv2 healthy + no human face in frame → faceless, edge-energy fallback is
   the intended behavior. All three produce the identical symptom (edge-energy box) because
   `detect_faces` returns `[]` silently in every case — only the probe separates them.
4. **Obfuscation drift vs forgot-to-decode** (gibberish). Run **both** cipher suites:
   `node cipher.test.js` and `python curation/cipher.test.py`. One fails the shared fixed
   vector = the two implementations drifted (KEY/SENTINEL/scheme out of sync) — stop, this
   breaks all published content; see degreesoffilm-architecture-contract. Both green =
   the ciphers are fine and some render path skipped its decode call (§2a gibberish row lists
   the three known decode points).
5. **Deploy lag vs never-pushed** (live site stale). `git log --oneline origin/main..main` —
   non-empty = never pushed. Empty → fetch the raw live manifest URL (§2d): new content there
   = your browser cache; old content there = Pages build in progress (wait minutes, then
   re-check) or the commit didn't touch `docs/`.

## 5. Escalation map

- **Rules / scoring / matcher behavior is wrong** (not broken, *wrong*): do NOT hot-patch.
  Matcher changes are test-first against `match.test.js` (the contract). Route via
  **degreesoffilm-validation-and-qa** for the evidence bar and test-writing pattern.
- **The fix requires crossing a zone boundary** (key near `docs/`, DOM in `game.js`, a
  client TMDB call, runtime writes): check **degreesoffilm-architecture-contract** first —
  you are probably about to violate an invariant.
- **Landing the fix** (PR vs direct-to-main, spoiler-safe commit message, rollback):
  **degreesoffilm-change-control**.
- **Need measurement, not eyeballing** (content validation, per-puzzle reports, endpoint
  safety table): **degreesoffilm-diagnostics-and-tooling**.
- **"Has this been tried before?"** — check the settled-battles index in
  **degreesoffilm-failure-archaeology** before re-investigating anything in §3.

## When NOT to use this skill

- Setting up the machine, venv, or deps from scratch → **degreesoffilm-build-and-env**.
- Normal operation (publishing puzzles, running the tools when nothing is broken) →
  **degreesoffilm-run-and-operate**.
- Understanding design intent, invariants, or "is this allowed?" →
  **degreesoffilm-architecture-contract**.
- Term definitions, TMDB data model, matcher/image/color theory →
  **degreesoffilm-domain-reference**.
- Historical investigations and why past approaches were rejected →
  **degreesoffilm-failure-archaeology**.
- Writing or extending tests / the evidence bar → **degreesoffilm-validation-and-qa**.
- Config values and where they live → **degreesoffilm-config-and-flags**.

## Reusing this pattern beyond this project

The transferable template: (1) organize by **symptom**, not by module; (2) quote error
strings verbatim from source so grep finds the table row; (3) rank causes and give one
copy-pasteable discriminating probe per row; (4) write the 2–3 costliest incidents as
stories ending in "the experiment that would have found it in minutes"; (5) pair look-alike
causes explicitly. Project-specific content (zones, cipher, manifest semantics, Haar
fallback) does not transfer — the *shape* does.

## Provenance and maintenance

- Written 2026-07-03. Every quoted error string read directly from `docs/app.js`,
  `docs/daily.js`, `docs/cipher.js`, `docs/frame.js`, `docs/stats.js`, `curation/tmdb.py`,
  `curation/app.py`, `curation/images.py`, `curation/publish.py`, `curation/manifest.py`.
  Incident hashes (`772f4f7`, `257bcff`, `3e2cfbb`, `45b4085`, `388e645`) verified via
  `git log --oneline --all`. All probe commands in §1–§4 executed successfully on
  2026-07-03 (except server-start and live-write actions, derived from code by policy).
  All 7 JS suites + `curation/cipher.test.py` ran green the same day.
- Re-verify drift-prone facts:
  - Error strings: `grep -n "Could not load" docs/app.js` · `grep -n "TMDB_API_KEY not set" curation/tmdb.py` · `grep -rn "HTTPException" curation/app.py`
  - Key-needing endpoints: `grep -n "= _key()" curation/app.py` (exactly 7 call sites expected)
  - Runway/next-date: the probe in §2a
  - Manifest health: the probe in §2c
  - cv2 health: the probe in §2b
