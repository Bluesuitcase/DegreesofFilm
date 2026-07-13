---
name: degreesoffilm-run-and-operate
description: >
  Operational runbook for Degrees of Film. Load this skill when you need to: run or serve
  the game locally (docs/ on a local HTTP server, the ?play/?archive/?id=N routes); start
  the curation tool (FastAPI on port 8001) or understand its UI; publish a new daily puzzle
  end-to-end ("how do I add tomorrow's puzzle"); edit or reschedule an existing puzzle;
  unschedule upcoming puzzles (Clear scheduled); check the content runway / how many days
  are stocked; know exactly which files a publish produces and how to commit/push them
  spoiler-safely; or use the headless curation CLIs (discover, build_rungs, decoys,
  credits_images, backfill, obfuscate). Publishing puzzles is this project's core recurring
  operation — this is its canonical checklist.
---

# Degrees of Film — run and operate

The project's one recurring operation is **publishing daily puzzles**. This skill covers
running the game, running the curation tool, and the publishing runbook (section 3).
Jargon (rung, ladder, tier, decoy, manifest, ledger, runway…) is defined in
`degreesoffilm-domain-reference`'s glossary; brief inline definitions appear where needed.

Two owner rules apply to everything here (rationale in `degreesoffilm-change-control`):

- **IMMUTABLE PAST** — never modify a published puzzle dated **on or before today**
  (players already played it). Edit only future-dated puzzles. The tooling will happily
  edit any id; the rule is discipline.
- **SPOILER DISCIPLINE** — commit messages are public. Content commits reference the
  puzzle **number and date only** ("Add puzzle 008 (2026-07-05)"), never the film title
  until its date has passed. Two historical commits (`bdca151`, `3d7d17e`) violated this;
  don't repeat it.

## 1. Run the game locally

The client fetches JSON, so `file://` won't work — serve `docs/` over HTTP:

```
# from the repo root (either platform; matches .claude/launch.json entry "docs")
python -m http.server 8000 --directory docs
```

Then open `http://localhost:8000/`. Routes are query-string based (verified in
`docs/app.js` `init()`):

