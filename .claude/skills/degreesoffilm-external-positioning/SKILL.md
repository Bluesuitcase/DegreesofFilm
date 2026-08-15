---
name: degreesoffilm-external-positioning
description: >
  The project's relationship to the outside world: TMDB terms and the mandatory attribution
  footer, the content-rights posture of shipping a factual credits graph (open questions —
  NOT legal advice), what is genuinely distinctive vs known art in the daily-game and
  film-connection ecosystem (Cine2Nerdle, six-degrees tradition), and the evidence bar for
  any public claim. Load this BEFORE: announcing or sharing the game publicly; writing a
  Product Hunt / Reddit / Hacker News / press post, README, or marketing copy; answering
  "can we monetize this?", "is this legal?", "do we need a TMDB license?", "can we remove
  the TMDB footer?"; comparing the game to Framed, Wordle, Cine2Nerdle, or any other daily
  game; or making any "first/only/better-than" claim. Also load when a change touches the
  attribution footer or the share string (line 1 is a frozen external contract).
---

# Degrees of Film — external positioning

How this project relates to TMDB, to rights questions, and to the daily-game ecosystem —
and what you are allowed to claim in public. This skill exists to **prevent overclaiming**.
When in doubt, claim less.

> **This skill is not legal advice and must never be read as such.** Where rights questions
> arise, it states the open question plainly and lists questions for a lawyer. Nobody on
> this project is qualified to clear a rights question, and no document in this repo does.

---

## 1. The TMDB relationship

### 1.1 Integration shape (what TMDB actually powers)

| Fact | Detail | Source |
|---|---|---|
| Where the API is called | **Curation time only**, from the private `curation/` tool on the owner's machine | `CLAUDE.md` "Architecture — three zones" |
| What players fetch | Finished static files under `docs/` (GitHub Pages). **No player request ever touches TMDB.** There is no server at all. | `CLAUDE.md`; `docs/app.js` fetches only `graph.json` / `challenges.json` |
| Key location | `curation/.env`, gitignored. Never in `docs/`, never in git history. | verified: no-key grep in §5 empty (2026-08-14) |
| Data used | Film details + key credits only — **no images are fetched or shipped** | `curation/harvest.py`, `curation/tmdb.py` |
| Usage volume | Incremental harvest sweeps: append-only caches mean a refresh fetches only films new to the pool (e.g., the 2026-08-14 refresh fetched 46 credit sets). Modest by any measure. | `curation/harvest.py`; `project_state.md` refresh record |
| TMDB rate ceiling | "somewhere in the 40 requests per second range" — as of 2026-07-03 (developer.themoviedb.org/docs/rate-limiting) — re-verify before public claims | external |

Consequence for positioning: you may truthfully say "built with TMDB data" and "no tracking,
no backend, no API calls from your browser." You may NOT imply TMDB endorsement (see below —
the required notice says the opposite).

### 1.2 The attribution obligation — the footer never comes off

Live in `docs/index.html` (lines 120–140, verified 2026-08-14):

```html
<!-- Mandatory TMDB attribution. The inline SVG is a faithful gradient-pill
     rendition of the TMDB mark; swap in the official logo from
     themoviedb.org/about/logos for strict brand compliance. -->
<footer class="attribution">
  <a class="tmdb" href="https://www.themoviedb.org/" target="_blank" rel="noopener"
     aria-label="The Movie Database (TMDB)">
    <svg viewBox="0 0 190 34" width="76" height="13.6" role="img" aria-hidden="true">
      ...
    </svg>
  </a>
  <p>This product uses TMDB and the TMDB APIs but is not endorsed, certified, or otherwise approved by TMDB.</p>
</footer>
```

**Rules:**

1. **The footer never comes off.** The rebuild kept it; there is no legitimate change that
   requires its removal (degreesoffilm-change-control lists attribution among the
   non-negotiables).
2. Any **new public surface** (a store listing, a native wrapper, a second page) needs the
   same notice + logo. TMDB requires attribution on the application, not just one page.
3. The SVG is a **rendition** of the TMDB mark, not the official logo file. For strict
   brand compliance before any high-visibility launch, swap in an official logo from
   themoviedb.org/about/logos.
4. The sentence matches TMDB's terms phrasing as verified 2026-07-03 against
   themoviedb.org/api-terms-of-use. Before any public launch, **re-read the current terms**
   and update the sentence if TMDB's required wording has moved — through change control
   like any `docs/` edit.

### 1.3 The non-commercial / commercial line (as TMDB draws it)

