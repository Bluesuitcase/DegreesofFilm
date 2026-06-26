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

**Failure & skips**
- Strike-out (3 wrong on one rung) **ends the run.** Score freezes at depth reached.
- Skips: blank on a rung you don't know, forfeit it, keep climbing. Each skip costs **−1 point**.
- Up to **5 skips** total. Needing a skip beyond the 5th ends the run.

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

**Modes**
- Daily puzzle (the hook) + replayable archive of past dailies. No practice/endless in v1.

**Open detail to finalize:** hint cost. Two hint tiers exist — progressive crop reveal
(show more of the frame), then multiple-choice options. Recommendation: hints cost points,
and the share card carries a clean/assisted flag so the depth brag stays honest.

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
  "images": ["frame-zoom3.jpg", "frame-zoom2.jpg", "frame-full.jpg"],
  "rungs": [
    { "role": "Film",            "answers": ["Pan's Labyrinth", "El laberinto del fauno"] },
    { "role": "Director",        "answers": ["Guillermo del Toro"] },
    { "role": "Cinematographer", "answers": ["Guillermo Navarro"] }
  ]
}
```

`images` are pre-cropped reveal tiers (most-zoomed first). `answers` arrays — including
alternate titles and language variants from TMDB — are frozen in at curation time. The
client just shows tier 1, then 2, then 3 as reveal hints are spent.

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
- [ ] Hint tiers: progressive crop reveal, then multiple-choice options (+ finalize cost).
- [ ] Daily mechanism (which puzzle is "today") + archive browser.
- [ ] **TMDB attribution UI** — logo + "uses the TMDB API but is not endorsed/certified by
      TMDB" notice. Mandatory; don't ship without it.
- [ ] Polish + depth-hero share card.

**The two things that decide whether it's fun** (de-risk these earliest): does
popularity-sorting credits produce good ladders, and is the matching forgiving enough to
feel fair? Everything else is execution.

---

## 6. v2 parking lot (deliberately deferred)

- Accounts + database → cross-device stats, global leaderboards.
- Server-side matching → answers never leave the backend (clean fix for the plaintext wart).
- Light obfuscation of client answers (base64/cipher) as an interim anti-snoop measure.
- True **degrees-of-separation** mode (connect film A → film B via a shared person).
- Practice / endless mode (needs its own pool or to draw against the used-ledger).
- Commercial TMDB agreement — required if this ever monetizes or scales as a real product.
