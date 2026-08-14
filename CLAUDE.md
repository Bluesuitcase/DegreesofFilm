# Degrees of Film

> **New session? Read [`project_state.md`](project_state.md) FIRST**, then keep it updated as you
> work. It's the running handoff — current task, decisions, next steps. This file (CLAUDE.md)
> explains how the code works; `project_state.md` tracks where we are right now.
>
> ⚠️ **The skill library under [`.claude/skills/`](.claude/skills/) is MID-MIGRATION.** It was
> written for the retired dig game (see below). The skills that described deleted tooling have been
> removed; the survivors are being reviewed. Trust this file, `project_state.md`, and the code over
> any skill until that pass is done.

A daily browser game about how films connect. You're given **two films** and you chain from one to
the other through the people who made them: name someone credited on the first film, then another
film they worked on, and keep going until you name someone who also worked on the target. Each hop
through a person is one **degree**. **Par** is the shortest chain that exists; the brag is your
degrees against par, golf-style.

**Status (2026-08-11): the game was rebuilt around this mode and the original game was retired.**
The previous game — a vertical dig through one film's credits, famous to obscure — is gone:
routes, puzzle files, images, curation UI, cipher, and the `/match` Worker were all deleted in the
rebuild. Its history is in git if it's ever wanted back.

Live at **https://bluesuitcase.github.io/DegreesofFilm/** (GitHub Pages, `main` `/docs`).

## The one idea that makes it work

**Ship the whole graph once, not a puzzle at a time.** `docs/graph.json` is the entire pool —
3,637 films, 9,679 people, 42,367 credited-on edges — in 188 KB gzip, cached by the browser after
the first play. Everything follows from that:

- A daily challenge is **~50 bytes** (`{id, date, start, goal, par}` with TMDB film ids). All 30
  currently scheduled fit in 1.9 KB.
- **Suggestions are global, validation is contextual.** You can type any film or person in the
  pool; the game then tells you whether that hop actually exists. An earlier prototype shipped a
  per-challenge subgraph and drew autocomplete from it, which handed the player the answer.
- Nothing about today's answer is in the shipped data, because the shipped data is everything.
- No images anywhere. The whole site is ~200 KB.

Two prunes make the corpus small enough: people credited on only one film can never be a hop
(67% of them — dropped), and the labels/adjacency are index-encoded with delta-hex gaps.

## Run & test

- **Play it:** serve `docs/` — the game uses `fetch`, so `file://` won't work. Use the `docs` entry
  in `.claude/launch.json` (port 8010) or `python -m http.server 8010 --directory docs`.
- **JS tests** (plain Node, no framework): `node match.test.js`, `node daily.test.js`,
  `node stats.test.js`, `node corpus.test.js`, `node chain.test.js` from the repo root. Each prints
  PASS/FAIL and exits non-zero on failure. `package.json` exists only to set `"type": "module"`.
  The matcher's case table lives in `match.cases.js`.
- **Python tests** (stdlib only — there is no longer a `.venv` or any pip dependency):
  `python curation/harvest.test.py`, `python curation/graph_build.test.py`,
  `python curation/challenge_gen.test.py`.
- **Verify the published dailies** against the corpus at any time:
  `python curation/challenge_gen.py --check` — re-derives every daily's par by BFS and confirms
  the cached titles still match. Run it after any corpus rebuild.

## Architecture — three zones

The design still turns on one fact: **the TMDB API key never reaches a player.** It lives only in
`curation/.env` on your machine. Players fetch finished static files and nothing else.

1. **PRIVATE (your machine)** — `curation/` holds the key and builds the corpus from TMDB.
2. **STATIC HOSTING (GitHub Pages)** — the `docs/` folder: the corpus, the dailies, the client.
3. **PLAYER BROWSER** — no key, no backend. Vanilla ES modules run the rules and the matching;
   streak and scorecard live in localStorage.

There is **no server**. Guess validation is client-side against the shipped graph. (The old
`/match` Cloudflare Worker existed to hide the dig's answers; with no answers shipped there is
nothing for it to protect. The deployed Worker at `dof-match.bluesuitcase.workers.dev` is orphaned
and should be deleted from the Cloudflare dashboard.)

