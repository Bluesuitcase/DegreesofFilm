---
name: degreesoffilm-external-positioning
description: >
  The project's relationship to the outside world: TMDB terms and the mandatory attribution
  footer, content-rights posture (re-hosted stills/headshots — open risks, NOT legal advice),
  what is genuinely novel vs known art in the daily-game ecosystem, and the evidence bar for
  any public claim. Load this BEFORE: announcing or sharing the game publicly; writing a
  Product Hunt / Reddit / Hacker News / press / app-store post; writing or editing README or
  marketing copy; answering "can we monetize this?", "is this legal?", "do we need a TMDB
  license?", "can we remove the TMDB footer?"; comparing the game to Framed, Wordle,
  Cine2Nerdle, or any other daily game; or making any "first/only/better-than" claim. Also
  load when a change touches the attribution footer, the home-page quotes, or the share string.
---

# Degrees of Film — external positioning

How this project relates to TMDB, to film rights-holders, and to the daily-game ecosystem —
and what you are allowed to claim in public. This skill exists to **prevent overclaiming**.
When in doubt, claim less.

> **This skill is not legal advice and must never be read as such.** Where rights questions
> arise, it states the open risk plainly and lists questions for a lawyer. Nobody on this
> project is qualified to clear a rights question, and no document in this repo does.

---

## 1. The TMDB relationship

### 1.1 Integration shape (what TMDB actually powers)

| Fact | Detail | Source |
|---|---|---|
| Where the API is called | **Curation time only**, from the private `curation/` tool on the owner's machine | `CLAUDE.md` "Architecture — three zones" |
| What players fetch | Finished static files under `docs/` (GitHub Pages). **No player request ever touches TMDB.** | `CLAUDE.md`; `docs/app.js` fetches only `puzzles/*` |
| Key location | `curation/.env`, gitignored. Never in `docs/`, never in git history. | verified: `grep -rin "api_key\|tmdb_api" docs/` → no hits (2026-07-03) |
| Data used | Film details + credits, recommendations/similar (decoys), person headshots, backdrops/posters (frames) | `curation/build_rungs.py`, `decoys.py`, `credits_images.py`, `images.py` |
| Usage volume | A handful to a few dozen requests **per puzzle authored** (one credits fetch, ~2 neighbour-list fetches, up to 8 neighbour-credits fetches for decoys, plus image downloads). One puzzle per day. Modest by any measure. | `curation/decoys.py` (`source_limit=8`), `build_rungs.py` |
| TMDB rate ceiling | "somewhere in the 40 requests per second range" — verified 2026-07-03 against developer.themoviedb.org/docs/rate-limiting | external |

Consequence for positioning: you may truthfully say "built with TMDB data" and "no tracking,
no backend, no API calls from your browser." You may NOT imply TMDB endorsement (see below —
the required notice says the opposite).

### 1.2 The attribution obligation — the footer never comes off

DESIGN.md §5 lists this as a ship-blocker: "**TMDB attribution UI** — logo + 'uses the TMDB
API but is not endorsed/certified by TMDB' notice. Mandatory; don't ship without it." It
shipped in commit `c2f59c3` ("Phase 3: TMDB attribution footer (ship-blocker)") and is live
in `docs/index.html` (lines 120–140 as of 2026-07-03):

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
  <p>This product uses the TMDB API but is not endorsed or certified by TMDB.</p>
