# Degrees of Film — v1 Design Doc

A daily browser game that tests film knowledge. You're shown a cropped frame from a
film (title hidden), name it, then dig down through its credits from famous to obscure.
How many degrees deep can you go?

> Note on the name: this is a **vertical dig into one film's credits**, not "six degrees
> of separation" (hopping between films via shared people). True degrees-of-separation is
> a clean Mode 2 for later — see the v2 parking lot.

---

## 1. Core ruleset (v1)

**The ladder**
- Rung 1 is special: name the **film** from a cropped frame (poster or still) with no title visible.
- Rungs 2+ are the film's credits, **sorted by TMDB popularity** — most famous first, most
  obscure deeper. Director is *not* locked to a fixed position; it floats by popularity
  like everyone else (usually lands around rung 2–3 on mainstream films).

**Answering**
- Free text, lenient: ignores leading "the", tolerates typos, accepts alternate titles and
  language variants.
- **3 attempts** per rung. The 3rd wrong guess is a strike-out.

**Failure**
- Strike-out (3 wrong on one rung) **ends the run.** Score freezes at depth reached.

**Assists — two lifelines, used in whatever order the player prefers**
- **I Need Help** (3× per game): converts the current rung to multiple choice (built from
  `decoys`, see §4) and caps its value at **0**. You still pick from the options; **a wrong pick
  burns an attempt and strike-out still applies** — the lifeline narrows the odds but never removes
  the risk of ending the run. *(Decided: wrong pick burns an attempt, not a guaranteed pass.)*
- **Skip** (5× per game): total blank, no help — advances you for **−1 point**. A skip beyond
  the 5th ends the run.
- Both advance you a rung, so they add depth but not points — consistent with depth = how far,
  points = how clean. A player naturally spends the 3 cheaper Need-Helps before the 5 Skips.

**Scoring**
- Hero stat: **depth** (rungs reached). The brag number.
- Sub-stat: **points** (tiebreaker — how cleanly you dug).
- Base: rung N is worth N points.
- Deep-dig bonus: starts at rung 6, climbs +1 per rung, caps at +5 from rung 10 onward.

  | Rung | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
  |------|---|---|---|---|---|----|----|----|
  | Points | 5 | 7 | 9 | 11 | 13 | 15 | 16 | 17 |

  (One rung-8 solve banks 11, erasing several earlier skips. Depth and points diverge on
  purpose — two players both 10 deep can have different point totals.)

**Film pool**
- TMDB films clearing `vote_count >= 800 AND vote_average >= 6.5`.
- (Score = "is it good." Vote count = "is it known." The count is your fame proxy — both
  dials, tuned against each other.)
- Never repeat a film (enforced by a master used-films ledger).

**Modes — v1 ships Cinephile only; the other two are sequenced fast-follows**
- **Cinephile** — the rules above, the full dig. **This is v1.**
- **Poser** *(fast-follow)* — all multiple choice, drops the obscure deep rungs, flat **+1**
  per correct answer. A lighter, easier game. Reuses the `decoys` system. No architecture change.
- **Movie Buff** *(fast-follow, gated on the v2 server move)* — Cinephile rules plus a title
  autocomplete on the film rung drawing from **all** TMDB titles (so the dropdown doesn't leak
  which films are eligible). This is the one feature that needs a backend or a large prebaked
  title index — a live TMDB call from the browser would expose the key — so it's tied to the
  server move. See parking lot.
- The **mode-select screen** ships in v1 with Cinephile lit and the other two shown as
  "coming soon," each with a short, funny cinema-term rules blurb.

**Daily & archive**
- Daily puzzle (the hook) + replayable archive of past dailies. No practice/endless in v1.

---

## 2. Architecture — three zones

The whole system splits on one fact: **the API key never leaves your machine.** TMDB only
talks to the private curation tool; players only ever read finished static files.

