---
name: degreesoffilm-change-control
description: >
  How changes to Degrees of Film are classified, gated, and landed. Use BEFORE committing,
  pushing, or merging ANYTHING in this repo; when deciding branch-vs-direct-to-main; before
  touching anything under docs/ (it deploys straight to live players); before editing or
  deleting any published puzzle; before landing puzzle content (the spoiler-safe commit gate
  — writing conventions themselves live in degreesoffilm-docs-and-writing); when asked
  "can I just push this?", "can I fix yesterday's puzzle?",
  "can I improve the ladder order / matcher / scoring?"; before running destructive curation
  endpoints; and when a bad push to main needs rolling back. Covers the change classification
  table, the project's non-negotiable rules with their incident history, landing checklists,
  commit/PR conventions, the owner-sign-off list, and rollback. NOT for the mechanics of
  publishing a puzzle (degreesoffilm-run-and-operate) or environment setup
  (degreesoffilm-build-and-env).
---

# Degrees of Film — Change Control

How work lands in this repo without breaking the live game, spoiling players, or re-fighting
settled battles. Facts below were verified against the repo on **2026-07-03** (HEAD `10668ca`,
clean tree, no open PRs); volatile ones are date-stamped.

**The two facts that drive everything:**

1. **`docs/` IS production.** GitHub Pages serves `main` `/docs` at
   https://bluesuitcase.github.io/DegreesofFilm/. Any push to `main` that touches `docs/`
   auto-deploys to real players in ~30s–3min. There is no staging environment.
2. **There is NO CI.** Nothing runs tests for you. The test suites are a manual gate that
   YOU run before every push. A push with red tests ships broken code to players.

