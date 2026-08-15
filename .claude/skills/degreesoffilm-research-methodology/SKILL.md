---
name: degreesoffilm-research-methodology
description: >-
  The discipline that turns a hunch into an accepted result in the Degrees of Film repo. Load
  this when you (or the user) say "I have an idea", "I think X would be better", "would it work
  if…", or "is X possible?"; when designing an experiment or de-risk probe; when deciding
  whether evidence is sufficient to accept a conclusion ("how do we know when we're done
  investigating?"); when proposing a change based on a theory rather than a bug; when retiring
  or rejecting an idea so it stays retired; or when an idea needs to be parked, gated
  (static-shaped vs owner-sign-off vs evidence-gated), sliced, or promoted. Covers the evidence
  bar, predict-numbers-before-running, the idea lifecycle (parking lot → de-risk → slice →
  test-first → ship or documented retirement), where good ideas came from here, experiment
  hygiene, and the hypothesis-card template.
---

# Degrees of Film — research methodology

How a hunch becomes an accepted result in THIS repo — or an honestly retired one. Everything
below is codified from what this project actually did, with the receipts cited. It is not a
textbook import: every rule has a named episode where following it paid or skipping it cost.

Two sentences of context (full picture in `degreesoffilm-architecture-contract`): the game is
a daily degrees-of-separation puzzle — connect two films through the people who made them —
served as a pure static site (`docs/` on GitHub Pages, live since 2026-08-14) with a private
stdlib-Python curation pipeline (`curation/`) and no server at all. The rebuild and the
Comeback Loop that launched it are the methodology's freshest receipts.

## 1. The evidence bar

**A conclusion is accepted when ONE mechanism explains ALL observations — including the
negative ones.** A theory that only explains why your idea would be nice is a hunch. A theory
that also explains the failures, absences, and weird edges you observed is a result.

Worked example — the owner-playtest diagnosis (2026-08-14). The verdict was "I like it, but
it's missing something… feels like a one-off rather than
I-need-to-come-back-and-play-this-again-asap." The accepted mechanism: **the game ends at the
wrong moment.**

| Observation | Explained by the accepted mechanism? |
|---|---|
| "Fun but a one-off" despite liking the core mechanic | Yes — the loop was broken, not the rules |
| End of a run: no countdown, no solution reveal, own chain hidden | Yes — the end card gave nothing to return for or compare |
| Share link unfurled bare; zero `@keyframes`; every scheduled par was 2–3 | Yes — nothing to brag with, no texture, no weekly rhythm |
| The playtest did NOT fault the matcher or the ruleset | Yes — and this negative kept rules changes correctly out of scope |

One mechanism explains every row, including what *didn't* go wrong. Evidence: the verdict,
diagnosis, and symptom list recorded verbatim in `project_state.md` (2026-08-14 evening
session record); the resulting Comeback Loop plan shipped as three waves the same day
(commits `c256b1c`, `1ef3682`, `1bf5555`) and merged live in PR #29.

**The adversarial-refutation pass.** Before writing ACCEPTED on any conclusion, it must
survive one attempted refutation:

- **Multi-agent session:** assign a red-team reviewer with the explicit brief "find an
  observation this mechanism does NOT explain, or a second mechanism that explains the same
  data." The Comeback Loop plan did exactly this — 3 adversarial critics ran against the
  12-agent research output; what survived became the plan, and what didn't went to the
  KILLED list with the why (see §3).
- **Solo:** write the strongest counter-argument yourself, in writing, and answer it in
  writing. "Could this be a cache artifact / a second cause / a coincidence of small N?"

A claim that has survived no attempted refutation is a **draft**, not a result. This is the
same bar `degreesoffilm-failure-archaeology` enforces structurally: entries require
personally-verified Evidence AND an "Unless" line (the reopening condition) — you cannot fill
in "Unless" without having thought about what would refute you.

Standing discriminator — environment vs code: the Fastly edge in front of GitHub Pages can
serve a stale `challenges.json`, which reproduces "my content push didn't work" perfectly.
Verify against `raw.githubusercontent.com` before concluding anything about the code
(recorded in `project_state.md`).

## 2. Hypothesis predicts the numbers — BEFORE running

Write down what you expect to observe, then run. If you run first, whatever appears will look
like confirmation — you will rationalize it. The written prediction is what makes the result
falsifiable.

**Worked example A — the small-world experiment (2026-08-14).** Wave 2's near-miss feature
("one degree away" temperature on a burned guess) carried a named risk, written into the plan
before any code: *small-world* — if nearly every wrong guess sits one degree from the goal,
temperature is one bucket and the feature is noise. The prediction was written before the
script ran; the measurement was 6,800 sampled distances: **d=1 27%, d=2 60%, d=3+ 15%**. The
worry was FALSIFIED by the numbers, and `chain.js nearMiss` shipped the same day (commit
`1ef3682`). The probe script never entered the repo — it lived in the session scratchpad;
only the prediction, the numbers, and the verdict were recorded (`project_state.md`, Wave 2
record). Had the distribution come back all-d=1, the feature died for the cost of one script.

**Worked example B — measure before build: the corpus-size decision.** The architecture
question "ship the whole graph, or a subgraph per challenge?" was answered by measurement,
not taste (table preserved in `project_state.md`, "The decision that made it work"):

| payload | raw | gzip |
|---|---|---|
| Whole corpus, pruned + index-encoded (`docs/graph.json`) | 424 KB | **188 KB** |
| …vs the `people-index.json` the old site already shipped | 478 KB | 212 KB |
| All 30 then-scheduled dailies (`docs/challenges.json`) | 1.9 KB | **0.5 KB** |

The whole pruned corpus cost *less* than a file the old site already served — so ship
everything once. The July per-challenge-subgraph prototype was abandoned with a second,
independent nail: its autocomplete drew from the subgraph, which handed the player the
answer. (Post-refresh the corpus is 190 KB gz; the decision-time numbers above are the ones
that decided it.)

**The anti-pattern, by name: run-first-rationalize-later.** Running the probe with no written
prediction, then declaring whatever came out "about what we expected." Without the written
small-world prediction, "27% at d=1" could have been shrugged either way.

Minimum discipline for any probe: **one sentence of prediction and one named falsifier,
written before the first command runs.** Use the hypothesis card in §6.

*Historical (dig era, compressed):* the same rule's original receipts were the
`validate_ladder.py` throwaway that falsified popularity-sorted credit ladders before any
tooling was built on them, and the character-stills feature that was built WITHOUT the
one-hour probe that would have killed it — both chronicled in
`degreesoffilm-failure-archaeology`.

## 3. The idea lifecycle HERE

```
                     hunch / "I think X would be better"
                                   |
                                   v
              project_state.md entry (open items / plan), WITH its gate:
        static-shaped (almost everything — the corpus makes features thin)
        | owner-sign-off (rules changes, player-facing rituals)
        | evidence-gated (needs measured data from real players)
                                   |
                                   v
              DE-RISK: the cheapest experiment that could KILL it
              (scratchpad script, or a pure investigation)
                   |                              |
              survives                        dies here
                   |                              |
                   v                              v
         smallest buildable slice        record the why (cheap!)
                   |                              |
                   v                              v
         test-first build                DOCUMENTED RETIREMENT
    (matcher contract rule)         (KILLED line / failure-archaeology
                   |                 entry: mechanism + revival trigger)
                   v
   ship via degreesoffilm-change-control → record in project_state.md
```

**Each stage, with its receipt:**

1. **Parking lot with a gate.** Parked ideas live in `project_state.md` — the open-items
   list and the plan's wave structure. The old DESIGN.md §6 v2/v3 parking lot is dead
   (DESIGN.md is historical; there is no server track). The gates now, with live examples:
   - *Static-shaped:* role glyphs in the share (parked: needs a harvest schema change +
     corpus rebuild), PWA manifest, in-game rules access from `?play` — all thin layers on
     the shipped corpus, parked only for priority.
   - *Owner-sign-off:* anything that changes the ruleset or a player-facing ritual — the
     rebuild itself, merge-to-launch, and the caddy below all waited on an explicit owner
     call.
   - *Evidence-gated:* the **soft-fail caddy** — the only unbuilt Comeback Loop item, and
     deliberately so: its own gate requires measured DNF rates from real players (<~10% →
     skip forever) PLUS owner sign-off (it is a rules change). No players yet, so it was
     NOT built — the plan's discipline applied to the plan's own last item.
2. **De-risk: the cheapest killing experiment.** The small-world probe (§2A) is the current
   canonical shape: named risk in the plan → scratchpad script → measured → feature shipped
   or died. Pure investigations (read the code, no script) count too.
3. **Smallest buildable slice.** The Comeback Loop shipped as three planned waves, each a
   coherent playable increment committed and browser-verified before the next began
   (`c256b1c` → `1ef3682` → `1bf5555`, all 2026-08-14).
4. **Test-first build.** For the matcher this is a hard contract rule (CLAUDE.md): **"Add a
   case to `match.cases.js` before touching the algorithm."** The suites (9 files, 268
   assertions at last count) are the acceptance floor for every slice. General form in
   `degreesoffilm-validation-and-qa`.
