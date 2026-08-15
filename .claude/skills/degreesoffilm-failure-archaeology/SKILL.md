---
name: degreesoffilm-failure-archaeology
description: The chronicle of every major investigation, dead end, rejected approach, and near-miss in the Degrees of Film repo — dig era and rebuild alike — recorded as symptom → root cause → evidence → status. Load this BEFORE proposing a redesign, revival, or new approach — "bring back the dig / keep both modes", "ship a per-challenge subgraph to save bytes", "why not accounts / leaderboards", "spoiler-gated challenge links", "a community-pulse server", or dig-era ideas that smell previously-tried ("sort by popularity / hash the answers / build a picker / upgrade OpenCV") — when investigating why the code is the way it is (whole-corpus shipping, near-miss temperature, the ritual end card), when a "bug" might be settled design (replays not touching the streak), or when tempted to reopen anything KILLED or PARKED. Ten seconds in the index below tells you whether the battle was already fought.
---

# Degrees of Film — failure archaeology

This skill exists so no session re-fights a settled battle. Entries 1–17 were verified
against git history, GitHub PRs, and the then-current code on 2026-07-03; the whole file
was re-verified 2026-08-14 after **the rebuild** (the dig retired and deleted 2026-08-11,
degrees-of-separation launched 2026-08-14 — entry 18). Dig-era entries STAY even where
their tooling is gone: this file's purpose is history, and the lessons transfer. Stories
that exist only in session-handoff docs (not reconstructible from git alone) are labeled
**recorded account**.

## Settled battles — do not re-fight (10-second index)

