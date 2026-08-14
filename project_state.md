# Project State — Degrees of Film

> **Running handoff doc. Read this first each session, and keep it updated.** Division of labor:
> `CLAUDE.md` = how the code works (durable); **this file = where we are right now** (living).

_Last updated: **2026-08-14** (short orientation session — no code changes). State re-verified
that day: `main` unmoved at `87699a9`, [PR #29](https://github.com/Bluesuitcase/DegreesofFilm/pull/29)
still OPEN/unmerged, live site still the old dig. The rebuilt game was served locally for the
owner playtest (clean load, zero console errors; daily #4 = The Prestige → The Purge: Anarchy,
par 2) but **the playtest itself did NOT happen — it remains the open gate.** Session side
effects: the `mattpocock-skills` plugin was installed at user scope (not project), and a
temporary uncommitted `connect` entry (serves this worktree's `docs/` on port 8010 by absolute
path) was added to `.claude/worktrees/amazing-sammet-cd9de5/.claude/launch.json` — drop or keep
at will. Everything below is the 2026-08-11 rebuild handoff, still accurate._

**THE GAME WAS REBUILT.** The vertical-dig daily (name the film
from a still, then dig through its credits) was **retired and deleted** at the owner's direction —
"I just don't find it very fun" — and the site is now built entirely around
**degrees-of-separation: connect two films through the people who made them**. All work is
**committed as `3da6a94`** on branch `claude/session-context-634bc2` (368 files, +2,080/−13,703)
— **pushed as [PR #29](https://github.com/Bluesuitcase/DegreesofFilm/pull/29), NOT merged, NOT live.**_

## ▶ Start here next session

1. **Read this file, then `CLAUDE.md`.** Ignore the skill library where it disagrees with them
   (see "Skill library — mid-migration" below).
2. **The one open question is whether the game is fun.** It has never been played by anyone but
   me. Serve it — `python -m http.server 8010 --directory docs` from the worktree, or the `docs`
   entry in `.claude/launch.json` — and play today's daily.
3. **Then merge or don't.** The branch is pushed and
   **[PR #29](https://github.com/Bluesuitcase/DegreesofFilm/pull/29) is open against `main`** —
   review it there. Merging is player-facing and destructive (the live site loses the dig and its
   21 puzzles), so it's deliberately left unmerged. Rebase-merge per `degreesoffilm-change-control`
   (`main` had not moved, so it's a clean 2-commit fast-forward). Pushing `docs/` to `main`
   auto-deploys to GitHub Pages.
4. The worktree is at `.claude/worktrees/session-context-634bc2`. The two gitignored TMDB caches
   were copied into it and are ~2.5 MB.

## What the game is now

Two films a day. Name someone credited on the first, then another film they worked on, and keep
hopping until you name someone who also worked on the target. Each person hop is a **degree**;
**par** is the shortest chain that exists; scoring is golf (E, +1, −1). Three wrong links on one
step ends the run.

**Today's example (daily #1):** Return of the Jedi → *Harrison Ford* → Ender's Game →
*Ben Kingsley* → Shang-Chi. Par 2.

## The decision that made it work

**Ship the whole graph once instead of a puzzle at a time.** Measured first, then built:

| payload | raw | gzip |
|---|---|---|
| Whole corpus, pruned + index-encoded (`docs/graph.json`) | 424 KB | **188 KB** |
| ...vs `people-index.json` the old site already shipped to Movie Buff players | 478 KB | 212 KB |
| All 30 scheduled dailies (`docs/challenges.json`) | 1.9 KB | **0.5 KB** |

3,637 films / 9,679 people / 42,367 edges. Two prunes got it there: people credited on only one
film can never be a hop (67% of them), and delta-hex index encoding. The corpus is fetched **only
when you actually play** — home and archive render from `challenges.json` alone.

Consequences worth remembering:
- A daily is ~50 bytes, so content generation is one command, not a curation session.
- **Suggestions are global; validation is contextual.** You can type any film or person in the
  pool and the game tells you whether that hop exists. The July prototype shipped a per-challenge
  subgraph and drew autocomplete from it — which handed the player the answer. That flaw is why
  the subgraph design was abandoned.
- Nothing about today's answer is in the shipped data, because the shipped data is everything.

## Status

- **Built, tested, verified in-browser, committed (`3da6a94`) and pushed as
  [PR #29](https://github.com/Bluesuitcase/DegreesofFilm/pull/29). NOT merged, NOT deployed.**
  The live site still serves the old dig until this branch lands.
- **Tests: 8 suites, 183 assertions, all green.** JS: match 25, daily 11, stats 22, corpus 35,
  chain 36. Python: harvest 8, graph_build 23, challenge_gen 23.
- **Content: 30 dailies, 2026-08-11 → 2026-09-09**, every one's par re-verified by BFS against
  the shipped corpus (`challenge_gen.py --check`).
- **In-browser evidence (localhost:8010):** today's daily played to a win at par; the verdict
  contract confirmed live (real-person-not-in-film burns an attempt, unknown name is free);
  autocomplete confirmed global (it offers Tom Hanks for a film he isn't in); stats, archive and
  scorecard render; **zero non-static requests**; no console errors; no horizontal overflow at
  375 px.

## What was deleted (all recoverable from git)

Player-facing: `game.js`, `frame.js`, `theme.js`, `cipher.js`, `buff.js`, `title-index.json`,
`people-index.json`, `docs/puzzles/` (21 puzzles + ~34 MB of images), the old `docs/challenges/`
subgraph. Server: all of `server/` (the `/match` Worker). Curation: the whole crop-and-publish
tool (`app.py`, `static/`, `build_rungs`, `decoys`, `credits_images`, `images`, `publish`,
`ledger`, `manifest`, `cipher`, `push_answers`, the backfills, `title_index`, `people_index`,
`discover`, `graph_extract`, `used_films.json`, `requirements.txt`). Tests for all of the above.

**The curation zone now has no third-party dependencies at all** — it's stdlib Python. The
repo-root `.venv` is no longer needed by anything.

## ⚠️ Open items for the owner

1. **Play it and tell me if the game is fun** before this merges. Serve `docs/` (port 8010 via
   `.claude/launch.json`) or review the branch. The whole point of the rebuild was fun; that's
   the one thing tests can't check.
2. **The deployed Cloudflare Worker is now orphaned.** `dof-match.bluesuitcase.workers.dev` has
   nothing to serve (it existed to hide the dig's answers). Delete it from the Cloudflare
   dashboard when convenient — it costs nothing but it's dead weight, and its KV namespace still
   holds the old puzzle answers.
3. **Merging is player-facing and destructive** (the live site loses the dig and 21 puzzles).
   Per `degreesoffilm-change-control` this wants a branch → PR → rebase-merge, with your explicit
   sign-off. **Pushed and open as [PR #29](https://github.com/Bluesuitcase/DegreesofFilm/pull/29)**
   (`3da6a94` + handoff commits) — deliberately not merged. One rebase-merge from being live.

## Next up (my recommendation, in order)

1. **Owner playtest** (above) — everything else is premature until the core is confirmed fun.
2. **Merge + deploy**, then verify the live site the same way (the Fastly edge can serve a stale
   `challenges.json`; the client's fetch is date-keyed, so it self-heals next day — verify against
   `raw.githubusercontent.com`, not the Pages URL).
3. **Refresh the corpus.** The caches were harvested 2026-07-11; a `harvest.py` run picks up
   films that have since crossed the pool floor. Then `graph_build.py` + `challenge_gen.py --check`.
4. **Difficulty tuning.** `count_routes` (how many distinct people can close a chain) is computed
   and stored in the solutions sidecar but not yet used to grade a daily. Obvious next lever: a
   difficulty label, or biasing the week's par mix.
5. **Product polish** worth considering: a hint (reveal one legal hop for a degree), an
   unlimited/freeplay mode (the corpus makes it nearly free — it was on the menu and you chose
   daily-only for now), custom pairs, a per-hop emoji share grid.
6. **Skill-library review** (below).

## Skill library — mid-migration

Seven skills described tooling that no longer exists and were **deleted** from both the repo and
the global mirror (`~/.claude/skills/`): `run-and-operate`, `worker-ops`, `server-move-campaign`,
`diagnostics-and-tooling`, `debugging-playbook`, `config-and-flags`, `build-and-env`.
`graph-mode-campaign` got a SUPERSEDED banner explaining what changed.

**The eleven survivors have NOT been re-verified** and still contain dig-era facts in places:
`architecture-contract`, `change-control`, `docs-and-writing`, `domain-reference`,
`external-positioning`, `failure-archaeology`, `proof-and-analysis-toolkit`, `research-frontier`,
`research-methodology`, `validation-and-qa`, `graph-mode-campaign`. Their *process* content
(how to land changes, how to write docs, how to prove a claim) is still good; their *inventory*
content (file lists, test counts, constants) is stale. Until that pass is done, **trust
`CLAUDE.md`, this file, and the code over any skill.**

## Key decisions (why things are the way they are)

- **Retire the dig completely** (owner, 2026-08-11) — not archive-only, not co-equal. Chosen over
  keeping 21 puzzles playable, because a half-retired game means maintaining two data pipelines.
- **Mode named "Degrees"**, not "Connect" (owner, 2026-08-11).
- **Daily challenge only** for now (owner) — unlimited/marathon/custom-pair were offered and
  deferred, though the corpus makes each of them a thin layer.
- **Full corpus over per-challenge subgraphs** — measured, not assumed; see the table above.
- **Unrecognized input doesn't burn an attempt**; only a real person/film that isn't a legal hop
  does. Typos and category slips are not strategy errors, and punishing them makes the game feel
  like a spelling test.
- **The surname rule is asymmetric on purpose.** In context (a dozen legal hops) "Bardem" is
  unambiguous and accepted; globally (9,679 names) a bare surname is accepted **only if exactly
  one person in the pool has it**, or "smith" would silently resolve to whichever Smith ranks
  highest. Index order is popularity order, so "first hit wins" = "most famous hit wins".
- **Challenges reference TMDB film ids, not array positions** — a corpus rebuild reorders the
  arrays, and positional refs would silently repoint old dailies at the wrong films.
- **Par is computed from the shipped corpus**, not the raw caches, so a published par is always
  reachable by the player.
- **Franchise pairs are rejected** by the generator (shared significant title words) — *Infinity
  War* → *Endgame* isn't a puzzle. Pairs also need >1 shortest route, so the answer isn't a needle.
- **Solutions never enter the repo** (`curation/challenge_solutions.json`, gitignored) — this repo
  is public.
- **Accepted, not a bug:** `challenges.json` ships future dailies, so a curious player can read
  tomorrow's pair. The pair is the prompt, not the answer, and a static site can't hide it.
- **Carried over unchanged:** the TMDB key never reaches a player; the pool floor
  (`vote_count >= 800`, `vote_average >= 6.5`); `match.js` and its 25-case contract; the
  ink/bone/amber look; DOM-free rules modules so Node tests import them directly.

## Workflow / gotchas

- **The `docs` launch entry moved to port 8010** — Docker holds 8000 on this machine.
- **Browser automation:** the harness's synthetic Enter keypress doesn't reach the input; the
  button path and JS-dispatched `keydown` both work. Not a product bug — verify with either.
- **Screenshots time out** when the Browser pane isn't displayed; DOM/computed-style checks via
  `javascript_tool` are the reliable fallback (this was already true in July).
- **Both TMDB caches were copied into this worktree** from the main checkout
  (`films_cache.jsonl`, `people_harvest_cache.jsonl` — gitignored, ~2.5 MB).