5. **Ship via `degreesoffilm-change-control`; record in `project_state.md`.**

**OR: documented retirement.** The Comeback Loop's KILLED list is the current canonical
case — three ideas retired in writing, each with its mechanism and (where honest) a revival
trigger, recorded in `project_state.md`:

- **Spoiler-gated challenge links** — killed as a leaky funnel.
- **Community-pulse Worker** — needs a server AND a crowd; revival trigger written down:
  organic strangers sharing + a min-N gate + owner sign-off.
- **Accounts/leaderboards** — owner's call; share-based social instead.

**The rule: retirement without a written why is a future re-fight.** Durable retirements get
a `degreesoffilm-failure-archaeology` entry (Symptom → Root cause → Evidence → Status →
Do-not → Unless); the "Unless"/revival-trigger line matters as much as the "Do not" — it
keeps retirement honest instead of dogmatic.

## 4. Where good ideas came from HERE (verified provenance)

| Source | Episode (verified) | Yield |
|---|---|---|
| **Owner playtest of the real artifact** | The 2026-08-14 verdict ("fun but a one-off") — one honest sentence from actually playing | The diagnosis, the plan, and the entire launch feature set |
| **A verdict put through a research workflow** | 12-agent research run + 3 adversarial critics against the owner's brief (Wordle is the model; no accounts) | The Comeback Loop plan: 3 waves built same day + 3 documented kills; critics also re-ranked priorities (difficulty arc above all but the end card) |
| **Measurement** | The corpus-size table (§2B) | The one idea that makes the game work: ship the whole graph once |
| **A named risk, measured** | The small-world probe (§2A) | Near-miss feedback shipped with confidence instead of vibes |