| URL | View |
|---|---|
| `?` (nothing) | Home (title card, play buttons) |
| `?modes` | Mode select (Cinephile / Poser / Movie Buff "coming soon") |
| `?play` | Today's daily, Cinephile mode |
| `?play&mode=poser` | Today's daily, Poser (all multiple-choice, 7 rungs, flat +1) |
| `?id=N` | Replay archived puzzle N (doesn't touch daily stats) |
| `?archive` | Archive index (dates + accent swatches; **titles hidden** — by design) |
| `?practice` | Practice chooser (pick a ruleset) |
| `?practice&mode=cinephile` / `&mode=poser` | Endless practice run (random past puzzles) |

**Fresh-port rule (recurring trap):** the browser caches `docs/` JS/CSS per
`origin:port`, and `python -m http.server` serves stale ES modules happily. Only the
manifest fetch is cache-busted (`puzzles/manifest.json?d=<todayISO>` — `docs/app.js:27`).
After editing any `docs/` file, verify on a **fresh port** (e.g. 8010) or hard-reload
with cache disabled. If you're chasing a "my change didn't take" mystery, this is the
first suspect — see `degreesoffilm-debugging-playbook`.

## 2. Run the curation tool

```
# Windows (matches .claude/launch.json entry "curation"):
.venv/Scripts/python -m uvicorn app:app --app-dir curation --port 8001
# POSIX equivalent:
.venv/bin/python -m uvicorn app:app --app-dir curation --port 8001
```

Run from the **repo root** (launch.json uses the relative `.venv/Scripts/python.exe`).
Then open `http://localhost:8001/`. Requires the repo-root `.venv` (Pillow + FastAPI +
uvicorn + optional opencv-python-headless — setup in `degreesoffilm-build-and-env`) and
`curation/.env` containing the TMDB key (gitignored; never print or commit it).

**Key handling is per-request** (`_key()` in `curation/app.py`): the server starts fine
without a key. Endpoints that touch TMDB return **HTTP 500** with the missing-key message;
the rest work key-less:

| Needs the TMDB key (500 without it) | Works without a key |
|---|---|
| `GET /api/discover` | `GET /` (the crop page) |
| `GET /api/random` | `GET /api/next-date` |
| `GET /api/search?q=` | `GET /api/schedule?days=14` |
| `GET /api/film/{id}` | `GET /api/clear-schedule` (dry preview) |
| `GET /api/puzzle/{pid}` | `POST /api/clear-schedule` (LIVE-WRITE) |
| `POST /api/approve` (LIVE-WRITE) | `GET /api/autocrop?url=&scale=` |
| `POST /api/update` (LIVE-WRITE) | |

### UI tour (behavior verified against `curation/static/index.html` JS, as of 2026-07-03)

**Schedule strip (top).** Loads `/api/schedule?days=14`. Headline = the **runway**:
"**N** days of runway — stocked through <date>", or a red "0 days of runway — today has
no puzzle." Each of the next 14 days is a card:

- **Filled day** — shows the decoded film title + accent swatch; **clicking it opens that
  puzzle for editing** (`loadPuzzleForEdit(slot.id)`).
- **Empty day** (dashed border) — **clicking it targets that date**: sets the approve
  date field and marks the card "targeted ✓".
- **🗑 Clear scheduled** — see section 5.

**1 · Find a film — three ways** (all render into the same card grid except Randomize):

1. **Search** — free-text box + Search button (Enter works too) → `GET /api/search?q=`,
   all of TMDB. Films already made into puzzles carry a "used · edit #N" badge, and
   clicking them opens the **editor** for that puzzle instead of authoring a duplicate.
2. **Discover** — `GET /api/discover?sort=<dropdown>` → up to 12 *unused* films clearing
   the pool floor (vote_count ≥ 800, vote_average ≥ 6.5). Clicking a card calls
   `loadFilm(id)` and opens the crop panel.
3. **🎲 Randomize** — `GET /api/random?sort=<dropdown>` → **one** random unused film shown
   as a *preview card only*. It deliberately does **not** auto-open the editor: the card
   has "**Use this film →**" (which calls `loadFilm(f.id)` and commits) and "🎲 Randomize
   again" (re-rolls). The sort dropdown shapes which slice of the catalog the random page
   is drawn from. A 404 "couldn't find an unused film — try Randomize again" after 6
   internal retries is normal-ish; just re-roll.

**2 · Crop & review** (appears after a film loads via `loadFilm`):

- **Stills strip** — the film's TMDB backdrops (first 12) + poster. For a *new* puzzle the
  first still is auto-selected; click another to switch.
- **Crop box** — drag a rectangle on the still. That box = **reveal tier 1** (the tightest
  crop); tiers 2–3 (wider, then full frame) are derived automatically at approve. Boxes
  under 2% width/height are rejected ("Box too small — drag again").
- **✨ Auto-crop** — enabled once a still is selected. Calls
  `GET /api/autocrop?url=&scale=` which suggests a tier-1 box (face-first via OpenCV Haar
  when cv2 is installed, else edge-energy) and **draws it as the selection — nothing is
  written**; you approve it or re-drag. The **size slider** ranges **0.25–0.85**
  (step 0.05, default 0.50; smaller = tighter zoom; the server clamps to 0.2–0.9).
  Releasing the slider re-runs auto-crop if an auto box is already drawn.
- **Rungs textarea** — the drafted ladder as editable JSON: rung 1 = the film, then cast
  by **billing order** (max 6 via the tool), director floated early (after the top 2
  leads), technical crew deepest. Decoys (`decoys` arrays) and headshot helper fields
  (`profile`, `character`, `caption`) are already attached. **Edit/reorder freely** —
  this is where the human fixes edge cases (see the runbook's quality checks).
- **Credit images are automatic** — every cast/crew rung uses that person's TMDB
  headshot; there is nothing to pick (the bottom panel just says so). A person with no
  TMDB headshot holds the full frame.
- **Date field** — defaults to today, then immediately to `/api/next-date` (= the day
  after the latest manifest date, so back-to-back publishes queue instead of colliding).
  Clicking an empty schedule day overrides it.
- **Accent override** — checkbox + color picker; unchecked, the accent is sampled from
  the tier-1 crop.
- **Approve & write puzzle** — the live-write. See the runbook.

Verification tip: automated screenshot tooling **times out on this page** — assert via the
browser devtools console / computed styles instead (recorded in `project_state.md`
"Workflow / gotchas").

## 3. THE PUBLISHING RUNBOOK — add a new daily puzzle

One puzzle, end to end. Steps 1–6 are reversible; **step 7 (Approve) writes files** (still
git-reversible until committed); **step 12 (push) makes it public**.

1. **Start the tool** (section 2) and open `http://localhost:8001/`.
2. **Check the runway** in the schedule strip. Decide the target date — normally just let
   it auto-fill the next free day; click an empty day only to target a specific date.
3. **Pick a film** — Search / Discover / Randomize (section 2). Prefer widely-known films
   that clear the pool floor; the ledger already excludes everything used before.
4. **Pick a still and crop.** Choose a frame that is recognizable-but-not-instant. Hit
   ✨ Auto-crop, then judge it: the tier-1 crop must **not show the title, credits text,
   or a watermark**, and ideally not a single giveaway face of the top-billed star.
   Re-drag or resize (slider) until right. Remember tiers 2–3 widen from this box — a
   crop near the frame edge widens less interestingly.
5. **Review the rungs draft** (edit the JSON in place). Quality checks — the full content
   QA checklist lives in `degreesoffilm-validation-and-qa`:
   - Ladder order feels famous → obscure; reorder edge cases (billing order is a draft,
     not gospel). Trim bit parts / "(uncredited)" style entries you wouldn't quiz on.
   - Every rung has ≥ 1 answer; add alternate name forms/foreign titles to `answers`
     (the matcher accepts any listed form — matcher logic never special-cases names).
   - Decoys: ~3 per rung, plausible, same category, and **not accidentally correct**.
   - Prompts read sensibly ("Who played X?" — check odd character strings).
6. **Confirm the date field** (next free day unless you targeted one) and accent
   (sampled unless overridden).
7. **Approve & write puzzle** — `POST /api/approve`. **Point of no return for the working
   tree**: this writes real files (list in step 9) and appends the ledger + upserts the
   manifest. Expect "✓ wrote NNN.json (id N, accent #rrggbb) + tier images, ledger,
   manifest updated." (An earlier "accent undefined" quirk here was fixed in `e7c1f69`,
   2026-07-03 — see degreesoffilm-failure-archaeology entry 13.)
8. **Verify locally, before any commit:**
   - Run the content validator if present:
     `.venv/Scripts/python .claude/skills/degreesoffilm-diagnostics-and-tooling/scripts/validate_content.py`
     (POSIX: `.venv/bin/python …`) — from `degreesoffilm-diagnostics-and-tooling`; it
     checks manifest/puzzle/image/ledger consistency.
   - Play it: serve `docs/` on a **fresh port** and open `http://localhost:<port>/?id=N`.
     Confirm: crop renders and doesn't spoil; wrong guesses on rung 1 widen the crop
     (3 tiers); each answered credit rung shows a headshot + caption; you can finish it.
   - Sanity: `git status` should show exactly the files in step 9.
9. **Stage exactly the produced files** (N = the new id, zero-padded to 3 digits):
   ```
   git add docs/puzzles/NNN.json \
           docs/puzzles/images/NNN-1.jpg docs/puzzles/images/NNN-2.jpg docs/puzzles/images/NNN-3.jpg \
           docs/puzzles/images/NNN-r*.jpg \
           docs/puzzles/manifest.json curation/used_films.json
   ```
   That is: the puzzle JSON; three reveal tiers `NNN-{1,2,3}.jpg`; one `NNN-rK.jpg` per
   credit rung whose person has a headshot (K = 1-based rung index, so typically r2 and
   up — the film rung never has one); the manifest (upserted); the ledger (appended).
10. **Commit spoiler-safe** — the template:
    ```
    git commit -m "Add puzzle NNN (YYYY-MM-DD)"
    ```
    Number and date only. **No film title** (public repo = public spoiler).
11. **Run the offline test suites** if you touched anything beyond content (content-only
    publishes don't change code, but it's cheap insurance): `node match.test.js` etc. —
    inventory in `degreesoffilm-validation-and-qa`.
12. **Push** — `git push`. **Public point of no return**: any push to `main` touching
    `docs/` auto-deploys GitHub Pages.
13. **Confirm the deploy** (Pages can lag a minute or two):
    ```
    curl -s https://bluesuitcase.github.io/DegreesofFilm/puzzles/manifest.json
    ```
    The new entry's `date`/`id` must appear (titles are obfuscated blobs — that's
    correct). Optionally play the live `?id=N`.
