---
name: degreesoffilm-architecture-contract
description: The load-bearing design decisions, testable invariants, and known weak points of Degrees of Film (the degrees-of-separation rebuild, 2026-08). Load this BEFORE any structural change; when asking "can I add X here?" or "which zone does this belong in?" (docs/ player client vs curation/ private tool); when touching the shape of docs/graph.json, docs/challenges.json, or the share string; when changing imports between docs/*.js modules or anything involving the TMDB key; when judging whether a feature is static-shaped or would need a server (there is none); and before "fixing" the daily-rollover date logic — it is guarded here. NOT for how changes land (degreesoffilm-change-control), doc ownership (degreesoffilm-docs-and-writing), term definitions (degreesoffilm-domain-reference), public claims/attribution (degreesoffilm-external-positioning), past dead ends (degreesoffilm-failure-archaeology), or the evidence bar (degreesoffilm-validation-and-qa).
---

# Degrees of Film — Architecture Contract

The contract you must not break, stated testably, with the weak points admitted.
Inventory facts (corpus size, test counts, file list, ruleset, share grammar) live in
`CLAUDE.md` — this file deliberately does not cache them. How a change *lands* is
`degreesoffilm-change-control`; what "proven" means is `degreesoffilm-validation-and-qa`.

## 1. The two load-bearing facts

**F1 — The TMDB key never reaches a player.** It lives only in gitignored
`curation/.env`, read by `curation/tmdb.py` at harvest time. Players fetch finished
static files from GitHub Pages (`main` `/docs`) and nothing else. There is **no
server anywhere** — the old `/match` Worker is deleted and Cloudflare is torn down
(2026-08-14). Anything needing a play-time secret or a runtime write has no home in
this architecture; proposing one is a project-posture decision, not a feature.

**F2 — Ship the whole graph once, not a puzzle at a time.** `docs/graph.json` is the
entire pool (see CLAUDE.md for current counts/size); a daily in `docs/challenges.json`
is ~50 bytes of endpoints + par. Because the shipped data is *everything*, nothing
about today's answer is in it. The corollary that keeps it true:
**suggestions are global, validation is contextual** — autocomplete draws from the
whole pool, and only then does the game judge whether the hop exists. A per-challenge
subgraph (an earlier prototype did this) hands the player the answer via autocomplete.

Zones: **curation/** (private, key-holder, builds corpus + dailies) → **docs/**
(static, world-served) → **player browser** (no key, no backend; state in localStorage).

## 2. Invariants — each testable from the repo root (Git Bash syntax)

**I1 — Key confinement.** No TMDB API access, key, or API URL under `docs/`. Only
permitted reference: the attribution footer's link + wording in `docs/index.html`.
*Breaks:* public key → quota abuse, revocation, terms violation.
*Verify (must print nothing):*
```
grep -rniE "api_key|tmdb_api_key|api\.themoviedb|image\.tmdb" docs/
```

**I2 — Layering law (the exact import graph).** `docs/match.js` imports **nothing**;
`docs/corpus.js` imports **only** `./match.js`; `docs/chain.js`, `daily.js`,
`stats.js`, `solve.js` import **nothing** (`chain.js` *takes* a corpus as a
constructor argument); `docs/app.js` imports the rest and does **ALL** DOM work.
*Why:* rules/graph logic stay Node-importable for the framework-free test suites;
`app.js` stays a thin render layer with no automated tests of its own.
*Verify (all `import` lines are in app.js + the one in corpus.js):*
```
grep -n "^import" docs/*.js
```

**I3 — Pure, DOM-free logic modules.** Every module except `app.js` runs under plain
Node with no browser globals (exception: `stats.js` load/save touch `localStorage`
inside try/catch; `recordResult` and friends are pure).
*Verify:* run the JS suites listed in CLAUDE.md § Run & test — they import the
modules directly and would throw on any DOM reference.

**I4 — Global suggestions, contextual validation.** `corpus.js` `suggest*` scans the
whole pool, never the legal candidates; `resolve` is deliberately asymmetric (in
context: exact → typo → last-word; globally: last-word only when unique).
*Breaks:* candidate-scoped suggestions = autocomplete leaks the answer (F2).
*Verify:* `node corpus.test.js` (the asymmetry is asserted there), and read the
comment block above `suggest` in `docs/corpus.js`.

**I5 — Challenges reference TMDB film ids, never array positions.** `start`/`goal`
in `challenges.json` are TMDB ids; `from`/`to` are cached display labels only.
*Why:* corpus rebuilds reorder indices; ids are stable, so published dailies survive.
*Verify:* `python curation/challenge_gen.py --check` re-derives every daily's par
AND labels from ids against the shipped corpus. Run it after any corpus rebuild.

**I6 — Par comes from the shipped corpus.** `challenge_gen.py` reads
`docs/graph.json` — the same bytes the client plays — and BFS-asserts par at build.
*Breaks:* generating from raw caches could promise a par the player can't reach.
*Verify:* the module docstring says so; `--check` proves it for every published daily.

**I7 — Fairness gates on pair selection.** `pick_pair` rejects franchise/sequel
pairs (`too_similar`: shared significant title words) and requires more than one
shortest route (`MIN_ROUTES = 2` distinct closing people) — one single path is a
needle, not a daily.
*Verify:* `python curation/challenge_gen.test.py`.

**I8 — Solutions sidecar never ships.** `curation/challenge_solutions.json` is
gitignored — this repo is **public**.
*Verify:* `git check-ignore curation/challenge_solutions.json` prints the path.

**I9 — Share line 1 is FROZEN (2026-08-14).** Accountless leagues (Discord bots
parsing group-chat shares) depend on it; line 1 may only ever *gain* content after
the final `)`. Lines 2–4 may evolve. Grammar: CLAUDE.md § Share grammar;
implementation: `shareText()` in `docs/app.js` (the FROZEN comment sits above it).
The golf label uses `−` U+2212, not a hyphen.
*Verify:* `grep -n "FROZEN" docs/app.js` hits the shareText comment.

**I10 — Curator's-note geodesic rule.** Notes ship publicly in `challenges.json`
*before* their date, so: texture only — a note must never identify a film or person
on any geodesic (endpoint titles are the prompt and are allowed). Enforced, not just
discipline: `challenge_gen.py --check` runs `note_violations` against every possible
par closer plus the solutions sidecar.
*Verify:* `python curation/challenge_gen.py --check` (fails loudly on a leak).

**I11 — Replays never touch daily stats.** `app.js` sets
`isReplay = Boolean(id) && entry.date !== todayISO()` — so `?id=N` for a *past*
daily records via `recordArchive` (isolated per-id channel), and only a genuine
today's-daily run reaches `recordResult`/the streak. A `?id` pointing at today
deliberately counts as the daily.
*Breaks:* replays polluting the streak destroys the daily hook.
*Verify:* `grep -n "recordResult\|recordArchive" docs/app.js` → one guarded branch;
`node stats.test.js` covers both channels.

**I12 — Immutable past (owner rule, not code-enforced).** Never modify a published
daily dated ≤ today: players' shared lines reference its `#id` and par. Future-dated
entries are fair game. The tooling will happily edit anything; the rule is discipline.

## 3. Date semantics — guarded, don't "fix"

`daily.js` `todayISO()` uses the **device-local** date; every player rolls over at
their own midnight. This is deliberate (Wordle-alike convention; no server exists to
hold a canonical clock). Changing it to UTC is a decision, not a bugfix — route it
through `degreesoffilm-change-control`. Adjacent fact that makes it safe: `app.js`
fetches `challenges.json?d=${todayISO()}`, so the challenge index is re-fetched at
most once per local day and a stale CDN copy self-heals at rollover.

## 4. Known weak points — stated plainly

| # | Weak point | Why accepted | What would change it |
|---|---|---|---|
| W1 | **Future dailies ship publicly** in `challenges.json` — a curious player can read tomorrow's pair. | The pair is the prompt, not the answer; a static site can't hide it. Same posture the dig took with its archive. | Only a server, which is off the table. |
| W2 | **localStorage-only stats**: device-bound, wiped with site data. | Zero infrastructure. Mitigation shipped: backup codes (`DOF1.` export/import in `stats.js`, merge = union keep-better + full recompute). | Accounts — not planned; codes are the answer. |
| W3 | **No CI.** Green suites are a manual pre-push gate. | 9 suites run in seconds locally; solo project. | CI someday; until then "suites green before push" is discipline (see change-control). |
| W4 | **Single curator.** One machine holds the key and the restock flow; published content keeps serving regardless. | Hobby scale. Long runway is the mitigation — see CLAUDE.md § Content operations. | A second keyed machine, or nothing. |
| W5 | **CDN staleness.** GitHub Pages' edge can serve stale files. `challenges.json` self-heals daily via the `?d=` date key (§3); `graph.json` is fetched un-busted and relies on revalidation — a just-restocked daily could briefly meet a cached older graph. | Ids are stable (I5) and `--check` keeps old dailies valid across rebuilds, so the window is narrow and self-heals. | Version-keyed graph fetch, if it ever actually bites. |

## 5. "Before you add X here" — decision table

Rules of thumb: needs the TMDB key or writes files → `curation/`. Data consumed at
play time → a field in `graph.json`/`challenges.json` (remember: it ships to
everyone, forever, in a public repo). Pure client logic → the right `docs/*.js`
module + `app.js` glue. Needs a play-time secret, runtime write, or cross-device
state → **nowhere; stop** (F1).

| You want to add… | Where | Invariants touched |
|---|---|---|
| Rules variant / new verdict | `chain.js` (pure, + `chain.test.js`); `app.js` only picks the words | I2, I3; decide stats policy explicitly (I11) |
| New player stat | `stats.js` pure change + test, `app.js` render | I3, I11 (keep the replay guard), W2 |
| Matcher / suggestion change | add a `match.cases.js` row FIRST; respect `resolve`'s asymmetry | I4; matcher contract |
| New daily field | `challenge_gen.py` writer + `--check`; keep dailies tiny | I5; I10 if player-visible before its date |
| New corpus field | `graph_build.py` encode + `corpus.js` decode + both suites | F2 (whole pool ships — mind the size), I2 |
| Share change | `shareText()` — lines 2–4 only; line 1 append-only after final `)` | **I9** |
| Leaderboard / accounts / cross-device | Needs a server. There is none. Posture decision via change-control; backup codes (W2) are the current answer | F1 |
| Rollover / daily-selection change | `daily.js` — read §3 first | §3; decision, not bugfix |
| Editing a published daily | Future-dated only | **I12**, I10 |

## Reusing this pattern beyond this project

Transfers: "secret stays at build time, players get static files"; ship-the-whole-
corpus so nothing shipped is an answer; pure-core/DOM-shell layering enforced by an
import-graph invariant; frozen machine-parseable share line; immutable published
content + spoiler-safe commits for any daily game. Project-specific: TMDB, the
graph/challenge encodings, every constant cited here.

## Provenance and maintenance

- Rewritten **2026-08-14**, re-verified after the degrees-of-separation rebuild
  (dig-era content removed; the cipher, puzzle/manifest/ledger schemas, image
  conventions, and Worker sections are gone — git holds that history). Every import,
  guard, constant, and grep result above was verified by reading the named file or
  running the command in this worktree.
- Counts and inventories are deliberately NOT cached here — CLAUDE.md owns them
  (corpus size, suite list, file layout, ruleset, share grammar, content ops).
- Drift-prone facts and their re-verification one-liners: I1 grep; I2 grep; I5/I6/I10
  `python curation/challenge_gen.py --check`; I8 `git check-ignore`; I9/I11 greps in
  `docs/app.js`.
- If a code change invalidates any fact here, update this file and this date in the
  same session (see `degreesoffilm-docs-and-writing`).
