---
name: degreesoffilm-failure-archaeology
description: The chronicle of every major investigation, dead end, rejected approach, and near-miss in the Degrees of Film repo, recorded as symptom → root cause → evidence → status. Load this BEFORE proposing a redesign, optimization, or new approach ("why don't we just sort by popularity / hash the answers / build a picker / upgrade OpenCV…"), when an idea smells previously-tried, when investigating why the code is the way it is (billing order, the <5 pin, auto headshots, next_date), when tempted to reopen a parked feature (Score History, commercial TMDB), or when a "bug" might be settled design (poser/practice/archive not counting toward stats). Ten seconds in the index below tells you whether the battle was already fought.
---

# Degrees of Film — failure archaeology

This skill exists so no session re-fights a settled battle. Every entry was verified
against git history, GitHub PRs, and the current code on 2026-07-03. Stories that exist
only in session-handoff docs (not reconstructible from git alone) are labeled
**recorded account**.

## Settled battles — do not re-fight (10-second index)

| # | Claim you might be about to make | Verdict |
|---|----------------------------------|---------|
| 1 | "Sort the credit ladder by TMDB popularity" | SETTLED-REJECTED — buried the Joker at rung 13 |
| 2 | "Publish several puzzles today; the manifest will cope" | FIXED — `next_date` auto-assigns; collision orphaned 003/004 once |
| 3 | "Build a picker for in-character stills per rung" | SETTLED-REJECTED — built twice-over, TMDB data too sparse, removed |
| 4 | "Upgrade opencv past 5.0" | RULE-CREATED — 5.0 dropped Haar cascades; pin `<5` is load-bearing |
| 5 | "Reveal mechanic seems missing from v1" | SHIPPED in v2 — tiers were authored ahead from Phase 2 |
| 6 | "Discover can suggest a scheduled-but-unpublished film" | SETTLED-REJECTED — non-issue; ledger excludes at approve |
| 7 | "Test /api/update or /api/clear-schedule against real content" | RULE-CREATED — moved live puzzle 004 once; restore command exists |
| 8 | "My docs/ change didn't take effect — regression?" | RULE-CREATED — stale ES-module cache; verify on a fresh port |
| 9 | "Add a Score History screen now" | PARKED — deliberately v3, with accounts/DB |
| 10 | "Poser/practice/archive runs don't update stats — bug?" | SETTLED design — deliberate isolation guards in app.js |
| 11 | "Put the film title in the content commit message" | RULE-CREATED — two leaks happened; number/date only |
| 12 | "Home QUOTES film names are harmless" | OPEN — two quotes currently name films in the puzzle set |
| 13 | "Approve message shows `accent undefined`" | OPEN — known field-name mismatch, cosmetic |
| 14 | "Stack a PR on an unmerged PR" | RULE-CREATED — #13-on-#12 dirty-diff dance; prefer sequential |
| 15 | "Ship UX polish ad hoc" | Precedent — batch from a playtest, one PR per item (#7–#11) |
| 16 | "Monetize / scale up TMDB usage" | PARKED — commercial TMDB agreement gated on real monetization |
| 17 | "Hash/encrypt the answers client-side" | FENCED (enumerable answer space) — externally chronicled: see degreesoffilm-server-move-campaign wrong-path W1 and degreesoffilm-proof-and-analysis-toolkit recipe (e); index row only, no full entry here |

## The chronicle

Uniform format: **Symptom/Idea → Investigation → Root cause / finding → Evidence →
Status → Do not → Unless.** Past tense for the story; imperative for the rules.

### 1. Popularity-sorted credit ladder

- **Symptom/Idea:** Order rungs famous→obscure by sorting credits on TMDB `popularity`.
- **Investigation (2026-06-29):** Before building any curation tooling, a throwaway
  stdlib script pulled known films and printed credits both ways — (A) person
  popularity vs (B) billing order — for eyeballing. This was the project's declared
  riskiest assumption, tested for the price of one script.
- **Root cause / finding:** TMDB `popularity` is a *rolling/current* metric, not
  fame-for-this-film. It buried Heath Ledger's Joker at rung 13 and sank Tommy Lee
  Jones below a one-scene bit player. Billing order (`cast[].order`) fixed every test
  film (Joker → rung 3). Adopted: cast by billing order, popularity only as tiebreaker,
  director floats early, technical crew deepest; a human reorders edge cases.
- **Evidence:** commit `45b4085` (2026-06-29, message records the finding);
  `curation/validate_ladder.py` (still in-tree, header explains the protocol);
  `DESIGN.md` §1 (lines ~17–19) and §5 (~lines 206–210) record the decision;
  `curation/build_rungs.py` implements billing order.
- **Status:** SETTLED-REJECTED.
- **Do not** re-propose popularity-first ordering, or "simplify" build_rungs by
  dropping billing order.
- **Unless** TMDB ships a per-film, non-rolling fame signal — then re-run the
  validate_ladder A/B protocol on its 5-film stress set before touching build_rungs.

### 2. Manifest date-collision orphaned puzzles 003/004

- **Symptom/Idea:** Three puzzles published in one session; only the last appeared in
  the daily sequence.
- **Investigation (2026-06-30):** Puzzles 003/004/005 had all been published with date
  2026-06-30. The manifest is one-entry-per-day and `manifest.upsert` **silently
  replaces by date key**, so only the last writer (005) survived; 003/004 were orphaned
  (files on disk, absent from the index).
- **Root cause / finding:** The crop tool defaulted the publish date to "today", so
  back-to-back publishes collided. Silent-overwrite-by-key made the loss invisible
  until play. Recovery: re-dated 004→2026-07-01 and 005→2026-07-02 and rebuilt
  manifest.json from every puzzle file. Prevention: `publish.next_date(manifest)`
  returns the day after the latest puzzle (pure, tested); `GET /api/next-date` exposes
  it; the UI date field defaults to it.
- **Evidence:** recovery commit `772f4f7` (2026-06-30, message tells the whole story);
  fix commit `257bcff` (same day, 3 minutes later); `curation/publish.py`
  `next_date()` (line ~40) with docstring naming the collision rationale.
- **Status:** FIXED (high-cost incident; the mechanism — upsert replaces by date —
  is still live and correct).
- **Do not** hand-set the same date on two publishes, or assume the manifest warns on
  overwrite. Do not remove `next_date` defaulting.
- **Unless** the manifest gains multi-puzzle-per-day semantics (a v3-scale redesign
  through change control).

### 3. Character stills / the manual cast-photo picker

- **Symptom/Idea:** Credit rungs should reveal the actor *in character* (a tagged
  film still), not a generic headshot — so build a per-rung image picker.
- **Investigation (2026-07-01):** Built in full: PR #12 (client + schema, merged
  14:09Z) and PR #13 (curation authoring + a per-rung picker UI with candidate stills,
  merged 14:10Z). In real use, TMDB's person-tagged images proved too sparse — mostly
  generic backdrops shared across the whole cast, rarely an actual in-character still.
  The manual pass was parked the same day (recorded: user said "too much work"), crew
  and then cast were backfilled with automatic headshots (PRs #14, #15), and the
  picker was removed entirely that evening.
- **Root cause / finding:** Data reality beat the plan — the feature's value depended
  on TMDB tagged-image coverage that doesn't exist. ALL credit rungs (cast + crew) now
  use that person's TMDB profile headshot automatically; caption = "Name as Character"
  for cast, name only for crew; missing headshot → hold the full frame.
- **Evidence:** PRs #12/#13 (bodies describe `image_pick`, `candidate_stills`, the
  picker UI); backfills `7b98546`/`7a7acd3` + PRs #14/#15; removal commit `3e2cfbb`
  (2026-07-01, "drop the manual cast-photo picker — headshots are automatic", diff
  rips out `candidate_stills`/`tagged_still_urls`/`image_pick`); parked-first account
  in `007b3e2`'s project_state diff; current `curation/credits_images.py` has no
  picker concept.
