---
name: degreesoffilm-change-control
description: >
  How changes to Degrees of Film are classified, gated, and landed. Load BEFORE committing,
  pushing, or merging ANYTHING in this repo; before touching anything under docs/ (GitHub
  Pages serves it straight to live players — any push to main touching docs/ deploys);
  when deciding branch-vs-direct-to-main; before landing content (dailies/corpus via the
  challenge_gen.py CLI — the spoiler-safe commit gate); before editing or deleting any
  already-played daily; when asked "can I just push this?", "can I fix yesterday's daily?",
  "can I change the matcher / scoring / the share format?"; and when a bad push to main
  needs rolling back. Covers the change classification table, the non-negotiables with
  their incident history, landing checklists, commit/PR conventions, the owner-sign-off
  list, and rollback. NOT for writing conventions and doc templates
  (degreesoffilm-docs-and-writing), the test inventory and evidence bar
  (degreesoffilm-validation-and-qa), architecture rationale
  (degreesoffilm-architecture-contract), or the history of past investigations
  (degreesoffilm-failure-archaeology).
---

# Degrees of Film — Change Control

How work lands in this repo without breaking the live game, spoiling players, or re-fighting
settled battles. Facts below were re-verified against the repo on **2026-08-14**, after the
degrees-of-separation rebuild (the dig game and all its tooling are deleted; see CLAUDE.md).

**The two facts that drive everything:**

1. **`docs/` IS production.** GitHub Pages serves `main` `/docs` at
   https://bluesuitcase.github.io/DegreesofFilm/. Any push to `main` that touches `docs/`
   auto-deploys to real players in ~30s–3min. There is no staging environment and no server —
   the whole game is static files.
2. **There is NO CI.** Nothing runs tests for you. The suites (see CLAUDE.md "Run & test";
   9 suites as of 2026-08-14) are a manual gate that YOU run before every push. A push with
   red tests ships broken code to players.

Jargon, once: **daily** = one day's challenge, an entry in `docs/challenges.json`.
**Corpus** = `docs/graph.json`, the whole film/people graph. **Solutions sidecar** =
`curation/challenge_solutions.json`, gitignored (this repo is public). **Rebase-merge** =
GitHub's "Rebase and merge" button; this repo's history is fully linear (`git log --merges`
is empty, re-verified 2026-08-14). **Owner** = the human running this project; they confirm
the landing mode for each change. `gh` is installed but not logged in — auth per-command via
`GH_TOKEN` from the cached git credential (see `agents/issue-tracker.md`).

---

## 1. Change classification table

Classify every change FIRST. When a change spans rows, the strictest row wins.