As of 2026-07-03 (developer.themoviedb.org/docs/faq + themoviedb.org/api-terms-of-use) —
**re-verify before public claims**:

- The API is "free to use for non-commercial purposes as long as you attribute TMDB as the
  source." A project counts as commercial if "the primary purpose is to create revenue for
  the benefit of the owner."
- Commercial activity — charging users, selling an app that integrates TMDB, using the
  content on revenue-generating sites — requires a **separate written agreement**
  (contact: sales@themoviedb.org).
- The terms also prohibit use "in connection with, including for training, a machine
  learning (ML) or artificial intelligence (AI) based Application."

**Where this project stands today:** free game, no ads, no payments, no accounts, no
analytics — squarely on the non-commercial side. **Any monetization step (ads, tips, paid
tiers, sponsorship, merch tied to the game) trips the gate — get the TMDB commercial
agreement conversation started BEFORE the money switch is flipped, not after.** (The gate
was first parked in DESIGN.md §6, a historical doc; the gate itself stands.)

### 1.4 Key confidentiality

The three-zone architecture exists so the key never reaches a player (`CLAUDE.md`). Never
paste the key, `curation/.env` contents, or any TMDB request URL containing the key into a
public artifact — README, issue, screenshot, blog post, demo video, or commit. The grep in
§5 is the pre-publication check.

---

## 2. Content-rights posture (open questions, stated plainly — NOT legal advice)

### 2.1 What is actually shipped (2026-08-14)

**No images. No quotes. No excerpts.** The rebuild deleted every re-hosted still, headshot,
and home-page film quote that the retired dig game shipped — the old imagery-rights posture
is dead (its history is in git). What ships now is **factual credits data**, TMDB-sourced:

| Asset | Detail | Where |
|---|---|---|
| The corpus | 3,682 film titles + years, 9,791 people's names, 42,948 credited-on edges — the entire pool, index-encoded, in a **public repo** | `docs/graph.json` |
| Dailies | Film-id pairs + par + cached endpoint titles; optional one-sentence curator's notes (authored, texture-only) | `docs/challenges.json` |
| Site art | `og.png` (original artwork) and `favicon.svg` — `docs/index.html` carries an explicit comment that **TMDB imagery must never appear** in the unfurl art | `docs/index.html` lines 9–10 |

### 2.2 The honest framing

- Titles, years, names, and who-worked-on-what are **facts** — generally low-risk as
  content (as of training data; not a cleared right, verify before relying). This is a far
  narrower posture than the dig game's re-hosted imagery, but it is still a posture, not
  clearance.
- The data is **TMDB-sourced**, so TMDB's terms govern it: attribution is required (§1.2)
  regardless of how factual the data is, and the non-commercial line (§1.3) applies.
- The whole corpus is **redistributed in bulk** in a public git repo — anyone can download
  the full TMDB-derived dataset, forever. Whether TMDB's terms treat that as ordinary use
  or as data redistribution needing separate permission has **not been evaluated**.

### 2.3 Questions for a lawyer BEFORE monetization or meaningful scale

Take these, verbatim, to qualified counsel — do not attempt to answer them in-repo:

1. Does shipping the full TMDB-derived credits graph in a public repository count as data
   redistribution under TMDB's terms, and does the commercial agreement (§1.3) cover it?
2. Are film titles and cast/crew names as game content a problem anywhere (trademark,
   publicity rights) — and does that change with monetization?
3. What takedown process should we have ready (DMCA agent or equivalent) before scale?

---

## 3. Ecosystem map — what's distinctive here, honestly

### 3.1 Comparable games and prior art

| Game / tradition | One-line mechanic | Verification |
|---|---|---|
| **Six degrees / Oracle of Bacon** | The whole connect-people-through-films tradition; Oracle of Bacon has computed shortest film-connection paths since the 1990s. **The core mechanic here is a daily-game treatment of this known idea — never claim the connection concept itself.** | as of training data — re-verify before public claims |
| **Cine2Nerdle** | **Direct prior art:** movie-connection puzzles — link films via shared cast/crew; also a head-to-head "battle" linking mode | as of training data — re-verify before public claims |
| **Wordle** (NYT) | Daily word guess; origin of the spoiler-free emoji-grid share string and streak culture the whole genre copies | as of training data — re-verify before public claims |
| **Framed** (framed.wtf) | Daily guess-the-film-from-stills — genre neighbor, no longer a mechanic comparison (the dig is retired) | as of 2026-07-03 (framed.wtf) — re-verify before public claims |
| **NYT Connections & likes** | Representative of the broader daily-puzzle share culture | as of training data — re-verify before public claims |

