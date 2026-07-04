---
name: degreesoffilm-domain-reference
description: >-
  Domain-theory reference for Degrees of Film — the concepts a mid-level engineer
  or model won't already know, grounded in this repo's code. Load it WHEN: any
  question about TMDB (endpoints, fields, billing order vs popularity, image URLs,
  vote_count/vote_average, headshots vs backdrops); why a player's guess matched
  or didn't match (normalization, Levenshtein, typo tolerance, surname rule);
  before changing docs/match.js in any way; anything about crop tiers, auto-crop,
  edge energy, Haar face detection, or the OpenCV pin; accent/background color
  math (luminance, contrast, HSV clamps, WCAG); daily rollover, streak, manifest,
  or share-string behavior; or when a project term (rung, ladder, depth, tier,
  decoy, runway, sentinel, pool floor…) needs a definition — the canonical
  glossary lives here.
---

# Degrees of Film — domain reference

This skill teaches the *theory* behind the project's four specialty domains — TMDB's
data model, fuzzy string matching, image saliency math, and color/daily-game
conventions — exactly as this repo uses them. Every behavioral claim is cited to a
repo file; every worked example was actually executed on 2026-07-03. It explains
*why the code is the way it is*; for how to run things see
`degreesoffilm-run-and-operate`, for changing things see `degreesoffilm-change-control`.

## 1. Glossary (canonical — other skills point here)