## File layout

```
DESIGN.md              Original spec for the retired dig game — HISTORICAL, superseded by the
                       "Degrees" section at its top. This file + project_state.md are current.
CLAUDE.md              This file (how the code works).
project_state.md       Running session handoff — read FIRST.
package.json           Just { "type": "module" }.
match.cases.js         The matcher contract as data: [guess, answers, expected, label] rows.
match.test.js          Matcher tests (25).
daily.test.js          Daily-selection tests (11): pickPuzzle date logic.
stats.test.js          Streak/scorecard tests (22): recordResult, golf labels.
corpus.test.js         Corpus tests (35): decoding, resolution, suggestions + real-asset invariants.
chain.test.js          Chain-engine tests (36): verdicts, forged chains, back(), par.
docs/                  The entire static site = what gets hosted.
  index.html           Markup + element ids the JS binds to.
  style.css            Dark "ink/bone/amber" theme. CSS vars in :root. Breakpoint at 600px.
  app.js               DOM glue ONLY. Fetches, renders, wires buttons. No rules here.
  chain.js             The game: alternating film/person hops, degrees vs par, verdicts, back().
                       Pure logic, no DOM.
  corpus.js            The graph: decode, invert, lookup, contextual name resolution, global
                       suggestions. Pure logic, no DOM. Imports only match.js.
  match.js             Fuzzy name matching (normalize/levenshtein/matchGuess). No imports.
  daily.js             Which challenge is today's (pickPuzzle/pickById). Pure, no DOM.
  stats.js             localStorage streak + scorecard; recordResult is pure.
  graph.json           THE CORPUS: {v, ids, films, people, cast} — 188 KB gz. Built by
                       curation/graph_build.py. Fetched only when you actually play.
  challenges.json      {v, daily:[{id, date, start, goal, par, from, to}]} — every daily.
curation/              PRIVATE — never served. Holds the TMDB key (.env, gitignored).
  tmdb.py              Tiny stdlib TMDB v3 client (load_key + get).
  harvest.py           Step 1: sweep the pool floor and cache films + their key credits
                       (films_cache.jsonl, people_harvest_cache.jsonl — both gitignored,
                       append-only, so a refresh only fetches what's new).
  graph_build.py       Step 2: caches -> docs/graph.json. Prunes non-connectors, ranks, encodes,
                       and validates. Pure core + CLI (`--check` re-validates the shipped file).
  challenge_gen.py     Step 3: corpus -> docs/challenges.json. Picks pairs at an exact par from
                       the most popular films, rejects franchise pairs, requires >1 route, asserts
                       par at build. Solutions go to a GITIGNORED sidecar (this repo is public).
  *.test.py            Pure tests, stdlib only.
```

**Layering, keep it clean:** `match.js` has no imports. `corpus.js` imports only `match.js`.
`chain.js` imports nothing but takes a corpus. `app.js` does all DOM work. Rules and graph logic
stay DOM-free so the Node tests import them directly.

## The ruleset (as implemented in `chain.js`)

- **The chain:** from the current film, name a **person** credited on it; then a **film** they also
  worked on; repeat. Naming a person who is **also credited on the goal film** closes the chain and
  wins. You never step *into* the goal film.
- **Degrees** = person steps taken. **Par** = the shortest chain that exists (BFS at build time).
  Beating par is possible — the corpus only knows credits it has, and par is computed over the same
  data the player plays.
- **Attempts:** 3 per step. The third burn ends the run.
- **What burns an attempt:** naming a real person/film of the right kind that isn't a legal hop.
  **What's free:** a name nothing matches (a typo), naming a film where a person belongs (or vice
  versa), and naming the goal film. Punishing spelling makes the game feel like a spelling test.
- **No revisiting:** a person or film already in your chain can't be used again.
- **`back()`:** abandons the current person and returns to the previous film. The degree stays
  spent and the person stays blocked — no refunds, like a golf stroke.