- **Status:** SETTLED-REJECTED (dead end, high cost: built, merged, then removed).
- **Do not** rebuild a manual image picker or re-add `image_pick`-style helper fields.
- **Unless** a survey of the *actual* puzzle pool shows TMDB tagged-image coverage has
  materially improved (measure coverage first — that was the missing de-risk step).

### 4. OpenCV 5.0 dropped the bundled Haar cascades

- **Symptom/Idea:** "The opencv pin `<5` looks stale — bump it."
- **Investigation (2026-07-02):** While making auto-crop face-first, the dependency
  was pinned `opencv-python-headless>=4.9,<5` deliberately: OpenCV 5.0 removed the
  bundled Haar cascade files and ships only the DNN `FaceDetectorYN`, which requires a
  separately downloaded model file. 4.13 has a Python-3.14 wheel and keeps the classic
  cascade. cv2 is optional at runtime — `images.detect_faces` returns `[]` without it
  and auto-crop falls back to edge energy.
- **Evidence:** commit `388e645` (2026-07-02, message states the 5.0 rationale);
  `curation/requirements.txt` line `opencv-python-headless>=4.9,<5` + comment;
  project_state.md "Key decisions" records the same; `curation/images.py`
  `detect_faces` degrades gracefully (tested in `curation/images.test.py`).
