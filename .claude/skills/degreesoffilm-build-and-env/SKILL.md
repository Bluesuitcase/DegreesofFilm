---
name: degreesoffilm-build-and-env
description: >
  Set up, verify, and repair the Degrees of Film development environment.
  Use when: setting up a fresh clone or a new machine; the repo-root .venv is missing or broken;
  pip install trouble (especially opencv-python-headless pulling 5.x, or "ModuleNotFoundError:
  No module named 'PIL'/'fastapi'/'cv2'"); "the tests won't run"; questions about required tool
  versions (git/Node/Python/pip packages); creating curation/.env / TMDB_API_KEY setup; or
  deciding whether a requirements.txt pin can be bumped. Covers prerequisites, the from-scratch
  setup runbook with the full offline test gauntlet, the environment-artifact map
  (.venv, curation/.env, .claude/launch.json, SessionStart hook, package.json, docs/.nojekyll),
  known environment traps, and dependency-upgrade guidance. NOT for day-to-day operation or
  curating puzzles (degreesoffilm-run-and-operate) or runtime bugs
  (degreesoffilm-debugging-playbook).
---

# Degrees of Film — Build & Environment

Everything needed to go from `git clone` to a fully verified dev environment, and to fix that
environment when it breaks. All facts below marked **[verified]** were checked on the reference
machine (Windows 11, repo at commit `10668ca`) on **2026-07-02**; facts marked **[expectation]**
are reasonable portability claims that were *not* tested here.

Jargon, once: **"the venv"** = the Python virtual environment at the **repo root**, `.venv/`
(gitignored). **"the curation tool"** = the private FastAPI app in `curation/` that holds the
TMDB API key and authors puzzles. **"the game"** = the static site in `docs/` (vanilla ES
modules, zero build step). **TMDB** = themoviedb.org, the film-data API.

Dual command forms are given where platforms diverge:

| | Windows (PowerShell / Git Bash) | macOS / Linux |
|---|---|---|
| venv Python | `.venv/Scripts/python` | `.venv/bin/python` |
| system Python | `python` | `python3` (if `python` isn't on PATH) |

Forward-slash repo-relative paths work in PowerShell too — every command here is copy-pasteable
from the repo root on either platform (swap the venv path per the table).

## 1. Prerequisites

No npm install, ever — the game client has **zero npm dependencies** [verified: `package.json`
is exactly `{ "type": "module" }`; no scripts, no lockfile, no `node_modules`].

| Tool | Verified here (2026-07-02) | Floor | Why needed |
|---|---|---|---|
| git | 2.50.1.windows.1 | any modern git [expectation] | clone; ledger/manifest are git-tracked and git-reversible |
| Node.js | v24.17.0 | ≥ 18 should work [expectation — ES modules only, no deps, no `fetch` in tests] | run the 7 repo-root `*.test.js` suites, which `import` the `docs/` ES modules |
| Python | 3.14.6 (system **and** venv) | any version pip can resolve all four pins for; ~3.10–3.14 [expectation — only 3.14.6 tested] | pure curation tests (stdlib only) run on system Python; the venv runs the curation tool |
| pip + venv module | pip 26.1.2 in the venv | ships with Python [expectation] | install `curation/requirements.txt` into `.venv` |
| gh CLI | 2.95.0 | optional | PR/GitHub operations only; not needed to build or test |

Pinned packages, from `curation/requirements.txt` [verified — the file's header comments also
document the venv setup commands and cv2 optionality]:

| Package | Pin | Installed here | Pin rationale |
|---|---|---|---|
| pillow | `>=10,<12` | 11.3.0 | image cropping/sampling (`curation/images.py`) |
| fastapi | `>=0.110` | 0.138.2 | the curation tool server (`curation/app.py`) |
| uvicorn | `>=0.29` | 0.49.0 | serves the curation tool |
| opencv-python-headless | `>=4.9,<5` | 4.13.0.92 | **`<5` is load-bearing** — see Traps §4.1. cv2 is *optional at runtime* |

## 2. From-scratch setup runbook

Steps 1–5 need **no TMDB key**. Only step 6 (the key) unlocks the curation tool's
TMDB-touching endpoints and the four TMDB-hitting CLI modules (`curation/discover.py`,
`build_rungs.py`, `decoys.py`, `credits_images.py`, plus `backfill_credit_images.py`).

**Step 1 — clone and enter** (remote URL [verified] via `git remote -v`):

```
git clone https://github.com/Bluesuitcase/DegreesofFilm.git
cd DegreesofFilm
```

**Step 2 — create the venv at the repo root** (the location matters: `.claude/launch.json` and
all documented commands assume `.venv/` at the root):

```
python -m venv .venv          # Windows
python3 -m venv .venv         # macOS/Linux
```

**Step 3 — install curation deps into the venv** (always via the venv's own interpreter, never
bare `pip` — see Traps §4.2):

```
.venv/Scripts/python -m pip install -r curation/requirements.txt    # Windows
.venv/bin/python -m pip install -r curation/requirements.txt        # macOS/Linux
```

**Step 4 — verification gauntlet (all offline; no key, no network).** Every suite prints
PASS/FAIL lines, ends with `N passed, 0 failed`, and exits non-zero on any failure.
Expected: **all suites green** [verified here 2026-07-02]; canonical per-suite counts live
in **degreesoffilm-validation-and-qa** §2 — a count LOWER than it states is a red flag.

JS (repo root; Node): match · game · daily · theme · stats · frame · cipher.

```powershell
# PowerShell
foreach ($t in 'match','game','daily','theme','stats','frame','cipher') { node "$t.test.js" }
```
```bash
# bash/zsh
for t in match game daily theme stats frame cipher; do node "$t.test.js" || exit 1; done
```

Python pure suites (stdlib only — **system Python or the venv both work** [verified: all 8 pass
with system Python 3.14.6 that has *none* of the pip packages installed]): build_rungs ·
ledger · discover · decoys · manifest · publish · credits_images · cipher.

```powershell
# PowerShell
foreach ($t in 'build_rungs','ledger','discover','decoys','manifest','publish','credits_images','cipher') { python "curation/$t.test.py" }
```
```bash
# bash/zsh  (use python3 if needed)
for t in build_rungs ledger discover decoys manifest publish credits_images cipher; do python curation/$t.test.py || exit 1; done
```

Images suite (**needs the venv** — Pillow; cv2 optional, suite passes without it):

```
.venv/Scripts/python curation/images.test.py     # Windows
.venv/bin/python curation/images.test.py         # macOS/Linux
```

If all three blocks are green, the environment is good. Any red: see Traps (§4) first.

**Step 5 — serve and load the game** (no key needed). `file://` will **not** work — the client
`fetch()`es `puzzles/manifest.json` and puzzle JSON, so it must be served over HTTP:

```
python -m http.server 8000 --directory docs      # from the repo root (both platforms)
```

Open `http://localhost:8000`. Success = the dark home screen renders and `?play` loads a puzzle
image with a guess box (watch devtools: `manifest.json` then `NNN.json` fetches, no console
errors). Views: `?` home · `?play` today · `?play&mode=poser` · `?practice` · `?archive` · `?id=N`.

**Step 6 — TMDB key + curation tool** (the only step needing a key):

1. Get a free **v3 API key**: TMDB account → Settings → API → "API Key (v3 auth)"
   [expectation — external site flow].
2. Create `curation/.env` (gitignored [verified: `.gitignore` line 151 `.env` — confirmed via
   `git check-ignore -v curation/.env`]) containing one line:
   `TMDB_API_KEY=<your v3 key>`
   The key name and load order are set by `curation/tmdb.py` `load_key()` [verified]: it reads
   `curation/.env` first, then the process environment. If the key is unset **or still the
   placeholder `PASTE_YOUR_KEY_HERE`**, it raises SystemExit with the message
   "TMDB_API_KEY not set — put your key in curation/.env". Never commit, print, or paste the
   key; `tmdb.py` deliberately never logs request URLs (they carry the key).
3. Start the tool:

```
.venv/Scripts/python -m uvicorn app:app --app-dir curation --port 8001    # Windows
.venv/bin/python -m uvicorn app:app --app-dir curation --port 8001       # macOS/Linux
```

Open `http://localhost:8001`. Success = the crop UI with the 14-day week-ahead schedule strip
at the top. **The server starts fine without a key** [verified: `app.py` `_key()` loads the key
per-request, lines 39–43] — key-less, the page and the key-free endpoints (`/`, `/api/next-date`,
`/api/schedule`, `/api/clear-schedule`, `/api/autocrop` [verified: none call `_key()`]) work, and
each TMDB-touching endpoint (`/api/discover`, `/api/random`, `/api/search`, `/api/film/{id}`,
`/api/puzzle/{pid}`, `/api/approve`, `/api/update`) returns a helpful **HTTP 500** carrying the
`load_key` message. A wrong key surfaces as "HTTP 401 (check your TMDB_API_KEY)".

## 3. Environment map

| Artifact | Git status | What it is / why it exists |
|---|---|---|
| `.venv/` (repo root) | ignored (`.gitignore:153`) [verified] | The Python env for curation. Pillow + FastAPI + uvicorn + cv2 live here and only here. |
| `curation/.env` | ignored (`.gitignore:151` `.env`) [verified] | One line: `TMDB_API_KEY=<v3 key>`. Read by `tmdb.load_key()`. The whole architecture exists so this never reaches a player. |
| `.claude/launch.json` | tracked | Dev-server registry. Entry `"docs"`: `python -m http.server 8000 --directory docs` (port 8000). Entry `"curation"`: `.venv/Scripts/python.exe -m uvicorn app:app --app-dir curation --port 8001` (port 8001). **Note:** the curation entry hardcodes the Windows venv path; on macOS/Linux run the command by hand with `.venv/bin/python` (don't commit a platform edit). |
| `.claude/settings.json` | tracked | A `SessionStart` hook (a `node -e` one-liner) that injects `project_state.md` into every AI session as extra context [verified]. This is why fresh sessions "already know" the project state — it isn't magic, it's this hook. |
| `.claude/settings.local.json` | ignored (`.gitignore:221`) | Machine-local Claude Code settings. |
| `package.json` | tracked | Exactly `{ "type": "module" }` [verified]. Exists *solely* so the repo-root `*.test.js` files can `import` the ES modules under `docs/`. No deps, no `npm test`, no lockfile, no build step. |
| `docs/.nojekyll` | tracked [verified: exists] | Tells GitHub Pages to skip its default Jekyll build and serve `docs/` as raw static files [expectation — standard Pages behavior; not documented in-repo]. Don't delete it. |
| `curation/used_films.json` | **tracked** (deliberately) | The used-films ledger. Runtime data, but version-controlled so usage history can't silently corrupt and destructive ops are `git checkout`-reversible. Never hand-edit; never let a test write it. |

## 4. Known traps (symptom → cause → fix)

**4.1 — Auto-crop face detection breaks after a dependency refresh.**
*Symptom:* auto-crop stops finding faces / cv2 import or cascade errors after reinstalling deps.
*Cause:* an unpinned install resolved **OpenCV 5.x**, which **dropped the bundled Haar
cascades** (5.0 ships only the DNN `FaceDetectorYN`, which needs a separately downloaded model
file). *Fix:* keep the `opencv-python-headless>=4.9,<5` pin; 4.13.0.92 has a Python-3.14 wheel
and keeps the classic cascade [verified installed + rationale documented in
`project_state.md` and the `requirements.txt` header]. Remember cv2 is **optional**:
`images.detect_faces` returns `[]` without it, auto-crop degrades to the edge-energy path, and
the whole test suite passes with no cv2 at all — so "uninstall cv2" is a legitimate stopgap.

**4.2 — `ModuleNotFoundError: No module named 'PIL'` (or `fastapi`, `cv2`).**
*Symptom:* exactly that, from `images.test.py` or uvicorn; exit 1 [verified: this is precisely
what system Python produces here]. *Cause:* deps were installed with system `pip`, or you ran
with system Python instead of the venv. *Fix:* install with the venv's own interpreter
(`.venv/Scripts/python -m pip install -r curation/requirements.txt` / `.venv/bin/python …`) and
run with that same interpreter. Rule of thumb: **pure suites → either Python; anything touching
images or the server → the venv** [both directions verified].

**4.3 — Edited `docs/` JS or CSS but the browser shows old behavior.**
*Cause:* `python -m http.server` + the browser cache serve **stale ES modules**, keyed per
origin:port [documented in `project_state.md` "Dev cache gotcha"]. *Fix:* hard-reload with
devtools cache disabled, cache-bust the `import`/`<link>`, or serve on a fresh port. Never
conclude "my change did nothing" until you've done one of these.

**4.4 — Blank page / fetch errors opening `docs/index.html` directly.**
*Cause:* `file://` blocks the client's `fetch()` of manifest/puzzle JSON. *Fix:* always serve
over HTTP (step 5).

**4.5 — "Address already in use" on 8000/8001** (`WinError 10048` / `EADDRINUSE`).
*Cause:* a previous server instance is still running. *Fix:* stop it, or start on another port
(`--port 8002`, or change the http.server port argument). Changing ports has the side benefit
of dodging trap 4.3.

**4.6 — `.venv/Scripts/python: No such file or directory` (or the reverse).**
*Cause:* Windows venvs use `Scripts/`, POSIX venvs use `bin/`. *Fix:* use the table at the top.
A venv created on one OS is not portable to the other — recreate it, don't copy it.

**4.7 — Curation endpoints return 500 "TMDB_API_KEY not set…" (or 401).**
*Cause/fix:* see step 6. 500 with that message = `.env` missing or still the
`PASTE_YOUR_KEY_HERE` placeholder; 401 = key present but wrong.

**4.8 — `gh` says you're logged out.**
gh 2.95.0 is installed here [verified] and normally works directly. If `gh auth status` shows
logged-out, the documented fallback is to feed gh the token Git Credential Manager already
holds, for that one invocation: pipe `protocol=https` + `host=github.com` (plus a blank line)
into `git credential fill`, take the `password=` line's value, and set it as `GH_TOKEN` in the
environment of the single `gh` command. Never echo, log, or persist the token.

## 5. Upgrade guidance (bumping a pin safely)

1. **Stay inside the pin's rationale** (see the table in §1 and the `requirements.txt` header
   comments — the pins are documented *reasons*, not habits). Edit `curation/requirements.txt`,
   then reinstall: `.venv/Scripts/python -m pip install -r curation/requirements.txt --upgrade`
   (POSIX: `.venv/bin/python …`).
2. **Regression gauntlet:** rerun `images.test.py` (expect 32) plus the 8 pure Python suites
   (§2 step 4). For Pillow or OpenCV changes, follow with a *live* auto-crop sanity check —
   start the curation tool per **degreesoffilm-run-and-operate**, run Auto-crop on a still with
   an obvious face, and confirm the suggested box is face-centered, not just edge-energy.
3. **fastapi / uvicorn** are floor-only pins; routine bumps are fine — reinstall, rerun the
   gauntlet, smoke-test the tool UI.
4. **pillow `<12`**: widening past 12 needs the images gauntlet green plus a visual crop check;
   also confirm a wheel exists for your Python version before editing the pin.
5. **opencv `>=5` is NOT a routine bump.** OpenCV 5 removed the Haar cascades this project's
   face detection uses; moving means a deliberate migration to `FaceDetectorYN` including a
   model-file download/versioning story. Route that work through
   **degreesoffilm-research-frontier** — do not just widen the pin to "fix" an install error.
6. **Interpreter upgrades:** JS side is dependency-free — just rerun the 7 Node suites on the
   new Node. A Python upgrade means recreating the venv (delete `.venv/`, `python -m venv
   .venv`, reinstall) — venvs don't survive interpreter upgrades [expectation — standard venv
   behavior], and check pip can resolve all four pins on the new version first.

## 6. When NOT to use this skill

- **Running the servers day-to-day, curating puzzles, deploying to Pages** →
  `degreesoffilm-run-and-operate` (this skill only gets you to a verified environment).
- **Making/landing code changes, branch-vs-direct-commit policy** → `degreesoffilm-change-control`.
- **Something is broken at runtime and the environment checks out** → `degreesoffilm-debugging-playbook`
  (past incidents: `degreesoffilm-failure-archaeology`).
- **What the layers/zones are allowed to depend on** → `degreesoffilm-architecture-contract`.
- **Game rules, matcher semantics, puzzle schema meaning** → `degreesoffilm-domain-reference`.
- **Tunable constants, query-string modes, feature flags** → `degreesoffilm-config-and-flags`.
- **What to test before shipping / QA gates** → `degreesoffilm-validation-and-qa`
  (tooling for diagnosis: `degreesoffilm-diagnostics-and-tooling`).
- **OpenCV-5/FaceDetectorYN migration or other open research** → `degreesoffilm-research-frontier`
  (method: `degreesoffilm-research-methodology`; analysis instruments:
  `degreesoffilm-proof-and-analysis-toolkit`).
- **v3 backend work** → `degreesoffilm-server-move-campaign`. Docs/copy →
  `degreesoffilm-docs-and-writing`; public positioning → `degreesoffilm-external-positioning`.

## 7. Reusing this pattern beyond this project

The reusable shape: (a) a zero-dependency static client whose only `package.json` line is
`{"type":"module"}`, letting plain-Node test files import the shipped ES modules directly — no
framework, no build; (b) a private Python venv whose `requirements.txt` carries the *reason* for
each pin as a header comment, so future bumps are informed, not blind; (c) secrets in a
module-local gitignored `.env` read by a tiny loader that hard-fails on placeholders and never
logs URLs; (d) `.claude/launch.json` + a SessionStart hook as executable, self-updating docs.

## 8. Provenance and maintenance

Authored **2026-07-02** against commit `10668ca` on Windows 11 (PowerShell 7); every command in
§2 was executed and every count/version above matches observed output on that date. Volatile
facts (versions, test counts, endpoint list, remote URL) will drift — re-verify before trusting:

- Versions: `git --version && node --version && python --version && .venv/Scripts/python --version` (POSIX: `.venv/bin/python`).
- Packages: `.venv/Scripts/python -m pip list` (POSIX: `.venv/bin/python -m pip list`) vs `curation/requirements.txt`.
- Suites + counts: rerun §2 step 4 (three blocks, expect 137 / 138 / 32).
- Key-free vs key-needing endpoints: `grep -n "_key()" curation/app.py` vs the `@app.get/post` routes.
- Env artifacts: `git check-ignore -v curation/.env .venv` and re-read `.claude/launch.json` + `.claude/settings.json`.

When a fact here goes stale (e.g. the opencv pin is finally migrated, or Python/Node major
bumps), update this file in the same change — this skill is only useful while it is true.