</footer>
```

**Rules:**

1. **The footer never comes off.** Removing or hiding it violates change control
   (degreesoffilm-change-control lists attribution among the non-negotiables). There is no
   legitimate change that requires its removal.
2. Any **new public surface** (a store listing, a native wrapper, a second page, a v3
   server-rendered page) needs the same notice + logo. TMDB requires attribution on the
   application, not just one page of it.
3. Note the in-repo comment above the footer: the SVG is a **rendition** of the TMDB mark,
   not the official logo file. For strict brand compliance (i.e., before any high-visibility
   launch), swap in an official logo from themoviedb.org/about/logos.
4. **Wording drift check** (verified 2026-07-03 against themoviedb.org/api-terms-of-use):
   TMDB's current terms phrase the notice as "uses TMDB and the TMDB APIs but is not
   endorsed, certified, or otherwise approved by TMDB." The shipped footer uses the older
   FAQ wording ("uses the TMDB API but is not endorsed or certified by TMDB"), which still
   appears on developer.themoviedb.org/docs/faq (verified 2026-07-03). Before a public
   launch, re-read the current terms and update the sentence if TMDB's required wording has
   moved — that update goes through change control like any `docs/` edit.

### 1.3 The non-commercial / commercial line (as TMDB draws it)

Verified 2026-07-03 against developer.themoviedb.org/docs/faq and
themoviedb.org/api-terms-of-use:

- The API is "free to use for non-commercial purposes as long as you attribute TMDB as the
  source." A project counts as commercial if "the primary purpose is to create revenue for
  the benefit of the owner."
- Commercial activity — charging users, selling an app that integrates TMDB, using the
  content on revenue-generating sites — requires a **separate written agreement**
  (contact: sales@themoviedb.org).
- The terms also prohibit using TMDB "as an image hosting service for banner advertisements,
  graphics, etc." and prohibit use "in connection with, including for training, a machine
  learning (ML) or artificial intelligence (AI) based Application."

**Where this project stands today:** free game, no ads, no payments, no accounts, no
analytics — squarely on the non-commercial side. DESIGN.md §6 parks the gate explicitly:
"**Commercial TMDB agreement** — required only if this ever monetizes or scales as a real
product." **Any monetization step (ads, tips, paid tiers, sponsorship, merch tied to the
game) trips that gate — get the TMDB commercial agreement conversation started BEFORE the
money switch is flipped, not after.**

### 1.4 Key confidentiality

The whole three-zone architecture exists so the key never reaches a player (`CLAUDE.md`).
Never paste the key, `curation/.env` contents, or any TMDB request URL containing the key
into a public artifact — README, issue, screenshot, blog post, demo video, or commit. The
grep in §5 is the pre-publication check.

---

## 2. Content-rights posture (open risks, stated plainly — NOT legal advice)

### 2.1 What is actually re-hosted

| Asset | Origin | Where it lives now | Volume (2026-07-03) |
|---|---|---|---|
| Film frames (3 reveal tiers per puzzle) | TMDB-hosted backdrops/posters, cropped by `curation/images.py` | `docs/puzzles/images/NNN-{1,2,3}.jpg` in the **public** GitHub repo, served by GitHub Pages | 7 puzzles |
| Credit headshots | TMDB person profile images | `docs/puzzles/images/NNN-rK.jpg`, same repo | ~92 files total in `docs/puzzles/images/` |
| Film quotes | Hand-picked one-liners on the home page | `docs/app.js` `QUOTES` | 6 quotes, kept deliberately short — DESIGN §5: "rotating short film quotes (keep them short — copyright)" |
| Film titles / people's names as answers | TMDB data | puzzle JSONs (obfuscated on disk) | all puzzles |

### 2.2 The honest framing

- **TMDB's terms cover access to TMDB's API and services.** TMDB asserts ownership of the
  APIs ("TMDB owns all rights, title, and interest in and to the TMDB APIs" — verified
  2026-07-03 against themoviedb.org/api-terms-of-use). The **underlying film images**
  (posters, backdrops, stills) are the studios'/rights-holders' property — as of training
  data, TMDB's image library is community-contributed artwork whose copyright TMDB does not
  itself hold; verify before relying. **Complying with TMDB's terms does not clear the
  images themselves.**
- The game's use — low-resolution crops, in a trivia/commentary context, non-commercial,
  one film per day — is a **fair-use-shaped posture, not a cleared right**. Nobody has
  evaluated it; no license covers it. The same is true of the home-page quotes (short,
  deliberately so) and, to a much lesser degree, titles and names (facts/short phrases are
  generally low-risk — as of training data; verify before relying).
- Re-hosting the images in a **public git repository** means they are downloadable in bulk
  by anyone, forever, in history even if later deleted. That is a broader distribution than
  "shown in a game" and is part of the exposure.
- **Risk today is plausibly low** (tiny audience, no revenue, transformative-leaning use)
  but that is a *posture assessment*, not advice, and the calculus changes completely with
  scale or money.

### 2.3 Questions for a lawyer BEFORE monetization or meaningful scale

Take these, verbatim, to qualified counsel — do not attempt to answer them in-repo:

1. Does re-hosting cropped film stills and person headshots in a public repo + static site
   qualify for a fair-use (or local-equivalent) defense in the jurisdictions we'd operate
   in, and does that survive monetization?
2. Do the home-page film quotes, at their current length, need clearance — and does daily
   rotation change anything?
3. Are film titles and cast/crew names as quiz answers a problem anywhere (trademark,
   publicity rights for the headshots specifically)?
4. Does the TMDB commercial agreement (§1.3 gate) cover the images, or only the API/data —
   i.e., would we ALSO need studio-side clearance?
5. What takedown process should we have ready (DMCA agent or equivalent) before scale?

Cross-reference: the DESIGN §6 "Commercial TMDB agreement" parking-lot item is the in-repo
gate; treat "talk to a lawyer" as an implicit second gate that trips at the same time.

---

## 3. Ecosystem map — what's novel here, honestly

### 3.1 Comparable games

| Game | One-line mechanic | Verification |
|---|---|---|
| **Framed** (framed.wtf) | Daily: "Guess the film from 6 frames" — each wrong guess reveals another still; variant modes (one frame, title shots, posters) | **verified 2026-07-03 against framed.wtf** |
| **Wordle** (NYT) | Daily word guess; origin of the spoiler-free emoji-grid share string and streak culture the whole genre copies | as of training data — verify before relying |
| **Cine2Nerdle** | Movie-connection puzzles — link films via shared cast/crew on a grid; also a head-to-head "battle" linking mode | as of training data — verify before relying |
| **Actorle** | Daily: guess the actor from a filmography of redacted titles/genres/years | as of training data — verify before relying |
| **NYT Connections & likes** | Daily: group 16 items into 4 hidden categories; representative of the broader daily-puzzle share culture | as of training data — verify before relying |

### 3.2 Novelty analysis (the only version you may repeat in public)

**Genuinely distinctive here** (no prior art found among the §3.1 comparables, most rows
as-of-training-data — but see the ban below before saying "first"):

- The **vertical credit dig**: one film, then down through ITS credits famous→obscure, with
  **depth as the brag stat**. Comparable games guess one thing or hop between films;
  none found digs a single film's credit ladder.
- The **billing-order famous→obscure ladder** as a difficulty curve (TMDB billing order,
  director floated early, technical crew deepest — `CLAUDE.md` v1 ruleset; de-risked in
  `curation/validate_ladder.py`).
- **Per-puzzle sampled theming** — accent + background tones sampled from the day's still
  (`curation/images.py`, `docs/theme.js`).
- **Curator-authored reveal tiers** — three pre-cropped zoom levels spent on wrong guesses
  (`docs/frame.js`), vs Framed's new-still-per-guess.

**Known art — never claim these as innovations:** daily cadence; guess-a-film-from-a-still
(Framed's core loop, live since ~2022 — as of training data); spoiler-free emoji share
strings (Wordle); streaks and localStorage stats; multiple-choice easy modes.

**HARD RULE: "first", "only", "the original", and superlatives ("the hardest movie game")
are BANNED** unless someone re-verifies against the live ecosystem **at claim time** and
records the check (what was searched, when). The table above is a snapshot; it goes stale.
Safe phrasings that need no re-verification: "a different kind of film game," "not another
guess-the-still game — you dig," "depth is the score."

---

## 4. Claim standards — provable vs not

Every public sentence about the game must be one of: (a) reproducible from the repo,
(b) externally verified and dated, or (c) clearly framed as opinion/flavor.

- **Behavior claims** ("typo-tolerant matching", "3 reveal tiers", "spoiler-free share")
  must be reproducible by running the repo's tests/scripts — the 16 offline suites and the
  content validator (see degreesoffilm-validation-and-qa for the evidence bar and
  degreesoffilm-diagnostics-and-tooling `scripts/validate_content.py` for content checks).
- **Superiority claims** ("more forgiving than X", "harder than Y") require a defined
  metric AND the comparison actually run and recorded. None has ever been run. So: none
  are currently permitted.
- **NO analytics exists.** Verified 2026-07-03: no analytics/tracking code in `docs/`
  (`grep -rin "gtag\|analytics\|plausible\|umami" docs/*.js docs/*.html` → no hits); stats
  are per-device localStorage only (`docs/stats.js`). Therefore **any player-count,
  engagement, retention, or "players love it" claim is impossible to substantiate. Do not
  make one.** (Flip side you MAY claim: "no tracking, no analytics, no accounts.")

| Provable today (with the proof) | NOT provable today (don't claim) |
|---|---|
| Game rules & scoring curve (`node game.test.js` — asserts the 1,2,3,4,5,7,9,11,13,15,16,17 curve) | Any player count, DAU, streak stats, "growing fast" |
| Fuzzy-matching behavior incl. typo tolerance + surname rule (`node match.test.js`) | "Players find the matching fair" (no data) |
| Spoiler-free share format (`docs/app.js` `shareText`: `🎬 Degrees of Film #N` + depth bar of 🟫/⬛ — no title, no answers) | "The most shareable movie game" |
| No tracking / no backend for players / key never shipped (greps above + architecture) | "More private than competitors" (no comparison run) |
| Daily puzzle + archive + 3 modes exist and work (play them; `node daily.test.js`) | "Harder/deeper than Framed" (no metric defined) |
| Answers obfuscated on disk (`node cipher.test.js`) — describe as "anti-peek", **never as "secure"** (CLAUDE.md: "not real security") | "Cheat-proof" — false until v3 server-side matching (degreesoffilm-server-move-campaign) |

---

## 5. Going-public checklist

Run ALL of these before any announcement, listing, or press/readme push. One numbered pass:

1. **Attribution visible on every public surface** — the footer (§1.2) on the site; notice +
   logo in any README/store/press copy that shows the game. Re-check after any layout change.
2. **Spoiler sweep of the repo history and public surfaces.** Commit messages are public.
   Two historical commits named upcoming films — `bdca151` named puzzle 006's film in its
   subject, and `3d7d17e` named puzzle 007's film before its date — the lesson behind the
   rule: content commits say puzzle NUMBER/date only until the date passes (history was NOT
   rewritten; don't). Check: `git log --oneline -20` — no future-dated puzzle's film named.
   **Known OPEN spoiler issue in the home-page QUOTES as of 2026-07-03** (puzzle 4's and
   puzzle 6's films quoted) — full account: degreesoffilm-failure-archaeology entry 12.
   **Do not announce publicly while home-page quotes name puzzle films**; check current
   state with the validator's quotes-vs-ledger group, or cross-check `QUOTES` titles
   against `curation/used_films.json`.
3. **TMDB terms re-read at announcement time** (themoviedb.org/api-terms-of-use +
   developer.themoviedb.org/docs/faq): still non-commercial? notice wording unchanged?
   (§1.2 rule 4). If anything monetizes: §1.3 gate + §2.3 lawyer questions FIRST.
4. **Quota headroom sanity** — usage is ~tens of requests per puzzle (§1.1) vs a ~40 req/s
   ceiling; fine. Re-assess only if adding bulk/automated curation.
5. **No key in any published artifact** —
   `grep -rin "api_key\|tmdb_api\|Bearer eyJ" docs/ README.md 2>/dev/null` → must be empty;
   also eyeball screenshots/videos for terminal output containing the key.
6. **Copy passes the claim standards** (§4): no "first/only", no superlatives without a run
   comparison, no player-count claims, obfuscation never called "secure".
7. **Share string still spoiler-free** — `docs/app.js` `shareText` emits only puzzle number,
   mode tag, depth/score, and the emoji bar. Any change to it re-runs this check.

---

## When NOT to use this skill

| Need | Go to |
|---|---|
| How a change lands (PR vs direct), non-negotiables enforcement | **degreesoffilm-change-control** |
| The evidence bar, test inventory, content QA before publishing a puzzle | **degreesoffilm-validation-and-qa** |
| Running the content validator / measurement scripts cited in §4 | **degreesoffilm-diagnostics-and-tooling** |
| TMDB *data model* (endpoints, billing order, image URLs) as used in code | **degreesoffilm-domain-reference** |
| The v3 server move (server-side matching, accounts, leaderboard) | **degreesoffilm-server-move-campaign** |
| House style for commits/PRs/docs (incl. the spoiler-safe commit template) | **degreesoffilm-docs-and-writing** |
| Architecture invariants (key confinement, layering, spoiler discipline as invariants) | **degreesoffilm-architecture-contract** |
| Past incidents in full (the spoiler commits, character-stills dead end) | **degreesoffilm-failure-archaeology** |

## Reusing this pattern beyond this project

The template transfers to any project built on a third-party data API: (1) quote the
provider's attribution/commercial terms with verification dates and pin the shipped
attribution artifact; (2) separate "API terms compliance" from "underlying content rights"
— they are different questions with different owners; (3) keep a dated ecosystem table and
ban unverified "first/only" claims; (4) maintain a provable/not-provable two-column table
tied to reproducible checks; (5) gate going-public on a checklist that includes a
secret-leak grep and a history sweep. Project-specific: TMDB specifics, the spoiler
discipline, the exact hashes and file paths.

## Provenance and maintenance

- **Written 2026-07-03.** In-repo facts verified against the working tree at HEAD `10668ca`
  (clean): footer quoted from `docs/index.html` (lines 120–140); `shareText` and `QUOTES`
  read from `docs/app.js`; ledger from `curation/used_films.json`; DESIGN §5/§6 items and
  commit hashes `c2f59c3`/`bdca151`/`3d7d17e` confirmed via `git log`/`git show`; the
  no-key and no-analytics greps in §4–§5 actually run (both empty).
- **External facts verified live 2026-07-03**: TMDB FAQ (developer.themoviedb.org/docs/faq),
  TMDB API terms (themoviedb.org/api-terms-of-use), rate limits
  (developer.themoviedb.org/docs/rate-limiting), Framed (framed.wtf). Cine2Nerdle, Actorle,
  Wordle/Connections rows are **as of training data — re-verify before public comparison**.
- Re-verify one-liners:
  - Footer intact: `grep -n "not endorsed or certified by TMDB" docs/index.html`
  - Key/analytics absent: `grep -rin "api_key\|gtag\|analytics" docs/ | head`
  - QUOTES-vs-puzzles conflict: compare `grep -n "QUOTES = \[" -A 8 docs/app.js` titles
    against `curation/used_films.json`
  - Spoiler-safe recent commits: `git log --oneline -20`
  - TMDB terms current: re-fetch themoviedb.org/api-terms-of-use and
    developer.themoviedb.org/docs/faq (attribution wording + commercial line).
- If the QUOTES incident gets fixed, or the footer wording is updated to TMDB's newer
  phrasing, update §1.2/§5 and this date in the same session.
