---
name: degreesoffilm-config-and-flags
description: >-
  Catalog of every configuration axis in the Degrees of Film repo — game-rule constants
  (attempts/skips/helps/scoring curve), matcher typo thresholds, query-string routes,
  localStorage keys, CSS variables, curation pool floor, ladder ordering knobs (max_cast,
  director_after), decoy counts, imaging/auto-crop parameters, cipher KEY/SENTINEL, TMDB
  endpoints/timeouts, pip pins, and launch/hook config. Load when asking "what does X
  default to", "where is Y configured", "how do I change attempts / skips / scoring /
  the pool floor / crop size / decoy count", "is there a flag for Z", when a constant in
  code disagrees with docs, or when adding any new option/knob to the project. Every value
  is dated and comes with a re-verification probe because constants drift.
---

# Degrees of Film — configuration and flags catalog

**All values verified 2026-07-03** by reading the defining file and/or running the probe
shown. If today is later, run the [master re-verification block](#master-re-verification-block)
and trust its output over these tables. Terms (rung, tier, decoy, ledger, manifest, runway…)
are defined in **degreesoffilm-domain-reference**'s glossary.

## 1. How configuration works here

There is **no feature-flag system, no config file, no env-driven behavior switches** in the
player client. "Configuration" in this repo is exactly six mechanisms:

| # | Mechanism | Where | Example |
|---|-----------|-------|---------|
| 1 | Module-level constants | top of a `docs/*.js` or `curation/*.py` module | `MAX_ATTEMPTS = 3` in `docs/game.js` |
| 2 | Function keyword defaults | pure functions take knobs as params (testability) | `order_rungs(..., max_cast=8, director_after=2)` |
| 3 | Query-string params | `docs/app.js` `init()` routing | `?play&mode=poser` |
| 4 | CSS variables | `:root` in `docs/style.css`, overridden per-puzzle by `applyTheme` | `--amber:#eba53c` |
| 5 | Environment variables | exactly one: `TMDB_API_KEY` (from gitignored `curation/.env`) | `curation/tmdb.py` `load_key()` |
| 6 | pip version pins | `curation/requirements.txt` | `opencv-python-headless>=4.9,<5` |

**Picking a mechanism for a new option:** pure-logic knob → keyword default with a
module-constant default value (mechanism 1+2 — Node/Python tests can assert it); player-visible
mode/view → query param (mechanism 3); cosmetic → CSS variable (4). Never a new env var unless
it is a secret (only the TMDB key qualifies today); never a runtime config file (the client is
static hosting — there is nowhere to put one). See the [checklist](#5-add-a-new-config-axis-checklist).

**Table format:** columns are Name | Value | Defined in | What it does | Gate. Gates:
**free** (edit, run suites, land per change-control's normal path) · **test-first** (a test
asserts it — change the test in the same commit, red→green) · **change-control** (player-facing
or cross-file consequences; route through **degreesoffilm-change-control**) · **owner** (owner
sign-off required) · **FROZEN** (changing it breaks published content — do not touch).
Each table ends with its tested re-verification probe (Git Bash, repo root); the master block
at the bottom runs them all.

## 2. Catalog

### A. Client game rules

| Name | Value | Defined in | What it does | Gate |
|---|---|---|---|---|
| `MAX_ATTEMPTS` | 3 | docs/game.js | wrong guesses per rung; 3rd ends the run (`strikeout`) | test-first (game.test.js) |
| `MAX_SKIPS` | 5 | docs/game.js | skips per game at −1 pt each; a skip beyond the 5th ends the run (`out_of_skips`) | test-first (game.test.js) |
| `MAX_HELPS` | 3 | docs/game.js | I-Need-Help uses per game; helped rung worth 0 | test-first (game.test.js) |
| `scoreForRung(n)` | `n + min(max(n−5,0),5)` → 1,2,3,4,5,7,9,11,13,15,16,17 for rungs 1–12 | docs/game.js | rung value: N pts + deep-dig bonus from rung 6, capped +5 from rung 10 | **owner** + test-first (asserted verbatim in game.test.js) |
| Skip penalty | −1 | docs/game.js `skip()` | hardcoded `this.score -= 1` | test-first |
| Poser scoring | flat +1 per correct | docs/game.js `guess()` | `mode === 'poser' ? 1 : …` — mode changes ONLY scoring in game.js | test-first |
| `POSER_RUNGS` | 7 | docs/app.js | Poser trims the ladder to the first 7 decoy-bearing rungs (`poserPuzzle`) | change-control (player-facing, no test covers it) |
| `roastTier` thresholds | won→cinephile; ratio ≥0.6→almost; ≥0.3→buff; else poser | docs/app.js | picks the end-screen roast tier + mode-nudge CTA | free (tone), change-control if thresholds move |

```bash
node -e "import('./docs/game.js').then(g=>console.log('attempts',g.MAX_ATTEMPTS,'skips',g.MAX_SKIPS,'helps',g.MAX_HELPS,'curve',[1,2,3,4,5,6,7,8,9,10,11,12].map(g.scoreForRung).join(',')))"
grep -n "POSER_RUNGS = \|ratio >= " docs/app.js
```

### B. Client UI / routing

All routing lives in `docs/app.js` `init()` (query string on `docs/index.html`).

| Name | Value | Defined in | What it does | Gate |
|---|---|---|---|---|
| Routes | `?` home · `?modes` · `?play` daily · `?play&mode=poser` · `?id=N` archive replay · `?archive` index · `?practice` chooser · `?practice&mode=cinephile\|poser` endless | docs/app.js `init()` | view selection; unknown `mode` values fall back to `cinephile` | change-control (player-facing) |
| `MODE_LABELS` | `{cinephile:'Cinephile', poser:'Poser', buff:'Movie Buff'}` | docs/app.js | mode-badge text (`buff` is v3 — label exists, mode doesn't) | free |
| `QUOTES` | 6 film-quote one-liners (the master-block overlap probe prints the live list; two currently collide with the puzzle set) | docs/app.js | home-screen quote, rotates by day number `% QUOTES.length` | change-control — **spoiler constraint, see trap box 4** |
| `ROASTS` | 4 tiers: poser×4, buff×4, almost×2, cinephile×3 lines | docs/app.js | end-screen roast pool, random pick within tier | free (tone; keep spoiler-free) |
| Manifest cache-bust | `puzzles/manifest.json?d=` + `todayISO()` | docs/app.js `init()` | date-keyed fetch so a cached manifest can't freeze the daily | change-control |
| Practice pool | manifest minus today's daily; avoids immediate repeat when pool > 1 | docs/app.js `practicePool`/`nextPracticeEntry` | endless-run film picker; practice/poser/archive runs never touch daily stats | change-control |
| Daily pick fallback | exact date → most recent on/before → earliest | docs/daily.js `pickPuzzle` | pool-dry shows the latest puzzle again (silent repeat, not a crash) | test-first (daily.test.js) |
| Rollover boundary | device-LOCAL date | docs/daily.js `todayISO()` | known accepted divergence from DESIGN §4's "global" wording — flag, don't fix | **owner** |

```bash
grep -n "params.has(\|MODE_LABELS\|const QUOTES\|manifest.json?d=" docs/app.js | head -12
node -e "import('./docs/daily.js').then(d=>console.log('todayISO()',d.todayISO()))"
```

### C. Client persistence

| Name | Value | Defined in | What it does | Gate |
|---|---|---|---|---|
| localStorage key | `'dof-stats-v1'` | docs/stats.js (`KEY`) | the ONLY persisted player state | **effectively FROZEN** — renaming orphans every player's stats/streak; a rename is a v2→v3 migration task |
| `defaultStats()` shape | `{played, wins, bestDepth, currentStreak, maxStreak, lastDate, lastDepth, histogram}` | docs/stats.js | stats schema; `loadStats` spreads defaults under parsed JSON, so ADDING a field is safe, renaming isn't | test-first (stats.test.js) |
| Streak rule | same `lastDate` → no-op (idempotent); day-gap 1 extends, else resets to 1 | docs/stats.js `recordResult` | replaying today can't double-count | test-first (stats.test.js) |

```bash
grep -n "dof-stats" docs/stats.js
```

### D. Matcher thresholds (docs/match.js)

**Contract-first module**: match.test.js is the spec. Add a case there BEFORE touching the
algorithm. Gate for everything in this table: **owner + test-first**.

| Name | Value | What it does |
|---|---|---|
| `maxDist(len)` | 0 for ≤3 chars · 1 for ≤6 · 2 for ≤10 · `floor(len*0.2)` above | Levenshtein typo tolerance vs the normalized answer's length |
| Surname rule | single-token guess === answer's LAST token (multi-token answers only) | "Bardem" matches "Javier Bardem"; "Joel" does NOT match "Joel Coen" |
| `normalize()` pipeline | lowercase → strip diacritics → `&`→` and ` → punctuation→space → collapse ws → drop ONE leading `the`/`a`/`an` | applied to both guess and answers before comparison |

```bash
node -e "import('./docs/match.js').then(m=>console.log('maxDist(3,6,10,20)=',[3,6,10,20].map(m.maxDist).join(','),'| norm:',m.normalize('The Coën, Brothers & Co')))"
```

### E. Theming / CSS

| Name | Value | Defined in | What it does | Gate |
|---|---|---|---|---|
| `onAccentText` defaults | `dark='#1a1206'`, `light='#ece7dd'` | docs/theme.js | text color placed ON the accent — higher WCAG contrast wins; unparseable accent → dark | test-first (theme.test.js) |
| `:root` CSS vars | `--ink:#121013 --ink2:#1a171c --bone:#ece7dd --muted:#8c867b --amber:#eba53c --amber-deep:#caa64f --on-accent:#1a1206 --red:#c2543f --line:#2a262d` (+ `--font`, `--mono` stacks) | docs/style.css lines 1–6 | the dark ink/bone/amber base theme | change-control (player-facing) |
| Per-puzzle override map | `theme.accent`→`--amber`+`--amber-deep`+`--on-accent`; `theme.bg`→`--ink`; `theme.bg2`→`--ink2`; body gradient `linear-gradient(180deg, bg2 0%, bg 55%)` | docs/app.js `applyTheme` | puzzle JSON `theme` recolors the page; **bone text stays fixed** for legibility | change-control |
| Mobile breakpoints | `max-width:600px` (main), `max-width:380px` (tiny), plus `prefers-reduced-motion` kill-switch | docs/style.css | responsive layout | free |

```bash
sed -n '1,6p' docs/style.css; grep -n "@media (" docs/style.css
node -e "import('./docs/theme.js').then(t=>console.log('on #eba53c ->',t.onAccentText('#eba53c')))"
```

### F. Curation — pool floor & ladder ordering

| Name | Value | Defined in | What it does | Gate |
|---|---|---|---|---|
| `POOL_MIN_VOTES` | 800 | curation/discover.py | TMDB `vote_count` floor — the fame proxy | free (curation-only; affects future puzzles) |
| `POOL_MIN_AVG` | 6.5 | curation/discover.py | TMDB `vote_average` floor — the quality proxy | free |
| `discover_unused` defaults | `pages=3`, `sort_by="popularity.desc"` | curation/discover.py | CLI/library discover paging (`--count` CLI default 8) | free |
| `order_rungs` defaults | `max_cast=8, director_after=2` | curation/build_rungs.py | cast trimmed to max_cast; director inserted after top-2 leads — **see trap box 1: app.py overrides max_cast to 6** | test-first (build_rungs.test.py) |
| Cast sort | billing order `cast[].order` asc, popularity desc tiebreak | curation/build_rungs.py `order_cast` | THE settled ordering decision — popularity-sort was rejected (buried the Joker at rung 13); do not re-fight | **owner** |
| `ROLES` jobs | Director→"Director" · Cinematographer→"Director of Photography" · Composer→"Original Music Composer" · Editor→"Editor" · Production Designer→"Production Design" | curation/build_rungs.py | rung role → TMDB crew `job` string + player prompt; **Writer is deliberately NOT a rung** | change-control |
| `DEEP_ROLES` order | Cinematographer, Composer, Editor, Production Designer | curation/build_rungs.py | fixed deepest-rung crew order | change-control |

```bash
python -c "import sys;sys.path.insert(0,'curation');import discover,build_rungs,inspect;print('floor',discover.POOL_MIN_VOTES,discover.POOL_MIN_AVG);print(inspect.signature(build_rungs.order_rungs));print('deep',build_rungs.DEEP_ROLES)"
```

### G. Curation — decoys

All in `curation/decoys.py`; gate **free** (curation-only, future puzzles), pure core asserted
by decoys.test.py.

| Name | Value | What it does |
|---|---|---|
| `pick_decoys` `n` | 3 | decoys per rung (feeds I-Need-Help MC + all of Poser) |
| `gather_pools` `source_limit` | 8 | neighbour films mined for candidates (`/recommendations` first, `/similar` fallback) |
| `gather_pools` `cast_per_film` | 5 | top-billed cast taken per neighbour film |
| `gather_pools` `min_votes` | 400 | neighbour-film vote floor (keeps decoys recognizable) |
| Pool hygiene | popularity-sorted, de-duped, anyone in THIS film excluded | a decoy can never be accidentally correct |
| `DEEP_JOBS` | same role→job map as build_rungs `ROLES` (minus prompts) | same-category decoys for crew rungs |

```bash
python -c "import sys;sys.path.insert(0,'curation');import decoys,inspect;print(inspect.signature(decoys.pick_decoys));print(inspect.signature(decoys.gather_pools))"
```

### H. Curation — imaging & auto-crop

`curation/images.py` unless noted. Gate **free** (curation-only) except the pin (trap box 3);
pure math asserted by images.test.py.

| Name | Value | What it does |
|---|---|---|
| `DEFAULT_FACTORS` | `(1.0, 1.8, None)` | reveal tiers: tight box ×1.0, ×1.8 wider, `None`=full frame (most-zoomed first) |
| `crop_tiers` `out_width` | 1000 | every tier resized to 1000px wide |
| `save_tiers` `quality` | 85 | tier JPEG quality; filenames `{stem}-{i}.jpg` (i from 1) |
| `auto_crop_box` defaults | `scale=0.5`, `sample_w=160` | suggested box side = 50% of frame; edge-energy map downscaled to 160px wide |
| `box_around` clamp | scale clamped 0.05–1.0; normalized w == h | keeps the frame's pixel aspect so tiers zoom smoothly |
| `deweight_bands` | `top=0.12, bottom=0.18, factor=0.35` | title-card/subtitle bands' edge energy ×0.35 |
| Haar params (`detect_faces`) | `scaleFactor=1.1, minNeighbors=5, minSize=max(16, min(w,h)//12)` sq; largest face first; cv2 optional → `[]` fallback | face-first auto-crop; falls back to edge energy |
| `clamp_accent` | `min_sat=0.45, min_val=0.45, max_val=0.92` | keeps the sampled accent legible on the dark base |
| `sample_accent` | 64×64 average then clamp | `theme.accent` when curator doesn't override |
| `sample_palette` / `derive_background` | 8 colors @128×128; `bg` value=0.14, `bg2` value=0.28, sat clamped 0.42–0.55 (`to_background`, own default value=0.12) | `theme.bg`/`theme.bg2` gradient tones |
| API scale clamp | `max(0.2, min(scale, 0.9))` | curation/app.py `api_autocrop` — server-side bound |
| UI slider | `min=0.25 max=0.85 step=0.05 value=0.5` (`#cropscale`) | curation/static/index.html line 148 — narrower than the API clamp, by design |
| Credit-image saver | downscale to width 1000 if wider, quality 85 | curation/app.py `_credit_saver` |
| Credit filename | `{stem}-r{n}.jpg` (1-based rung n) | curation/credits_images.py `rung_image_name` — `r` keeps them distinct from tier files |
| `HELPER_KEYS` stripped at approve | `character, person_id, profile, candidates, image_pick` | draft-only fields that must never reach a published file (test-first: credits_images.test.py) |

```bash
python -c "import sys;sys.path.insert(0,'curation');import images,inspect;print(images.DEFAULT_FACTORS);print(inspect.signature(images.crop_tiers));print(inspect.signature(images.auto_crop_box));print(inspect.signature(images.deweight_bands));print(inspect.signature(images.clamp_accent));print(inspect.signature(images.save_tiers))"
grep -n "cropscale\" min" curation/static/index.html; grep -n "max(0.2, min(scale" curation/app.py
```

### I. Cipher (keep-in-sync pair) — see trap box 2

| Name | Value | Defined in | What it does | Gate |
|---|---|---|---|---|
| `SENTINEL` | U+0001 (`"\x01"` / `String.fromCharCode(1)`) | curation/cipher.py AND docs/cipher.js | prefix marking an obfuscated string; makes encode idempotent + decode a plaintext passthrough | **FROZEN** |
| `KEY` | `"degrees-of-film"` (UTF-8 bytes) | both files | repeating-key XOR key; base64 after XOR | **FROZEN** |
| Scope | rung `answers[]` + `caption` + manifest `title` encoded; `decoys`/`prompt`/`role`/`image` stay plaintext | curation/cipher.py `_map_rungs`, publish.py | anti-devtools-snoop only — NOT security (key ships to the client) | change-control |

```bash
JS=$(node -e "import('./docs/cipher.js').then(c=>console.log(c.encode('parity-check')))"); PY=$(python -c "import sys;sys.path.insert(0,'curation');import cipher;print(cipher.obfuscate('parity-check'))"); [ "$JS" = "$PY" ] && echo "cipher parity OK" || echo "CIPHER DRIFT: js=$JS py=$PY"
```

### J. Network / API

| Name | Value | Defined in | What it does | Gate |
|---|---|---|---|---|
| `TMDB_API_KEY` | (secret — never print; lives in gitignored `curation/.env` or the environment) | read by curation/tmdb.py `load_key()` | the ONLY env var; searched in `curation/.env`, `curation/.env` via cwd, `./.env`; missing → `SystemExit` | **owner** (key hygiene invariant) |
| `API` base | `https://api.themoviedb.org/3` | curation/tmdb.py | all TMDB API calls | change-control |
| API timeout | 20 s | curation/tmdb.py `get()` | urlopen timeout; 401 → "check your TMDB_API_KEY" RuntimeError | free |
| `IMG_BASE` | `https://image.tmdb.org/t/p/original` | **defined TWICE**: curation/credits_images.py AND curation/app.py — keep in sync | image URL prefix (headshots, stills) | change-control |
| Image download timeout | 30 s + non-TMDB URLs rejected (HTTP 400) | curation/app.py `_download_rgb` | guard: only `https://image.tmdb.org/` sources | free |
| `/api/schedule` `days` | 14 | curation/app.py | week-ahead slots (runway scan itself goes 366 days — publish.py `runway`) | free |
| `/api/discover` defaults | `sort="vote_count.desc", count=12`, scans ≤3 pages | curation/app.py | tool shortlist (NB: CLI discover.py defaults differ — popularity.desc, count 8) | free |
| `/api/random` | 6 tries over random pages; paging capped at 500 (TMDB hard cap); 404 when unlucky | curation/app.py | Randomize preview pick | free |
| `/api/search` `count` | 18 | curation/app.py | search-hit cap | free |
| Stills offered | `backdrops[:12]` + poster | curation/app.py `_film_stills` | crop-stage source frames | free |
| Publish paths | `PUZZLES_DIR=docs/puzzles` (publish.py), images `docs/puzzles/images` (app.py `IMG_DIR`), ledger `curation/used_films.json` (ledger.py), manifest `docs/puzzles/manifest.json` (manifest.py) | respective modules | where content lands; stem format `f"{id:03d}"` | change-control |
| Manifest `FIELDS` | `('date','id','file','title','accent')` | curation/manifest.py | entry schema; upsert keyed by date AND id | test-first (manifest.test.py) |
| `next_date` | day after the latest manifest date, else today | curation/publish.py | collision-proof default publish date (the 2026-06-30 collision fix) | test-first (publish.test.py) |

```bash
grep -n "^API = \|timeout=20" curation/tmdb.py; grep -n "IMG_BASE = " curation/credits_images.py curation/app.py
grep -n "days: int = \|count: int = \|sort: str = \|range(6)\|500)" curation/app.py | head -8
python -c "import sys;sys.path.insert(0,'curation');import manifest,publish;print(manifest.FIELDS, publish.puzzle_stem(7))"
```

### K. Environment & tooling

| Name | Value | Defined in | What it does | Gate |
|---|---|---|---|---|
| pip pins | `pillow>=10,<12` · `fastapi>=0.110` · `uvicorn>=0.29` · `opencv-python-headless>=4.9,<5` | curation/requirements.txt | repo-root `.venv` deps; **the `<5` is load-bearing — trap box 3** | change-control |
| Launch: `docs` | `python -m http.server 8000 --directory docs`, port 8000 | .claude/launch.json | serve the game locally (`file://` won't work — fetch) | free |
| Launch: `curation` | `.venv/Scripts/python.exe -m uvicorn app:app --app-dir curation --port 8001`, port 8001 | .claude/launch.json | the crop tool | free |
| `package.json` | `{ "type": "module" }` — its ONLY purpose | package.json | lets `*.test.js` `import` the ES modules under docs/; there is NO `npm test` | change-control |
| SessionStart hook | `node -e` reads `project_state.md` into session context | .claude/settings.json | the handoff-doc injection; no other hooks/permissions configured | free |

```bash
grep -vE "^\s*#|^\s*$" curation/requirements.txt; cat package.json
python -c "import json;c=json.load(open('.claude/launch.json'));print([(x['name'],x['port']) for x in c['configurations']])"
```

## 3. Trap boxes — read before changing anything they name

> **⚠ 1. `max_cast` is 8 in the library, 6 in the tool.** `build_rungs.order_rungs`
> defaults `max_cast=8`, but `curation/app.py` `api_film` passes `max_cast=6` — every puzzle
> authored through the crop tool gets 6 cast rungs, not 8. The `decoys.py` and
> `credits_images.py` CLIs also default `--max-cast 6`; only the `build_rungs.py` CLI keeps 8.
> To change the shipped ladder length, edit the **app.py call site**, not the library default.

> **⚠ 2. The cipher KEY/SENTINEL pair is effectively FROZEN.** `KEY = "degrees-of-film"`
> and `SENTINEL = U+0001` exist in BOTH `docs/cipher.js` and `curation/cipher.py` and must
> change together (a shared fixed vector in both cipher test suites enforces parity). More
> importantly: **changing the key breaks every published puzzle** — all on-disk
> `docs/puzzles/*.json` answers/captions and manifest titles are encoded with the current key,
> and old clients/files can't be re-keyed atomically on static hosting. Treat both constants
> as frozen until v3 server-side matching retires the cipher entirely.

> **⚠ 3. `opencv-python-headless>=4.9,<5` — the `<5` is load-bearing.** OpenCV 5.0 dropped
> the bundled Haar cascades that `images.detect_faces` loads
> (`cv2.data.haarcascades + "haarcascade_frontalface_default.xml"`). Lifting the pin silently
> degrades auto-crop to edge-energy-only (detect_faces catches the failure and returns `[]`).
> Pinned deliberately in commit 388e645; migrating to OpenCV 5 (e.g. FaceDetectorYN) is a
> deliberate future step, not a pin bump.

> **⚠ 4. QUOTES spoiler constraint.** The home-screen `QUOTES` in docs/app.js must only
> quote films NOT in `curation/used_films.json` (a quote names its film — that spoils a
> puzzle). A prior violation here (two quotes named puzzle films) was **FIXED `ee4ec54`,
> 2026-07-03** (full account: degreesoffilm-failure-archaeology entry 12). This is a
> standing constraint, not a one-off: whenever you add a QUOTES entry OR publish a puzzle,
> run the overlap probe (table B / master block) and expect `none`; changes here are
> player-facing → route through **degreesoffilm-change-control**.

> **⚠ 5. The scoring curve is asserted verbatim by game.test.js.**
> `check('score curve rungs 1-12', curve, [1,2,3,4,5,7,9,11,13,15,16,17])` — any change to
> `scoreForRung` is test-first BY CONSTRUCTION and needs owner sign-off (it changes every
> player's comparable score). Same discipline for matcher thresholds (match.test.js is the
> contract).

## 4. Where's the flag for…? (quick answers)

- **Difficulty**: no single dial. Levers = pool floor (F), `max_cast` at the app.py call
  site (trap 1), matcher tolerance (D — owner-gated), attempts/skips/helps (A).
- **Crop tightness**: curator-facing = the UI slider (H); the suggestion default =
  `auto_crop_box scale=0.5`; tier widening = `DEFAULT_FACTORS`.
- **Turn off Poser/Practice**: no flag — they're routes (B). Removing = editing
  index.html/app.js, player-facing change control.
- **Dark/light theme toggle, sound, language, analytics, A/B tests**: none exist. Don't
  assume; add via the checklist below if wanted.

## 5. "Add a new config axis" checklist

1. **Define it in exactly ONE module**, as a module constant consumed via a keyword default
   (`def f(..., *, knob=KNOB)`) so pure functions stay testable and callers can override.
   Client zone if it's a game rule (respect the layering law: match.js imports nothing,
   game.js imports only match.js, app.js does all DOM); curation zone if it's authoring.
2. **Thread it** from the constant to the call sites — never duplicate the literal. If a
   tool call site needs a different value (like `max_cast=6`), that's an explicit override
   at the call site, documented here (trap-box style).
3. **Add a test asserting the default** in the module's suite (game.test.js /
   build_rungs.test.py / …) so drift is caught. New behavior = new test, red→green.
4. **Document it**: add a row to the right table in THIS skill (with the date) + a
   re-verify probe in the master block; mention it in CLAUDE.md only if durable/architectural.
5. **Provide the re-verify one-liner** and RUN it before shipping (a probe that prints the
   live value — `node -e "import(...)"` or `python -c "…inspect.signature(…)"`).
6. **Land it through degreesoffilm-change-control** (player-facing → PR path; curation-only
   may go direct-to-main per owner's per-change choice).

## 6. Master re-verification block

Paste into Git Bash at the repo root; diff the output against the tables above. (All
read-only; safe anytime.)

```bash
echo "=== A/C/D/E: client constants ==="
node -e "import('./docs/game.js').then(g=>console.log('attempts',g.MAX_ATTEMPTS,'skips',g.MAX_SKIPS,'helps',g.MAX_HELPS,'curve',[1,2,3,4,5,6,7,8,9,10,11,12].map(g.scoreForRung).join(',')))"
node -e "import('./docs/match.js').then(m=>console.log('maxDist(3,6,10,20)=',[3,6,10,20].map(m.maxDist).join(',')))"
node -e "import('./docs/theme.js').then(t=>console.log('onAccent(#eba53c)=',t.onAccentText('#eba53c')))"
grep -n "POSER_RUNGS = \|ratio >= \|dof-stats" docs/app.js docs/stats.js
sed -n '1,6p' docs/style.css; grep -n "@media (" docs/style.css
echo "=== B: routes + QUOTES spoiler check (expect overlap none) ==="
grep -n "params.has(\|manifest.json?d=" docs/app.js | head -8
python -c "import json,re;src=open('docs/app.js',encoding='utf-8').read();block=re.search(r'const QUOTES = \[(.*?)\n\];',src,re.S).group(1);films=re.findall(r\", '([^']+)'\]\",block);used={str(r['title']) for r in json.load(open('curation/used_films.json',encoding='utf-8'))};print('QUOTES:',films);print('SPOILER OVERLAP:',sorted(set(films)&used) or 'none')"
echo "=== F/G/H/I/J: curation constants ==="
python -c "import sys;sys.path.insert(0,'curation');import discover,build_rungs,decoys,images,cipher,manifest,publish,inspect;print('floor',discover.POOL_MIN_VOTES,discover.POOL_MIN_AVG);print(inspect.signature(build_rungs.order_rungs),build_rungs.DEEP_ROLES);print(inspect.signature(decoys.pick_decoys));print(inspect.signature(decoys.gather_pools));print(images.DEFAULT_FACTORS,inspect.signature(images.auto_crop_box),inspect.signature(images.deweight_bands));print(inspect.signature(images.clamp_accent),inspect.signature(images.save_tiers));print('SENTINEL',repr(cipher.SENTINEL),'KEY',cipher.KEY);print(manifest.FIELDS,publish.puzzle_stem(1))"
JS=$(node -e "import('./docs/cipher.js').then(c=>console.log(c.encode('parity-check')))"); PY=$(python -c "import sys;sys.path.insert(0,'curation');import cipher;print(cipher.obfuscate('parity-check'))"); [ "$JS" = "$PY" ] && echo "cipher parity OK" || echo "CIPHER DRIFT: js=$JS py=$PY"
grep -n "max_cast=6" curation/app.py; grep -n "cropscale\" min" curation/static/index.html
grep -n "^API = \|timeout=20" curation/tmdb.py; grep -n "IMG_BASE = " curation/credits_images.py curation/app.py
grep -n "days: int = 14\|count: int = 18\|count: int = 12" curation/app.py
echo "=== K: env & tooling ==="
grep -vE "^\s*#|^\s*$" curation/requirements.txt; cat package.json
python -c "import json;c=json.load(open('.claude/launch.json'));print([(x['name'],x['port']) for x in c['configurations']])"
```

## When NOT to use this skill

- Setting up the venv/Node/toolchain, or a probe fails with import/module errors →
  **degreesoffilm-build-and-env**.
- Running the game or curation tool, publishing a puzzle → **degreesoffilm-run-and-operate**.
- Deciding whether/how a constant change may land, PR vs direct-to-main, sign-off →
  **degreesoffilm-change-control**.
- WHY a constant is what it is (invariants, zones, design contract) →
  **degreesoffilm-architecture-contract**; theory behind matcher/imaging/TMDB values →
  **degreesoffilm-domain-reference**.
- A value is behaving wrongly at runtime → **degreesoffilm-debugging-playbook**; history of a
  rejected setting (e.g. popularity sort) → **degreesoffilm-failure-archaeology**.
- Test inventory / how to assert a new default → **degreesoffilm-validation-and-qa**.

## Reusing this pattern beyond this project

The transferable template: (1) enumerate the finite set of configuration *mechanisms* before
cataloging values — most small projects have 4–6, not a flag system; (2) one table per zone
with an explicit change-gate column; (3) every table carries an executable probe that prints
the live values, plus one master block for whole-catalog drift checks; (4) trap boxes for
frozen/keep-in-sync/overridden constants. The values, gates, and probes themselves are
entirely project-specific — regenerate them per repo.

## Provenance and maintenance

- **Authored 2026-07-03.** Every value read directly from the defining file that day.
  Refinements recorded here: decoys.py and
  credits_images.py CLIs default `--max-cast 6` (not just app.py's call site);
  image downloads use a 30 s timeout (API calls 20 s); CLI vs API discover defaults differ.
- All probes in this file were **executed in Git Bash on 2026-07-03** and printed the values
  shown (including the cipher parity check and the QUOTES overlap — two titles, puzzles 4
  and 6; see trap box 4).
- **Maintenance rule:** any commit that changes a value cataloged here must update the row,
  the date in the header, and (if needed) the probe — in the same session. If a probe's
  output disagrees with a table, the probe wins; fix the table.
