---
name: degreesoffilm-research-methodology
description: >-
  The discipline that turns a hunch into an accepted result in the Degrees of Film repo. Load
  this when you (or the user) say "I have an idea", "I think X would be better", "would it work
  if…", or "is X possible?"; when designing an experiment or de-risk probe; when deciding
  whether evidence is sufficient to accept a conclusion ("how do we know when we're done
  investigating?"); when proposing a change based on a theory rather than a bug; when retiring
  or rejecting an idea so it stays retired; or when an idea needs to be parked, gated (v2
  static vs v3 server), sliced, or promoted. Covers the evidence bar, predict-numbers-before-
  running, the idea lifecycle (parking lot → de-risk → slice → test-first → ship or documented
  retirement), where good ideas historically came from here, experiment hygiene, and the
  hypothesis-card template.
---

# Degrees of Film — research methodology

How a hunch becomes an accepted result in THIS repo — or an honestly retired one. Everything
below is codified from what this project actually did, with the receipts cited. It is not a
textbook import: every rule has a named episode where following it paid or skipping it cost.

Two sentences of context (full picture in `degreesoffilm-architecture-contract`): the project
is a daily film-guessing game with a private curation tool (`curation/`), a static site
(`docs/` on GitHub Pages, live), and no player backend. v1+v2 are complete and live; the
methodology below is what got them there.

## 1. The evidence bar

**A conclusion is accepted when ONE mechanism explains ALL observations — including the
negative ones.** A theory that only explains why your idea would be nice is a hunch. A theory
that also explains the failures, absences, and weird edges you observed is a result.

Worked example — the character-stills retirement (2026-07-01):

| Observation | Explained by the accepted mechanism? |
|---|---|
| The manual per-rung still picker felt useless in real use | Yes — there was almost nothing worth picking |
| The few candidate images that DID appear were shared across the whole cast | Yes — they were generic backdrops tagged to everyone, not in-character stills |
| Crew rungs never had candidates at all | Yes — nobody tags crew into stills |

One mechanism — **"TMDB person-tagged images are sparse, mostly generic backdrops shared
across the cast"** — explains every row, including the negatives. That is when the feature was
retired, not before. Evidence: removal commit `3e2cfbb` ("removes the sparse/unreliable
character-still path entirely"); the mechanism recorded in `project_state.md` Key decisions
("TMDB tagged images are too sparse — mostly generic backdrops shared across the cast");
full arc in `degreesoffilm-failure-archaeology` entry 3.

**The adversarial-refutation pass.** Before writing ACCEPTED on any conclusion, it must
survive one attempted refutation:

- **Multi-agent session:** assign one agent as red-team reviewer with the explicit brief
  "find an observation this mechanism does NOT explain, or a second mechanism that explains
  the same data."
- **Solo:** write the strongest counter-argument yourself, in writing, and answer it in
  writing. "Could this be a cache artifact / a second cause / a coincidence of small N?"

A claim that has survived no attempted refutation is a **draft**, not a result. This is the
same bar `degreesoffilm-failure-archaeology` enforces structurally: every entry requires
personally-verified Evidence AND an "Unless" line (the reopening condition) — you cannot fill
in "Unless" without having thought about what would refute you.

Anti-example this repo already paid for: discriminating environment from code. A stale
ES-module cache reproduces "my fix didn't work" perfectly; the accepted mechanism must explain
why a fresh port behaves differently before you conclude anything about the code (see
`degreesoffilm-debugging-playbook`, dev-cache trap).

## 2. Hypothesis predicts the numbers — BEFORE running

Write down what you expect to observe, then run. If you run first, whatever appears will look
like confirmation — you will rationalize it. The written prediction is what makes the result
falsifiable.

**Worked example A — the ladder validation (`curation/validate_ladder.py`, commit `45b4085`).**
The single riskiest assumption in the project ("does sorting credits by TMDB popularity
produce a sane famous→obscure ladder?") was tested with a throwaway script whose pass/fail
criterion is stated in its own docstring and printed at run time, before any query executes:

> "If the lead actors and director sit near the top and it descends gracefully into obscure
> crew, the core premise holds…" / "EYEBALL TEST: do recognizable stars + the director sit at
> the top, descending smoothly into obscure crew? Watch for anyone wildly out of place."

The prediction failed, and the falsifying observation was **specific, not vibes**: popularity
sort buried Heath Ledger's Joker at rung 13 and sank Tommy Lee Jones below a one-scene bit
player — because TMDB `popularity` is a rolling/current metric, not fame-for-this-film.
Recorded with the rejected alternative in `DESIGN.md` §5 Phase 2 de-risk item. The script even
prints ladder [A] (popularity) next to ladder [B] (billing order) so the fix was validated in
the same run as the falsification. The adopted ordering (billing order, director early,
technical crew deepest) is now the shipped rule.

**Worked example B — the scoring curve.** `docs/game.js` `scoreForRung(n) = n +
min(max(n−5,0),5)` was derived from the formula first, and the full expected sequence is
asserted as a literal in `game.test.js` (lines 11–12, as of 2026-07-03):

```js
const curve = [1,2,3,4,5,6,7,8,9,10,11,12].map(scoreForRung);
check('score curve rungs 1-12', curve, [1,2,3,4,5,7,9,11,13,15,16,17]);
```

The predicted numbers exist in the test file independent of the implementation — if someone
"simplifies" the formula, the prediction catches it.

**The anti-pattern, by name: run-first-rationalize-later.** Running the probe with no written
prediction, then declaring whatever came out "about what we expected." If validate_ladder had
been run without the docstring criterion, "Joker at rung 13" could have been shrugged into
"popularity is roughly fame, ship it" — and the core game mechanic would be broken today.

Minimum discipline for any probe: **one sentence of prediction and one named falsifier,
written before the first command runs.** Use the hypothesis card in §6.

## 3. The idea lifecycle HERE

```
                         hunch / "I think X would be better"
                                       |
                                       v
                    DESIGN.md §6 parking-lot entry, WITH its gate
                    (v2 = stays static | v3 = needs the server move)
                                       |
                                       v
                  DE-RISK: the cheapest experiment that could KILL it
                  (throwaway script, or a pure investigation)
                       |                              |
                  survives                        dies here
                       |                              |
                       v                              v
             smallest buildable slice        record the why (cheap!)
                       |                    e.g. "exclude scheduled":
                       v                    DROPPED as a non-issue
             test-first build                         |
        (matcher contract rule)                       |
                       |                              |
                       v                              v
     ship via degreesoffilm-change-control    DOCUMENTED RETIREMENT
                       |                    (failure-archaeology entry:
                       v                     mechanism + evidence + Unless)
        record in project_state.md
```

**Each stage, with its receipt:**

1. **Parking lot with a gate.** Ideas enter `DESIGN.md` §6 tagged v2 (no architecture change)
   or v3 (needs the backend). The gate is load-bearing: "The dividing line is the server move"
   (§6 preamble). Movie Buff sits in v3 explicitly because "a live TMDB call from the browser
   would expose the API key… This is the feature that triggers the server move." Gates can be
   revised by analysis: Auto-crop arrived mid-session as a question, was initially classed v3,
   reclassified v2 after a feasibility look (Pillow-only, no server), and shipped the same day
   (commit `7957b19`; its project_state diff records "was queued as v3, reclassified v2 and
   built").
2. **De-risk: the cheapest killing experiment.** Two verified shapes:
   - *Throwaway script:* `curation/validate_ladder.py` (§2 above) — one script instead of a
     whole curation tool built on a false premise. Its own header says THROWAWAY.
   - *Pure investigation, no code:* "Randomize/Discover should exclude scheduled-but-unpublished
     films" was queued as a follow-up, investigated, and **DROPPED as a non-issue** — the ledger
     already excludes every approved film immediately and locally; the gap didn't exist.
     Recorded verbatim in project_state at the time (`git show 388e645:project_state.md`,
     lines 36–37: "DROPPED as a non-issue (investigated: …there's no such gap)"). Total cost:
     one reading of `ledger.py`/`publish.py`. That is what a good death looks like.
3. **Smallest buildable slice.** The reveal mechanic shipped as ONE PR (#18 → rebase-merged
   `995c01e`) because the expensive part (3 crop tiers) had been authored ahead since Phase 2 —
   the slice was pure client wiring (see §4, author-ahead).
4. **Test-first build.** For the matcher this is a hard contract rule (CLAUDE.md): "match.test.js
   is the contract… **Add a case there before touching the algorithm.**" The scoring curve
   follows the same pattern (§2B). General form in `degreesoffilm-validation-and-qa`.
5. **Ship via `degreesoffilm-change-control`; record in `project_state.md`.**

**OR: documented retirement.** The character-stills arc is the canonical case AND the
canonical warning, because **it skipped step 2 and paid for it**:

- Parked at spec time with the risk already named in writing — `DESIGN.md` §6 UX-polish list:
  "**Bigger than it looks:** character-specific stills aren't reliably on TMDB, so the
  practical fallback is the person's profile photo."
- Built anyway, in full, WITHOUT first probing tagged-image coverage: PR #12 (client + schema)
  and PR #13 (curation authoring + picker UI), both merged 2026-07-01 ~14:10Z.
- Data reality killed it the same day in real use (mechanism in §1); the manual pass was
  parked ("too much work" — recorded account), crew then cast were backfilled with automatic
  headshots (PRs #14/#15, commits `7b98546`/`7a7acd3`), and the picker was removed that
  evening (`3e2cfbb`, 19:00 −0500).
- A one-hour de-risk probe — "pull tagged images for 3 films' casts, count real in-character
  stills" — would have killed it for ~1% of the cost. The spec had literally already written
  the hypothesis; nobody ran the killing experiment. **Don't idealize the lifecycle: this
  project skipped a step once, and that skip is the strongest lesson in this file.**
- What was done RIGHT: the retirement was documented. The why lives in `project_state.md`
  (Key decisions), CLAUDE.md ("the manual picker was removed"), commit `3e2cfbb`'s body, and
  `degreesoffilm-failure-archaeology` entry 3 (with its "Unless" reopening condition).

**The rule: retirement without a written why is a future re-fight.** Every retired idea gets a
`degreesoffilm-failure-archaeology` entry (its Entry template enforces
Symptom → Investigation → Root cause → Evidence → Status → Do-not → Unless). The "Unless" line
matters as much as the "Do not": it keeps retirement honest instead of dogmatic.

## 4. Where good ideas came from HERE (verified provenance)

| Source | Episodes (verified) | Yield |
|---|---|---|
| **Playtesting the live game** | The 2026-06-30 playtest (so titled in `DESIGN.md` §6: "UX polish (from playtesting 2026-06-30)") produced the ENTIRE UX batch: PRs #7–#11 (tagline order, Skip tooltip, mode label, CTA tooltips, full-frame reveal). Opened 01:17–01:35Z, all five merged by 01:37Z — roughly 20 minutes from first PR to batch merged. | 5 shipped changes from one play session |
| **Curation pain (using the tool)** | Randomize (`afec469`), Auto-crop (`7957b19`, then slider `4496c81`, face-first `388e645`), Clear-scheduled (`125c4a5`, then frees-films `c0329a2`) — every one born from friction while actually publishing puzzles, all curation-only commits | 3 features + 3 refinements |
| **Spec-time foresight (author-ahead)** | 3 crop tiers were authored per puzzle from Phase 2 onward although v1 showed only tier 1; `DESIGN.md` §5 Phase 3 optional item says why: "Tiers are already authored by the cropper; this only wires them into the client." The reveal mechanic later shipped for the cost of the wiring (PR #18 → `995c01e`). | a v2 feature at client-wiring cost |
| **User questions** | "Is auto-crop possible?" arrived as a mid-session question; feasibility analysis reclassified it v3→v2 and it shipped the same day (`7957b19` project_state: "was queued as v3, reclassified v2 and built") | 1 shipped feature |

**The lesson: instrument the places ideas come from.** Ideas here did not come from
brainstorming sessions; they came from *contact with the artifact*. Play the game (a session
yielded 5 PRs). Use the curation tool for its real job (yielded 6 commits). When writing spec,
ask "what cheap thing can we author now that a future feature will need?" (yielded the reveal
mechanic). Treat user questions as candidate parking-lot entries with a gate to check.

## 5. Experiment hygiene

1. **Never experiment against live/committed data.** The incident: verifying the curation
   tool's edit/reschedule endpoint against real content moved committed puzzle 004's manifest
   entry — the LIVE-WRITE endpoints modify the actual `docs/puzzles/manifest.json` and
   `curation/used_films.json`; there is no sandbox mode. The standing restore plan (in
   `project_state.md` Workflow/gotchas, and know it BEFORE you start, not after):
   ```
   git checkout -- docs/puzzles/manifest.json curation/used_films.json
   ```
   Full account: `degreesoffilm-failure-archaeology` entry 7. Endpoint safety table
   (SAFE-READ-ONLY vs LIVE-WRITE): `degreesoffilm-diagnostics-and-tooling`.
2. **Experiments must be git-reversible by construction.** Clear-scheduled was *designed* so
   that everything it mutates is git-tracked ("manifest + ledger are git-tracked, so the whole
   action is reversible via `git checkout`" — `DESIGN.md` §6). Before any mutating experiment,
   confirm every file it can touch is committed and clean; if a probe would touch something
   git can't restore (or a live player's day — see the IMMUTABLE PAST rule in
   `degreesoffilm-change-control`), redesign the probe.
3. **Name the falsifier before starting.** One sentence: "this idea is dead if we observe X."
   validate_ladder's falsifier was "anyone wildly out of place" — and X arrived (Joker,
   rung 13). If you cannot name a falsifier, you are not running an experiment; you are
   collecting decoration for a decision already made.
4. **Label throwaway scripts THROWAWAY** so they don't calcify into load-bearing tools.
   `curation/validate_ladder.py` line 3: "Phase 2 de-risk script (THROWAWAY)". It still exists
   as *evidence* (DESIGN §5 cites it) but nothing imports it and no test depends on it. If a
   probe script turns out to be durably useful, promote it deliberately into
   `degreesoffilm-diagnostics-and-tooling`'s scripts with tests — don't let it drift there.
5. **Predictions in writing first** (§2). For anything multi-step, that means a hypothesis
   card (§6) in `project_state.md` before the first command.

## 6. The hypothesis card

Copy this template. Fill the top half BEFORE running anything.

```markdown
### Hypothesis: <one-line claim>
- **Claim:** <the mechanism or improvement, stated so it can be wrong>
- **Predicted numbers (written before running):** <what you expect to observe —
  counts, orderings, thresholds. "Leads + director in the top 4 rungs for all
  5 test films" — not "the ladder looks good">
- **Experiment (exact commands):** <copy-pasteable; read-only or with the restore
  command named; THROWAWAY script path if any>
- **Falsifier:** <the specific observation that kills the claim>
- **Status:** DRAFT → TESTED → ACCEPTED | RETIRED (with the why, one line)
- **Where recorded:** <project_state.md section / DESIGN §6 entry / skill updated>
```

Status discipline: a card is DRAFT until run, TESTED until it survives the adversarial-
refutation pass (§1), and only then ACCEPTED. RETIRED requires the why.

**Routing accepted and retired results:**

| Outcome | Route |
|---|---|
| Accepted → code/content change | `degreesoffilm-change-control` (classification, gates, landing mode) |
| Accepted → decision of record | Decision-record template in `degreesoffilm-docs-and-writing` (Decision/Date/Why/Rejected/Evidence) — note DESIGN §5's ladder entry records the REJECTED alternative alongside the fix; do likewise |
| Retired / dropped / dead end | Append a `degreesoffilm-failure-archaeology` entry (its template; include "Unless") |
| Idea survives but is frontier-sized (automated curation, novel modes, scale & integrity) | Start from `degreesoffilm-research-frontier`'s tracks and falsifiable milestones |
| Idea needs the backend | Gate it v3; if it's server-move-shaped, see `degreesoffilm-server-move-campaign` |
| Live cards in progress | `project_state.md` (the session handoff — see `degreesoffilm-docs-and-writing`) |

## When NOT to use this skill

- **Diagnosing a concrete failure** (something is broken, not hypothesized) →
  `degreesoffilm-debugging-playbook`.
- **Checking whether an idea was already tried and killed** → `degreesoffilm-failure-archaeology`
  (settled-battles index — check it BEFORE writing a hypothesis card).
- **Running/landing an accepted change** → `degreesoffilm-change-control`;
  publishing content → `degreesoffilm-run-and-operate`.
- **What tests to run / how to add one / the test-evidence bar for code changes** →
  `degreesoffilm-validation-and-qa` (this skill's evidence bar is about *conclusions*; that
  one's is about *changes*).
- **Measurement scripts and probes to run during an experiment** →
  `degreesoffilm-diagnostics-and-tooling`.
- **Analysis recipes (how to actually construct the proof/experiment)** →
  `degreesoffilm-proof-and-analysis-toolkit`; **which frontier problem to pick** →
  `degreesoffilm-research-frontier`.
- **Where to write the record** → `degreesoffilm-docs-and-writing`.
- **Facts about constants/architecture** → `degreesoffilm-config-and-flags` /
  `degreesoffilm-architecture-contract`.

## Reusing this pattern beyond this project

The transferable core: (1) one-mechanism-explains-all-observations-including-negatives as the
acceptance bar, plus a mandatory attempted refutation; (2) written prediction + named
falsifier before any probe runs; (3) a parked-idea queue where every entry carries its
architectural gate; (4) the cheapest killing experiment before building; (5) retirement is
only real when the why is written where the next person will look. Project-specific and NOT
transferable as-is: the v2/v3 gate definitions, the specific restore command, and the sibling
skill names.

## Provenance and maintenance

Written 2026-07-03. Every episode verified directly against the repo that day: commit bodies
via `git show` (`45b4085`, `3e2cfbb`, `7957b19`, `995c01e`, `7b98546`, `7a7acd3`, `afec469`,
`4496c81`, `388e645`, `125c4a5`, `c0329a2`), PR dates/branches via
`gh pr list --state all --json number,title,createdAt,mergedAt` (#7–#18), historical
project_state text via `git show 388e645:project_state.md` and `git show 7957b19` (the
"DROPPED as a non-issue" and "reclassified v2" lines), `curation/validate_ladder.py`
docstring/EYEBALL-TEST lines read in full, `game.test.js:11-12` and `DESIGN.md` §5–§6 read
directly. The "too much work" remark and the "is auto-crop possible?" question are recorded
accounts (session history relayed into docs), not repo artifacts — labeled as such above.

Re-verify one-liners (run from repo root):
- Ladder de-risk + criteria: `head -20 curation/validate_ladder.py` and `git show 45b4085 --stat`
- Character-stills arc: `git show 3e2cfbb --stat` and `gh pr view 13`
- Exclude-scheduled drop: `git show 388e645:project_state.md | grep -n -A1 "DROPPED"`
- Scoring-curve assertion: `grep -n "score curve" game.test.js`
- Matcher contract rule: `grep -n "Add a case there" CLAUDE.md`
- Playtest batch timing: `gh pr list --state all --json number,createdAt,mergedAt --limit 20`
- Restore command still documented: `grep -n "git checkout --" project_state.md`
