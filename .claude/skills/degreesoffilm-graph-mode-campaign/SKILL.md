---
name: degreesoffilm-graph-mode-campaign
description: >
  The decision-gated campaign for TRUE degrees-of-separation — the last big unbuilt
  mode (connect film A to film B through shared credits) and the final stay-static
  parking-lot item. Load when: starting degrees-of-separation in any form; anyone says
  "six degrees", "connect the films", "graph mode", or "Cine2Nerdle-style"; designing
  the film/person graph extractor or challenge format; asking whether the mode needs a
  server; or proposing to bulk-crawl TMDB for graph data (a fenced path — the buff
  harvest cache already holds the corpus). Status as of 2026-07-13: **G0 PASSED**
  (daily challenge · alternate film↔person hops · par-based scoring · autocomplete on ·
  spoilability accepted) and **G1 PASSED** (extractor built + measured: 3,663 films /
  29,774 people / 63,084 edges; corpus 630 KB gz → per-challenge subgraphs, which
  measure ~4 KB gz median; median pair distance 2 degrees, p95 4). Next: Phase G2 —
  offline chain validator + challenge generator. NOT for the vertical-dig game's rules
  (that is the shipped game) or server phases (degreesoffilm-server-move-campaign).
---

# Degrees of Film — the graph-mode campaign (true degrees-of-separation)

An executable, decision-gated plan patterned on the server-move campaign (phases,
numeric gates, fenced wrong paths). **Everything below is CANDIDATE as of 2026-07-11.**
When a phase ships, mark it DONE here with date + evidence, same session.

## 1. Charter

**The mode:** connect film A to film B through shared credits — *"Heat → Al Pacino →
The Godfather Part II → Robert De Niro → …"* — in as few hops as possible. This is the
"six degrees" game DESIGN's banner explicitly says the shipped game is NOT; it becomes a
SECOND mode with its own schema and route, never a change to the dig.

**Why this project can do it static** (nobody credible does — Cine2Nerdle and kin run
live backends): the three-zone architecture prebakes everything players touch, and as of
2026-07-11 the raw graph material is ALREADY ON DISK — `curation/people_harvest_cache.jsonl`
(gitignored, rebuildable) maps every pool-floor film (3,663 films, vote_count≥800 &
vote_average≥6.5) to its top-billed cast + five key crew. That cache was built for Movie
Buff autocomplete; it doubles as the film↔person edge list. **v0 needs zero new TMDB calls.**

### Hard requirements (inherit the house constraints)