**The lesson: ideas here come from *contact with the artifact*, not brainstorming.** Play the
game. Put verdicts — even vague ones — through diagnosis before acting: "missing something"
became "ends at the wrong moment" became fourteen concrete shipped changes. And when a plan
names a risk, measure it before building on it.

*Historical (dig era, compressed):* the same pattern held before the rebuild — one playtest
yielded a five-PR UX batch; curation-tool friction yielded six features; spec-time
author-ahead made a v2 feature cost only its wiring. Chronicle in
`degreesoffilm-failure-archaeology`.

## 5. Experiment hygiene

1. **Predictions in writing first** (§2). For anything multi-step, a hypothesis card (§6) in
   `project_state.md` before the first command.
2. **Name the falsifier before starting.** One sentence: "this idea is dead if we observe X."
   The small-world probe had one and could have died by it. If you cannot name a falsifier,
   you are not running an experiment; you are collecting decoration for a decision already
   made.
3. **Experiments must be git-reversible by construction.** Everything the curation pipeline
   writes (`docs/graph.json`, `docs/challenges.json`) is git-tracked; confirm the tree is
   clean before a mutating run so `git checkout --` restores it. The gitignored curation
   assets (`films_cache.jsonl`, `people_harvest_cache.jsonl`, `challenge_solutions.json`)
   are append-only and canonical in the MAIN checkout's `curation/` — a worktree doesn't
   inherit them; copy in before content ops, copy back after (`project_state.md`
   Workflow/gotchas). Never read or copy `curation/.env` anywhere.
4. **Probe scripts stay out of the repo.** The current shape: write them in the session
   scratchpad, record the prediction + numbers + verdict in `project_state.md`, let the
   script go (the small-world experiment, §2A). If a probe proves durably useful, promote it
   deliberately into a tested suite file — don't let it drift into the tree.
5. **Verify claims against the shipped artifacts.** `python curation/challenge_gen.py
   --check` re-derives every published par by BFS and enforces the curator's-note rule;
   browser-verify on `:8010`. A conclusion about the game that hasn't touched the game is a
   draft.

## 6. The hypothesis card

Copy this template. Fill the top half BEFORE running anything.

```markdown
### Hypothesis: <one-line claim>
- **Claim:** <the mechanism or improvement, stated so it can be wrong>
- **Predicted numbers (written before running):** <what you expect to observe —
  counts, distributions, thresholds. "d=1 under 40% of sampled pairs" —
  not "distances look varied">
- **Experiment (exact commands):** <copy-pasteable; read-only or with the restore
  command named; scratchpad script path if any>
- **Falsifier:** <the specific observation that kills the claim>
- **Status:** DRAFT → TESTED → ACCEPTED | RETIRED (with the why, one line)
- **Where recorded:** <project_state.md section / failure-archaeology entry / skill updated>
```

