---
name: degreesoffilm-architecture-contract
description: The load-bearing design decisions, testable invariants, data contracts, and known weak points of Degrees of Film. Load this BEFORE any structural change; when asking "can I add X here?" or "which zone does this belong in?"; when a change spans both docs/ (player client) and curation/ (private tool); when evaluating whether a feature is static-v2-shaped or needs the v3 server move; when touching the puzzle/manifest/ledger schemas, the cipher, imports between docs/*.js modules, or anything involving the TMDB key. Also load it before "fixing" the daily-rollover date logic or editing an already-published puzzle — both are guarded here.
---

# Degrees of Film — Architecture Contract

This skill is the contract you must not break. It states the invariants testably, the
schemas exactly, and the weak points honestly. How to *run* things lives in
`degreesoffilm-run-and-operate`; how to *land* a change lives in `degreesoffilm-change-control`.

## 1. The one load-bearing fact

**The TMDB API key never reaches a player.** It lives only in gitignored `curation/.env`,
read by `curation/tmdb.py` on the curator's machine. Players only ever fetch finished
static files. Every other architectural choice follows from this.

```
TMDB API
   |  (queried with the key, curation time only)
   v
+--------------------------------------------------+
| ZONE 1: PRIVATE — curator's machine              |
|   curation/ (FastAPI tool, holds the key)        |
|   used-films ledger (never repeat a film)        |
+--------------------------------------------------+
   |  (publishes static files into docs/)
   v
+--------------------------------------------------+
| ZONE 2: STATIC HOSTING — GitHub Pages, main /docs|
|   puzzle JSON (one per day) + pre-cropped images |
|   game client (html / js / css)                  |
+--------------------------------------------------+
   |  (browser fetches files; nothing else)
   v
+--------------------------------------------------+
| ZONE 3: PLAYER BROWSER — no key, no backend      |
|   vanilla ES modules: rules + fuzzy matching     |
|   stats/streak in localStorage ('dof-stats-v1')  |
+--------------------------------------------------+
```

Consequences:

1. **No player backend exists.** All game logic — rules, scoring, fuzzy matching —
   runs client-side. Anything requiring a server-held secret or a runtime write is
   v3 ("the server move"), not a patch.
2. **The archive is nearly free.** A past puzzle is just an old file that still exists;
   `?id=N` re-fetches it.
3. **The curation tool is the only key-holder and the only writer.** Everything under
   `docs/puzzles/` is produced by `curation/publish.py` (or hand-authored once, puzzle 001).
4. **Answers must ship to the client** for matching to work, hence the obfuscation
   stopgap (invariant 7) and its honest limits (§5).

## 2. Invariants (numbered, testable)

Each: the rule, why, what breaks if violated, and a verification one-liner. Run one-liners
from the repo root; they work in Git Bash. (PowerShell: `grep` is available via Git for
Windows; if not, use `Select-String` equivalents.)

**I1 — Key confinement.** No TMDB API access, key, or API URL anywhere under `docs/`.
The only permitted TMDB reference in `docs/` is the attribution footer's link to
`https://www.themoviedb.org/` in `docs/index.html`.
*Why:* `docs/` is world-served by GitHub Pages; anything in it is public.
*Breaks:* key leak → quota abuse, key revocation, terms violation.
*Verify (must print nothing, exit 1):*
```
grep -rniE "api_key|tmdb_api_key|api\.themoviedb|image\.tmdb" docs/
```

**I2 — Layering law (the exact import graph).** As of 2026-07-03, the complete set of
imports across `docs/*.js` is:
- `docs/match.js` — imports **nothing**.
- `docs/game.js` — imports **only** `./match.js` (`matchGuess`).
- `docs/daily.js`, `docs/theme.js`, `docs/stats.js`, `docs/frame.js`, `docs/cipher.js` —
  import **nothing**.
- `docs/app.js` — imports `game.js`, `daily.js`, `theme.js`, `stats.js`, `frame.js`,
  `cipher.js` (not `match.js` directly), and does **ALL** DOM work.
*Why:* rules and matching stay DOM-free so Node tests import them directly; `app.js`
stays a thin render layer.
*Breaks:* DOM in a logic module → Node test suites can't load it; rules in `app.js` →
untestable behavior (app.js has NO automated tests).
*Verify (must print exactly 7 import lines, all in app.js + game.js):*
```
grep -n "^import" docs/*.js
```

**I3 — Pure-logic / no-DOM rule.** Every module except `app.js` must run under plain
Node with no browser globals (exception: `stats.js` `loadStats`/`saveStats` touch
`localStorage` inside try/catch; its `recordResult` is pure).
*Why:* the whole JS test strategy (`node <name>.test.js`, no framework) depends on it.
*Verify:* `node match.test.js && node game.test.js && node daily.test.js && node theme.test.js && node stats.test.js && node frame.test.js && node cipher.test.js`

**I4 — Self-contained puzzle files.** Each day is one JSON under `docs/puzzles/` plus its
images under `docs/puzzles/images/`. A puzzle references nothing outside those (image
paths are relative, e.g. `images/004-1.jpg`; `app.js` prefixes `puzzles/`).
*Why:* the archive works because old files simply still exist; no cross-puzzle joins.
*Breaks:* a shared mutable resource would make past puzzles editable-by-accident.
*Verify:* `python -c "import json;p=json.load(open('docs/puzzles/004.json'));print(sorted(p))"` → `['date', 'id', 'images', 'rungs', 'theme']`

**I5 — Manifest is the sole daily index.** The client never guesses filenames: `app.js`
fetches `puzzles/manifest.json` (cache-busted `?d=<todayISO>`), picks an entry via
`daily.js` (`pickPuzzle`/`pickById`), then fetches that entry's `file`. The archive view
is just a render of the manifest.
*Why:* one atomic index = no orphaned days, free archive.
*Breaks:* hard-coded puzzle fetches reintroduce the Phase-1 placeholder bug class.
*Verify:* `grep -n "fetch(" docs/app.js` → exactly two fetches: the manifest and `'puzzles/' + entry.file`.

**I6 — Ledger never-repeat.** `curation/used_films.json` (git-tracked) records every film
made into a puzzle; `ledger.add` refuses duplicate TMDB ids; Discover/Randomize exclude
used ids. Only `id` is load-bearing (`used_ids`); `title`/`year`/`puzzle` are bookkeeping.
`ledger.remove_by_puzzles` frees films when a *scheduled* (future) puzzle is cleared.
*Why:* a repeated film kills the daily's novelty and the "never repeat" promise (DESIGN §1).
*Verify:* `python curation/ledger.test.py` (12 tests) and
`python -c "import json;l=json.load(open('curation/used_films.json'));ids=[r['id'] for r in l];print(len(ids)==len(set(ids)))"` → `True`

**I7 — Cipher parity + sentinel scheme.** `docs/cipher.js` and `curation/cipher.py` are
byte-for-byte mirror implementations: repeating-key XOR (KEY `degrees-of-film`) over
UTF-8, base64, prefixed with SENTINEL U+0001. Properties (both sides): **idempotent
encode** (won't double-encode a sentinel-prefixed string) and **plaintext passthrough
decode** (un-prefixed strings return untouched — so hand-authored/half-migrated data
always works). Both test suites assert the same fixed cross-language vector:
`obfuscate("The Dark Knight")` = SENTINEL + `MA0CUiEEAUZPLUMPDgQZ`.
*Why:* publish encodes in Python, the client decodes in JS; drift = every player sees
gibberish answers. The KEY is effectively **frozen** — changing it breaks every published
puzzle.
*Verify:* `node cipher.test.js && python curation/cipher.test.py` (19 + 22 tests green).

**I8 — One puzzle per day (upsert semantics).** `curation/manifest.py` `upsert` replaces
by BOTH `date` (one puzzle per day) and `id` (one entry per puzzle), then sorts by date.
A reschedule therefore moves an entry rather than duplicating it — and a same-date publish
**silently replaces** the incumbent (this is the mechanism behind the 2026-06-30 manifest
collision incident; `publish.next_date()` auto-assigning the next free day is the fix).
*Why:* `pickPuzzle` assumes at most one entry per date.
*Verify:* `python curation/manifest.test.py` (13 tests) and
`python -c "import json;m=json.load(open('docs/puzzles/manifest.json'));d=[e['date'] for e in m];print(len(d)==len(set(d)))"` → `True`

**I9 — Archive hides titles.** The archive view renders date + `#id` + accent swatch,
never the film title; manifest `title` fields ship obfuscated (sentinel-prefixed) so
devtools doesn't leak them either.
*Why:* the film rung IS the puzzle; a visible title spoils every archived game.
*Verify:* `python -c "import json;m=json.load(open('docs/puzzles/manifest.json'));print(all(e['title'].startswith(chr(1)) for e in m))"` → `True`
(`chr(1)` is the U+0001 sentinel), and `grep -n "never the film title" docs/app.js` hits
the buildArchive comment.

**I10 — Archived / Poser / Practice runs never touch daily stats.** The single guard is in
`docs/app.js` `showEnd()`: `if (!isArchive && !poser && !isPractice)` wraps the only
`recordResult`/`saveStats` call. Practice additionally holds back today's daily from its
pool (`practicePool`).
*Why:* the streak is the daily hook; easier/replayed runs polluting it destroys its meaning.
*Verify:* `grep -n "recordResult" docs/app.js` → one import, one guarded call.

**I11 — TMDB attribution footer is mandatory.** `docs/index.html` ships a footer with the
TMDB mark and the exact sentence "This product uses the TMDB API but is not endorsed or
certified by TMDB." DESIGN §5 lists it as a ship-blocker; it never comes off.
*Verify:* `grep -c "not endorsed or certified by TMDB" docs/index.html` → `1`

**I12 — IMMUTABLE PAST (owner rule, not code-enforced).** Never modify a published puzzle
dated ≤ today — players played it; their shared results reference it. Edits (reschedule,
re-crop, rung fixes via `/api/update`) are for **future-dated** puzzles only. The tooling
will happily edit any id; the rule is discipline.
*Why:* retroactive edits silently invalidate players' results and streak context.
*Verify:* manual gate — before any edit, check the puzzle's `date` against today.

**I13 — SPOILER DISCIPLINE (owner rule).** Nothing player-visible may leak an answer:
archive titleless (I9), answers/captions/manifest-titles obfuscated (I7), home-page QUOTES
only from films NOT in the puzzle set (`docs/app.js` QUOTES comment), share text
spoiler-free, and — because commit messages are public on GitHub — content commits name
puzzle NUMBER/date only ("Add puzzle NNN (YYYY-MM-DD)"), never the film title until its
date passes. Two historical commits violated this (`bdca151` named puzzle 006's film in
its subject; `3d7d17e` named puzzle 007's film before its date) — cited as the lesson;
history was deliberately NOT rewritten.
*Verify:* before pushing content, `git log --oneline -5` and read your message as a player would.
Also cross-check the QUOTES list against `curation/used_films.json` titles:
```
python -c "import json,re;src=open('docs/app.js',encoding='utf-8').read();q=set(re.findall(r\"', '([^']+)'\\]\",src.split('const QUOTES')[1].split('];')[0]));l={r['title'] for r in json.load(open('curation/used_films.json'))};print(sorted(q&l) or 'OK')"
```
**Known OPEN spoiler issue in the home-page QUOTES as of 2026-07-03** (puzzle 4's and
puzzle 6's films quoted) — check current state with the validator's quotes-vs-ledger group
(or the probe above); full account: degreesoffilm-failure-archaeology entry 12.

## 3. Data contracts

All schemas verified against `docs/puzzles/004.json`, `docs/puzzles/manifest.json`,
`curation/used_films.json`, and the writers (`publish.py`, `manifest.py`, `ledger.py`)
as of 2026-07-03.

### 3.1 Puzzle JSON (`docs/puzzles/NNN.json`)

Written by `publish.assemble_puzzle`. Keys in file order:

| Field | Type | Obfuscated? | Notes |
|---|---|---|---|
| `id` | int | — | Matches filename stem (`4` ↔ `004.json`) and the manifest entry `id`. |
| `date` | `"YYYY-MM-DD"` | — | Omitted if falsy (publish only writes it when set). |
| `theme` | `{accent, bg, bg2}` hex strings | — | Sampled from the still; `applyTheme` in app.js maps accent→`--amber`, bg→`--ink`, bg2→`--ink2` + gradient. Bone text stays fixed. |
| `images` | `string[]` | — | Reveal tiers, most-zoomed FIRST; paths relative to `docs/puzzles/` (e.g. `images/004-1.jpg`). Tool authors 3; 001 has one (`images/001.jpg`). Last element = full frame. |
| `rungs` | array (below) | partly | Rung 0 is always the Film rung. |

Per rung:

| Field | Type | Obfuscated? | Notes |
|---|---|---|---|
| `role` | string | no | `Film`, `Cast`, `Director`, `Cinematographer`, `Composer`, `Editor`, `Production Designer`. |
| `prompt` | string | no | Player-facing question. |
| `answers` | `string[]` | **YES** | All accepted forms (alt titles, name variants). `answers[0]` is the canonical form: it's what multiple choice and the end-screen reveal display — keep it the display-quality one. |
| `decoys` | `string[]` | no (by design) | ~3 same-category wrong answers. Feeds I-Need-Help + Poser. Rung without decoys can't be helped and is dropped from Poser. |
| `image` | string, optional | no | Credit image path (e.g. `images/004-r2.jpg`). Film rung never has one. Missing → client holds the full frame. |
| `caption` | string, optional | **YES** | "Name as Character" for cast, name only for crew — it names the answer, hence obfuscated. |

Obfuscation boundary: exactly `answers[]` + `caption` per rung (see `cipher._map_rungs`,
mirrored by `docs/cipher.js` `decodeRungs`, called once in `app.js` `loadAndStart`).
If you add a new answer-revealing field, you MUST add it to **both** `_map_rungs` (Python)
and `decodeRungs` (JS) or it ships in plaintext / renders as gibberish.

### 3.2 Manifest entry (`docs/puzzles/manifest.json`)

Array of `{date, id, file, title, accent}` (`manifest.FIELDS`), sorted by date.
`title` = `cipher.obfuscate(movie.title)` — **obfuscated**; `accent` duplicated from the
theme so the archive can show swatches without fetching puzzles. Upsert semantics: I8.

### 3.3 Ledger record (`curation/used_films.json`)

Array of `{id, title, year, puzzle}` — **plaintext** (private zone, never served).
`id` = TMDB movie id (the only field logic reads); `puzzle` = the puzzle id it became;
`year` is a string for tool-published entries but int `2007` in the hand-authored 001
record — harmless, nothing parses it.

### 3.4 Image filename conventions (`docs/puzzles/images/`)

| Pattern | Meaning | Written by |
|---|---|---|
| `NNN-1.jpg`, `NNN-2.jpg`, `NNN-3.jpg` | Reveal tiers, tightest first; `-3` is the full frame | `images.save_tiers` (`f"{stem}-{i}.jpg"`) |
| `NNN-rK.jpg` | Credit image for rung K (1-based rung position; film rung K=1 gets none, so files start at `r2`) | `credits_images.rung_image_name` |
| `001.jpg` | Legacy: puzzle 001's single hand-authored frame | hand-authored |

92 files as of 2026-07-03. `NNN` = zero-padded puzzle id (`publish.puzzle_stem`).

## 4. Date semantics — a known spec/implementation divergence. Do not "fix" either side.

- **DESIGN.md §4 says:** the client "picks the entry whose `date` matches today's
  canonical date (a single global rollover, **not** the player's local clock — avoids
  timezone desync)".
- **The code does:** `docs/daily.js` `todayISO()` builds the date from
  `getFullYear()/getMonth()/getDate()` — the **device-local** date. Every player rolls
  over at their own local midnight; two players in different timezones can be on
  different dailies for a few hours.

Verified 2026-07-03 by reading both. This divergence is **accepted in practice**: local
rollover is what Wordle-alikes do, nobody has complained, and there is no server to hold a
canonical clock anyway. It is deliberately left unresolved. If you are tempted to align
either direction (change the code to UTC, or change DESIGN to bless local time), that is a
decision, not a bugfix — route it through `degreesoffilm-change-control`. Note the
adjacent trap: streak math (`stats.js` `dayDiff`) parses dates as UTC midnights (correct,
DST-proof) while the date *labels* are local — consistent as long as `todayISO` is the
single source of the label, which it is.

## 5. Known weak points — stated plainly

| # | Weak point | Why accepted today | What would change it |
|---|---|---|---|
| W1 | **Obfuscation ≠ security.** The XOR key ships in `docs/cipher.js`; answers are also enumerable from public TMDB data. Anyone determined reads tomorrow's answers. | No leaderboard = no incentive to cheat anyone but yourself. Defeats only "open devtools and read it." | v3 server-side matching (answers never leave the backend) — see `degreesoffilm-server-move-campaign`. Do NOT harden the cipher; it's a fenced wrong path (enumerable answer space). |
| W2 | **localStorage-only stats** (`'dof-stats-v1'`): device-bound, wiped by clearing site data, no sync. | Zero infrastructure; fine for a hobby daily. | v3 accounts + DB with import-on-first-login migration. |
| W3 | **Pool-dry silent repeat.** `pickPuzzle` falls back to the most recent on/before today, else the earliest — a dry pool means the daily silently repeats the latest puzzle, never 404s. As of 2026-07-03 the pool runs through 2026-07-04. | Deliberate: an old puzzle beats an error page. Operational, not a bug. | Curate ahead (the schedule/runway view exists for this) — see `degreesoffilm-run-and-operate`. |
| W4 | **No CI.** Green tests are a manual pre-push gate; nothing enforces them. | 16 suites run in seconds locally; solo project. | CI would help but is unprioritized; until then "tests green before push" is discipline (see `degreesoffilm-change-control`). |
| W5 | **Single-curator ops.** One machine holds the key and the publishing flow; the daily dies with the curator's laptop (content already published keeps serving). | Hobby scale. | Server move / hosted curation, or simply curating a long runway. |
| W6 | **Haar face detection misses angled/dark faces**, so auto-crop can center on the wrong region. | The curator approves or re-drags every box — auto-crop is a suggestion, never auto-published. | FaceDetectorYN/heuristics exploration is a research track — see `degreesoffilm-research-frontier`. |
| W7 | **Decoys and prompts are plaintext** in puzzle JSON. | By design: they're player-facing UI text, not the answer. A snoop learns four candidates, not which one. | Nothing planned; revisit only with server-side matching. |
| W8 | **Local-clock rollover** (§4). | Accepted divergence. | A v3 server clock, decided through change control. |
| W9 | **No automated tests for `docs/app.js`, `curation/app.py` endpoints, or `curation/static/index.html`.** | The layering law keeps them thin; logic lives in tested modules. | Manual browser verification on a fresh port is the gate — see `degreesoffilm-validation-and-qa`. |

## 6. "Before you add X here" — decision table

Zone rules of thumb: needs the TMDB key or writes files → Zone 1 (`curation/`). Pure data
consumed at play time → published fields in Zone 2 (`docs/puzzles/`). Pure client logic →
a new/existing `docs/*.js` module + `app.js` glue. Needs a secret at play time, a runtime
write, or cross-device state → **v3, stop and read `degreesoffilm-server-move-campaign`**.

| You want to add… | Zone / where | Invariants touched | Shape |
|---|---|---|---|
| New game mode (rules variant on existing puzzle data) | `docs/game.js` option (pure) + `docs/app.js` rendering — follow the Poser precedent: `Game(puzzle,{mode})` changes scoring only; trim/MC rendering in app.js | I2, I3, I10 (decide stats policy explicitly), I13 (share text) | static-v2 |
| Movie Buff (all-TMDB title autocomplete) | Live TMDB from the browser is BANNED (key leak). Either prebaked popular-title index (static, research track) or server proxy | I1 | v3-shaped (or prebaked-static candidate) |
| New rung type / role | `curation/build_rungs.py` ordering + decoys + schema; client renders rungs generically | I4, I7 (if it carries answer text), matcher contract (`match.test.js` first) | static-v2 |
| New per-rung data field | `publish.assemble_puzzle` path; if it reveals the answer: BOTH `cipher._map_rungs` and `docs/cipher.js decodeRungs`, plus both cipher suites | I4, **I7 (both languages or it breaks)** | static-v2 |
| New player stat | `docs/stats.js` (pure `recordResult` change + test) + `app.js` render | I3, I10 (keep the guard), W2 (device-bound) | static-v2 |
| New curation step / endpoint | `curation/` module (pure core + thin CLI/endpoint per house pattern), wire into `app.py` | I1 (key stays per-request server-side), I6/I8 if it writes ledger/manifest | static-v2 |
| New image kind | `curation/images.py` writer + a new filename convention (§3.4) + puzzle schema field | I4, §3.4 naming | static-v2 |
| Change daily selection / rollover | `docs/daily.js` — but read §4 first | I5, §4 | change-control decision |
| Leaderboard, accounts, score history, cross-device anything | Requires runtime writes + validated runs | I1, W1 (client-computed depth is forgeable) | **v3 only** |
| Anything needing a secret at play time | Nowhere in v2. The key never reaches a player. | I1 | **v3 only** |
| Editing a published puzzle | Future-dated only, via the edit flow | **I12**, I8 (upsert moves the entry), I6 (ledger untouched on update) | operational |

## When NOT to use this skill

- Setting up Node/Python/venv or fixing environment breakage → `degreesoffilm-build-and-env`.
- Deciding PR-vs-direct, commit wording, landing checklists → `degreesoffilm-change-control`.
- Running the game/curation tool or publishing a puzzle end-to-end → `degreesoffilm-run-and-operate`.
- What a term means, TMDB data-model details, matcher/color/image math theory → `degreesoffilm-domain-reference`.
- Looking up or changing a constant's value → `degreesoffilm-config-and-flags`.
- A live symptom to triage → `degreesoffilm-debugging-playbook`; its history → `degreesoffilm-failure-archaeology`.
- Measuring content health / running validators → `degreesoffilm-diagnostics-and-tooling`; evidence standards → `degreesoffilm-validation-and-qa`.
- Executing the v3 move itself → `degreesoffilm-server-move-campaign`; open research problems → `degreesoffilm-research-frontier`.

## Reusing this pattern beyond this project

Transfers as a template: the three-zone "secret stays at build time, players get static
files" architecture; sentinel-prefixed idempotent obfuscation with a shared cross-language
test vector; manifest-as-sole-index with date-keyed upsert; pure-core/DOM-shell layering
enforced by an import-graph invariant; "immutable published content" + spoiler-safe commit
discipline for any daily-content game. Project-specific: TMDB, the rung/ladder schema, the
exact cipher KEY, and every constant cited here.

## Provenance and maintenance

- Written 2026-07-03 against a clean `main` (HEAD `10668ca`). Every import, schema field,
  constant, commit hash, and grep result above was verified by reading the named file or
  running the command in this repo; test counts confirmed by running the suites
  (cipher 19 JS + 22 py, game 34, match 25, daily 11, publish 36, manifest 13, ledger 12 — all green).
- Drift-prone facts and their re-verification one-liners:
  - Import graph (I2): `grep -n "^import" docs/*.js`
  - Key confinement (I1): `grep -rniE "api_key|tmdb_api_key|api\.themoviedb|image\.tmdb" docs/` → nothing
  - Cipher parity + frozen vector (I7): `node cipher.test.js && python curation/cipher.test.py`
  - Manifest/ledger uniqueness (I6/I8): the two `python -c` one-liners in §2 → `True` twice
  - Attribution (I11): `grep -c "not endorsed or certified by TMDB" docs/index.html` → `1`
  - Pool runway (W3): `python -c "import json;m=json.load(open('docs/puzzles/manifest.json'));print(max(e['date'] for e in m))"`
  - Puzzle schema (§3.1): re-read `docs/puzzles/004.json` + `curation/publish.py assemble_puzzle`
- If a code change invalidates any fact here, update this file and this date in the same
  session (see `degreesoffilm-docs-and-writing`).