14. **Sync the /match Worker's KV** (since 2026-07-11 — server matching is LIVE, so new
    puzzles need their answers in KV; the publish sink already refreshed the gitignored
    `server/answers-bulk.json`). **Easiest (since 2026-07-13): the tool's
    "⬆ Sync answers to server" button** in the schedule row (`POST /api/kv-sync` —
    reports "✓ N puzzles' answers live in KV"). Manual equivalent:
    ```
    cd server && npx wrangler kv bulk put answers-bulk.json \
      --namespace-id c6672c863072425f9b94d6b0501e2b03 --remote
    ```
    (auth: export `CLOUDFLARE_API_TOKEN`/`CLOUDFLARE_ACCOUNT_ID` from `curation/.env` first;
    the `--remote` flag is MANDATORY — wrangler 4 silently writes to a local simulator
    without it. Full Worker ops → `degreesoffilm-worker-ops`.) Not urgent same-minute —
    the client falls back to local matching for unknown puzzles — but do it before the
    puzzle's date arrives.
15. **Occasionally: rebuild the Movie Buff people index** (`curation/people_index.py
    --source credits --out docs/title..` see its docstring) — films cross the 800-vote pool
    floor over time and their crews should join autocomplete. Monthly is plenty; re-runs
    only fetch films the gitignored harvest cache hasn't seen.