### 3.2 Distinctive claims (the only version you may repeat in public)

State these as **claims with in-repo evidence**, never as "first/only":

- **The whole graph ships once** — the entire pool (188–190 KB gz) is the shipped data;
  a daily is ~50 bytes; no server, no backend, ~200 KB site (`docs/graph.json`,
  `CLAUDE.md` "The one idea").
- **Par/golf scoring against a BFS-computed shortest chain** — par is provably the
  shortest route in the shipped data, asserted at build (`curation/challenge_gen.py`) and
  re-checkable any time (`--check`).
- **Suggestions are global, validation is contextual** — autocomplete draws from the whole
  pool, so it structurally cannot leak the answer (`docs/corpus.js`; the per-challenge-
  subgraph prototype that DID leak was rejected — `CLAUDE.md`).
- **Frozen machine-parseable share line 1** — designed for accountless group-chat leagues
  (Discord bots parsing shares); frozen 2026-08-14 (`CLAUDE.md` "Share grammar").
- **Obscurity score** on wins (`docs/solve.js obscurity()`) and **curator's notes** on the
  end card — texture, hard-checked to never identify a connector (`challenge_gen --check`).

**Known art — never claim as innovations:** film-connection play itself (Cine2Nerdle, the
six-degrees tradition); daily cadence; spoiler-free emoji share strings (Wordle); streaks
and localStorage stats. **All dig-era novelty claims (vertical credit dig, reveal tiers,
per-puzzle sampled theming) are DEAD — the features were deleted. Never repeat them.**

**HARD RULE: "first", "only", "the original", and superlatives are BANNED** unless someone
re-verifies against the live ecosystem **at claim time** and records the check (what was
searched, when). Safe phrasings needing no re-verification: "a daily game about how films
connect," "par is the shortest chain that exists," "the whole site is smaller than one
poster jpeg."

---

## 4. Claim standards — provable vs not

Every public sentence about the game must be one of: (a) reproducible from the repo,
(b) externally verified and dated, or (c) clearly framed as opinion/flavor.

- **Behavior claims** must be reproducible by running the repo's tests: 6 JS suites
  (`node {match,daily,stats,corpus,chain,solve}.test.js`) + 3 Python suites
  (`curation/*.test.py`) + `challenge_gen.py --check` (see degreesoffilm-validation-and-qa
  for the evidence bar).
- **Superiority claims** ("more forgiving than X", "harder than Y") require a defined
  metric AND the comparison actually run and recorded. None has ever been run. So: none
  are currently permitted.