Status discipline: a card is DRAFT until run, TESTED until it survives the adversarial-
refutation pass (§1), and only then ACCEPTED. RETIRED requires the why.

**Routing accepted and retired results:**

| Outcome | Route |
|---|---|
| Accepted → code/content change | `degreesoffilm-change-control` (classification, gates, landing mode) |
| Accepted → decision of record | Decision-record template in `degreesoffilm-docs-and-writing` — record the REJECTED alternative alongside the fix (the subgraph prototype's why is preserved next to the corpus decision; do likewise) |
| Retired / dropped / dead end | KILLED line in `project_state.md`, then a `degreesoffilm-failure-archaeology` entry (with "Unless") — the 2026-08 KILLED list is recorded there as entry 22 |
| Idea survives but is frontier-sized | `degreesoffilm-research-frontier`'s tracks and falsifiable milestones |
| Idea needs a server or player data | Gate it explicitly (evidence-gated / owner-sign-off) in `project_state.md`, like the soft-fail caddy — there is no server track to punt to anymore |
| Live cards in progress | `project_state.md` (the session handoff — see `degreesoffilm-docs-and-writing`) |

## When NOT to use this skill

- **Checking whether an idea was already tried and killed** → `degreesoffilm-failure-archaeology`
  (settled-battles index — check it BEFORE writing a hypothesis card).
- **Running/landing an accepted change** → `degreesoffilm-change-control`.
- **What tests to run / how to add one / the test-evidence bar for code changes** →
  `degreesoffilm-validation-and-qa` (this skill's evidence bar is about *conclusions*; that
  one's is about *changes*).
- **Analysis recipes (how to actually construct the proof/experiment)** →
  `degreesoffilm-proof-and-analysis-toolkit`; **which frontier problem to pick** →
  `degreesoffilm-research-frontier`.
- **Where to write the record** → `degreesoffilm-docs-and-writing`.
- **Facts about the architecture/data contracts** → `degreesoffilm-architecture-contract`;
  **domain terms and matcher behavior** → `degreesoffilm-domain-reference`.
- **Evidence bar for public claims (announcements, comparisons)** →
  `degreesoffilm-external-positioning`.

## Reusing this pattern beyond this project

The transferable core: (1) one-mechanism-explains-all-observations-including-negatives as the
acceptance bar, plus a mandatory attempted refutation; (2) written prediction + named
falsifier before any probe runs; (3) a parked-idea queue where every entry carries its gate
(here: static-shaped / owner-sign-off / evidence-gated); (4) the cheapest killing experiment
before building; (5) retirement is only real when the why — and the revival trigger — is
written where the next person will look. Project-specific and NOT transferable as-is: the
gate definitions, the cache-copying ritual, and the sibling skill names.

## Provenance and maintenance

Written 2026-07-03; **re-verified and rewritten 2026-08-14 after the degrees rebuild** (the
dig game and its tooling were deleted; dig-era examples compressed to labeled historical
mentions). Verified that day directly against the repo: the playtest verdict, diagnosis,
Comeback Loop plan (with the KILLED list and critic pass), Wave 1–3 records, small-world
numbers, corpus-size table, caddy gate, and parked follow-ups all read in
`project_state.md`; commits via `git show` (`72a0581` rebuild, `c256b1c`/`1ef3682`/`1bf5555`
waves, `71454d3` restock; PR #29 merged as `87699a9`→`ce6b4dd`); `chain.js nearMiss` and
`solve.js obscurity` located in source; the matcher contract rule read in CLAUDE.md. The
small-world probe script itself is a session-scratchpad artifact (not in the repo) — its
prediction-first protocol and numbers are the recorded account in `project_state.md`.

Re-verify one-liners (run from repo root):
- Small-world record: `grep -n "small-world" project_state.md`
- Corpus decision table: `grep -n "per-challenge subgraphs" project_state.md`
- Caddy gate: `grep -n "DNF" project_state.md`
- KILLED list + revival trigger: `grep -n "KILLED" project_state.md`
- Matcher contract rule: `grep -n "match.cases.js" CLAUDE.md`
- Near-miss shipped: `grep -n "nearMiss" docs/chain.js` and `git log --oneline --grep="Wave 2"`
- Dailies still verify: `python curation/challenge_gen.py --check`