```
TMDB API
   │  (queried with your key)
   ▼
┌─────────────────────────────────────────────┐
│ PRIVATE — your machine                       │
│   Curation tool (holds API key)              │
│   Used-films ledger (never repeat)           │
└─────────────────────────────────────────────┘
   │  (publishes static files)
   ▼
┌─────────────────────────────────────────────┐
│ STATIC HOSTING — free host                   │
│   Puzzle files (one JSON/day)                │
│   Cropped images (frame + reveal tiers)      │
│   Game site (html · js · css)                │
└─────────────────────────────────────────────┘
   │  (browser fetches files)
   ▼
┌─────────────────────────────────────────────┐
│ PLAYER BROWSER — no key, no server           │
│   Game client (rules + matching)             │
│   Local stats (streak, on device)            │
└─────────────────────────────────────────────┘
```

This is why v1 needs no backend for players: the secret, expensive part runs on your
machine at curation time, not when anyone plays.

---

## 3. Stack

- **Curation tool:** Python (Flask or FastAPI) backend — holds the key in a local `.env`,
  hits TMDB, slices crops with Pillow. Browser frontend for visual cropping (HTML5 canvas
  or Cropper.js). Runs on localhost.
- **Hosting:** GitHub Pages. Puzzle files, images, and the used-films ledger all live in
  the repo (ledger is version-controlled — usage history can't silently corrupt).
- **Game client:** Vanilla / featherweight JS (Alpine or Preact if anything). State is
  tiny; a heavy framework isn't worth it. The real engineering is the fuzzy matching.

---

## 4. Puzzle file format

Each day is one self-contained JSON + its images. (This is also why the archive is nearly
free — a past puzzle is just an old file that still exists.)

```json
{
  "id": 142,
  "date": "2026-06-25",
  "theme": { "accent": "#c98a3d" },
  "images": ["frame-zoom3.jpg", "frame-zoom2.jpg", "frame-full.jpg"],
  "rungs": [
    {
      "role": "Film",
      "prompt": "Name the film.",
      "answers": ["Pan's Labyrinth", "El laberinto del fauno"],
      "decoys": ["The Shape of Water", "Crimson Peak", "The Orphanage"]
    },
    {
      "role": "Director",
      "prompt": "Who directed it?",
      "answers": ["Guillermo del Toro"],
      "decoys": ["Alfonso Cuarón", "Alejandro Iñárritu", "Pedro Almodóvar"]
    }
  ]
}
```

`images` are pre-cropped reveal tiers (most-zoomed first). **The curation tool authors 3 tiers per
puzzle, but the v1 client renders only tier 1** (`images[0]`) — the progressive-crop-reveal hint
was cut (assists are now *I Need Help* + *Skip*), so tiers 2–3 are authored-ahead for a future
reveal mechanic (e.g. reveal-on-wrong-guess; see Phase 3) rather than consumed today. `answers`
arrays — alternate titles and language variants from TMDB — are frozen in at curation time.
Two fields are new:

- **`theme.accent`** — a hex colour sampled from the still at curation time, used as the page
  accent. The ink base and bone text stay fixed for legibility; only the accent shifts. Clamp
  sampled colours to a saturation/contrast floor, and let the curator override an ugly auto-pick.
- **`decoys`** — ~3 plausible wrong answers per rung, same category as the answer (other
  directors for a director rung, other actors for a cast rung), generated at curation. Consumed
  by **I Need Help**'s multiple choice in Cinephile, and by all of Poser later. So MC support is
  a v1 schema + curation requirement, not deferred.

**Daily selection — a `manifest.json` index.** The client never guesses filenames. The curation
tool maintains `docs/puzzles/manifest.json`: an array of `{ date, id, file, title, accent }`, one
entry per published puzzle, appended atomically with the puzzle file + ledger. The client fetches
the manifest, picks the entry whose `date` matches today's canonical date (a single global
rollover, **not** the player's local clock — avoids timezone desync), then fetches that puzzle
file. The archive browser is then a free render of the manifest, and the archive list can show
title/accent without fetching every puzzle. Puzzle files stay date-stamped for readability;
`app.js`'s current hard-coded `fetch('puzzles/001.json')` is the Phase-1 placeholder this replaces.

> v1 ships answers in plaintext (a player can read them in devtools). Acceptable with no
> leaderboard. See v2 parking lot.

---

## 5. Build roadmap

Organizing principle: **prove the loop is fun with one hand-made puzzle before building the
curation machine.** Phases are ordered so you're never blocked waiting on an unbuilt piece.

### Phase 0 — De-risk (no tooling)
- [ ] Hand-author **one** puzzle JSON: pick a film, manually crop an image into 3 tiers,
      hand-list the rungs and accepted answers. No code yet.

### Phase 1 — Prove the fun
- [ ] Game core loop against that one file: render frame, take a guess, advance rungs,
      enforce 3 attempts / skip / strike-out / scoring.
- [ ] **Fuzzy matching** as an isolated, unit-tested module — normalization (lowercase,
      strip diacritics, drop leading "the") + Levenshtein for typos. This is where the
      real hours go; build it test-first against a table of `guess → should-match?` cases.
- [ ] Play it. Is it fun? Is the rung difficulty curve right? Fix the *concept* here,
      cheaply, before investing in tooling.

### Phase 2 — The curation machine (build once fun is proven)
- [ ] Data layer: pull a film clearing the pool floor + not in the ledger; pull credits;
      sort by popularity into rungs. **Validate on several known films** — does popularity
      sorting actually yield a sane easy→obscure ladder? This is the riskiest data
      assumption; prove it before building UI around it.
- [ ] Backend endpoints (Flask/FastAPI): discover-unused-film, build-rungs, crop→3 tiers (Pillow).
- [ ] Crop UI: show poster/still, drag the crop box, preview tiers, approve, write puzzle
      JSON + images + append to ledger. Now you can manufacture real puzzles at will.

### Phase 3 — Make it a daily game
- [ ] Stats + localStorage: best depth, depth histogram, daily streak.
- [ ] **I Need Help** lifeline (3×): convert the rung → multiple choice from `decoys`, value 0.
      Requires decoys in puzzles, so add decoy generation to the curation tool.
- [ ] **Dynamic accent theming** from `theme.accent` (ink base + text fixed; contrast floor).
- [ ] **Home page** — "Welcome to Degrees of Film," rotating short film quotes (keep them short —
      copyright), a script display face. Personality lives here; the play screen stays quiet.
- [ ] **Mode-select screen** — Cinephile lit, Poser + Movie Buff shown "coming soon" with funny blurbs.
- [ ] Daily mechanism — `manifest.json` index (`date` → puzzle file), client picks today's
      canonical date; archive browser renders the manifest. Replaces app.js's hard-coded
      `fetch('puzzles/001.json')`. Manifest entry: `{ date, id, file, title, accent }`.
- [ ] *(Optional)* Reveal mechanic that spends image tiers 2–3 (e.g. a wider crop after a wrong
      guess). Tiers are already authored by the cropper; this only wires them into the client.
- [ ] **TMDB attribution UI** — logo + "uses the TMDB API but is not endorsed/certified by
      TMDB" notice. Mandatory; don't ship without it.
- [ ] Polish + depth-hero share card.

**The two things that decide whether it's fun** (de-risk these earliest): does
popularity-sorting credits produce good ladders, and is the matching forgiving enough to
feel fair? Everything else is execution.

---

## 6. v2 parking lot (deliberately deferred)

- **Poser mode** (fast-follow) — all-MC, trimmed ladder, flat +1. Reuses the `decoys` schema;
  no architecture change. Closest of the deferred items.
- **Movie Buff mode** — all-TMDB title autocomplete on the film rung. Needs a prebaked
  popular-title index or a backend search proxy; gated behind the server move, since a live
  TMDB call from the browser would expose the API key.
- Accounts + database → cross-device stats, global leaderboards.
- Server-side matching → answers never leave the backend (clean fix for the plaintext wart).
- Light obfuscation of client answers (base64/cipher) as an interim anti-snoop measure.
- True **degrees-of-separation** mode (connect film A → film B via a shared person).
- Practice / endless mode (needs its own pool or to draw against the used-ledger).
- Commercial TMDB agreement — required if this ever monetizes or scales as a real product.