- **NO analytics exists.** Verified 2026-08-14: no analytics/tracking code in `docs/`
  (grep in §5 empty); stats are per-device localStorage only (`docs/stats.js`). Therefore
  **any player-count, engagement, retention, or "players love it" claim is impossible to
  substantiate. Do not make one.** (Flip side you MAY claim: "no tracking, no analytics,
  no accounts.")

| Provable today (with the proof) | NOT provable today (don't claim) |
|---|---|
| Ruleset: attempts, free typos, back(), verdicts (`node chain.test.js`) | Any player count, DAU, "growing fast" |
| Typo-tolerant matching + contextual resolution (`node match.test.js`, `node corpus.test.js`) | "Players find the matching fair" (no data) |
| Par = shortest chain in the shipped data (`challenge_gen.py --check`) | "Fairest difficulty curve" |
| Spoiler-free share: glyph trail, no names ever (`docs/app.js shareText`; grammar in `CLAUDE.md`) | "The most shareable movie game" |
| ~200 KB site, no server, key never shipped (greps + architecture) | "More private than competitors" (no comparison run) |
| **Known and accepted:** future dailies' film pairs ship in `challenges.json` — the pair is the prompt, not the answer; say so plainly if asked, never pretend it's hidden | "Cheat-proof" / "answers hidden" — false; validation is client-side against shipped data |

---

## 5. Going-public checklist

Run ALL of these before any announcement, listing, or press/README push. One numbered pass:

1. **Attribution visible on every public surface** — the footer (§1.2) on the site; notice
   + logo in any README/store/press copy that shows the game. Check:
   `grep -n "otherwise approved by TMDB" docs/index.html` → one hit. Re-check after any
   layout change.
2. **Spoiler sweep of repo history and public surfaces.** Commit messages are public and
   must never name a future daily's chain (endpoint pairs are the public prompt; the
   *route* is the spoiler). Check: `git log --oneline -20` — no connector names.
   `curation/challenge_solutions.json` must be gitignored (`git check-ignore
   curation/challenge_solutions.json` → hit). Curator's notes ship publicly before their
   date — `python curation/challenge_gen.py --check` hard-enforces texture-only; run it.
3. **TMDB terms re-read at announcement time** (themoviedb.org/api-terms-of-use +
   developer.themoviedb.org/docs/faq): still non-commercial? notice wording unchanged?
   (§1.2 rule 4). If anything monetizes: §1.3 gate + §2.3 lawyer questions FIRST.
4. **No key in any published artifact** —
   `grep -rin "api_key\|tmdb_api\|Bearer eyJ" docs/ README.md 2>/dev/null` → must be
   empty; also eyeball screenshots/videos for terminal output containing the key.
5. **Copy passes the claim standards** (§4): no "first/only", no superlatives without a
   run comparison, no player-count claims, no "answers hidden" claims, dig-era features
   never mentioned as current.
6. **Share line 1 untouched** — the grammar is FROZEN as of 2026-08-14 (`CLAUDE.md` "Share
   grammar"): external parsers (Discord-bot leagues) depend on it; line 1 may only ever
   gain content after the final `)`. Any change to `shareText()` re-runs this check and is
   an external-contract change, not a copy tweak.
7. **OG/unfurl art is original** — `og.png` and `favicon.svg` only; the `docs/index.html`
   comment ("TMDB imagery must never appear here") is the rule. No TMDB image may ever
   enter `docs/`.

---

## When NOT to use this skill

| Need | Go to |
|---|---|
| How a change lands (PR vs direct), non-negotiables enforcement | **degreesoffilm-change-control** |
| The evidence bar and test inventory behind §4 | **degreesoffilm-validation-and-qa** |
| Proving a claim from first principles (recipes) | **degreesoffilm-proof-and-analysis-toolkit** |
| TMDB *data model* (endpoints, fields) as used in code | **degreesoffilm-domain-reference** |
| Architecture invariants (key confinement, layering, zones) | **degreesoffilm-architecture-contract** |
| House style for commits/PRs/docs (incl. spoiler-safe commits) | **degreesoffilm-docs-and-writing** |
| Past incidents in full (the dig-era spoiler commits, dead ends) | **degreesoffilm-failure-archaeology** |
| What to build next / research-grade ideas | **degreesoffilm-research-frontier** |
| Turning an idea into an accepted result (evidence discipline) | **degreesoffilm-research-methodology** |

## Reusing this pattern beyond this project

The template transfers to any project built on a third-party data API: (1) quote the
provider's attribution/commercial terms with verification dates and pin the shipped
attribution artifact; (2) separate "API terms compliance" from "underlying content rights"
— different questions with different owners; (3) keep a dated ecosystem table and ban
unverified "first/only" claims; (4) maintain a provable/not-provable table tied to
reproducible checks; (5) gate going-public on a checklist that includes a secret-leak grep
and a history sweep.

## Provenance and maintenance

- **Written 2026-07-03; rewritten 2026-08-14 after the degrees-of-separation rebuild**
  (the dig game and all its shipped imagery were deleted 2026-08-11; launch was
  2026-08-14). In-repo facts verified against this worktree at HEAD `71454d3`: footer
  quoted from `docs/index.html` (lines 120–140); og.png/no-TMDB-imagery comment at
  `docs/index.html` lines 9–10; `shareText` read from `docs/app.js`; corpus numbers from
  `project_state.md` refresh record; the no-key and no-analytics greps in §4–§5 actually
  run (both empty); 9 test suites confirmed present.
- **External facts NOT re-verified for this rewrite** (no web access): TMDB terms/FAQ/rate
  rows carry their 2026-07-03 verification date; Cine2Nerdle, Oracle of Bacon, Wordle,
  Connections rows are as of training data. **Re-verify all of them before any public
  comparison or terms-dependent claim.**
- Re-verify one-liners:
  - Footer intact: `grep -n "otherwise approved by TMDB" docs/index.html`
  - Key/analytics absent: `grep -rin "api_key\|gtag\|analytics" docs/ | head`
  - Solutions sidecar ignored: `git check-ignore curation/challenge_solutions.json`
  - Spoiler-safe recent commits: `git log --oneline -20`
  - Notes texture-only: `python curation/challenge_gen.py --check`
  - TMDB terms current: re-fetch themoviedb.org/api-terms-of-use and
    developer.themoviedb.org/docs/faq (attribution wording + commercial line).