- **Verdicts** are richer than right/wrong (`correct`, `won`, `wrong`, `unknown`, `over`,
  `ignored`) with a `reason` (`notCredited`, `used`, `wrongType`, `goalFilm`, `unrecognized`), so
  the UI can say *why*. `app.js` only picks the words.
- **Stats:** daily results only. Replays (`?id=N`) never touch the streak or scorecard.

**Routes:** `?` home · `?play` today · `?id=N` replay a past daily · `?archive` · `?history`.

## Name matching (`match.js` + `corpus.js`) — the part that decides if it feels fair

- `normalize(s)`: lowercase → strip diacritics → `&`→`and` → punctuation to spaces → collapse
  whitespace → drop a single leading article.
- `matchGuess`/`levenshtein`/`maxDist` are unchanged from the original game and still under
  `match.test.js`. **Add a case to `match.cases.js` before touching the algorithm.**
- `corpus.resolve` is the new layer, and its asymmetry is deliberate:
  - **In context** (the handful of legal hops): exact → typo → last-word. "Bardem" or "Fiction"
    is unambiguous among a dozen candidates.
  - **Globally** (9,679 names): exact → typo → last-word **only if exactly one name in the pool
    ends that way**. Otherwise "smith" would silently resolve to whichever Smith ranks highest.
  - Index order is rank order (popularity), so "first hit wins" means "most famous hit wins" —
    that's how duplicate titles like *Heat (1995)* vs *Heat (1986)* resolve, and why context beats
    rank when the lower-ranked one is the legal hop.
- Worst case (a guess matching nothing, scanning all 9,679 names) measures **~5 ms**.

## Share grammar (FROZEN — never reformat line 1)

The share string's first line is a machine-parseable contract. Accountless leagues
(Discord bots parsing group-chat shares) depend on it; changing it breaks every parser
silently, so it is frozen as of 2026-08-14. `shareText()` in `docs/app.js` implements it.

```
line 1 (win):   Degrees of Film #<id> — <degrees>° (par <par>, <E|+n|−n>)
line 1 (loss):  Degrees of Film #<id> — X (par <par>)
line 2:         <start title (year)> → <goal title (year)>
line 3 (win):   <glyph trail>[ · streak <n>]        n >= 2, daily runs only
line 3 (loss):  💔 <glyph trail>
line 4:         the site URL
```

Glyph trail = the run's shape in play order, names never included: `🔗` a completed
degree · `🟥` a burned attempt · `↩` a back-up. Runs longer than 14 glyphs compress to
`🔗×a 🟥×b`. Lines 2–4 may evolve; **line 1 may only ever gain content after the final
`)`** so prefix parsers keep working. The golf label uses `−` (U+2212), matching
`relativeLabel`.

## Content operations

Refreshing the corpus and stocking dailies is now three commands, and only the first needs TMDB:

```bash
python curation/harvest.py         # refresh caches (only fetches films it hasn't seen)
python curation/graph_build.py     # rebuild docs/graph.json + validate
python curation/challenge_gen.py --days 30    # append 30 dailies + verify par
```

After a corpus rebuild, run `python curation/challenge_gen.py --check` — film ids are stable, but
this catches a daily whose endpoint fell out of the pool.

**Spoiler discipline:** `curation/challenge_solutions.json` is gitignored and must stay that way —
this repo is public. Commit messages must not name a future daily's chain.

**Known and accepted:** `challenges.json` ships future dailies, so a curious player can read
tomorrow's film pair. The pair is the prompt, not the answer, and a static site can't hide it —
same posture the original game took with its archive.

## Agent skills

Per-repo config for the `mattpocock-skills` engineering flows. Note the path adaptation:
`docs/` is the deployed site, so these live at the repo root instead of the usual `docs/…`.

### Issue tracker

Issues live in this repo's GitHub Issues, driven via the `gh` CLI (with a per-command
`GH_TOKEN` from the cached git credential). See `agents/issue-tracker.md`.

### Domain docs

Single-context: `CONTEXT.md` at the repo root and ADRs in `adr/` (both created lazily; until
then, `CLAUDE.md` + `project_state.md` carry the vocabulary and decisions). See
`agents/domain.md`.