16. **Update `project_state.md`** if anything notable happened (new runway number is
    usually enough to mention when it was critical). Direct-to-main is fine for that file.

## 4. Edit / reschedule an existing puzzle

**FUTURE-dated puzzles only** (IMMUTABLE PAST — the tool does not enforce this; you do).

Open the editor by clicking a **filled schedule day**, or a **"used · edit #N"** search
result. That calls `GET /api/puzzle/{pid}`: it maps the puzzle to its film via the ledger
(404 "no ledger entry" if missing), **decodes** the stored answers/captions so you edit
plaintext, re-stamps fresh headshot metadata, and loads existing date/accent. The banner
reads "Editing an existing puzzle…"; the button becomes "Update puzzle #N".

- **The frame stays as-is** unless you pick a still AND drag a new box (picking a still
  without a box blocks the update with an error).
- Edit rungs / date / accent freely; **Update** posts `POST /api/update`.

What `/api/update` **does**: rewrites `docs/puzzles/NNN.json` in place (re-encoding
answers), re-downloads and re-saves the credit headshots (`NNN-rK.jpg`), re-crops tiers +
re-samples theme **only** if a new still+box came in (accent-only override keeps the
frame), and **moves the manifest entry** — `manifest.upsert` is keyed by BOTH `id` and
`date`, so a reschedule drops the stale old-day entry cleanly.

What it does **NOT** do: touch the ledger (the film stays "used"), delete old image
files, or create a new id. Commit the changed files with the same spoiler-safe pattern,
e.g. `"Reschedule puzzle NNN to YYYY-MM-DD"`.

## 5. Clear scheduled (unschedule the upcoming queue)

Use when you want to rebuild the upcoming schedule (e.g. reorder the queue, or free films
picked in error). The **🗑 Clear scheduled** button is a **two-click arm/confirm**:

1. First click → `GET /api/clear-schedule` (dry, changes nothing) and arms the button:
   "⚠ Clear N upcoming — click again". Disarms itself after 5 seconds.
2. Second click within 5 s → `POST /api/clear-schedule`, which:
   - drops every manifest entry dated **strictly after today** (today's daily + all past
     days are kept);
   - **frees those films** — removes their ledger records, so Discover/Randomize can
     suggest them again;
   - **keeps the puzzle files and images on disk.**

Restore (both files are git-tracked — this is the designed undo):

```
git checkout -- docs/puzzles/manifest.json curation/used_films.json
```

Note the freed films' **puzzle files remain**; re-approving one of those films later mints
a **new** id (`next_id` scans existing `NNN.json` files as well as the manifest, so
orphaned files are never clobbered).

## 6. Headless / CLI alternates

All run from the repo root; swap `.venv/Scripts/python` ↔ `.venv/bin/python` per platform.
The first four **need the TMDB key** (`curation/.env`) and are **print-only — verified
against the code: none of them writes any file**. Useful for previewing a ladder without
the UI.

| Command | Prints | Writes? |
|---|---|---|
| `.venv/Scripts/python curation/discover.py [--count 8] [--sort popularity.desc] [--pages 3]` | Unused films clearing the pool floor (id, rating, votes, title). NB: CLI default sort is `popularity.desc`; the UI's is `vote_count.desc`. | No |
| `.venv/Scripts/python curation/build_rungs.py --id N [--max-cast 8] [--json]` | The draft ladder (or full puzzle-skeleton JSON with `--json`). Also takes `--title` / `--year` instead of `--id`. | No |
| `.venv/Scripts/python curation/decoys.py --id N [--max-cast 6]` | The draft ladder with each rung's ~3 decoys. | No |
| `.venv/Scripts/python curation/credits_images.py --id N [--max-cast 6]` | Each rung's caption + TMDB headshot URL (or "no TMDB headshot" note). | No |