| Change type | Example paths | Deploys to live players? | Landing path | Required tests BEFORE landing | Verification AFTER landing |
|---|---|---|---|---|---|
| **Player-facing code** | `docs/*.js`, `docs/style.css`, `docs/index.html` | **YES** | Branch → PR → rebase-merge on the owner's explicit "merge" (precedent: PR #29 the rebuild, PR #30 the corpus refresh) — **ask per change** | All JS suites green + manual browser check on a **fresh port** | Confirm Pages redeploy (§3a step 8) + play the live site |
| **Game rules / matcher** | `docs/chain.js`, `docs/match.js` | **YES** | Same as above, **plus owner sign-off** (§5) | **Test-first**: add the case to `match.cases.js` / the failing test to `chain.test.js` BEFORE changing the algorithm, then all JS suites | Same as above + replay a daily end-to-end |
| **Content publish** (corpus refresh / new dailies) | `docs/graph.json`, `docs/challenges.json` via the curation CLI (§3c) | **YES** | Branch → PR → rebase-merge (precedent: PR #30) — ask | `challenge_gen.py --check` green + all suites; spoiler-safe commit message (§2.2) | Confirm Pages redeploy; load the site without spoiling yourself |
| **Content edit** (an existing daily) | Rescheduling / editing a `challenges.json` entry or its `note` | **YES** | **Future-dated dailies ONLY** (§2.1); ask the owner | `--check` green (it also enforces the curator's-note rule) | Same as content publish |
| **Curation-only code** | `curation/*` with **zero `docs/` diff** | No | Direct to `main` — still confirm | The 3 Python suites (stdlib only, no venv) | `git status` clean |
| **Docs-of-record** | `project_state.md`, `CLAUDE.md`, `DESIGN.md` | No | Direct to `main` with a `Docs:` commit (established precedent, e.g. `ed73605`, `36c9e57`) | None (but don't let docs contradict code) | Spot-read the rendered file |
| **Meta** | `.claude/` (skills, settings, launch.json), `agents/`, `adr/` | No | Direct to `main`; owner confirms | None mandatory | — |

Verify the "no deploy" claim for a mixed diff before trusting it:
```
git diff --stat -- docs/
```
If that prints anything, the change is player-facing. Test commands live in CLAUDE.md
"Run & test".

---

## 2. The non-negotiables

Each rule exists because something happened (details: degreesoffilm-failure-archaeology).
Do not relitigate them without owner sign-off.

### 2.1 IMMUTABLE PAST — never modify a daily dated ≤ today
- **Rule:** Dailies whose date is today or earlier are frozen — no endpoint swaps, no par
  "fixes", no reschedules, no deletions. Edits are for **future-dated** dailies only.
- **Status:** Carried over from the dig era (where it was hard-learned); no current doc of
  record restates it for the rebuilt game yet, but the rationale transfers exactly: players
  already played it — streaks, scorecards, and share cards reference the result, and the
  archive (`?id=N`) replays old dailies forever, so a "fix" silently rewrites history.
- **The trap:** Nothing in code enforces this — `challenges.json` is a plain file. The rule
  is discipline, not tooling.

### 2.2 SPOILER DISCIPLINE — commit messages are public
- **Rule:** Nothing public may leak a route before its date: content commits and PR
  titles/bodies must never name any film or person on a future daily's chain (endpoint
  pairs already ship in `challenges.json`, but don't volunteer them either — precedent
  shape: `Content: corpus refresh + restock 30 dailies (runway through 2026-10-13)`,
  commit `71454d3`). The solutions sidecar is gitignored and must stay that way. Curator's
  notes are texture-only — `challenge_gen.py --check` hard-enforces that a note never
  identifies anyone on any geodesic.
- **Incident (dig era, rule still live):** commits `bdca151` and `3d7d17e` named unplayed
  puzzles' films in their subjects; history was deliberately NOT rewritten — the convention
  was adopted instead. Cite these as the lesson, don't repeat them.

### 2.3 KEY CONFINEMENT — the TMDB key never reaches a player
- **Rule:** The key lives only in gitignored `curation/.env`. Nothing under `docs/` may
  contain it, fetch TMDB directly, or embed anything derived from a live key call. The
  three-zone architecture (CLAUDE.md) exists to guarantee this. Check before pushing:
  `git grep -i tmdb_api_key -- docs/` must return nothing.

### 2.4 TESTS GREEN BEFORE PUSH — because there is no CI
- **Rule:** Run the suites relevant to your diff (CLAUDE.md "Run & test") and get zero
  failures before every push. A new behavior needs a new test that was red before your
  change and green after. Evidence bar: degreesoffilm-validation-and-qa.

### 2.5 LAYERING LAW — rules never touch the DOM
- **Rule:** `docs/match.js` imports nothing; `docs/corpus.js` imports only `match.js`;
  `docs/chain.js` imports nothing and takes a corpus; `docs/app.js` does ALL DOM work;
  `daily.js`/`stats.js` stay pure. The Node suites import these modules directly — DOM
  leakage breaks the entire manual test gate (CLAUDE.md "Layering, keep it clean").

### 2.6 MATCHER TEST-FIRST — the contract precedes the algorithm
- **Rule:** Add the new case to `match.cases.js` BEFORE touching `docs/match.js`. The case
  table IS the fairness spec; a regression here rejects a correct guess from a live player
  with no error anywhere.

### 2.7 SHARE GRAMMAR LINE 1 IS FROZEN
- **Rule:** The share string's first line is a machine-parseable contract (frozen
  2026-08-14; full grammar in CLAUDE.md "Share grammar"). Accountless leagues parse it;
  changing it breaks every parser silently. Line 1 may only ever GAIN content after the
  final `)`. Any change here is an owner-sign-off item (§5).

### 2.8 ATTRIBUTION IS MANDATORY — the TMDB footer never comes off
- **Rule:** `docs/index.html` ships the "not endorsed or certified by TMDB" attribution
  (verified present 2026-08-14, ~lines 120–136). No redesign, refactor, or copy pass may
  drop it. Context: degreesoffilm-external-positioning.

### 2.9 DAILIES GO THROUGH THE GENERATOR — and `--check` gates the commit
- **Rule:** Stock dailies via `python curation/challenge_gen.py --days N` (it picks pairs,
  rejects franchise matches, asserts par by BFS, writes solutions to the gitignored
  sidecar). Never hand-author a daily. Run `challenge_gen.py --check` before committing any
  content change, and again after any corpus rebuild — it re-derives every published
  daily's par and enforces the curator's-note rule.

### 2.10 STATS ISOLATION — only the real daily touches streaks
- **Rule:** Replays (`?id=N`) never write daily stats or the streak — they record into an
  isolated archive channel (guards in `docs/app.js` + `docs/stats.js`; stated in CLAUDE.md
  "The ruleset"). Any new mode inherits this by default. The streak is localStorage-only —
  polluting it is unfixable.

---

## 3. Landing checklists

### 3a. Player-facing change (anything diffing `docs/`)

1. Confirm the landing mode with the owner (branch → PR → rebase-merge is the precedent
   for player-facing work — PRs #29 and #30 both landed on an explicit "merge"; ask,
   don't assume).
2. Branch, kebab-case and feature-scoped: `git checkout -b my-feature-name`.
3. Make the change. If it alters rules/matcher behavior: write the failing test FIRST
   (§2.6) and get owner sign-off (§5).
4. Run every JS suite from the repo root (commands in CLAUDE.md "Run & test") — all must
   pass; each exits non-zero on failure.
5. Verify in a browser on a **fresh port** (browsers cache modules per origin:port — a
   recurring trap): `python -m http.server 8123 --directory docs`, open
   `http://localhost:8123/?play`.
6. Commit per §4; push the branch; open the PR (`gh` with a per-command `GH_TOKEN` —
   see `agents/issue-tracker.md`; no spoilers anywhere in the title or body).
7. Rebase-merge on the owner's explicit go-ahead and delete the branch. Don't stack a
   second PR on the branch while it's open (§4).
8. Confirm the Pages redeploy (`gh run list --limit 1` — expect "pages build and
   deployment … success"), then hard-reload the live site (Ctrl+F5 — changed JS/CSS can
   be cached) and verify the change live.

### 3b. Curation-only change (no `docs/` diff)

1. Confirm `git diff --stat -- docs/` is empty — otherwise use §3a.
2. Confirm the landing mode with the owner (precedent is direct-to-main).
3. Run the three Python suites (stdlib only — there is no venv):
   ```
   python curation/harvest.test.py && python curation/graph_build.test.py && python curation/challenge_gen.test.py
   ```
4. Commit direct to `main` (`Curation:` area tag) and push. No player-visible deploy
   follows.

### 3c. Content publish (corpus refresh and/or new dailies)

Content ops are three CLI commands (CLAUDE.md "Content operations") — there is no curation
UI and no live-write endpoint anymore. The change-control gates:

1. `python curation/harvest.py` (only step that needs the TMDB key) →
   `python curation/graph_build.py` → `python curation/challenge_gen.py --days N`.
2. **After any corpus rebuild, run `challenge_gen.py --check`** — film ids are stable, but
   this catches a published daily whose endpoint fell out of the pool, re-asserts every
   par, and enforces the curator's-note rule. Green `--check` is the commit gate.
3. Run all 9 suites; play a daily locally on a fresh port.
4. **Spoiler-safe commit message** (§2.2): describe the operation and runway, never a
   chain (`Content: corpus refresh + restock 30 dailies (runway through YYYY-MM-DD)`).
5. Land per the owner's chosen mode (PR #30 is the precedent: branch → rebase-merge),
   confirm the Pages deploy, and load the live site without spoiling yourself. The push
   is the point of no return — the dailies are scheduled for real players.

### 3d. Docs-of-record update

1. `project_state.md`: edit in place on `main`, commit direct, no PR. Keep it updated as
   part of finishing any substantive session.
2. `CLAUDE.md` / `DESIGN.md`: direct to `main` with a `Docs:` commit. DESIGN.md is
   historical for the dig — CLAUDE.md + project_state.md are current; don't revive
   superseded DESIGN.md claims.
3. No spoilers in docs either: docs of record are in a public repo.

---

## 4. Commit and PR conventions

**Commit format:** `Area: imperative summary` (areas in use: `Game:`, `Content:`,
`Curation:`, `Docs:`, `Meta:`). Full conventions and PR body structure:
**degreesoffilm-docs-and-writing**. This section keeps only the gates.

**Spoiler-safe content commits** (§2.2): operation + runway, never a chain.

**Rebase-merge, always.** `main` has zero merge commits (`git log --merges` empty,
re-verified 2026-08-14); every merged PR through #30 was rebase-merged with its branch
deleted. Linear history keeps `git revert` and `git bisect` trivial — no merge commits,
no squash.

**Prefer sequential PRs.** A stacked PR historically cost a rebase-and-force-push dance
(dig era, PR #13 on #12) — land one, then branch the next from fresh `main`.

---

## 5. What requires explicit owner sign-off

Get a yes from the owner BEFORE doing any of these. "The tooling let me" is not consent.

1. **Destructive operations** — deleting or rewriting published dailies, replacing
   `docs/graph.json` outside the §3c pipeline, removing solutions-sidecar entries.
2. **Anything touching a past daily** (§2.1) — including "just fixing" its par or note.
3. **Changing rules, scoring, matcher behavior, or the share string** (`docs/chain.js`
   verdicts/attempts, `docs/match.js` thresholds, share line 1 — §2.7) — this changes the
   game under live players' feet and can silently break external parsers.
4. **Mass TMDB usage** — anything beyond the incremental `harvest.py` refresh (quota +
   terms exposure; see degreesoffilm-external-positioning).
5. **Force-push to any shared branch**, history rewriting, or amending pushed commits.
6. **Changing these landing conventions themselves** (PR-vs-direct policy, commit format,
   rebase-merge discipline) — the conventions are the owner's, per-change, on record in
   `project_state.md`.
7. Anything the classification table (§1) marks "ask per change" — when in doubt, it's a
   sign-off item.

---

## 6. Escalation and rollback

**Bad push to `main` touching `docs/`:** players see it within minutes. Don't panic-reset.

1. **Revert, don't reset.** `main` is shared and Pages tracks it; rewriting it strands
   clones and can race the deploy. Linear history makes reverts clean:
   ```
   git revert <bad-sha>        # one commit
   git revert <old>..<new>     # a range
   git push
   ```
   The revert push triggers a fresh Pages deploy restoring the previous state.
2. **Content is git-reversible — with one asymmetry.** `docs/graph.json` and
   `docs/challenges.json` are tracked, so a bad publish reverts cleanly. But the solutions
   sidecar is gitignored — after reverting `challenges.json`, re-run
   `challenge_gen.py --check` to confirm the sidecar and the shipped dailies still agree.
3. **If a spoiler shipped in a commit message:** do NOT rewrite history (precedent: the
   `bdca151`/`3d7d17e` leaks were left in place — §2.2). Tell the owner; the damage is
   time-limited and rewriting public `main` is worse.
4. **Unsure whether live is broken or your cache is stale?** Check on a fresh port
   locally and hard-reload live (Ctrl+F5) before concluding anything.

---

## When NOT to use this skill

- **WHY an invariant exists at the architecture level** (zones, corpus encoding, the
  static-graph idea) → **degreesoffilm-architecture-contract**.
- **What tests exist / how to write one / is this enough evidence** →
  **degreesoffilm-validation-and-qa**.
- **Prose style, doc templates, commit-message craft** → **degreesoffilm-docs-and-writing**.
- **The history of past investigations and dead ends** →
  **degreesoffilm-failure-archaeology** (it owns the chronicle; this skill only cites the
  incidents that still carry a live rule).
- **TMDB terms, attribution rationale, public claims** →
  **degreesoffilm-external-positioning**.
- **Matching/normalization theory, project glossary** → **degreesoffilm-domain-reference**.
- **Proving a claim before building on it** → **degreesoffilm-proof-and-analysis-toolkit**;
  idea-to-result discipline → **degreesoffilm-research-methodology**.

## Reusing this pattern beyond this project

The transferable template: (1) classify changes by blast radius FIRST, with a table mapping
type → deploy consequence → landing path → test gate → post-land check; (2) write each
non-negotiable as rule + rationale + the incident that created it, so successors don't
relitigate; (3) when prod deploys straight from a branch with no CI, make "tests green + a
named check command" the manual gate. Project-specific and NOT portable: the spoiler
discipline, immutable-past rule, TMDB key confinement, and the exact PR/commit conventions.

## Provenance and maintenance

- **Written 2026-07-03; re-verified and rewritten 2026-08-14** after the
  degrees-of-separation rebuild (dig-era rows, live-write rules, manifest/ledger jargon,
  and the Worker removed). Verified by read-only git commands in this repo: `git log`
  (incident hashes `bdca151`/`3d7d17e`/`71454d3`; `Docs:` direct-to-main precedent),
  `git log --merges` (empty → linear), the attribution footer read from `docs/index.html`,
  the PR #29/#30 landing record in `project_state.md`, and the test/CLI inventory against
  CLAUDE.md "Run & test" / "Content operations".
- **Re-verify when drift is suspected:** merge discipline via `git log --merges --oneline`;
  the §2.1 past/future boundary via the `date` fields in `docs/challenges.json`; suite
  inventory via CLAUDE.md "Run & test"; published-daily integrity via
  `python curation/challenge_gen.py --check`.
