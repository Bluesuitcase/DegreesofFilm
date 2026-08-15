---
name: degreesoffilm-proof-and-analysis-toolkit
description: First-principles proof recipes for the Degrees of Film repo — how to PROVE a claim instead of assuming it. Load this when about to claim something works ("this approach will scale", "these two implementations match", "this fallback is safe"), when choosing between algorithms or approaches, when verifying parity between dual implementations (the JS/Python BFS pair), when assessing a security or robustness claim, when asked "how do I prove this?", or before building anything big on an untested assumption. Eight recipes, each with a worked example from this repo's real history — the corpus-size measurement that decided the rebuild, the small-world near-miss experiment, the match.cases.js matcher contract, the par --check invariant. NOT for running the existing suites (degreesoffilm-validation-and-qa), settled investigations (degreesoffilm-failure-archaeology), or the idea lifecycle (degreesoffilm-research-methodology).
---

# Proof and analysis toolkit

The house rule of this project: **prove it, don't just install it.** Every recipe below was
actually used here. Worked examples cite current artifacts where they exist; two are labeled
HISTORICAL (their code was deleted in the 2026-08 degrees rebuild — git has it). Numbers were
verified 2026-08-14 by running the shown commands — re-run them, don't trust prose, and treat
CLAUDE.md + the code as the source for any count or constant not shown being computed here.

Pick the recipe matching the claim you're about to make:

| You're about to claim… | Recipe |
|---|---|
| "This approach will work" (before building on it) | (a) Measure before building |
| "My algorithm change did what I intended and nothing else" | (b) Contract-first change |
| "These two implementations are equivalent" | (c) Cross-implementation parity |
| "This logic is correct" (but it's tangled in IO/DOM) | (d) Pure-core / IO-shell |
| "This client-side protection is good enough" | (e) Enumerable-domain analysis |
| "This generated data is correct and stays correct" | (f) Invariant at build + re-check |
| "This formula/distribution behaves the way we want" | (g) Predict numbers before running |
| "This degrades gracefully when X fails" | (h) Fallback-chain analysis |

---

## (a) Measure before building

**When to use:** before building anything expensive (a tool, a pipeline, a mode) whose value
rests on ONE unproven assumption or one decisive number. Find out the assumption is false —
or the number is fine — for the price of a script, not the price of the build.

**Steps:**
1. Name the single riskiest assumption (or the single decisive number) in one sentence.
2. Build the cheapest experiment that could kill it — stdlib only, no product code, marked
   THROWAWAY. It never has to be maintained; it has to be decisive.
3. State pass/fail criteria *before* running, so you can't rationalize the output afterward.
4. Choose inputs to break the assumption, not confirm it.
5. If comparing approaches, measure them side-by-side on identical inputs.
6. Record the verdict — with the numbers — where the next person will look
   (here: `project_state.md`), then build on it.

**Worked example — the corpus-size decision that made the rebuild work.** The degrees game
had two candidate architectures: ship a per-challenge subgraph (the July prototype) or ship
the entire pruned graph once. The decisive number was measured before committing (table in
`project_state.md`, "The decision that made it work"): the whole corpus, pruned and
index-encoded, gzipped to **188 KB — smaller than the 212 KB `people-index.json` the old
site already shipped** to Movie Buff players, while every daily after it costs ~50 bytes.
Two prunes got it there, both measured: people credited on only one film can never be a hop
(67% of all people — dropped), and delta-hex index encoding (both explained in
`curation/graph_build.py`'s docstring). The measurement didn't just pick the cheaper option —
it killed the subgraph scheme's fatal flaw for free: a per-challenge subgraph *is* a hint,
while the whole pool says nothing about today's answer (see recipe e). Current sizes: run
`python curation/graph_build.py --check` (2026-08-14: `3682 films / 9791 people / 429 KB
raw / 190 KB gz`).

**What would falsify it:** the corpus outgrowing the "cheaper than what we already shipped"
argument — re-measure with `--check` after any harvest; a size jump reopens the decision,
and belongs in `project_state.md`, not a silent shrug.

---

## (b) Contract-first algorithm change

**When to use:** changing any algorithm whose behavior is a *contract* with users — here,
above all, the fuzzy matcher (`docs/match.js`), which decides whether the game feels fair.

**Steps:**
1. Find the spec table — here `match.cases.js`, the matcher contract *as data*: literal
   `[guess, answers, expected, label]` rows, consumed by `match.test.js`.
2. **Add your new case to the table FIRST** and run it. It must FAIL (red). If it already
   passes, the behavior exists and you're done — don't touch the algorithm.
3. Make the smallest change that turns it green.
4. Re-run the whole table. Every pre-existing row must still pass — that's the proof the
   change did what was intended *and nothing else*. A row you have to "fix" is a behavior
   change you must justify explicitly.
5. Leave the new row in the table permanently. The table only grows.

**Worked example — `match.cases.js` + `docs/match.js`:** 25 rows as of 2026-08-14 (all green
under `node match.test.js`), encoding accepts (foreign titles, typos, surname-only "Bardem")
AND rejects ("Roger Moore" vs Roger Deakins — right first name, wrong surname). CLAUDE.md
makes the rule explicit: *add a case to `match.cases.js` before touching the algorithm.*
The mechanism behind one row, computed against the live module:

```
$ node -e "import('./docs/match.js').then(({normalize,levenshtein,maxDist})=>{ ... })"
"no country for old men" len 22   levenshtein("...old man") = 1   maxDist(22) = 4
```

"No Country for Old Man" is accepted because it is 1 edit from the 22-char normalized answer
and `maxDist(22) = floor(22*0.2) = 4`. If you widened `maxDist`, only the reject rows can
prove you didn't just accept everything — that's why the table carries both kinds.

**What would falsify it:** any pre-existing row flipping without an explicit, argued decision;
or shipping a matcher change with no new red-first row (then you have no evidence the change
did anything at all).

---

## (c) Cross-implementation parity

**When to use:** any behavior implemented twice (two languages, build-time + run-time, old +
new system) that must agree. Here: **BFS shortest-chain exists in both Python and JS** —
`curation/challenge_gen.py` (`bfs_path`/`degrees_between`) sets each daily's par at build,
and `docs/solve.js` (`shortestChain`/`degreesBetween`) recomputes routes in the player's
browser for the end-card reveal. If they disagreed, the end card would show a route that
contradicts par.

**Steps:**
1. Make both implementations consume the **same frozen data**, not equivalent-looking data.
   Here both run over the shipped `docs/graph.json`; par disagreement is directly visible.
2. Pin behavior with shared fixtures asserted on both sides — not "each side self-consistent",
   which each can pass alone even when they disagree with each other. Here `chain.test.js`
   and `solve.test.js` deliberately use the *same* tiny synthetic corpus (the Heat →
   Goodfellas graph — `solve.test.js` says so in its header) so the two JS engines are
   pinned to identical routes; and `challenge_gen.py --check` re-derives every published
   daily's par by BFS against the shipped corpus (64/64 OK, 2026-08-14).
3. Include at least one adversarial input (ties, unreachable pairs, non-ASCII names —
   whatever the domain's classic divergence is).

**Honest gap:** there is no frozen cross-*language* literal vector asserting a specific
Python-computed par inside a JS test; parity rests on the shared asset + `--check` + the
shared synthetic fixture. If the BFS pair ever drifts (e.g. different tie-breaks becoming
player-visible), add such a vector before debugging by eye.

**HISTORICAL (code deleted; git has it):** the dig-era cipher (`docs/cipher.js` ↔
`curation/cipher.py`) proved byte-parity with a frozen literal vector — one XOR+base64
payload produced by Python, asserted verbatim in both suites, plus a Unicode case. The
lesson transfers unchanged: a pinned literal catches drift in encoding, alphabet, key
bytes, and sentinel placement; a human diff of two implementations catches almost none.

**What would falsify it:** `--check` reporting a par the corpus no longer supports, or the
end-card reveal showing a chain shorter than par (that's the JS BFS beating the Python one —
a genuine parity bug, not a player achievement).

---

## (d) Pure-core / IO-shell decomposition as a provability strategy

**When to use:** whenever logic worth proving is entangled with pixels, files, network, or
DOM. Split it: a pure core you can prove with hand-checkable inputs, and a thin shell whose
IO you exercise separately.

**Steps:**
1. Extract the decision logic into functions of plain data with no IO/DOM imports.
2. Prove the core on an input small enough to compute BY HAND. Write the hand answer down
   first; then run the function and compare.
3. Keep the shell thin and parameterized (no hard-coded paths, no logic worth testing).

**Worked example — the entire `docs/` layer.** House law (CLAUDE.md "Layering"): `chain.js`,
`corpus.js`, `match.js`, `daily.js`, `stats.js`, `solve.js` are pure logic — no DOM anywhere;
`app.js` is DOM glue ONLY, with no rules in it. That single decision is why the whole game is
provable by plain-Node suites (`node match.test.js`, `daily`, `stats`, `corpus`, `chain`,
`solve` — no framework, no browser, no mocks) that import the real modules directly. The
hand-checkable-fixture discipline is visible in `solve.test.js`: a 5-film corpus whose two
par-2 routes you can verify by reading the cast strings, and an obscurity fixture whose
expected grades (0 / 77 / 38) were hand-computed through the blend before running.

**Worked example — `curation/graph_build.py`:** its docstring declares the split: *"Pure core
(no network, no IO): connector_ids / rank_people / encode_deltas / decode_deltas /
build_corpus / validate"* — the CLI is a thin reader/writer around them. Same shape in
`challenge_gen.py` (`adjacency`/`bfs_path`/`degrees_between`/`count_routes`/`note_violations`
pure; argparse shell). That's why the Python suites are stdlib-only and network-free.

**What would falsify it:** a core function growing an IO or DOM import (it can no longer be
proved on plain data), or rules logic appearing in `app.js` (it silently exits the tested
surface — the suites would stay green while the game changed).

---

## (e) Enumerable-domain security analysis

**When to use:** before trusting ANY client-side protection of secret values — hashing,
encryption, obfuscation. The question that decides it: **can an attacker enumerate the
plaintext space?** If yes, no client-side scheme survives, no matter how strong the cipher.

**Steps:**
1. Write down what's being protected and where every key/salt/secret physically lives.
2. If any secret ships to the client: dead on arrival — the attacker just runs your own
   decode. Stop here.
3. Even if the key were secret: characterize the plaintext domain. Finite and public
   (film titles, names, dates, IDs)? Then the attacker encodes every candidate with your
   deterministic scheme and compares against the shipped blob — an offline dictionary
   attack. This same argument kills "just hash the answers": hashing is deterministic too.
4. Conclude honestly: label the mechanism for what it is, and name the real fix — which may
   be a server, or may be **not having a secret at all**.

**Worked example — how the rebuild DISSOLVED the problem.** The dig-era game shipped its
answers to the client and tried to hide them (HISTORICAL: an XOR+base64 cipher whose key
shipped in `docs/cipher.js` — kill shot 1 — over a plaintext domain of public TMDB titles
and names — kill shot 2; the repo's own docstring called it "NOT security", and a
`/match` Worker was later built to hold answers server-side; all deleted, git has it).
The degrees rebuild ended the arms race by removing the secret: **ship everything, hide
nothing.** `docs/graph.json` is the entire pool; a daily is just `{start, goal, par}`
endpoints, which are the prompt, not the answer. Nothing about today's answer is in the
shipped data *because the shipped data is everything* — there is no blob to enumerate
against and no oracle to invert. Guess validation is client-side against the shipped graph,
and that's fine, because a "leak" would only reveal what every player is freely given. When
someone proposes protecting a client-held secret here again, first ask whether the design
can stop having one.

**What would falsify it:** a future feature reintroducing a per-day secret into shipped data
(e.g. a hint payload, a hidden solution). The moment it does, steps 1–3 apply in full, and
the answer will again be "a server or nothing" — see the enumeration argument above.

---

## (f) Invariant at build + independent re-check

**When to use:** generating data whose correctness depends on another artifact that can
change under it (here: dailies whose par depends on the corpus). Two layers, both cheap:
**assert the invariant at generation time** (a bad artifact is never written), and provide
an **independent re-check command** that re-derives the invariant from scratch (a later
change to the substrate is caught before it ships).

**The implementation, verified 2026-08-14:**
1. **At generation:** `challenge_gen.py` asserts `degrees_between(adj, a, b) == par` for
   every pair it writes (a literal `assert` in the picker loop), after already requiring
   BFS to find a path at exactly that par and `count_routes` > 1.
2. **Re-check, dailies:** `python curation/challenge_gen.py --check` re-derives EVERY
   published daily's par by BFS against the currently shipped corpus, confirms the cached
   `from`/`to` titles still match (ids are authoritative), and hard-enforces the curator's-
   note rule — a note may never name any possible closer nor anything on the sidecar chain
   (`par_closers` + `note_violations`). Output 2026-08-14: `64 dailies, 0 broken`.
3. **Re-check, corpus:** `python curation/graph_build.py --check` re-validates the shipped
   `docs/graph.json` (decode round-trip, structure, sizes) without rebuilding it.

The run-order rule in CLAUDE.md follows directly: after any corpus rebuild, run
`challenge_gen.py --check` — film ids are stable, but this is what catches a daily whose
endpoint fell out of the pool or whose par silently changed.

**HISTORICAL (code deleted; git has it):** the dig-era migration proved a different flavor —
*idempotence by construction*: an encode that no-ops on already-encoded input (sentinel
prefix outside the base64 alphabet = perfect discriminator) and a decode that passes
plaintext through, so re-running the migration on mixed data was safe by algebra, not by
runbook. Reach for that pattern for any future in-place migration: make the converted form
self-identifying, prove encode∘encode = encode and decode(plaintext) = plaintext in the
suite, then write the migration as a bare map.

**What would falsify it:** a generation path that writes without the assert, or a `--check`
run skipped after a corpus rebuild (the invariant then only *probably* holds — exactly the
state this recipe exists to forbid).

---

## (g) Predict numbers before running

**When to use:** any formula, threshold, curve, or distribution. Derive the expected values
by hand FIRST, write them down, then run. If you run first, you'll rationalize whatever
comes out — the prediction is the experiment's integrity.

**Steps:**
1. From the formula/spec — or from your stated worry — commit to concrete expected numbers
   in writing before executing anything.
2. Run the real code. Compare against the written-down values, not your memory.
3. Freeze the outcome where it governs a decision: as a literal test assertion, or as a
   recorded verdict in `project_state.md`.

**Worked example — the small-world near-miss experiment (Wave 2, 2026-08-14).** Before
building near-miss feedback (`chain.js nearMiss`: a burned guess reports "one degree away" /
"two degrees off" / "stone cold"), the worry was written down: in a small-world graph,
almost *everything* might be one degree away, making the feedback noise. The prediction was
committed before running; the throwaway script then sampled **6,800** wrong-hop cases
against the real corpus and measured **d=1 27%, d=2 60%, d=3+ 15%** — the worry was
FALSIFIED (d=1 is the *minority*), and the feature shipped. The verdict and numbers are
recorded in `project_state.md` (Wave 2 section); the discipline — prediction first, then
measurement, then ship-or-kill — is the point. Smaller everyday form: the hand-computed
obscurity grades frozen as literals in `solve.test.js` (hub → 0, floor → 77, pair → 38),
derived through the blend by hand before the function ran.

**What would falsify it:** an assertion edited to match new output without a derivation
showing why the new numbers are intended; or a "measured" claim with no written prediction
predating the run. Distribution changes are game-feel changes — route through
degreesoffilm-change-control.

---

## (h) Fallback-chain failure analysis

**When to use:** before claiming "it degrades gracefully". A fallback you haven't traced is
a hope, not a design. For each hop: name the **trigger**, verify the trigger is **actually
detectable in code** (cite the function), and test the **terminal state** — the chain's
floor is what users hit on the worst day.

**Steps:**
1. Enumerate the chain hop by hop, ending at the terminal state (which may be "give up
   loudly" — fine, if explicit).
2. For each hop, find the exact code that detects the trigger. If detection is missing, the
   "fallback" never fires — that's the bug this recipe exists to catch.
3. Test the terminal state directly, plus at least one mid-chain hop.

**Worked example 1 — guess resolution (`docs/corpus.js` `resolve`):**

| Hop | Trigger | Detection (verified in code) |
|---|---|---|
| Exact match among legal hops | normalized text in lookup ∩ `within` | `pick(lookup.get(g), within)` |
| → fuzzy/last-word in context | no exact contextual hit | `fuzzy(..., {lastToken:'any'})` — a dozen candidates, "Bardem" is unambiguous |
| → exact match globally | not a legal hop | `pick(lookup.get(g), null)` → `scope:'elsewhere'` |
| → fuzzy/last-word globally | no global exact | `{lastToken:'unique'}` — `lastTokenMatch` returns −1 on a second match ("ambiguous surname: refuse to guess") |
| → null | nothing in the pool | `resolve` returns null → the `unrecognized` verdict |

The floor is deliberate game design: an unrecognized name is FREE (no burned attempt —
CLAUDE.md: "punishing spelling makes the game feel like a spelling test"), and the
refuse-to-guess branch is why "smith" doesn't silently resolve to whichever Smith ranks
highest. Contextual and global behavior are both pinned in `corpus.test.js` (35 green).

**Worked example 2 — par step-down in `challenge_gen.py`:** a par-4 Saturday the popular
pool can't satisfy steps down (4 → 3 → 2) rather than aborting the whole run — trigger:
`pick_pair` returns `None`; detection: the explicit `while picked is None ... par -= 1`
loop, which prints each step-down to stderr; terminal state: a hard `return 1` with
actionable guidance (`try a larger --top or fewer --days`). Every hop is visible in the
run's output — a silent step-down would be a difficulty-arc bug.

**What would falsify it:** a new hop added without a detectable trigger, or a terminal
state that fails silently (a swallowed `None`, a step-down that doesn't print) instead of
an explicit floor.

---

## When NOT to use this skill

- Running/choosing the existing test suites, coverage gaps, how to add a test →
  **degreesoffilm-validation-and-qa**.
- "Was this already investigated/rejected?" (don't re-fight settled battles) →
  **degreesoffilm-failure-archaeology**.
- The full idea lifecycle (parking lot → de-risk → slice → ship) and experiment hygiene →
  **degreesoffilm-research-methodology** (this skill supplies its proof techniques).
- What to build next / research-grade ambitions → **degreesoffilm-research-frontier**.
- Which zone/module a change belongs in → **degreesoffilm-architecture-contract**.
- Landing a change once proven → **degreesoffilm-change-control**.
- Recording the verdict → **degreesoffilm-docs-and-writing**; project vocabulary →
  **degreesoffilm-domain-reference**; public claims → **degreesoffilm-external-positioning**.

## Reusing this pattern beyond this project

None of the eight recipes is really about film. To re-instantiate on another repo, keep the
recipe skeletons (when / steps / falsifier) and swap the worked examples for that repo's own
artifacts: its decisive pre-build number (a), its contract test table (b), any dual
implementation (c), its most tangled logic (d), any client-side "protection" (e), any
generated-data invariant (f), any magic curve or distribution (g), and any "degrades
gracefully" claim (h). The discipline that transfers unchanged: state the criteria before
running, compute expected numbers by hand first, and record verdicts with the falsifying
evidence where the next person will look.

## Provenance and maintenance

- Written 2026-07-03 for the dig-era game; **rewritten 2026-08-14, re-verified after the
  degrees rebuild.** Two dig-era examples (cipher parity vector, sentinel idempotence) are
  retained compressed and labeled HISTORICAL; everything else cites current code, read in
  full before citing.
- Verified 2026-08-14 by running: `node match.test.js` (25 pass), `node chain.test.js` (51),
  `node solve.test.js` (20), `node corpus.test.js` (35);
  `python curation/challenge_gen.py --check` → `64 dailies, 0 broken`;
  `python curation/graph_build.py --check` → `OK 3682 films / 9791 people / 429 KB raw /
  190 KB gz`; the matcher mechanism one-liner in recipe (b) (`22 / 1 / 4`).
- Drift-prone facts: all counts and corpus sizes (re-run the commands above — CLAUDE.md and
  the code are authoritative, not this file); the "no frozen cross-language vector" gap in
  recipe (c) (delete the caveat if one is added); the small-world numbers (sourced from
  `project_state.md`'s Wave 2 record — the throwaway script lived in a session scratchpad,
  not the repo).