Jargon, once: **puzzle** = one day's game (`docs/puzzles/NNN.json` + its images).
**manifest** = `docs/puzzles/manifest.json`, the date→puzzle daily index the client reads.
**ledger** = `curation/used_films.json`, the never-repeat-a-film record. **rebase-merge** =
GitHub's "Rebase and merge" button: PR commits are replayed onto `main` with no merge commit
(this repo's history is fully linear — `git log --merges` is empty, verified 2026-07-03).
**Owner** = the human running this project; they confirm the landing mode for each change.

---

## 1. Change classification table

Classify every change FIRST. When a change spans rows, the strictest row wins.

| Change type | Example paths | Deploys to live players? | Landing path | Required tests BEFORE landing | Verification AFTER landing |
|---|---|---|---|---|---|
| **Player-facing code** | `docs/*.js`, `docs/style.css`, `docs/index.html` | **YES** | Branch → PR → rebase-merge (historical default); owner has also chosen direct-to-main late in v2 — **ask per change** | All 7 JS suites green + manual browser check on a **fresh port** | Confirm Pages redeploy (§3a step 9) + play the live site |
| **Game rules / matcher** | `docs/game.js`, `docs/match.js` | **YES** | Same as above, **plus owner sign-off** (§5) | **Test-first**: add the failing case to `match.test.js`/`game.test.js` BEFORE changing the algorithm, then all 7 JS suites | Same as above + replay a real puzzle end-to-end |
| **Content publish** (new puzzle) | `docs/puzzles/*` via the curation tool's Approve | **YES** | Direct commit to `main` (established precedent: `772f4f7`, `bdca151`, `3d7d17e`) | Content validation (see gates in §3c); workflow lives in degreesoffilm-run-and-operate | Confirm Pages redeploy; load `?id=N` on the live site without spoiling yourself |
| **Content edit** | Re-crop / reorder / reschedule an existing puzzle | **YES** | Direct to `main`, **future-dated puzzles ONLY** (non-negotiable §2.1) | Same content gates; use the tool's edit flow (`/api/update`) | Same as content publish |
| **Curation-only code** | `curation/*` with **zero `docs/` diff** | No (Pages rebuilds but output is byte-identical) | Direct to `main` per owner's repeated per-change choice (e.g. `afec469`, `7957b19`, `125c4a5`, `3e2cfbb`) — still confirm | The 8 pure Python suites + `images.test.py` if touching image code | `git status` clean; re-run the tool locally if endpoints changed |
| **Docs-of-record** | `project_state.md`, `CLAUDE.md`, `DESIGN.md` | No | Direct to `main`; `project_state.md` explicitly needs **no PR** (stated in the file itself) | None (but don't let docs contradict code) | Spot-read the rendered file |
| **Meta** | `.claude/` (skills, settings, launch.json) | No | Direct to `main`; owner confirms | None mandatory; run any shipped scripts once | — |

Verify the "no deploy" claim for a mixed diff before trusting it:
```
git diff --stat main origin/main -- docs/    # or: git show --stat HEAD -- docs/
```
If that prints anything, the change is player-facing. Full test commands are in §3.

---

## 2. The non-negotiables

Each rule exists because something happened. Do not relitigate them without owner sign-off.

### 2.1 IMMUTABLE PAST — never modify a published puzzle dated ≤ today
- **Rule:** Puzzles whose manifest date is today or earlier are frozen — no re-crops, no
  answer fixes, no reschedules, no deletions. Edits are for **future-dated** puzzles only.
  (As of 2026-07-03 only puzzle 007, dated 2026-07-04, is editable.)
- **Rationale:** Players already played it; their streaks, stats, and share cards reference
  it. Changing it invalidates real people's results. The archive (`?id=N`) replays old files
  forever, so a "fix" also silently rewrites history for archive players.
- **The trap:** The edit tooling does NOT enforce this — `/api/puzzle/{id}` + `/api/update`
  will happily rewrite any id. The rule is discipline, not code.

### 2.2 SPOILER DISCIPLINE — commit messages are public
- **Rule:** Nothing public may leak an answer before its date: content commits reference
  puzzle **number and date only** — `Add puzzle NNN (YYYY-MM-DD)` — never the film title
  until the date has passed. Same for PR titles/bodies and doc edits.
- **Incident:** Two historical commits violated this: `bdca151` named puzzle 006's film in
  its subject, and `3d7d17e` named puzzle 007's film before its date — the repo is public, so
  anyone reading the log had those answers early. History was deliberately NOT rewritten
  (rewriting shared `main` is worse); the convention was adopted instead. Cite these as the
  lesson, don't repeat them.

### 2.3 KEY CONFINEMENT — the TMDB key never reaches a player
- **Rule:** The key lives only in gitignored `curation/.env`. Nothing under `docs/` may
  contain it, fetch TMDB directly, or embed anything derived from a live key call at runtime.
- **Rationale:** The entire three-zone architecture (CLAUDE.md) exists to guarantee this.
  It's why Movie Buff mode is deferred to v3 — browser autocomplete against TMDB would leak
  the key. Check before pushing: `git grep -i tmdb_api_key -- docs/` must return nothing.

### 2.4 TESTS GREEN BEFORE PUSH — because there is no CI
- **Rule:** Run the suites relevant to your diff (see §3) and get zero failures before every
  push. A new behavior needs a new test that was red before your change and green after.
- **Rationale:** No CI means the manual gate is the only gate. Suites verified green
  2026-07-03 (match 25, game 34, publish 36 — spot-checked by running them).

### 2.5 LAYERING LAW — rules never touch the DOM
- **Rule:** `docs/match.js` imports nothing; `docs/game.js` imports only `match.js`;
  `docs/app.js` does ALL DOM work. `daily/theme/stats/frame/cipher.js` stay pure.
- **Rationale:** The Node test suites import these modules directly; DOM leakage breaks the
  entire manual test gate (CLAUDE.md "Layering, keep it clean").

### 2.6 MATCHER TEST-FIRST — the contract precedes the algorithm
- **Rule:** Add the new case to `match.test.js` BEFORE touching `docs/match.js` (CLAUDE.md:
  "Add a case there before touching the algorithm"). The test table IS the fairness spec.
- **Rationale:** The matcher decides whether the game feels fair; a regression here rejects
  a correct guess from a live player with no error anywhere.

### 2.7 NEVER REPEAT A FILM — the ledger is authoritative
- **Rule:** Every published film is recorded in `curation/used_films.json`; Discover and
  Randomize exclude it. Don't hand-author a puzzle that bypasses the ledger, and don't
  remove ledger entries except via the tool's Clear-scheduled flow (which only frees
  strictly-future, unpublished-in-spirit films — commit `c0329a2`).

### 2.8 ATTRIBUTION IS MANDATORY — the TMDB footer never comes off
- **Rule:** `docs/index.html` ships "This product uses the TMDB API but is not endorsed or
  certified by TMDB." (verified line 139). DESIGN §5 treated it as a ship-blocker; it landed
  as `c2f59c3`. No redesign, refactor, or copy pass may drop it.

### 2.9 ONE PUZZLE PER DAY — publishes go through the tool
- **Rule:** One manifest entry per date. Publish via the curation tool, which auto-assigns
  the next free day (`publish.next_date`).
- **Incident:** On 2026-06-30, multiple same-day publishes collided — `manifest.upsert`
  replaces by date, so puzzles 003/004 were silently orphaned (files on disk, no manifest
  entry). Recovered in `772f4f7` ("Add curated puzzles 004/005 + recover the manifest");
  prevented structurally by `257bcff` (next-free-date auto-assign). Hand-editing the
  manifest reopens this footgun.

### 2.10 STATS ISOLATION — only the real daily touches streaks
- **Rule:** Archived (`?id=N`), Poser, and Practice runs must never write daily stats or
  streaks (guards live in `docs/app.js`). Any new mode inherits this rule by default.
- **Rationale:** The streak is the retention mechanic; polluting it from replays makes it
  meaningless and unfixable (localStorage-only — there's no server copy to repair).

### 2.11 LIVE-WRITE ENDPOINTS ONLY WITH A RESTORE PLAN
- **Rule:** `/api/approve`, `/api/update`, and POST `/api/clear-schedule` write the real
  `docs/puzzles/` + manifest + ledger. Never point a test of them at committed content, and
  never invoke them without this restore command ready:
  ```
  git checkout -- docs/puzzles/manifest.json curation/used_films.json
  ```
- **Incident:** A live-write reschedule test moved committed puzzle 004 and needed a
  surgical restore (recorded account in `project_state.md` "Workflow / gotchas").

### 2.12 SETTLED DESIGN DECISIONS — don't "improve" them casually
- **Ladder order:** cast by TMDB **billing order**, popularity only a tiebreaker. A
  popularity sort was tried and REJECTED after de-risk `45b4085`
  (`curation/validate_ladder.py`): rolling popularity buried Heath Ledger's Joker at
  rung 13. Don't re-sort the ladder by popularity.
- **Credit images:** ALL cast+crew rungs use automatic TMDB headshots. A manual
  character-stills picker was built (PRs #12/#13), then REMOVED in `3e2cfbb` — TMDB tagged
  images proved too sparse (mostly generic backdrops). Don't rebuild it.

---

## 3. Landing checklists

### 3a. Player-facing change (anything diffing `docs/`)

1. Confirm the landing mode with the owner (PR is the historical default for player-facing
   work — all 18 PRs; late-v2 the owner chose direct-to-main even for player-facing commits
   like `811ee40`/`314b98f`/`8be6434`, so ask, don't assume).
2. Branch, kebab-case and feature-scoped (real examples from `gh pr list`:
   `week-ahead-schedule`, `ux-skip-tooltip`, `v2-poser`, `phase-3-daily`):
   ```
   git checkout -b my-feature-name
   ```
3. Make the change. If it alters rules/matcher behavior: write the failing test FIRST (§2.6).
4. Run the full JS gauntlet from the repo root — all must print `0 failed`:
   ```
   node match.test.js && node game.test.js && node daily.test.js && node theme.test.js && node stats.test.js && node frame.test.js && node cipher.test.js
   ```
5. Verify in a browser on a **fresh port** (the browser caches modules per origin:port —
   a recurring trap): `python -m http.server 8123 --directory docs` then open
   `http://localhost:8123/?play`.
6. Commit using the conventions in §4; push the branch; open the PR:
   ```
   gh pr create --title "Area: imperative summary" --body "..."
   ```
   (body format: degreesoffilm-docs-and-writing §4; no film-title spoilers anywhere in it).
7. Rebase-merge and delete the branch (every one of the 18 merged PRs did both):
   ```
   gh pr merge <n> --rebase --delete-branch
   ```
8. Do NOT stack a second PR on this branch while it's open — see the stacked-PR warning, §4.
9. Confirm the Pages redeploy (both verified working 2026-07-03):
   ```
   gh run list --limit 1        # expect "pages build and deployment ... success" (~30s-3min)
   gh api repos/Bluesuitcase/DegreesofFilm/pages --jq .status   # expect "built"
   ```
10. Hard-reload https://bluesuitcase.github.io/DegreesofFilm/ and verify the change live.
    Note: the client cache-busts only the **manifest** (`?d=<date>`); changed JS/CSS may need
    a hard reload (Ctrl+F5) to appear.

### 3b. Curation-only change (no `docs/` diff)

1. Confirm `git diff --stat -- docs/` is empty — otherwise use §3a.
2. Confirm the landing mode with the owner (precedent is direct-to-main: `afec469`,
   `7957b19`, `4496c81`, `125c4a5`, `c0329a2`, `388e645`, `3e2cfbb` all landed without PRs).
3. Run the Python suites (pure ones run with any Python; images needs the venv):
   ```
   python curation/build_rungs.test.py && python curation/ledger.test.py && python curation/discover.test.py && python curation/decoys.test.py && python curation/manifest.test.py && python curation/publish.test.py && python curation/credits_images.test.py && python curation/cipher.test.py
   .venv/Scripts/python curation/images.test.py
   ```
   (macOS/Linux: `.venv/bin/python`.) If you touched `cipher.py`, ALSO run
   `node cipher.test.js` — the two languages share a fixed parity vector.
4. Commit direct to `main` ("Curation: …" area tag) and push. No deploy follows (Pages
   rebuilds but `docs/` output is byte-identical).

### 3c. Content publish (new puzzle) — gates only; workflow in degreesoffilm-run-and-operate

The full click-by-click runbook belongs to **degreesoffilm-run-and-operate**. The
change-control gates that apply regardless:

1. Publish through the curation tool's Approve (never hand-edit the manifest — §2.9).
2. Before pushing, validate the content: puzzle JSON parses, images exist, the crop doesn't
   show the title, decoys aren't accidentally correct, and play it once locally via
   `?id=N` on a fresh port.
3. **Spoiler-safe commit message** (§2.2): `Add puzzle NNN (YYYY-MM-DD)` — number and date,
   never the title.
4. Direct commit to `main`, push, then confirm the Pages deploy (§3a step 9). The push is
   the point of no return: the puzzle is live (or scheduled) for real players.

### 3d. Docs-of-record update

1. `project_state.md`: edit in place on `main`, commit direct, no PR (the file says so
   itself). Keep it updated as part of finishing any substantive session.
2. `CLAUDE.md` / `DESIGN.md`: direct to `main` with a `Docs:` commit. Remember precedence:
   DESIGN.md is the spec and wins conflicts — don't let CLAUDE.md drift contradictory.
3. No spoilers in docs either: docs of record are in a public repo.

---

## 4. Commit and PR conventions

**Commit format:** `Area: imperative summary`. Area-prefix conventions, real examples, and
PR body structure: **degreesoffilm-docs-and-writing §4**. This section keeps only the gates.

**Spoiler-safe content-commit template** (the ONLY acceptable shape until the date passes):
```
Add puzzle NNN (YYYY-MM-DD)
```

**Rebase-merge, always.** All 18 PRs were rebase-merged and their branches deleted; `main`
has zero merge commits (verified: `git log --merges` is empty). This keeps history linear so
`git revert` and `git bisect` stay trivial — don't introduce merge commits or squash (squash
would break the one-commit-per-logical-change granularity the log shows).

**Stacked-PR warning.** PR #13 was stacked on #12 (its own body says so); after #12
rebase-merged, the stacked branch needed a rebase-and-force-push dance before #13 was clean
(recorded account — the PR body documents the stacking; the dance is from project history).
Known cost: **prefer sequential PRs** — land one, then branch the next from fresh `main`.

**Reveal-mechanic branch history:** see degreesoffilm-failure-archaeology entry 5 — the
remote branch is already deleted; `22c07e4` survives only as a harmless dangling local
object. Do not try to "recover" it.

---

## 5. What requires explicit owner sign-off

Get a yes from the owner BEFORE doing any of these. "The tooling let me" is not consent.

1. **Destructive operations** — committing a POST `/api/clear-schedule` result, deleting any
   file under `docs/puzzles/`, removing ledger entries.
2. **Anything touching a published/past puzzle** (§2.1) — including "just fixing a typo in
   an answer list" for a puzzle dated ≤ today.
3. **Changing scoring, rules, or matcher behavior** (`docs/game.js` constants/curve,
   `docs/match.js` thresholds) — this changes the game under live players' feet and
   invalidates score comparisons across days.
4. **Mass TMDB usage** — bulk backfills, crawling, anything beyond one-puzzle-at-a-time
   curation (quota + terms exposure).
5. **Force-push to any shared branch**, history rewriting, or amending pushed commits.
6. **Changing these landing conventions themselves** (PR-vs-direct policy, commit format,
   rebase-merge discipline) — the conventions are the owner's, per-change, on record in
   `project_state.md`.
7. Anything the classification table (§1) marks "ask per change" — when in doubt, it's a
   sign-off item.

---

## 6. Escalation and rollback

**Bad push to `main` touching `docs/`:** players see it within ~3 minutes (Pages deploys
automatically; recent builds took 23s–2m28s, verified via `gh run list`). Don't panic-reset.

1. **Revert, don't reset.** `main` is shared and Pages tracks it; rewriting it strands
   clones and can race the deploy. Linear history makes reverts clean:
   ```
   git revert <bad-sha>        # one commit
   git revert <old>..<new>     # a range, newest-first reverts
   git push
   ```
   The revert push triggers a fresh Pages deploy that restores the previous state. Confirm
   with `gh run list --limit 1` then hard-reload the live site.
2. **Content ops are git-reversible by design.** The manifest and ledger are both
   git-tracked, so a bad publish, update, or clear-schedule is fully recoverable:
   uncommitted damage → `git checkout -- docs/puzzles/manifest.json curation/used_films.json`
   (plus any new puzzle files via `git clean -n docs/puzzles/` first to SEE what's untracked,
   then `git clean -f <paths>` only after reading the list). Committed damage → `git revert`.
3. **If a spoiler shipped in a commit message:** do NOT rewrite history (precedent: the
   `bdca151`/`3d7d17e` leaks were left in place — §2.2). Tell the owner; the damage is
   time-limited (the date passes) and rewriting public `main` is worse.
4. **If you're unsure whether the live site is broken or your cache is stale:** check on a
   fresh port locally, and hard-reload live — only the manifest fetch is cache-busted, not
   JS/CSS. If still unsure, escalate to degreesoffilm-debugging-playbook.

---

## When NOT to use this skill

- **Publishing/curating a puzzle step-by-step** (running the crop tool, Approve flow,
  schedule strip) → **degreesoffilm-run-and-operate**. This skill only owns the gates.
- **Setting up the machine, venv, deps, or `curation/.env`** → **degreesoffilm-build-and-env**.
- **Understanding WHY an invariant exists at the architecture level** (zones, cipher parity,
  schemas) → **degreesoffilm-architecture-contract**.
- **A bug or unexplained behavior** → **degreesoffilm-debugging-playbook**; the history of
  past investigations → **degreesoffilm-failure-archaeology**.
- **What tests exist / how to write one** → **degreesoffilm-validation-and-qa**.
- **Prose style for docs, handoffs, templates** → **degreesoffilm-docs-and-writing**.
- **Planning the v3 backend** → **degreesoffilm-server-move-campaign**.

## Reusing this pattern beyond this project

The transferable template: (1) classify changes by blast radius FIRST, with a table mapping
type → deploy consequence → landing path → test gate → post-land check; (2) write each
non-negotiable as rule + rationale + the incident that created it, so successors don't
relitigate; (3) when prod deploys straight from a branch with no CI, make "tests green + a
named restore command" the manual gate. Project-specific and NOT portable: the spoiler
discipline, immutable-past rule, TMDB key confinement, and the exact PR/commit conventions.

## Provenance and maintenance

- **Written 2026-07-03** against HEAD `10668ca` (clean tree). Every hash, PR number, branch
  name, and command above was verified by running read-only git/gh commands in this repo:
  full `git log --oneline`, `git log --merges` (empty → linear), `git show --stat` on each
  incident hash, `gh pr list --state all --limit 50` (18 PRs, all MERGED, kebab-case),
  `gh pr view 13/18 --json title,body,mergeCommit`, the manifest
  read via Python (7 puzzles, 2026-06-28..07-04), test suites spot-run (match/game/publish
  all green), the attribution footer read from `docs/index.html:139`, and the Pages config
  via `gh api repos/Bluesuitcase/DegreesofFilm/pages` (main `/docs`, status built).
  The stacked-PR rebase dance and the live-write puzzle-004 incident are **recorded
  accounts** (PR #13 body / `project_state.md`), not directly re-runnable.
- **Re-verify when drift is suspected:**
  - PR/merge conventions: `gh pr list --state all --limit 50` and `git log --merges --oneline`
  - Which puzzles are past vs future (the §2.1 boundary moves daily):
    `python -c "import json;[print(e['date'],e['id']) for e in json.load(open('docs/puzzles/manifest.json'))]"`
  - Pages still serving main /docs: `gh api repos/Bluesuitcase/DegreesofFilm/pages`
  - Suites still green: the §3a/§3b command blocks.