- **Status:** RULE-CREATED (pin-with-rationale). The pin is load-bearing.
- **Do not** bump to `>=5` casually; auto-crop face detection silently degrades to
  edge-energy (no crash — you'd only notice worse crops).
- **Unless** you do a deliberate migration to `FaceDetectorYN` — model download,
  storage location, offline behavior, and re-testing `images.test.py` — as its own
  change-controlled task.

### 5. Progressive-crop reveal: cut from v1, shipped in v2 (author-ahead)

- **Symptom/Idea:** "The cropper writes 3 reveal tiers but only the tightest is
  used — dead code?" / "Let's add a reveal mechanic."
- **Investigation:** The tier pipeline was built in Phase 2 (`841e1d3`, 2026-06-29:
  "image prep — reveal-tier crops"), but the client mechanic was consciously deferred
  to the v2 parking lot — content was **authored ahead** so every already-published
  puzzle would support the mechanic the day it shipped. It shipped 2026-07-01 via
  PR #18: `frame.js` `pickCreditFrame` gained a `revealTier` param (= `game.attempts`);
  each wrong guess on the film rung widens the crop one tier, clamped to the widest;
  single-tier puzzles (001) stay put.
- **Evidence:** `841e1d3` (tiers authored 2026-06-29); PR #18 (opened 2026-07-01T19:01Z,
  merged 23:12Z, body includes live verification on puzzle 004: 004-1 → 004-2 →
  004-3 across misses); rebase-merged as `995c01e`; `DESIGN.md` §6 v2 list; current
  `docs/frame.js`. **Branch hygiene note (as of 2026-07-03):** the pre-rebase PR head
  `22c07e4` survives only as a dangling local object (same message/date as `995c01e`,
  different hash — that's rebase-merge, not a duplicate feature); `git ls-remote
  --heads origin` shows only `main`, so the old `reveal-mechanic` remote branch is
  already gone. Ignore `22c07e4`; do not "recover" it.
- **Status:** SHIPPED (v2). The author-ahead pattern is the reusable lesson.
- **Do not** treat tiers 2–3 as dead weight, and do not rebuild the mechanic — it
  exists.
- **Unless** you're extending reveals to credit rungs — that's new design, not
  recovery (credit rungs are deliberately unaffected).

### 6. "Exclude scheduled-but-unpublished films from Discover" — non-issue

- **Symptom/Idea:** Randomize/Discover might re-suggest a film that's already been
  made into a scheduled (future-dated) puzzle.
- **Investigation (2026-07-02):** Logged as a possible follow-up after Randomize
  shipped, then investigated and **dropped**: the ledger (`curation/used_films.json`)
  is appended at **approve time**, immediately and locally, and Discover/Randomize
  exclude every ledger film. There is no "scheduled but not yet in the ledger" state —
  scheduling *is* approving. Instead the user chose the inverse feature:
  **Clear-scheduled frees the films** (`ledger.remove_by_puzzles`) so cleared films
  become suggestible again.
- **Evidence:** recorded account in project_state.md history — the follow-up appears
  in `f2ffe28`'s version and the DROPPED verdict ("investigated: the ledger already
  excludes every approved film immediately + locally; there's no such gap") appears in
  the section removed by `10668ca` (see `git show 10668ca -- project_state.md`);
  code path: `curation/app.py` `api_approve` → `publish.publish()` → ledger append;
  frees-films commit `c0329a2`.
- **Status:** SETTLED-REJECTED (non-issue; a cheap investigation killed it cleanly).
- **Do not** add a "scheduled exclusion" filter to discover.py — it would filter
  nothing.
- **Unless** the approve flow is ever split so a puzzle can exist without a ledger
  entry (that would reopen this for real).

### 7. Live-write verification moved committed puzzle 004

- **Symptom/Idea:** "Just test /api/update (or /api/clear-schedule) against the tool's
  real data to verify it."
- **Investigation:** Recorded account (2026-07-02 session; not reconstructible from
  git because the damage was reverted before commit): a reschedule test during
  live-endpoint verification moved committed puzzle 004's manifest entry. Because
  `docs/puzzles/manifest.json` and `curation/used_films.json` are git-tracked, restore
  was one command.
- **Root cause / finding:** The curation tool's LIVE-WRITE endpoints
  (`/api/approve`, `/api/update`, `POST /api/clear-schedule`) operate on the real
  repo files — there is no sandbox mode. Rule: never point live-write tests at
  committed content without a restore plan; restore =
  `git checkout -- docs/puzzles/manifest.json curation/used_films.json`.
- **Evidence:** the rule is codified in project_state.md "Workflow / gotchas"
  ("Verifying destructive curation endpoints … restore with `git checkout -- …`");
  incident itself = recorded account. A same-session precedent of doing it *right*:
  Clear-scheduled was verified live then the manifest "restored from git"
  (`10668ca` project_state diff).
- **Status:** RULE-CREATED.
- **Do not** run live-write endpoints against committed content casually; know your
  restore command *before* the POST. Written puzzle *files/images* are untracked-new
  until committed — those you delete by hand.
- **Unless** the tool grows a dry-run/sandbox mode (only `GET /api/clear-schedule`
  has one today — it's a dry count).

### 8. Stale ES-module cache — the recurring verification trap

- **Symptom/Idea:** "I edited docs/ JS/CSS, reloaded, and nothing changed — my change
  is broken / a regression appeared."
- **Investigation (recurring, first recorded 2026-07-01):** `python -m http.server`
  plus browser per-origin:port caching serves **stale ES modules and CSS** after
  edits. Cost real debugging time more than once across sessions.
- **Root cause / finding:** Environment, not code. Rule: verify UI changes on a
  **fresh port** (or cache-bust the `<link>`/`import`). Note the client itself only
  cache-busts the **manifest** fetch (`?d=<todayISO>`), nothing else. Related
  environment trap from the same sessions: the preview `screenshot` tool often times
  out on the heavy curation page — use DOM/computed-style checks instead.
- **Evidence:** recorded account — project_state.md "Workflow / gotchas" ("Dev cache
  gotcha"), present in every version since at least `007b3e2` (2026-07-01), including
  current; fresh-port procedure spelled out in the `f2ffe28` version.
- **Status:** RULE-CREATED.
- **Do not** conclude "regression" from a browser reload alone; discriminating
  experiment = same page on a fresh port.
- **Unless** the dev server gains cache-control headers (nobody has bothered; the
  rule is cheaper).

### 9. Score History — deliberately parked for v3

- **Symptom/Idea:** "A screen of the player's previous daily scores is doable
  client-only from localStorage — quick win?"
- **Investigation:** Considered at design time and deliberately slotted into v3:
  "Doable client-only, but far more useful backed by accounts/DB (cross-device,
  durable), so it lands here with them."
- **Evidence:** `DESIGN.md` §6 v3 list (Score History item, ~line 317);
  project_state.md "Next steps" lists it under the stay-static v3 track.
- **Status:** PARKED (not rejected — sequenced).
- **Do not** build it as a v2 afterthought without owner sign-off; the parking was a
  choice, not an oversight.
- **Unless** the owner re-prioritizes the stay-static track — it's genuinely buildable
  client-only if they say go.

### 10. Poser/practice/archive runs don't touch daily stats — settled design

- **Symptom/Idea:** "Streak/stats didn't update after my run — bug in stats.js?"
- **Investigation:** Not a bug. `docs/app.js` `showEnd` guards recording explicitly:
  `if (!isArchive && !poser && !isPractice)` before `recordResult` (line ~376, with
  the comment "archive/poser/practice runs don't touch the daily streak/stats").
  Practice shows its own running tally; poser skips the roast and tags its share
  "(Poser)".
- **Evidence:** `docs/app.js` (~line 376); the isolation is stated in CLAUDE.md,
  project_state.md "Key decisions", and has held since archive (`3f32163`,
  2026-06-30), poser (`abe9b58`), and practice (`811ee40`, 2026-07-01) shipped.
- **Status:** SETTLED (deliberate design, invariant-grade).
- **Do not** "fix" stats to count these modes.
- **Unless** a per-mode stats design goes through change control (the v3
  leaderboard's asterisk rule is the sanctioned direction for mode-aware scoring).

### 11. Spoiler leak in commit messages

- **Symptom/Idea:** Descriptive content commits — "what's the harm in naming the film?"
- **Investigation (recognized 2026-07-02):** The repo is public and commit messages
  are player-visible. Two content commits leaked future answers: `bdca151`
  (2026-06-30) named puzzle 006's film in its subject, and `3d7d17e` (2026-07-01)
  named puzzle 007's film before its date. Convention adopted: content commits
  reference puzzle NUMBER and date only ("Add puzzle NNN (YYYY-MM-DD)") until the
  date passes. History was **deliberately not rewritten** (rewriting public main
  costs more than the leak). Historical spoiler incidents are cited by hash and
  puzzle number, never by film title, until the puzzle's date has passed.
- **Evidence:** commits `bdca151`, `3d7d17e` (verified messages + dates); the
  convention is an owner rule recorded 2026-07-02 (recorded account; see also
  degreesoffilm-change-control).
- **Status:** RULE-CREATED (the two historical leaks stand as the lesson).
- **Do not** name an unplayed film in any commit message, PR title/body, or other
  public surface. Do not force-push history rewrites to scrub the old ones.
- **Unless** the puzzle's date has passed — then the title is fair game.

### 12. Home-screen QUOTES name films that are in the puzzle set — OPEN

- **Symptom/Idea:** Found 2026-07-03 during the architecture-contract review: the
  home screen's rotating quotes cite their source films, and the owner's spoiler rule
  says quotes must come from films NOT in the puzzle set.
- **Finding:** As of 2026-07-03, `docs/app.js` `QUOTES` (lines ~126–133) includes
  "Why so serious?" — *The Dark Knight* (puzzle 4, date passed) — and a second quote
  crediting puzzle 6's film (dated 2026-07-03; title withheld here per entry 11's
  citation rule until its date passes); both films are in `curation/used_films.json`.
  A player on the home screen can see the answer to an archived daily. A fix was chipped to the
  owner; it had NOT landed as of 2026-07-03 (HEAD `10668ca`, both quotes still
  present).
- **Evidence:** `docs/app.js` lines 126–133 (verified today); `curation/used_films.json`
  entries for puzzles 4 and 6.
- **Status:** OPEN (fix = swap those two quotes for films outside the puzzle set;
  player-facing docs/ change → PR path).
- **Do not** add new quotes without checking `used_films.json` first — and future
  curation of those quoted films re-creates this bug, so re-check on every publish.
- **Unless** already fixed when you read this — verify with:
  `grep -n "Toy Story\|Dark Knight" docs/app.js` (empty = fixed; update this entry).

### 13. Approve success message shows "accent undefined" — OPEN

- **Symptom/Idea:** Found 2026-07-03 during skill authoring: after a successful
  Approve, the curation UI prints ``✓ wrote NNN.json (id N, accent undefined)``.
- **Finding:** Field-name mismatch. `curation/static/index.html` line ~489 reads
  `j.accent`, but `curation/app.py` `api_approve` (~lines 290–304) returns
  `publish()`'s `{id, file, puzzle_path}` plus `res["theme"] = theme` — there is no
  top-level `accent` key (the accent is at `j.theme.accent`). Cosmetic only: the
  puzzle, images, ledger, and manifest are all written correctly.
- **Evidence:** `curation/static/index.html` line 489; `curation/app.py` lines
  290–304; `curation/publish.py` return dict (line ~132). All verified 2026-07-03;
  a chipped fix had NOT landed at HEAD `10668ca`.
- **Status:** OPEN (one-line fix: read `j.theme?.accent` or return `accent`
  server-side; curation-only → direct-to-main precedent applies).
- **Do not** misread the "undefined" as a failed publish — check the files, not the
  toast.
- **Unless** already fixed — verify with: `grep -n "j.accent" curation/static/index.html`.

### 14. Stacked PR #13-on-#12 — the rebase dance

- **Symptom/Idea:** "Build the next feature on top of the unmerged previous PR's
  branch to keep moving."
- **Investigation (2026-07-01):** PR #13 was stacked on #12. Its own body had to warn:
  "Until #12 merges, this PR's diff will also show the `frame.js` client changes;
  after #12 merges into `main` it cleans up." Because this repo rebase-merges
  (new hashes on main), the stacked branch then needed rebasing onto the rewritten
  commits before its own merge — reviewable-diff noise and an extra dance for zero
  speed gain at this project's PR cadence (the two PRs merged 83 seconds apart).
- **Evidence:** PR #13 body (verified via `gh pr view 13`); the two PRs were opened
  11 minutes apart (13:53Z / 14:04Z) and merged 83 seconds apart
  (14:09:04Z / 14:10:27Z).
- **Status:** RULE-CREATED — prefer sequential PRs; land the base first.
- **Do not** stack unless truly blocked and the base is expected to merge same-day.
- **Unless** using a tool that manages stacks natively (this repo doesn't).

### 15. UX-polish playtest batch (PRs #7–#11) — process precedent, not a failure

- **Story (2026-06-30 → 07-01):** A real playtest on 2026-06-30 produced a concrete
  punch list recorded in DESIGN §6 ("UX polish (from playtesting 2026-06-30)"); it
  shipped as five small single-purpose PRs (#7 tagline, #8 skip tooltip, #9 mode
  label, #10 CTA tooltips, #11 full-frame reveal) — #7–#11 opened over ~18 minutes
  (01:17–01:35Z) and batch-merged within seconds by 01:37Z, all 2026-07-01.
- **Evidence:** `DESIGN.md` §6 (~line 286); PRs #7–#11 titles/timestamps; commits
  `398dcc4`/`3ed8c10`/`31c737a`/`7e86ae5`/`7fa0df4`.
- **Status:** SETTLED precedent — playtest → written punch list → one PR per item.
  Some items were later *upgraded* (native `title` tooltips → themed `data-tip`
  bubbles, `314b98f`; DESIGN marks them "DONE, then upgraded").
- **Do not** bundle unrelated UX tweaks into one mega-PR; the small-batch pattern is
  the house style.

### 16. Commercial TMDB agreement — parked

- **Idea:** Get a commercial TMDB license "to be safe".
- **Finding:** Deliberately parked in DESIGN §6 v3: "required only if this ever
  monetizes or scales as a real product." Current usage is hobby-scale, curation-time
  only, with the mandatory attribution footer shipped (`c2f59c3`).
- **Evidence:** `DESIGN.md` §6 (~line 323); see degreesoffilm-external-positioning
  for the full terms/rights posture.
- **Status:** PARKED. **Do not** pursue it pre-monetization. **Unless** monetization
  or real scale is actually on the table — then it's a prerequisite, not optional.

## Patterns across entries

These recur; recognize them before starting new work (the discipline itself is
formalized in **degreesoffilm-research-methodology**):

- **De-risk before building** (entry 1): the project's riskiest assumption got a
  throwaway stdlib script *before* any tool was built. Contrast entry 3, where the
  missing de-risk step (measure TMDB tagged-image coverage first) cost two merged PRs.
- **Data reality beats the plan** (entries 1, 3): both big reversals came from the
  *shape of TMDB's actual data* (rolling popularity; sparse tagged images), not from
  code defects. Sample the data before designing around it.
- **Author-ahead** (entry 5): when a mechanic is deferred, keep authoring the content
  it needs (reveal tiers) so shipping later needs zero backfill.
- **Silent-overwrite-by-key** (entry 2): keyed upserts destroy without warning.
  When writing to a keyed store, ask "what happens on key collision?" first.
- **Pin-with-rationale** (entry 4): every non-obvious version pin gets its reason in
  the commit and requirements comment, so "stale pin" bumps get stopped by the record.
- **Verification-environment traps** (entries 7, 8): the two costliest debugging
  wastes were the *environment* (stale cache) and the *blast radius of verification
  itself* (live-write test). Discriminate environment-vs-code first; know the restore
  command before mutating.
- **Investigate-then-drop is a valid outcome** (entry 6): a cheap investigation that
  ends in "non-issue" is a success — but only if it's written down (that's this file's
  job).

## Entry template (append new entries with this)

```markdown
### N. <Short title>

- **Symptom/Idea:** <what someone observed or proposed>
- **Investigation (<YYYY-MM-DD>):** <what was actually done to find out>
- **Root cause / finding:** <the mechanism, stated plainly>
- **Evidence:** <commit hash / PR # / file:line / doc § — each one personally
  verified; project_state-only stories labeled "recorded account">
- **Status:** SETTLED-REJECTED | FIXED | RULE-CREATED | PARKED | OPEN | SHIPPED
- **Do not** <the imperative that saves the next session>
- **Unless** <the honest reopening condition — what NEW evidence would change this>
```

Where the raw sources live: `git log --oneline --all` + `git show <hash>` (commit
messages here are unusually narrative — read them in full); `gh pr list --state all`
+ `gh pr view <n> --json title,body` (18 PRs, all rebase-merged); `project_state.md`
current + its git history (`git log -p --follow -- project_state.md`) for recorded
accounts; `DESIGN.md` §5–§6 for decision language ("rejected", "instead",
"DONE, then upgraded", the parking lot); `CLAUDE.md` for the settled shape of things.
Concluded investigations MUST land an entry here — a retirement without a written
"why" will be re-fought.

## When NOT to use this skill

- Diagnosing a live failure right now → **degreesoffilm-debugging-playbook**
  (symptom→triage tables; this file is the *history* behind several of its rules).
- Checking whether a change is allowed / how it must land →
  **degreesoffilm-change-control**.
- Understanding the current design and its invariants →
  **degreesoffilm-architecture-contract**.
- TMDB data model, matcher theory, image math →
  **degreesoffilm-domain-reference**.
- Running the game/curation tool or publishing a puzzle →
  **degreesoffilm-run-and-operate** (and **degreesoffilm-build-and-env** for setup).
- How to conduct a NEW investigation properly →
  **degreesoffilm-research-methodology**.
- Config values and pins as they are today → **degreesoffilm-config-and-flags**.

## Reusing this pattern beyond this project

The transferable template: a single "settled battles" index + uniform
symptom→cause→evidence→status entries, with an honest **Unless** clause per entry and
a hard rule that every concluded investigation appends an entry. The
project-specific payload (TMDB quirks, manifest semantics, this repo's hashes) does
not transfer; the format, the status vocabulary, and the "recorded account" labeling
discipline do.

## Provenance and maintenance

- **Written:** 2026-07-03, against HEAD `10668ca` (branch `main`, clean tree except
  `.claude/skills/`).
- **How verified:** every commit hash re-read via `git show` (message + stat, full
  diff where load-bearing); PRs #12/#13/#18 bodies read via `gh pr view`; all 18 PR
  titles/timestamps from `gh pr list --state all`; DESIGN/CLAUDE/project_state
  sections re-read; recorded-account items traced through project_state.md git
  history (`f2ffe28`, `10668ca` diffs); OPEN items 12–13 confirmed still-present in
  the working tree on 2026-07-03; remote branch state confirmed via
  `git ls-remote --heads origin` (only `main`).
- **Drift checks:** entry 12 → `grep -n "Toy Story\|Dark Knight" docs/app.js`;
  entry 13 → `grep -n "j.accent" curation/static/index.html`; entry 4 →
  `grep opencv curation/requirements.txt`; entry 5's dangling object →
  `git cat-file -t 22c07e4` (may eventually be gc'd — that's fine).
- **Maintenance:** when an OPEN entry gets fixed, update its Status to FIXED with the
  landing hash in the same session. When any investigation concludes anywhere in this
  repo, append an entry using the template above and refresh this section's date.