| # | Requirement |
|---|---|
| G-R1 | The dig (daily game) is untouched: no `game.js`/`match.js` changes, no shared state. New route, new schema, new pure module(s). |
| G-R2 | TMDB key never reaches a player (three-zone law). All graph data prebaked by curation. |
| G-R3 | Static play: the mode works from GitHub Pages files alone. Server validation is an OPTIONAL later hardening via the server-move campaign, never a launch dependency. |
| G-R4 | Payload budget: a playable challenge ships in **≤ 150 KB gzip** (measured, not vibes — that's smaller than one puzzle's image set). Whole-corpus shipping only if it measures under budget; otherwise per-challenge subgraphs. |
| G-R5 | Spoiler posture decided at G0 and written down. Static graph = shipped solution space (same enumerability as the dig's answers — accepted there, probably acceptable here; say so explicitly). |

## 2. Phase G0 — owner decision gate  [DONE 2026-07-13 — ALL FIVE ANSWERED]

> **Owner answers (2026-07-13):** (1) Shape = **daily challenge** first. (2) Hop format =
> **alternate film↔person** (the classic form). (3) Assist = **autocomplete on by default**
> (recommendation stood unvetoed; reuses both buff indexes). (4) Scoring = **par-based**
> (BFS shortest path = par, golf-style hops-vs-par brag; per-hop attempts in the dig's
> 3-guess rhythm). (5) Spoiler posture = **accept shipped solution space, like the dig**
> (static-first; server validation stays an optional later hardening, W-G3 upheld).

Questions for the owner (record answers in project_state.md):
1. **Shape:** daily A→B challenge (one per day, like the dig) — or freeplay generator?
   (Recommendation: daily first; it reuses the manifest/archive mental model.)
2. **Guess granularity:** does the player name the connecting PEOPLE, the FILMS, or
   alternate person→film→person (recommendation: alternate — it's the classic form and
   both indexes already exist for autocomplete)?
3. **Assist posture:** Movie Buff-style autocomplete on by default, or a mode variant?
4. **Par & scoring:** score = hops over par (BFS shortest path = par)? Attempts/limits?
5. **Spoiler posture** (G-R5): accept shipped solution space at launch?

**Exit gate G0:** answers recorded; scope = which phases below are wanted.

## 3. Phase G1 — extractor + size budget  [DONE 2026-07-13 — GATE G1 PASSED]

> **Measured 2026-07-13** (`curation/graph_extract.py`, 11 pure tests green; films
> metadata cached in gitignored `curation/films_cache.jsonl`): graph = **3,663 films /
> 29,774 people / 63,084 edges**; person degree median 1, p95 7, max 74. Whole corpus =
> 1,721 KB raw / **630 KB gz** → over the 150 KB G-R4 budget, so **DECISION: per-challenge
> subgraphs** (as expected). A 2-hop pair subgraph measures **median 10 KB raw / 4 KB gz,
> max 18/8** — far under budget, leaving ample room for decoy padding (and for k=3 balls
> when par > 2; the generator must size k to the par). Path lengths over 300 random pairs:
> 1° 3%, **2° 49%, 3° 34%**, 4° 8%, 5° 2%, 6° 0.3%, unreachable 2.3% — median 4 edges
> (2 degrees), p95 8. Consequence for G2: natural dailies sit at par 2–4; par-1 pairs are
> rare enough to be "easy day" specials; unreachable pairs must be filtered by the
> generator (BFS returning None).

1. `curation/graph_extract.py` (pure core + CLI, house pattern): read the harvest cache
   → nodes (films, people) + edges (credited-on), emit JSON. Include film year + person
   role class (cast/crew) — challenge generation wants both.
2. **Measure before designing:** whole-corpus bytes raw/gz; then per-challenge subgraph
   bytes for k-hop neighborhoods (k=2,3) around sample film pairs. Predict first, then
   run (research-methodology).
3. Feasibility probe: BFS over the full graph — distribution of shortest-path lengths
   between random pool-film pairs (if 90% of pairs are ≤3 hops, challenges need curation
   toward interesting/longer pairs; if typical is 4–6, dailies are naturally rich).

**Exit gate G1 (numbers):** extractor tested (pure suite, house style); corpus + subgraph
sizes measured and written into project_state; path-length distribution known. Decision
recorded: whole-corpus vs per-challenge shipping (G-R4 budget applied).

## 4. Phase G2 — offline prototype  [CANDIDATE]

1. A pure `docs/graph.js`-shaped module (no DOM): load a challenge JSON, validate a
   player's chain step-by-step (is X actually credited on Y?), track hops/par/complete.
   Test-first in Node (the dig's engine purity pattern — it paid for itself twice).
2. A challenge generator CLI: pick A→B with target par, emit the subgraph + challenge
   JSON (id, films, par, subgraph). Hand-author challenge 001 with it.
3. Tamper thought-pass: what stops a player reading the subgraph in devtools? (Answer:
   nothing — G-R5 posture; the subgraph should include DECOY nodes/edges beyond the
   solution paths so reading it isn't trivially the answer. Measure how many decoy nodes
   fit the G-R4 budget.)

**Exit gate G2:** the validator accepts a legit hand-played chain and rejects three forged
ones (wrong credit, skipped hop, out-of-graph node) — binary, offline, one terminal session.

## 5. Phase G3 — playable client behind a route  [CANDIDATE]

New route (`?graph` or `?connect`; register in config-and-flags when it lands), new
section in index.html, rendering in app.js only (G-R1). Autocomplete via the existing
buff indexes per G0's answer. Ships OFF the mode-select until G4.

**Exit gate G3:** a person who is not the builder completes a challenge on a served
static copy; payload ≤ G-R4's measured budget; the dig's 9 JS suites still green;
devtools shows zero non-static requests.

## 6. Phase G4 — dailyization + promotion  [CANDIDATE]

Curation-tool integration (challenge publisher beside the puzzle publisher — its own
manifest or a shared one, G0 decides), archive semantics, mode-select tile, share
string. Owner sign-off per change-control; stats isolation rule applies by default.

## 7. FENCED WRONG PATHS

- **W-G1 — Bulk-crawling TMDB for a bigger graph.** The pool-floor corpus (3,663 films)
  is the graph. Obscure films outside the pool make challenges LESS fun (unrecognizable
  hops), cost thousands of calls, and bloat the payload. Extend the corpus only with a
  measured reason.
- **W-G2 — Entangling with the dig.** No shared Game state, no matcher changes, no
  "reuse the rung renderer". The dig's purity is a campaign asset elsewhere; keep it.
- **W-G3 — Server-side validation as a launch requirement.** It reintroduces the
  backend dependency the static design exists to avoid; G-R5 accepts spoilability like
  the dig does. If a leaderboard ever wants verified chains, that routes through the
  server-move campaign's Phase 3 replay pattern.
- **W-G4 — Shipping the whole corpus without measuring.** G1's numbers decide; a
  per-challenge subgraph with decoys is the expected winner.

## When NOT to use this skill

- The shipped vertical-dig game, its rules or matcher → CLAUDE.md + domain-reference.
- Server phases, accounts, leaderboards → **degreesoffilm-server-move-campaign**.
- The research framing of this idea (why it's SOTA-adjacent) →
  **degreesoffilm-research-frontier** entry 2a (this campaign is its executable form).
- Landing anything → **degreesoffilm-change-control**.

## Provenance and maintenance

- Written 2026-07-11. Asset claims verified that day: `people_harvest_cache.jsonl`
  exists with 3,663 film records (built during the Movie Buff all-rungs work, PR #25);
  pool size from the live discover sweep; the dig/graph banner distinction from
  CLAUDE.md. Nothing else verified because nothing else exists yet.
- When G0 is asked and answered, record it here + project_state the same session.