Two **re-runnable migration CLIs DO write** — do not run casually; both are already-applied
migrations kept for re-runs:

- `curation/backfill_credit_images.py [--ids N …] [--dry-run]` — needs the key; rewrites
  puzzle files and `docs/puzzles/images/NNN-rK.jpg` headshots for existing puzzles
  (re-derives from TMDB; running twice just refreshes). `--dry-run` prints without writing.
- `curation/obfuscate_puzzles.py [--dry-run]` — no key/network; encodes any still-plaintext
  answers/captions in puzzle files + manifest titles. Idempotent (the cipher's sentinel
  prefix skips already-encoded strings).

There is **no headless publish** — approving (writing a puzzle) goes through the tool's
`POST /api/approve`; the CLIs only preview.

## 7. Operational cadence

- **Check the runway** whenever you touch the project: the schedule strip, or key-less
  `curl -s http://localhost:8001/api/schedule` (`runway` = consecutive stocked days from
  today; `publish.runway()`). As of **2026-07-04** the pool is puzzles 001–011 dated
  2026-06-28 → 2026-07-08 — a **5-day runway**. Keep curating to extend it.
- **Two traps confirmed in the 2026-07-04 batch:** (1) opening a filled TODAY/past slot in the
  editor and re-saving silently re-crops a LIVE puzzle — IMMUTABLE PAST is on you; diff `docs/`
  before staging and revert anything dated ≤ today (007 was caught and reverted this way).
  (2) Trimming rungs via `/api/update` leaves **orphaned `NNN-rK.jpg` headshots** — delete the
  unreferenced ones before staging (009 left r9–r11 orphans).
- **Keep several days stocked.** Publishing auto-queues onto the next free day, so a
  batch session (pick → crop → approve, repeat) extends the runway one day per approve.
- **When the pool runs dry, nothing crashes**: `pickPuzzle` (docs/daily.js) falls back to
  the most recent puzzle on/before today (then the earliest), so players **silently see a
  repeat** of the last puzzle. No error, no 404 — which means a dry pool is easy to miss.
  The runway number is the only warning light; check it.

## When NOT to use this skill

- Setting up the machine (Node/Python/.venv/pip installs, `.env` creation) →
  **degreesoffilm-build-and-env**.
- How a change should land (PR vs direct-to-main, gates, sign-offs, rollback) →
  **degreesoffilm-change-control**.
- Running/adding tests, the content QA checklist in depth, the evidence bar →
  **degreesoffilm-validation-and-qa**.
- Measuring content health (validator/report scripts and their interpretation) →
  **degreesoffilm-diagnostics-and-tooling**.
- Something is broken and you're triaging symptoms → **degreesoffilm-debugging-playbook**.
- What a rung/tier/decoy/manifest/ledger *is*, TMDB data model, matcher theory →
  **degreesoffilm-domain-reference**.
- Which invariants a change must not break → **degreesoffilm-architecture-contract**.
- Config values and where they live (ports, floors, slider ranges as constants) →
  **degreesoffilm-config-and-flags**.

## Reusing this pattern beyond this project

The transferable template: for any content-pipeline project, write ONE numbered
publish runbook with (a) the exact artifact list a publish produces, (b) a marked
point-of-no-return, (c) a verify-before-push step on a cache-proof origin, (d) a
public-safe commit-message template, and (e) a "what users see when content runs out"
answer. The specifics here — TMDB, FastAPI endpoints, tier/headshot filenames, the
spoiler rule — are project-specific.

## Provenance and maintenance

- Written 2026-07-03. Every endpoint, parameter, filename, UI behavior, and route was
  verified by reading `curation/app.py`, `curation/static/index.html` (its JS),
  `curation/{publish,manifest,ledger,discover,build_rungs,decoys,credits_images}.py`,
  `curation/{backfill_credit_images,obfuscate_puzzles}.py`, `docs/app.js` `init()`,
  `docs/daily.js`, `.claude/launch.json`, and `docs/puzzles/` contents. No live-write
  endpoint or server was run.
- Volatile facts: puzzle pool/runway numbers (dated above).
- Re-verify one-liners:
  - Endpoints: `grep -n "@app\." curation/app.py`
  - Routes: `grep -n "params.has" docs/app.js`
  - Slider range: `grep -n "cropscale" curation/static/index.html`
  - Runway/pool: `python -c "import json;m=json.load(open('docs/puzzles/manifest.json'));print(m[0]['date'],m[-1]['date'],len(m))"`
  - Launch entries: `cat .claude/launch.json`