| # | Claim you might be about to make | Verdict |
|---|----------------------------------|---------|
| 1 | "Sort the credit ladder by TMDB popularity" | SETTLED-REJECTED; MOOT (dig deleted) — the popularity-is-rolling lesson still governs |
| 2 | "Publish several puzzles today; the manifest will cope" | FIXED; MOOT — silent-overwrite-by-key lesson stands |
| 3 | "Build a picker for in-character stills per rung" | SETTLED-REJECTED; MOOT — no images anywhere in the rebuilt site |
| 4 | "Upgrade opencv past 5.0" | RULE-CREATED; MOOT — curation is stdlib-only now, no pip deps at all |
| 5 | "Reveal mechanic seems missing from v1" | SHIPPED in v2, deleted with the dig — author-ahead is the surviving lesson |
| 6 | "Discover can suggest a scheduled-but-unpublished film" | SETTLED-REJECTED; MOOT — discover/ledger deleted |
| 7 | "Test live-write curation endpoints against real content" | RULE-CREATED; MOOT — no endpoints exist; know-your-restore transfers |
| 8 | "My docs/ change didn't take effect — regression?" | RULE-CREATED — **still live**: stale ES-module cache; verify on a fresh port |
| 9 | "Add a Score History screen now" | OBE — the rebuild ships `?history` + calendar + handicap client-only; accounts KILLED (entry 22) |
| 10 | "Replay/off-daily runs don't update stats — bug?" | SETTLED design, carried into the rebuild — replays record to an isolated archive channel |
| 11 | "Put the film title in the content commit message" | RULE-CREATED — **still live**, generalized: never name a future daily's chain |
| 12 | "Home QUOTES film names are harmless" | FIXED `ee4ec54`; MOOT — QUOTES deleted with the dig; check-public-surfaces lesson lives in the curator's-note rule |
| 13 | "Approve message shows `accent undefined`" | FIXED `e7c1f69`; MOOT — curation UI deleted |
| 14 | "Stack a PR on an unmerged PR" | RULE-CREATED — still applies; the repo still rebase-merges (PR #29 was) |
| 15 | "Ship UX polish ad hoc" | Precedent (dig-era) — playtest → written punch list → small batches |
| 16 | "Monetize / scale up TMDB usage" | PARKED — still live; commercial TMDB gated on real monetization |
| 17 | "Hash/encrypt the answers client-side" | FENCED (enumerable answer space); MOOT — Worker + cipher deleted with the dig, Cloudflare torn down 2026-08-14, nothing secret ships; chronicle survives in degreesoffilm-proof-and-analysis-toolkit recipe (e) |
| 18 | "Bring back the dig / run both modes side by side" | SETTLED (2026-08-11, owner) — dig retired and DELETED; git holds the history |
| 19 | "Ship a per-challenge subgraph to save bytes" | SETTLED-REJECTED — it handed players the answer set; whole corpus is smaller anyway |
| 20 | "Near-miss feedback is meaningless in a small-world graph" | FALSIFIED by measurement (6,800 samples) — and shipped |
| 21 | "The game is fun; retention polish can wait" | FIXED — "feels like a one-off" verdict → the Comeback Loop, built and launched same day |
| 22 | "Spoiler-gated links / community-pulse Worker / accounts" | KILLED (2026-08-14 planning pass), each with a recorded revival trigger |
| 23 | "The button works, ship it" | RULE-CREATED (2026-08-15 TDZ incident) — module state above boot(); verification asserts the page's primary content, not just the feature |

## The chronicle

Uniform format: **Symptom/Idea → Investigation → Root cause / finding → Evidence →
Status → Do not → Unless.** Past tense for the story; imperative for the rules.
Entries 1–17 are dig-era; 18–22 are the rebuild.

### 1. Popularity-sorted credit ladder

- **Symptom/Idea:** Order rungs famous→obscure by sorting credits on TMDB `popularity`.
- **Investigation (2026-06-29):** Before building any curation tooling, a throwaway
  stdlib script pulled known films and printed credits both ways — (A) person
  popularity vs (B) billing order — for eyeballing. This was the project's declared
  riskiest assumption, tested for the price of one script.
- **Root cause / finding:** TMDB `popularity` is a *rolling/current* metric, not
  fame-for-this-film. It buried Heath Ledger's Joker at rung 13 and sank Tommy Lee
  Jones below a one-scene bit player. Billing order (`cast[].order`) fixed every test
  film (Joker → rung 3). Adopted: cast by billing order, popularity only as tiebreaker.
- **Evidence:** commit `45b4085` (2026-06-29, message records the finding); the
  validator and `build_rungs.py` existed in-tree until the rebuild deleted them.
- **Status:** SETTLED-REJECTED; **MOOT since 2026-08-11** — the ladder and its tooling
  were deleted with the dig. The lesson still governs: the rebuilt corpus uses
  popularity only to *rank suggestions* (`curation/graph_build.py` header), where
  current fame is exactly the right signal, and `harvest.py` takes cast by top
  *billing* (`CAST_TOP = 12`).
- **Do not** treat TMDB `popularity` as per-film fame in any future feature.
- **Unless** TMDB ships a per-film, non-rolling fame signal — then re-run an A/B
  eyeball protocol like `45b4085`'s before relying on it.

### 2. Manifest date-collision orphaned puzzles 003/004

- **Symptom/Idea:** Three puzzles published in one session; only the last appeared in
  the daily sequence.
- **Investigation (2026-06-30):** Puzzles 003/004/005 had all been published with date
  2026-06-30. The manifest was one-entry-per-day and `manifest.upsert` **silently
  replaced by date key**, so only the last writer (005) survived; 003/004 were orphaned
  (files on disk, absent from the index).
- **Root cause / finding:** The crop tool defaulted the publish date to "today", so
  back-to-back publishes collided. Silent-overwrite-by-key made the loss invisible
  until play. Recovery: re-dated and rebuilt the manifest. Prevention:
  `publish.next_date(manifest)` auto-assigned the next free day.
- **Evidence:** recovery commit `772f4f7` (2026-06-30, message tells the whole story);
  fix commit `257bcff` (same day, 3 minutes later).
- **Status:** FIXED (high-cost incident); **MOOT since 2026-08-11** — manifest and
  publish tool deleted. The rebuilt equivalent (`challenge_gen.py`) *appends* dailies
  after the latest date by construction. The lesson — keyed upserts destroy without
  warning — transfers whole.
- **Do not** write to any keyed store without first asking "what happens on key
  collision?".
- **Unless** never — this one is a permanent pattern (see Patterns below).

### 3. Character stills / the manual cast-photo picker

- **Symptom/Idea:** Credit rungs should reveal the actor *in character* (a tagged
  film still), not a generic headshot — so build a per-rung image picker.
- **Investigation (2026-07-01):** Built in full: PR #12 (client + schema) and PR #13
  (curation authoring + a per-rung picker UI with candidate stills), merged a minute
  apart. In real use, TMDB's person-tagged images proved too sparse — mostly generic
  backdrops shared across the whole cast, rarely an actual in-character still. The
  manual pass was parked the same day (recorded: user said "too much work"), rungs
  were backfilled with automatic headshots (PRs #14, #15), and the picker was removed
  entirely that evening.
- **Root cause / finding:** Data reality beat the plan — the feature's value depended
  on TMDB tagged-image coverage that doesn't exist.
- **Evidence:** PRs #12/#13 (bodies describe `image_pick`, `candidate_stills`);
  backfills `7b98546`/`7a7acd3`; removal commit `3e2cfbb` (2026-07-01, "drop the
  manual cast-photo picker — headshots are automatic").
- **Status:** SETTLED-REJECTED (dead end, high cost: built, merged, then removed);
  **MOOT since 2026-08-11** — the rebuilt site ships **no images at all** (~200 KB
  total). The missing de-risk step (measure coverage first) is the surviving lesson.
- **Do not** design any feature around TMDB tagged-image coverage without measuring
  coverage on the actual pool first.
- **Unless** a measured survey shows coverage materially improved AND the site ever
  wants images again (it deliberately doesn't).

### 4. OpenCV 5.0 dropped the bundled Haar cascades

- **Symptom/Idea:** "The opencv pin `<5` looks stale — bump it."
- **Investigation (2026-07-02):** The dependency was pinned
  `opencv-python-headless>=4.9,<5` deliberately: OpenCV 5.0 removed the bundled Haar
  cascade files and ships only the DNN `FaceDetectorYN`, which requires a separately
  downloaded model file. cv2 was optional at runtime — face detection degraded
  gracefully to edge-energy cropping.
- **Evidence:** commit `388e645` (2026-07-02, message states the 5.0 rationale).
- **Status:** RULE-CREATED (pin-with-rationale); **MOOT since 2026-08-11** — the crop
  pipeline, `requirements.txt`, and every pip dependency were deleted with the dig;
  `curation/` is stdlib-only Python now. The pattern (every non-obvious pin gets its
  reason in the commit and a comment) transfers.
- **Do not** add an unexplained version pin anywhere in this repo.
- **Unless** never — pattern, not inventory.

### 5. Progressive-crop reveal: cut from v1, shipped in v2 (author-ahead)

- **Symptom/Idea:** "The cropper writes 3 reveal tiers but only the tightest is
  used — dead code?" / "Let's add a reveal mechanic."
- **Investigation:** The tier pipeline was built in Phase 2 (`841e1d3`, 2026-06-29),
  but the client mechanic was consciously deferred — content was **authored ahead** so
  every already-published puzzle would support the mechanic the day it shipped. It
  shipped 2026-07-01 via PR #18 (rebase-merged as `995c01e`): each wrong guess widened
  the crop one tier.
- **Evidence:** `841e1d3`; `995c01e`. (The pre-rebase PR head `22c07e4` was a dangling
  duplicate from the rebase-merge — never "recover" a pre-rebase twin; the same
  duality now exists rebuild-side, see entry 18's evidence.)
- **Status:** SHIPPED (v2), then **deleted with the dig 2026-08-11**. Author-ahead is
  the reusable lesson — the rebuild used it too: `count_routes` was computed and
  stored in the solutions sidecar before anything consumed it, then powered the Wave 1
  difficulty arc and route-count reveal.
- **Do not** treat content fields with no current consumer as dead weight before
  checking whether they're authored-ahead.
- **Unless** the deferred mechanic has been explicitly killed — then they really are
  dead weight.

### 6. "Exclude scheduled-but-unpublished films from Discover" — non-issue

- **Symptom/Idea:** Randomize/Discover might re-suggest a film that's already been
  made into a scheduled (future-dated) puzzle.
- **Investigation (2026-07-02):** Logged as a possible follow-up, then investigated
  and **dropped**: the ledger was appended at **approve time**, immediately and
  locally, and Discover excluded every ledger film. There was no "scheduled but not
  yet in the ledger" state — scheduling *was* approving.
- **Evidence:** recorded account in project_state.md history — the DROPPED verdict
  is in the section removed by `10668ca` (`git show 10668ca -- project_state.md`);
  frees-films commit `c0329a2`.
- **Status:** SETTLED-REJECTED (non-issue); **MOOT since 2026-08-11** — Discover and
  the ledger were deleted. Kept as the flagship example that a cheap
  investigation ending in "non-issue" is a success *if written down*.
- **Do not** build a filter before confirming there's anything to filter.
- **Unless** never — pattern, not inventory.

### 7. Live-write verification moved committed puzzle 004

- **Symptom/Idea:** "Just test the curation tool's live-write endpoints against its
  real data to verify them."
- **Investigation:** Recorded account (2026-07-02 session; damage reverted before
  commit): a reschedule test during live-endpoint verification moved committed puzzle
  004's manifest entry. Because the touched files were git-tracked, restore was one
  `git checkout --` command.
- **Root cause / finding:** The tool's live-write endpoints operated on the real repo
  files — no sandbox mode. Rule: never point live-write tests at committed content
  without knowing the restore command *before* the POST.
- **Evidence:** the rule was codified in dig-era project_state.md "Workflow /
  gotchas"; incident itself = recorded account.
- **Status:** RULE-CREATED; **MOOT since 2026-08-11** — the tool and all its endpoints
  are gone; the rebuilt curation scripts only write two committed outputs
  (`docs/graph.json`, `docs/challenges.json`), and `git checkout --` still restores
  them. Know-your-restore transfers whole.
- **Do not** run anything that mutates committed content without the restore command
  in hand first.
- **Unless** never — pattern, not inventory.

### 8. Stale ES-module cache — the recurring verification trap — STILL LIVE

- **Symptom/Idea:** "I edited docs/ JS/CSS, reloaded, and nothing changed — my change
  is broken / a regression appeared."
- **Investigation (recurring, first recorded 2026-07-01):** `python -m http.server`
  plus browser per-origin:port caching serves **stale ES modules and CSS** after
  edits. Cost real debugging time more than once across sessions.
- **Root cause / finding:** Environment, not code. Rule: verify UI changes on a
  **fresh port** (or cache-bust the `<link>`/`import`). Related trap, still true
  post-rebuild: the preview `screenshot` tool times out when the Browser pane isn't
  displayed — use DOM/computed-style checks via `javascript_tool` instead.
- **Evidence:** recorded account — project_state.md "Workflow / gotchas" (present in
  every version since 2026-07-01, including the current post-launch one, which
  re-confirms the screenshot trap).
- **Status:** RULE-CREATED — **fully applicable to the rebuilt site** (docs/ is still
  vanilla ES modules served by http.server; the `docs` launch entry moved to port
  8010 because Docker holds 8000).
- **Do not** conclude "regression" from a browser reload alone; discriminating
  experiment = same page on a fresh port.
- **Unless** the dev server gains cache-control headers (nobody has bothered; the
  rule is cheaper).

### 9. Score History — parked for v3, then overtaken by the rebuild

- **Symptom/Idea:** "A screen of the player's previous daily scores is doable
  client-only from localStorage — quick win?"
- **Investigation:** Dig-era design parked it for v3 on the premise "far more useful
  backed by accounts/DB (cross-device, durable)". That premise died 2026-08-14: the
  owner killed accounts/leaderboards outright (entry 22), and the rebuild shipped the
  feature client-only anyway — `?history` with a scorecard, then Wave 3's completion
  calendar + rolling handicap — with **backup codes** (`stats.js`
  `exportRecord`/`importRecord`, `DOF1.` prefix, merge = union keep-better) as the
  accountless answer to cross-device durability.
- **Evidence:** Wave 3 commit `1bf5555` (branch `dcafaac`); `docs/stats.js`;
  project_state.md Wave 3 record.
- **Status:** OBE (overtaken by events) — built client-only, accounts never coming.
- **Do not** re-propose accounts as the prerequisite for any stats feature; the
  backup-code path is the settled durability answer.
- **Unless** the owner reopens accounts (entry 22's third item — his call alone).

### 10. Off-daily runs don't touch daily stats — settled design, carried forward

- **Symptom/Idea:** "Streak/stats didn't update after my run — bug in stats.js?"
- **Investigation:** Not a bug, in either era. The dig guarded
  `recordResult` behind `if (!isArchive && !poser && !isPractice)`. The rebuild
  carried the design forward and upgraded it: replays (`?id=N`) record into an
  **isolated archive channel** (`stats.js` `recordArchive`, by id, keep-better — the
  per-mode stats design entry 10 once anticipated), and the streak stays untouched.
- **Evidence:** `docs/app.js` (~lines 409–411: archive → `recordArchive`, daily →
  `recordResult`); `docs/stats.js` `recordArchive` (line ~144); CLAUDE.md ruleset
  ("Replays (`?id=N`) never touch the streak or scorecard"); tested in
  `stats.test.js`.
- **Status:** SETTLED (deliberate design, invariant-grade — now with its own channel).
- **Do not** "fix" replays to count toward the streak or scorecard.
- **Unless** a design change goes through change control with owner sign-off.

### 11. Spoiler leak in commit messages — STILL LIVE, generalized

- **Symptom/Idea:** Descriptive content commits — "what's the harm in naming the film?"
- **Investigation (recognized 2026-07-02):** The repo is public and commit messages
  are player-visible. Two content commits leaked future answers: `bdca151`
  (2026-06-30) named puzzle 006's film in its subject, and `3d7d17e` (2026-07-01)
  named puzzle 007's film before its date. History was **deliberately not rewritten**
  (rewriting public main costs more than the leak).
- **Root cause / finding:** Convention adopted: content commits reference number and
  date only until the date passes. The rebuild generalized it: **commit messages must
  not name a future daily's chain** (CLAUDE.md "Spoiler discipline"), and the
  solutions sidecar (`curation/challenge_solutions.json`) is gitignored. Same posture,
  new surface: curator's notes ship publicly before their date, so
  `challenge_gen.py --check` hard-enforces "texture only, never a connector"
  (`note_violations`, checked against every possible closer + the sidecar).
- **Evidence:** commits `bdca151`, `3d7d17e`; CLAUDE.md "Content operations";
  `curation/challenge_gen.py` `note_violations` (line ~128) and its `--check` hook
  (~line 240).
- **Status:** RULE-CREATED — the two historical leaks stand as the lesson; the rule is
  live and now machine-enforced for notes.
- **Do not** name a future daily's connectors in any commit, PR, note, or other
  public surface. Do not force-push history rewrites to scrub old leaks.
- **Unless** the daily's date has passed — then it's fair game.

### 12. Home-screen QUOTES named films in the puzzle set

- **Symptom/Idea:** Found 2026-07-03: the home screen's rotating quotes cited their
  source films, two of which were answer films for published puzzles — a player on
  the home screen could see the answer to an archived daily.
- **Fix:** commit `ee4ec54` (2026-07-03) swapped both for one-liners from films
  outside the puzzle set; a quotes-vs-ledger validator group guarded it thereafter.
- **Evidence:** `git show ee4ec54`.
- **Status:** FIXED; **MOOT since 2026-08-11** — the QUOTES feature was deleted with
  the dig (`grep QUOTES docs/app.js` is empty). The lesson — audit every *public
  surface* against the answer set, not just the data files — lives on as the
  curator's-note rule (entry 11).
- **Do not** add any player-visible flavor text without checking it against what it
  could spoil.
- **Unless** never — pattern, not inventory.

### 13. Approve success message showed "accent undefined"

- **Symptom/Idea:** Found 2026-07-03: after a successful Approve, the curation UI
  printed ``✓ wrote NNN.json (id N, accent undefined)`` — a field-name mismatch
  (UI read `j.accent`; the server returned it at `j.theme.accent`). Cosmetic only.
- **Fix:** commit `e7c1f69` (2026-07-03) — the UI read `j.theme?.accent`.
- **Evidence:** `git show e7c1f69`.
- **Status:** FIXED; **MOOT since 2026-08-11** — the curation UI was deleted whole.
  Kept as a small honest example of chronicling even cosmetic finds.
- **Do not / Unless** — nothing to guard; historical.

### 14. Stacked PR #13-on-#12 — the rebase dance

- **Symptom/Idea:** "Build the next feature on top of the unmerged previous PR's
  branch to keep moving."
- **Investigation (2026-07-01):** PR #13 was stacked on #12; its body had to warn that
  its diff showed #12's changes until #12 merged. Because this repo rebase-merges
  (new hashes on main), the stacked branch then needed rebasing onto the rewritten
  commits — reviewable-diff noise and an extra dance for zero speed gain (the two PRs
  merged 83 seconds apart).
- **Evidence:** PR #13 body (verified 2026-07-03 via `gh pr view 13`); merge
  timestamps 83 s apart.
- **Status:** RULE-CREATED — prefer sequential; land the base first. **Still applies
  unchanged**: the repo still rebase-merges (PR #29, the rebuild, was rebase-merged
  2026-08-14 — which is why branch/main hash twins like `3da6a94`/`72a0581` exist).
- **Do not** stack unless truly blocked and the base is expected to merge same-day.
- **Unless** using a tool that manages stacks natively (this repo doesn't).

### 15. UX-polish playtest batch (PRs #7–#11) — process precedent

- **Story (2026-06-30 → 07-01):** A real playtest produced a concrete written punch
  list; it shipped as five small single-purpose PRs (#7–#11), opened over ~18 minutes
  and batch-merged within seconds.
- **Evidence:** PRs #7–#11 titles/timestamps; commits `398dcc4`…`7fa0df4`.
- **Status:** SETTLED precedent (dig-era) — playtest → written punch list → small
  reviewable units. The rebuild scaled the same shape up: the 2026-08-14 playtest
  verdict became a written plan, built as one wave-sized commit per wave on a single
  owner-gated PR (#29). The invariant is *verdict → written list → sized units*, not
  the specific unit size.
- **Do not** bundle unrelated changes into one unreviewable blob, and do not act on a
  playtest verdict without writing the punch list down first.

### 16. Commercial TMDB agreement — parked, still live

- **Idea:** Get a commercial TMDB license "to be safe".
- **Finding:** Deliberately parked: required only if the project ever monetizes or
  scales as a real product. Usage remains hobby-scale and curation-time-only —
  the rebuild *reduced* the TMDB surface (no images at all; the key never reaches a
  player; harvests are incremental against append-only caches).
- **Evidence:** dig-era DESIGN.md §6 v3 (now historical but the reasoning stands);
  see degreesoffilm-external-positioning for the full terms/rights posture.
- **Status:** PARKED. **Do not** pursue it pre-monetization. **Unless** monetization
  or real scale is actually on the table — then it's a prerequisite, not optional.

### 17. (Index row only) Hash/encrypt the answers client-side

FENCED — an enumerable answer space makes client-side obfuscation theater; the full
chronicle lived in the (deleted) server-move-campaign skill and survives as
degreesoffilm-proof-and-analysis-toolkit recipe (e). **MOOT since the rebuild:** the
`/match` Worker and cipher were deleted 2026-08-11 and Cloudflare was fully torn down
2026-08-14 (Worker + ANSWERS KV deleted; endpoint 404s). Nothing secret ships —
solutions live in a gitignored sidecar, and the shipped graph is *everything*, so
there is no answer to hide. Do not reintroduce a secrecy layer for shipped data.

### 18. The dig retirement — full deletion, not a second mode

- **Symptom/Idea:** The original game — the vertical dig through one film's credits,
  21 published puzzles, the crop-and-publish curation tool, the `/match` Worker —
  got its owner verdict on 2026-08-11: **"I just don't find it very fun."**
- **Investigation (2026-08-11):** The fun part was the `?connect` degrees prototype
  (G3, PR #28, commit `54a42f9`). Options were archive-the-dig-as-a-mode vs full
  retirement. Full deletion chosen deliberately: **a half-retired game means
  maintaining two data pipelines** (project_state.md "Key decisions": "not
  archive-only, not co-equal").
- **Root cause / finding:** The site was rebuilt entirely around
  degrees-of-separation. Deleted: the dig client (`game.js`, `frame.js`, `theme.js`,
  `cipher.js`, `buff.js`, 21 puzzles + ~34 MB images), all of `server/`, and the
  whole crop-and-publish curation tool. Everything is recoverable from git.
- **Evidence:** rebuild commit `3da6a94` on the branch, rebase-merged to main as
  `72a0581` ("Game: rebuild the site around degrees-of-separation, retire the dig",
  368 files, +2,080/−13,703 — verified `git show 72a0581 --stat`); PR #29 merged
  2026-08-14 on the owner's explicit "merge" (launch recorded in `36c9e57`);
  project_state.md "What was deleted".
- **Status:** SETTLED (owner decision, executed and launched).
- **Do not** propose resurrecting the dig, a two-mode site, or "recovering" deleted
  dig files as a side quest.
- **Unless** the owner asks — git history holds it all if he ever does.

### 19. Per-challenge subgraph autocomplete leak

- **Symptom/Idea:** Ship each challenge with a small subgraph (the July `?connect`
  prototype's geodesic-ellipse design, ~4 KB gz median) and draw autocomplete from
  it — tiny payloads, no full-corpus download.
- **Investigation (July prototype → 2026-08-11 rebuild):** The prototype worked, but
  drawing autocomplete from the per-challenge subgraph means **the suggestion list IS
  the answer set** — typing a letter handed the player the legal hops. The rebuild
  inverted the design: ship the whole graph once, make **suggestions global and
  validation contextual**, so nothing about today's answer is in the shipped data —
  because the shipped data is everything.
- **Root cause / finding:** Measured, not assumed: the whole corpus, pruned +
  index-encoded, is **188 KB gz** (190 KB after the 2026-08-14 refresh) — *smaller*
  than the 212 KB gz `people-index.json` the old site already shipped to Movie Buff
  players, and cached after first play. Two prunes got it there: one-film people can
  never be a hop (67% dropped), and delta-hex index encoding.
- **Evidence:** prototype commit `54a42f9`; project_state.md payload table ("The
  decision that made it work") and its "Consequences" bullet naming the leak;
  CLAUDE.md "The one idea that makes it work"; `docs/graph.json` in-tree.
- **Status:** SETTLED-REJECTED design.
- **Do not** reintroduce per-challenge payloads "to save bytes" — the bytes argument
  was measured and lost, and the leak is structural: any challenge-scoped data that
  feeds autocomplete leaks the answer set.
- **Unless** the corpus grows past sensible budgets — and even then, solve the
  suggestion-vs-validation separation first; the leak, not the bytes, killed this.

### 20. Small-world near-miss worry — falsified by measurement, then shipped

- **Symptom/Idea:** Worry raised in the Comeback Loop plan: in a small-world graph,
  every wrong guess might be "one degree away", making near-miss temperature feedback
  meaningless noise.
- **Investigation (2026-08-14):** Measured **before building**, with the prediction
  written down before the script ran (the house predict-numbers-first discipline).
  6,800 sampled wrong guesses against the corpus: **d=1 27%, d=2 60%, d=3+ 15%.**
- **Root cause / finding:** The worry is false — the distance distribution has real
  spread, so temperature is informative. Shipped in Wave 2: `chain.js nearMiss`
  ("one degree away (a shared 2010 film)" / "two degrees off" / "stone cold").
- **Evidence:** `docs/chain.js` `nearMiss` (in-tree, tested in `chain.test.js`);
  Wave 2 commit `1ef3682` (branch twin `a1c4c12`); project_state.md Wave 2 record.
  The experiment script lived in the session scratchpad — the raw numbers are a
  **recorded account**; the shipped feature and suite are not.
- **Status:** FALSIFIED-AND-SHIPPED.
- **Do not** remove near-miss feedback on the "small-world makes it meaningless"
  argument — it was measured and it's wrong. Do not skip the predict-first step on
  the next graph-shaped hunch.
- **Unless** a corpus rebuild materially changes the graph's shape — then re-run the
  sampling before trusting the old distribution.

### 21. The "one-off" playtest verdict → the Comeback Loop

- **Symptom/Idea:** Owner playtest of the rebuilt game, 2026-08-14: "I like it, but
  it's missing something… feels like a one-off rather than
  I-need-to-come-back-and-play-this-again-asap."
- **Investigation (same day):** The verdict went through a 12-agent research workflow
  + 3 adversarial critics, merged with the owner's brief (Wordle is the model;
  beating-friends/route-comparison wanted; share-based social; NO accounts).
- **Root cause / finding:** **The game ended at the wrong moment.** Diagnosis, item
  by item: no countdown to tomorrow, no solution reveal (a loss paid off nothing),
  the player's own chain hidden at the end, share links unfurling bare (no
  OG/favicon), zero @keyframes anywhere, and a flat par mix (all 30 dailies par 2–3).
  Fix = the Comeback Loop, Waves 1–3, **built and launched the same day**: ritual end
  card + durable record + share overhaul + weekly difficulty arc (Wave 1); near-miss
  + juice pass + obscurity score (Wave 2); completion calendar + handicap + backup
  codes + curator's note (Wave 3). The fourth Wave 3 item — the soft-fail caddy — was
  **deliberately not built**: gated on measured DNF rates from real players (>~10%)
  plus owner sign-off, since it's a rules change.
- **Evidence:** main commits `c256b1c`+`88ed6bf` (Wave 1), `1ef3682` (Wave 2),
  `1bf5555` (Wave 3); PR #29 rebase-merged 2026-08-14; project_state.md plan + all
  three wave records (268 assertions green at session end).
- **Status:** FIXED. The transferable lesson: **the end card is the retention
  surface** — the moment after the last guess is where a daily game earns tomorrow's
  visit.
- **Do not** treat end-card work as optional polish, and do not build the caddy
  before its evidence gate fires.
- **Unless** real-player data contradicts the diagnosis (the first signal to watch:
  does anyone come back on day 3).

### 22. The Comeback Loop's KILLED list — three ideas with revival triggers

- **Symptom/Idea:** Three plausible-sounding features surfaced by the 2026-08-14
  research pass: spoiler-gated challenge links, a community-pulse Worker ("N% of
  players used this route today"), and accounts/leaderboards.
- **Root cause / finding:** All three killed in the plan, each with its reason
  recorded: **spoiler-gated challenge links** = a leaky funnel (the gate leaks and
  the friction kills the share);
  **community-pulse Worker** = needs a server AND a crowd, and the project just
  finished deleting its last server (Cloudflare fully torn down 2026-08-14) —
  revival trigger recorded: organic strangers sharing + a min-N gate + owner
  sign-off; **accounts/leaderboards** = the owner's explicit call — share-based
  social instead, which is why the share string's line-1 grammar is FROZEN
  (2026-08-14): accountless Discord-bot leagues parse it.
- **Evidence:** project_state.md "The Comeback Loop" KILLED paragraph (with the
  workflow run id); CLAUDE.md "Share grammar (FROZEN)".
- **Status:** SETTLED-REJECTED, each with an honest revival trigger on record.
- **Do not** re-pitch any of the three as a quick win, and never reformat share
  line 1 — line 1 may only ever gain content after the final `)`.
- **Unless** the recorded trigger fires: real organic sharing at scale (Worker),
  or the owner reopens accounts (his call alone).

### 23. The invite-button TDZ — a caught error hid a broken home card from verification

- **Symptom/Idea:** Launch-eve 2026-08-15: the live home card rendered "Couldn't load
  today's connection. Cannot access 'inviteFile' before initialization" for ~30 min
  after the mobile-share fix (PR #36) deployed. The owner caught it, not the checks.
- **Root cause / finding:** `boot()` is invoked at the TOP of `docs/app.js` (line ~46);
  PR #36 declared `let inviteFile` mid-module, so `renderHome()` hit the temporal dead
  zone. The throw was caught into the today-card's error handler — no console error —
  and the pre-merge browser check asserted the BUTTON under test, which worked (bound
  before the throw), while the card beside it was already broken.
- **Evidence:** hotfix PR #37 (`6370e99`, state hoisted to the module-state block);
  incident record in project_state.md 2026-08-15.
- **Status:** FIXED, rule adopted.
- **Do not** declare module state below the `boot()` call in app.js, and do not sign
  off a browser verification that only inspects the feature under change — **assert the
  page's primary content too** (home: the today-card; play: the chain; end: the card).
- **Unless** app.js's boot-at-top structure changes (then re-derive the rule).

## Patterns across entries

These recur; recognize them before starting new work (the discipline itself is
formalized in **degreesoffilm-research-methodology**):

- **Measure before building** (entries 1, 3, 19, 20): the project's four best calls
  were measurements. The two flagship examples are now rebuild-era: the
  whole-corpus-vs-subgraph decision was settled by a size table (188 KB gz for
  everything vs 212 KB the old site already shipped — entry 19), and the small-world
  worry died to 6,800 samples with the prediction written first (entry 20). Contrast
  entry 3, where the missing measurement cost two merged PRs.
- **Data reality beats the plan** (entries 1, 3): both big dig-era reversals came
  from the *shape of TMDB's actual data*, not code defects. Sample first.
- **Owner verdict is data** (entries 18, 21): both era-defining pivots were
  one-sentence playtest verdicts ("not fun"; "feels like a one-off") translated into
  mechanisms — deletion and the Comeback Loop — not argued with.
- **The end card is the retention surface** (entry 21): a daily game earns tomorrow's
  visit in the moment after the last guess.
- **Author-ahead** (entries 5, 21): defer the mechanic, keep authoring what it needs
  (reveal tiers then; `count_routes` in the sidecar now) so shipping needs no
  backfill.
- **Silent-overwrite-by-key** (entry 2): keyed upserts destroy without warning. Ask
  "what happens on key collision?" before writing to any keyed store.
- **Pin-with-rationale** (entry 4): every non-obvious pin gets its reason in the
  commit and a comment. (Applies today to frozen contracts too — the share line-1
  freeze carries its rationale in CLAUDE.md.)
- **Verification-environment traps** (entries 7, 8): the costliest debugging wastes
  were the *environment* (stale cache — still live) and the *blast radius of
  verification itself*. Discriminate environment-vs-code first; know the restore
  command before mutating.
- **Investigate-then-drop is a valid outcome** (entries 6, 22): a cheap investigation
  ending in "non-issue" or "killed, with a revival trigger" is a success — but only
  if it's written down (that's this file's job).

## Entry template (append new entries with this)

```markdown
### N. <Short title>

- **Symptom/Idea:** <what someone observed or proposed>
- **Investigation (<YYYY-MM-DD>):** <what was actually done to find out>
- **Root cause / finding:** <the mechanism, stated plainly>
- **Evidence:** <commit hash / PR # / file:line / doc § — each one personally
  verified; project_state-only stories labeled "recorded account">
- **Status:** SETTLED-REJECTED | FIXED | RULE-CREATED | PARKED | OPEN | SHIPPED |
  KILLED | FALSIFIED-AND-SHIPPED | OBE | MOOT-suffixed
- **Do not** <the imperative that saves the next session>
- **Unless** <the honest reopening condition — what NEW evidence would change this>
```

Where the raw sources live: `git log --oneline --all` + `git show <hash>` (commit
messages here are unusually narrative — read them in full; remember the repo
rebase-merges, so branch/main hash twins exist); `project_state.md` current + its git
history (`git log -p --follow -- project_state.md`) for recorded accounts; `CLAUDE.md`
for the settled shape of things; for PRs, `gh` is installed but **not logged in** —
auth per-command with a `GH_TOKEN` from the cached git credential (see
`agents/issue-tracker.md`). Concluded investigations MUST land an entry here — a
retirement without a written "why" will be re-fought.

## When NOT to use this skill

- Checking whether a change is allowed / how it must land →
  **degreesoffilm-change-control**.
- Understanding the current design and its invariants →
  **degreesoffilm-architecture-contract**.
- TMDB data model, matcher theory, project glossary →
  **degreesoffilm-domain-reference**.
- How to conduct a NEW investigation properly →
  **degreesoffilm-research-methodology** (and **degreesoffilm-proof-and-analysis-toolkit**
  for the proof recipes themselves).
- What evidence a change needs before landing → **degreesoffilm-validation-and-qa**.
- Public claims, TMDB terms, positioning vs other daily games →
  **degreesoffilm-external-positioning**.
- What to build next / research-grade ideas → **degreesoffilm-research-frontier**.
- Session handoffs, decision records, commit wording →
  **degreesoffilm-docs-and-writing**.

## Reusing this pattern beyond this project

The transferable template: a single "settled battles" index + uniform
symptom→cause→evidence→status entries, with an honest **Unless** clause per entry and
a hard rule that every concluded investigation appends an entry. When a system is
deleted wholesale (as the dig was), entries about it go **MOOT, not deleted** — the
inventory dies, the lesson transfers. The project-specific payload does not transfer;
the format, the status vocabulary, and the "recorded account" labeling discipline do.

## Provenance and maintenance

- **Written:** 2026-07-03 against dig-era HEAD `10668ca`. **Re-verified and extended
  2026-08-14** (post-rebuild, post-launch) against HEAD `71454d3` on branch
  `claude/project-state-review-0347aa`: entries 1–17 re-statused for the rebuild
  (MOOT where the tooling died, STILL LIVE where it didn't), entries 18–22 added.
- **How verified (2026-08-14 pass):** every cited hash re-checked via
  `git log --oneline <hash>` (all present, including both members of each
  rebase-merge twin pair: `3da6a94`/`72a0581`, `dcafaac`/`1bf5555`,
  `a1c4c12`/`1ef3682`); the rebuild's stat re-read via `git show 72a0581 --stat`
  (368 files, +2,080/−13,703); current-tree facts grepped directly (`nearMiss` in
  `docs/chain.js`, `recordArchive` in `docs/app.js`/`docs/stats.js`, `obscurity` in
  `docs/solve.js`, `note_violations` in `curation/challenge_gen.py`, QUOTES absent
  from `docs/app.js`, `curation/` stdlib-only with no `requirements.txt`);
  project_state.md and CLAUDE.md read in full. `gh` was unauthenticated this pass —
  PR-body facts carry from the 2026-07-03 verification; PR #29's merge is confirmed
  by project_state.md + the launch commit `36c9e57` on main.
- **Drift checks:** entry 8 → serve docs/ on a fresh port when in doubt; entry 10 →
  `grep -n "recordArchive" docs/app.js`; entry 11 → `python curation/challenge_gen.py
  --check` (enforces the note rule); entry 20 → `grep -n "nearMiss" docs/chain.js`;
  entry 22 → CLAUDE.md still says line 1 is FROZEN.
- **Maintenance:** when an OPEN entry gets fixed, update its Status with the landing
  hash in the same session. When any investigation concludes anywhere in this repo,
  append an entry using the template above and refresh this section's date. When a
  system is deleted, mark its entries MOOT — never delete them.