| Term | Meaning here |
|---|---|
| **rung** | One question in a puzzle. Rung 1 = name the film from a cropped frame; rungs 2+ = its credits. Schema: `{ role, prompt, answers[], decoys[], image?, caption? }` (`docs/puzzles/*.json`). |
| **ladder** | The ordered list of rungs, famous → obscure: film → top cast → director → rest of cast → technical crew (`curation/build_rungs.py`). |
| **depth** | How many rungs the player passed — the hero/brag stat (`docs/game.js`). |
| **score** | The tiebreaker: sum of `scoreForRung(n)` for solved rungs, minus 1 per skip. Two players at equal depth can differ on score. |
| **tier** | One of up to 3 pre-cropped versions of the frame image, most-zoomed first (`images[]` in the puzzle JSON; authored by `curation/images.py` with factors `(1.0, 1.8, None)`). |
| **reveal** | The mechanic that widens the film-rung crop one tier per wrong guess (`docs/frame.js` `pickCreditFrame(revealTier)`). |
| **decoy** | A plausible same-category wrong answer (~3 per rung, from neighbour films' credits — `curation/decoys.py`). Feeds I-Need-Help's multiple choice and all of Poser. Stored in **plaintext** (it's player-facing, not the answer). |
| **lifeline** | Either **Skip** (advance for −1 point, max 5/game) or **I Need Help** (convert a rung to multiple choice, caps its value at 0, max 3/game) (`docs/game.js`). |
| **strike-out** | Third wrong guess on a rung — ends the run (`MAX_ATTEMPTS = 3`, `docs/game.js`). |
| **manifest** | `docs/puzzles/manifest.json` — the sole daily index: array of `{ date, id, file, title, accent }` with `title` obfuscated. The client's only way to find puzzles. |
| **ledger** | `curation/used_films.json` — films already made into puzzles, so no film ever repeats (`curation/ledger.py`). |
| **runway** | Consecutive stocked days from today in the schedule view (`curation/publish.py` `runway()`). Runway 0 = tomorrow is empty. |
| **Cinephile / Poser / Movie Buff** | Game modes. Cinephile = the default full text-input dig. Poser = all-multiple-choice, trimmed to 7 decoy-bearing rungs, flat +1 scoring. Movie Buff = **not built**; a live browser TMDB call is BANNED (key leak) — needs either the v3 server move or a prebaked title index (see degreesoffilm-research-frontier 2b). |
| **billing order** | TMDB's `cast[].order` — the film's own credit order, lead = 0. Encodes importance *in this film*, unlike rolling popularity. The cast sort key (`curation/build_rungs.py`). |
| **pool floor** | Minimum fame bar for a puzzle film: TMDB `vote_count >= 800 AND vote_average >= 6.5` (`curation/discover.py`; DESIGN §1). |
| **sentinel** | U+0001, the one-char prefix marking a string as cipher-obfuscated. No real title contains it and base64 never produces it, so encoding is self-identifying and idempotent (`docs/cipher.js`, `curation/cipher.py`). |
| **headshot vs still vs backdrop vs poster** | *Headshot* = a person's TMDB `profile_path` portrait (used for every credit-rung image). *Backdrop* = a wide movie image (`backdrops[]` — the crop-source "stills"). *Poster* = the vertical one-sheet (offered as a last crop source). "Still" in this repo = the frame the curator crops, sourced from backdrops + poster (`curation/app.py` `_film_stills`). |

## 2. TMDB data model as used here

TMDB (The Movie Database) is a community-maintained film database with a free REST
API, version 3. This repo calls it **only from the private curation tool** — never
from the player client. The key lives in gitignored `curation/.env`; the client
(`curation/tmdb.py`) passes it as an `api_key=` query parameter and **never logs a
URL** (URLs carry the key). Newer TMDB docs prefer a bearer-token header (as of
training data — verify at developer.themoviedb.org); this repo's query-param form
is TMDB v3's classic style and works as coded.

| Endpoint | Used for | Key fields consumed | Calling file |
|---|---|---|---|
| `GET /discover/movie` | Find candidate films clearing the pool floor (Discover list, Randomize) | `results[].{id,title,release_date,vote_count,vote_average,popularity,backdrop_path}`, `total_pages` | `curation/discover.py`, `curation/app.py` |
| `GET /search/movie` | Free-text title search (curation UI + CLIs) | same as above, plus `used` flagging via the ledger | `curation/tmdb.py` `search_movie`, `curation/app.py` `api_search` |
| `GET /movie/{id}?append_to_response=credits` | The film + full credits in one call — the ladder's raw material | `title`, `original_title`, `credits.cast[].{id,name,character,order,popularity,profile_path}`, `credits.crew[].{id,name,job,popularity,profile_path}` | `curation/tmdb.py` `movie_with_credits` |
| `GET /movie/{id}/images` | Crop-source stills | `backdrops[].file_path` (first 12) + the movie's `poster_path` | `curation/app.py` `_film_stills` |
| `GET /movie/{id}/recommendations` then `/similar` | Neighbour films whose credits become decoy pools (recommendations first, similar as fallback) | `results[].{id,title,vote_count,popularity}` | `curation/decoys.py` `_source_films` |

> **⚠️ THE billing-vs-popularity trap — the project's foundational data lesson.**
> TMDB `popularity` is a **rolling, current-attention metric** (trending searches,
> recent releases), **not** fame-for-this-film. Sorting a film's credits by
> popularity produced nonsense ladders: it buried Heath Ledger's Joker at rung 13
> and sank Tommy Lee Jones below a one-scene bit player (evidence:
> `curation/validate_ladder.py`, the throwaway A/B de-risk script; DESIGN §5).
> The adopted rule: **cast sorts by billing order (`cast[].order`, lead = 0),
> popularity only breaks ties** — `curation/build_rungs.py` `order_cast` key is
> `(order, -popularity)`. Never "improve" a ladder by re-sorting on popularity;
> this battle is settled (see `degreesoffilm-failure-archaeology`).

**Ladder assembly** (`curation/build_rungs.py` `order_rungs`): film rung, then the
top `director_after=2` billed cast, then the Director, then remaining cast, then
deep crew in fixed order — Cinematographer (job `"Director of Photography"`),
Composer (`"Original Music Composer"`), Editor, Production Designer (`"Production
Design"`). **Writer is deliberately NOT a rung** (matches DESIGN §1 and puzzle 001).
Crew is matched by exact `job` string — TMDB jobs are free-ish text, so a film
crediting, say, "Music" instead of "Original Music Composer" simply yields no
Composer rung (`crew_rung` returns `None` and the role is skipped). Note the
default/override split: `order_rungs(max_cast=8)` but the tool passes `max_cast=6`
(`curation/app.py` `api_film`) — see `degreesoffilm-config-and-flags`.

**Image URL composition**: full URL = base + size + `file_path`, e.g.
`https://image.tmdb.org/t/p/original/xyz.jpg`. This repo always uses the size
segment `original` (`IMG_BASE` in `curation/credits_images.py` and
`curation/app.py`). Other sizes (`w500` etc.) exist and the `/configuration`
endpoint lists them (verified against developer.themoviedb.org/docs/image-basics,
2026-07-03) — unused here because images are downloaded once at curation time and
re-cropped/re-encoded locally anyway.

**Paging cap**: TMDB hard-caps list paging at **500 pages** — `curation/app.py`
`api_random` clamps `total_pages` to 500 before rolling a random page (line-level
comment in the code; also TMDB-documented as of training data).

**Key hygiene**: `curation/tmdb.py` never prints request URLs; its 401 handler
reports only `HTTP 401 (check your TMDB_API_KEY) on {path}` — path without query
string. Keep that property in any new TMDB code. Attribution to TMDB is a shipped
obligation (footer in `docs/index.html`) — terms, commercial line, and the exact
wording live in `degreesoffilm-external-positioning`.

Deeper per-endpoint parameter detail: [`references/tmdb.md`](references/tmdb.md).

*Where this bites you:* curation endpoints returning 500/401, empty search, or a
weird ladder → `degreesoffilm-debugging-playbook`; the `max_cast`/pool-floor knobs →
`degreesoffilm-config-and-flags`.

## 3. Fuzzy matching theory (`docs/match.js`)

This module decides whether the game *feels fair*. It has **no imports** (bottom of
the layering law) and a contract test table, `match.test.js` (25 cases mirroring
puzzle 001). **Rule: add a failing test case there before touching the algorithm.**

### 3.1 Normalization pipeline

`normalize(s)` canonicalizes both the guess and every accepted answer before any
comparison, so trivia knowledge is tested, not orthography. The stages, in order
(`docs/match.js` lines 4–13), with a real executed trace (2026-07-03):

| Stage | Operation | `"Amélie"` | `"The Lord of the Rings: The Return of the King"` | `"Joel & Ethan Coen"` |
|---|---|---|---|---|
| 1 | lowercase | `amélie` | `the lord of the rings: the return…` | `joel & ethan coen` |
| 2 | NFD-decompose, strip combining marks U+0300–U+036F (removes diacritics) | `amelie` | *(unchanged)* | *(unchanged)* |
| 3 | `&` → `" and "` | — | — | `joel  and  ethan coen` |
| 4 | non-`[a-z0-9\s]` → space (punctuation gone; note the colon) | — | `the lord of the rings  the return…` | — |
| 5 | collapse whitespace, trim | — | `the lord of the rings the return of the king` | `joel and ethan coen` |
| 6 | drop ONE leading article (`the`/`a`/`an`) | — | `lord of the rings the return of the king` | — |

Stage 2 works because Unicode NFD splits `é` into `e` + a combining accent, and
combining accents live in the block U+0300–U+036F — deleting them leaves the base
letter. Stage 6 removes only a *leading* article, once: interior "the"s survive
(see the LOTR trace), and "The The" would lose one "The". Non-Latin scripts
normalize to empty (every char is punctuation to stage 4); `matchGuess` skips
empty answers, so a Chinese-script alternate title in `answers[]` is inert, not
harmful.

### 3.2 Levenshtein distance and `maxDist`

**Levenshtein distance** = the minimum number of single-character **insertions,
deletions, or substitutions** to turn one string into another (each costs 1 —
there is no transposition/swap operation, so `teh`→`the` costs 2, not 1).
`docs/match.js` implements the classic dynamic-programming algorithm with the
**two-row optimization**: instead of the full (m+1)×(n+1) edit-distance matrix it
keeps only the previous and current rows, since each cell needs only its left,
upper, and upper-left neighbours — O(m·n) time, O(n) memory.

A guess is accepted when `levenshtein(guess, answer) <= maxDist(answer.length)`
(both post-normalization). Tolerance scales with the answer's length because a
fixed budget would be either useless for long titles or catastrophic for short
ones — with distance 1, `up` matches `us`, but `casablanca` shouldn't need a
perfect keyboard:

| normalized answer length | `maxDist` | intuition |
|---|---|---|
| ≤ 3 | 0 | `Up`, `Her`: any edit is a different word |
| ≤ 6 | 1 | one typo in a short name |
| ≤ 10 | 2 | `javier bardem` is 13 → next row, but `deakins`-scale names land here |
| > 10 | `floor(len * 0.2)` | ~1 typo per 5 chars |

Executed (2026-07-03): `levenshtein("javier bardum","javier bardem")` = **1**,
`maxDist(13)` = **2** → "Javier Bardum" matches. `maxDist(23)` = **4**, so
"No Country for Old Man" (distance 1) matches the full title. The generous 20%
band is deliberate: answers are proper nouns from a *closed set shown to no one*,
so near-misses are almost always the intended person. (The decoy generator excludes
the answers themselves from decoy pools, `curation/decoys.py` `pick_decoys`, but by
*exact* normalized name — nothing guards against a decoy landing within typo
distance of an answer; that's part of the pre-publish human review.)

### 3.3 The surname rule

If the guess is a **single token** and equals the **last token** of a multi-token
answer, it matches (`docs/match.js` lines 49–52): players say "Bardem", not
"Javier Bardem". Executed (2026-07-03):

- `matchGuess("Bardem", ["Javier Bardem"])` → `true`
- `matchGuess("Joel", ["…", "Joel Coen", …])` → **`false`** — first names do NOT
  match; "Joel" is not the *last* token of any answer.
- `matchGuess("Coen", [director answers])` → `true` (last token of "Joel Coen").
- `matchGuess("Roger Moore", ["Roger Deakins"])` → `false` — two tokens, so the
  surname rule never fires; and `match.test.js` pins "right first name wrong
  surname" as a rejection.

Deliberate tradeoffs: last-token-only means Spanish-style double surnames or
"Jr."-suffixed names credit only the final token ("García Bernal" → only "Bernal"
works as a single token); the fix is listing alternate forms in `answers[]`, never
matcher special-cases. Multi-word titles get no such shortcut — "Return of the
King" for the full LOTR title returns `false` (executed 2026-07-03): the rung
would need that alternate cut listed as an answer.

### 3.4 What the matcher deliberately does NOT do

No phonetic matching (Soundex/Metaphone), no token reordering ("Bardem Javier"
fails), no substring/containment matching, no per-rung thresholds. Each would
widen false-accepts in hard-to-reason-about ways (substring matching alone would
make "the" match half the catalog pre-normalization, and any partial title). The
project's escape valve is **data, not code**: every legitimate alternate form —
foreign-language titles, pseudonyms (editor "Roderick Jaynes" *is* the Coens),
name variants, "The Coens" — is an extra string in that rung's `answers[]`
(`match.test.js`; `curation/build_rungs.py` seeds `original_title` automatically).
That keeps the algorithm small, testable, and shared by every rung.

*Where this bites you:* "player says a fair guess was rejected" triage →
`degreesoffilm-debugging-playbook`; the maxDist thresholds are code constants, not
config → `degreesoffilm-config-and-flags`.

## 4. Image & saliency math (`curation/images.py`, `docs/frame.js`)

### 4.1 Concentric reveal tiers

The curator picks one tight crop box; `expand_boxes` derives all tiers by scaling
that box about its **centre** by factors `(1.0, 1.8, None)` — `None` = full frame —
each clamped inside the image. Executed (2026-07-03) on a 1920×1080 frame with box
`(760, 340, 1160, 740)`:

```
factor 1.0  -> (760, 340, 1160, 740)     tier 1: the tight crop
factor 1.8  -> (600, 180, 1320, 900)     tier 2: same centre, 1.8x each side
factor None -> (0, 0, 1920, 1080)        tier 3: full frame
```

**Aspect coupling**: tiers 1–2 inherit the *box's* aspect ratio but tier 3 is the
*frame's* aspect. If those differ, the reveal "zoom-out" visibly stretches at the
last step — which is why `box_around` (auto-crop) emits a box whose *normalized*
w = h, i.e. the frame's pixel aspect, and why the crop UI constrains dragging the
same way. Each tier is then resized to `out_width=1000` and saved as JPEG
quality 85 (`crop_tiers` / `save_tiers`). The client spends tiers via
`docs/frame.js`: `revealTier` = wrong-guess count on the film rung, clamped to the
last tier — a single-tier puzzle (hand-authored 001) legally just never widens.

### 4.2 Edge energy, the summed-area table, and band de-weighting

When no face is found, auto-crop falls back to a **saliency proxy**: interesting
regions of a frame tend to be detail-dense, and detail shows up as *edges*
(brightness discontinuities). `auto_crop_box` converts the image to grayscale,
downsizes it to width `sample_w=160` (saliency doesn't need full resolution and
the cost drops ~100×), applies Pillow's `FIND_EDGES` convolution filter, and
treats each pixel's edge response as "energy". The suggested crop is the
window with the greatest total energy.

Finding that window naively is O(positions × window area). `best_window` instead
builds a **summed-area table** (integral image): `sat[r][c]` = sum of all energy
above-and-left of (r,c). Any rectangle's sum is then four lookups —
`sat[r2][c2] − sat[r1][c2] − sat[r2][c1] + sat[r1][c1]` — making each candidate
window O(1) and the whole scan O(cols·rows). Ties break toward the top-left.
Executed sanity check (2026-07-03): a 4×4 grid with a hot 2×2 centre returns
window origin `(1, 1)`.

One systematic bias needs correcting: **text is extremely edge-rich**, and movie
backdrops often carry title cards near the top and subtitles/credits near the
bottom. `deweight_bands` scales the top 12% and bottom 18% of rows by ×0.35
before the scan, pushing the crop toward faces and action instead of typography.
Executed (2026-07-03): a uniform all-100 grid of 10 rows comes back
`[35.0, 100, …, 100, 35.0]` (with 10 rows, `int(10*0.12)` = 1 top row and
`int(10*0.18)` = 1 bottom row are de-weighted).

### 4.3 Haar face detection — and why the curator always approves

Preferred over edge energy is a face: `detect_faces` runs OpenCV's **Haar cascade**
(`haarcascade_frontalface_default.xml`). A Haar cascade is a 2001-era detector
(Viola–Jones): it slides windows over the grayscale image evaluating thousands of
cheap rectangle-contrast features ("eyes darker than cheeks"), arranged as a
*cascade* of stages so non-faces are rejected after a few checks. Parameters as
coded: `scaleFactor=1.1` (the window grows 10% per pass — finer pyramid, slower),
`minNeighbors=5` (a hit must be confirmed by ≥5 overlapping detections — fewer
false positives, more misses), and `minSize` = `max(16, min(w,h)//12)` so
tiny background blobs are ignored. The **largest** face wins and the crop centres
on it (`auto_crop_box`).

The "frontalface" in the filename is the honest limitation: profiles, tilted
heads, dramatic low-key lighting, and partial occlusion — i.e. *most interesting
film frames* — routinely go undetected or misfire on face-like textures. That is
why auto-crop is by design a **suggestion the curator approves or re-drags**,
never an autonomous decision, and why `detect_faces` degrades to `[]` (→ edge
energy) rather than erroring. It also explains the pin: `opencv-python-headless
>=4.9,<5` in `curation/requirements.txt` — **OpenCV 5.0 dropped the bundled Haar
cascade files** (`cv2.data.haarcascades`), so an unpinned upgrade silently kills
face detection (commit 388e645). cv2 is optional at import; the whole images test
suite passes without it.

*Where this bites you:* "auto-crop is off-centre" (cv2 missing? Haar miss? title
band?) → `degreesoffilm-debugging-playbook`; scale/band/Haar constants →
`degreesoffilm-config-and-flags`.

## 5. Color math (`docs/theme.js`, `curation/images.py`)

**WCAG relative luminance** answers "how bright does this color look?" on a 0–1
scale. `luminance(rgb)` in `docs/theme.js`: divide each channel by 255, linearize
(sRGB gamma: `c/12.92` if `c ≤ 0.03928`, else `((c+0.055)/1.055)^2.4` — undoing
the display's nonlinear encoding), then weight by how sensitive the eye is to each
primary: `0.2126·R + 0.7152·G + 0.0722·B` (green dominates, blue barely counts).
**Contrast ratio** between two luminances is `(lighter + 0.05) / (darker + 0.05)`,
range 1:1 to 21:1; WCAG calls 4.5:1 the body-text bar.

`onAccentText(accent)` picks the text color to sit *on* accent-colored buttons:
whichever of dark ink `#1a1206` or bone `#ece7dd` contrasts more with the accent
(ink wins ties; unparseable accents fall back to ink). Executed (2026-07-03):
amber `#eba53c` has luminance 0.4490; ink is 0.0067, bone 0.8021 → contrast vs ink
= (0.499)/(0.0567) ≈ 8.8, vs bone ≈ 1.7 → **dark ink**, as `theme.test.js` pins.
Dark brown `#734621` → **bone**.

**Accent sampling** (`curation/images.py` `sample_accent`): resize the still to
64×64, average all pixels, then `clamp_accent` pushes the mean into a usable range
in HSV space — saturation floored at 0.45 (a muddy mean still *reads* as a color),
value clamped to 0.45–0.92 (visible on the dark base, but never white-hot). Known
quirk, executed 2026-07-03: a pure gray `(40,40,40)` has hue 0 = red, so the
saturation floor turns it **reddish** (`#733f3f`) — desaturated films get warm
accents; the curator can override the accent at approve time.

**Backgrounds** (`derive_background`): quantize the still to an 8-color palette,
take the two most dominant colors, and re-emit each at low value (0.14 / 0.28) with
saturation clamped into 0.42–0.55 (`to_background`) — deep, film-hued tones for
the page gradient that keep text readable. **Bone text (`#ece7dd`) itself never
changes**: with backgrounds value-capped this low, a fixed near-white stays above
readable contrast on every puzzle, and one fixed text color means one legibility
proof instead of a per-puzzle gamble (`docs/theme.js` header comment; only the
accent and on-accent text shift per puzzle).

*Where this bites you:* "theme looks wrong / text unreadable" →
`degreesoffilm-debugging-playbook`; the clamp constants and the fixed ink/bone hexes →
`degreesoffilm-config-and-flags`.

## 6. Daily-game conventions

**Manifest-index pattern.** The client never lists directories; it fetches
`puzzles/manifest.json?d=<todayISO>` (date query-string = cache-buster so a cached
manifest can't outlive the day — `docs/app.js`), then `docs/daily.js` `pickPuzzle`
picks: exact date match → else most recent entry **on or before** today → else the
earliest entry. So an empty day silently *re-shows the latest puzzle* rather than
erroring — a pool-dry schedule looks like "same puzzle as yesterday", not a crash.
`?id=N` replays via `pickById`. The archive renders the manifest with **titles
hidden** (they're obfuscated in the manifest anyway) so the film rung stays a
challenge.

**Rollover — a known spec/code divergence.** DESIGN §4 specifies a *single global*
rollover, but `todayISO()` in `docs/daily.js` uses the **device-local date**
(`getFullYear`/`getMonth`/`getDate`). In practice: a player in Tokyo and one in LA
can be on different puzzles for some hours. This divergence is **accepted — flag
it, don't fix it** without going through `degreesoffilm-change-control`
(DESIGN.md §4 vs `docs/daily.js` `todayISO()` — accepted divergence; full statement in
degreesoffilm-architecture-contract §4, verified against the code 2026-07-03).

**Streak idempotence** (`docs/stats.js` `recordResult`): pure fold of one finished
run into stats. First line of defense is `if (s.lastDate === date) return s` — 
replaying the same day never double-counts or moves the streak. Day gaps are
computed UTC-safely (`Date.parse(date + 'T00:00:00Z')`, DST-proof); gap of exactly
1 extends the streak, anything else resets it to 1. Poser, practice, and archived
(`?id=N`) runs never call into daily stats at all (guarded in `docs/app.js`) — by
design, not a bug. Stats live in localStorage under `dof-stats-v1`.

**Spoiler-safe sharing.** `shareText` (`docs/app.js`) emits a depth bar + score —
never the film title or any answer (Wordle-share convention: brag without
spoiling). The same discipline runs through the whole surface: manifest titles and
puzzle `answers[]`/`caption`s are XOR+base64 obfuscated behind the U+0001 sentinel
(`docs/cipher.js` ↔ `curation/cipher.py`, byte-identical outputs verified by
executing both 2026-07-03; a shared fixed vector is asserted in both test suites).
This is **anti-snoop, not security** — the key `"degrees-of-film"` ships to the
client; the real fix is v3 server-side matching (`degreesoffilm-server-move-campaign`).
Even commit messages follow it: content commits name puzzle number/date, never the
film title, until the date passes.

*Where this bites you:* "wrong/old daily", "streak didn't move", "gibberish text" →
`degreesoffilm-debugging-playbook`; routes, storage key, and cipher constants →
`degreesoffilm-config-and-flags`.

## When NOT to use this skill

| You actually need | Go to |
|---|---|
| Run the game/curation tool, publish a puzzle | `degreesoffilm-run-and-operate` |
| Set up Node/Python/venv from scratch | `degreesoffilm-build-and-env` |
| A symptom → cause → fix table | `degreesoffilm-debugging-playbook` |
| Every constant's value, location, and change gate | `degreesoffilm-config-and-flags` |
| The zone/layering invariants and schemas | `degreesoffilm-architecture-contract` |
| How to land a change (PR vs direct, gates) | `degreesoffilm-change-control` |
| Test inventory, how to add tests, QA checklists | `degreesoffilm-validation-and-qa` |
| TMDB terms, attribution wording, rights posture | `degreesoffilm-external-positioning` |
| Why past ideas were rejected (full stories) | `degreesoffilm-failure-archaeology` |
| The v3 server move plan | `degreesoffilm-server-move-campaign` |

## Reusing this pattern beyond this project

The transferable template: a "domain reference" skill that teaches each specialty
concept in a few sentences, then immediately grounds it in the host repo's code
with executed, dated examples — plus one canonical glossary the sibling skills
link to instead of redefining terms. The concepts themselves travel well
(Levenshtein tolerance bands, summed-area tables, WCAG contrast, manifest-index
dailies, rolling-metric-vs-in-context-metric traps like TMDB popularity); every
constant, threshold, and file path here is project-specific.

## Provenance and maintenance

- **Written 2026-07-03** against a clean `main` (HEAD 10668ca). All quoted behavior
  read directly from the cited files; all worked examples executed that day via
  Node/Python one-off scripts (probe outputs pasted verbatim above);
  `match.test.js` (25), `theme.test.js` (15), `cipher.test.js` (19) run green.
- **TMDB external facts**: image-URL composition and /discover parameters verified
  against developer.themoviedb.org on 2026-07-03 (no key used); the 500-page cap
  and query-param auth are cited from this repo's code and labeled "as of training
  data" where the code isn't the source. Re-verify TMDB claims against
  https://developer.themoviedb.org before relying on them externally.
- **Re-verify drift-prone facts** (repo root):
  - Matcher behavior: `node match.test.js`
  - Surname/first-name rule: `node -e "import('node:url').then(u => import(u.pathToFileURL('docs/match.js').href)).then(m => console.log(m.matchGuess('Joel', ['Joel Coen']), m.matchGuess('Coen', ['Joel Coen'])))"` → expect `false true` (executed 2026-07-03; the `pathToFileURL` form avoids Windows backslash-escaping traps)
  - Theme numbers: `node theme.test.js`
  - Cipher parity: `node cipher.test.js && python curation/cipher.test.py`
  - Image math constants: `grep -n "DEFAULT_FACTORS\|min_sat\|scaleFactor\|top=0.12" curation/images.py`
  - Ladder order + pool floor: `grep -n "director_after\|POOL_MIN" curation/build_rungs.py curation/discover.py`
- If any cited file changes behavior, update the matching section AND this date.
