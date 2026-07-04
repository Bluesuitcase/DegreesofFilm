---
name: degreesoffilm-proof-and-analysis-toolkit
description: First-principles proof recipes for the Degrees of Film repo — how to PROVE a claim instead of assuming it. Load this when you are about to claim something works ("this ordering is sane", "these two implementations match", "this fallback is safe", "this obfuscation protects the answers"), when choosing between algorithms or approaches, when verifying parity between dual implementations (JS/Python), when assessing a security or robustness claim, when asked "how do I prove this?", or before building anything big on an untested assumption. Eight recipes, each with a worked example from this repo's real history (validate_ladder.py, the cipher vector, the scoring curve, the fallback chains).
---

# Proof and analysis toolkit

The house rule of this project: **prove it, don't just install it.** Every recipe below was
actually used here, and each worked example cites the real artifact. Numbers in the worked
examples were computed against the repo as of 2026-07-03 (commands shown — re-run them, don't
trust prose).

Pick the recipe matching the claim you're about to make:

| You're about to claim… | Recipe |
|---|---|
| "This approach will work" (before building on it) | (a) Throwaway de-risk script |
| "My algorithm change did what I intended and nothing else" | (b) Contract-first change |
| "These two implementations are equivalent" | (c) Shared fixed vector |
| "This logic is correct" (but it's tangled in IO) | (d) Pure-core / IO-shell |
| "This client-side protection is good enough" | (e) Enumerable-domain analysis |
| "This migration is safe to re-run / run on mixed data" | (f) Idempotence + sentinel proof |
| "This formula produces the values we want" | (g) Predict numbers before running |
| "This degrades gracefully when X fails" | (h) Fallback-chain analysis |

---

## (a) Throwaway de-risk script before building

**When to use:** before building anything expensive (a tool, a pipeline, a mode) whose value
rests on ONE unproven assumption. The whole point: find out the assumption is false for the
price of a script, not the price of the build.

**Steps:**
1. Name the single riskiest assumption in one sentence. Write it at the top of the script.
2. Build the cheapest experiment that could kill it — stdlib only, no product code, marked
   THROWAWAY. It never has to be maintained; it has to be decisive.
3. State the pass/fail criteria IN the script (docstring or printed banner) *before* running,
   so you can't rationalize the output afterward.
4. Choose inputs to break the assumption, not confirm it — edge cases, not the happy path.
5. If comparing approaches, print them side-by-side (A/B) on identical inputs.
6. Record the verdict — with the falsifying evidence — where the next person will look
   (here: DESIGN.md), then leave the script in the repo as the citation.

**Worked example — `curation/validate_ladder.py` (commit `45b4085` "Phase 2 de-risk:
validate the credit-ordering assumption"):**
- The assumption, verbatim from the docstring: *"does sorting a film's credits by TMDB
  popularity produce a sane 'famous -> obscure' ladder?"* — the single riskiest assumption in
  the whole project (if the ladder is nonsense, the game isn't fun and Phase 2 isn't worth
  building).
- Criteria stated before running, printed as a banner (lines 182–183): *"EYEBALL TEST: do
  recognizable stars + the director sit at the top, descending smoothly into obscure crew?
  Watch for anyone wildly out of place."*
- Stress set chosen to break it (lines 45–53): 5 films — *"ensemble, blockbuster, two
  foreign-language"* (Pulp Fiction, The Dark Knight, Parasite, Pan's Labyrinth) plus
  No Country for Old Men to cross-check hand-authored puzzle 001.
- A/B protocol: `build_ladder()` (sort by person popularity) and `billing_ladder()` (cast by
  `cast[].order`, then key crew) printed side-by-side per film as `[A]`/`[B]` blocks
  (lines 152–163).
- Verdict, recorded in DESIGN.md §5 (Phase 2, first checkbox): *"pure popularity-sort
  fails — it buried Heath Ledger's Joker at rung 13 and sank Tommy Lee Jones below a
  one-scene bit player, because TMDB `popularity` is a rolling/current metric, not
  fame-for-this-film. Fix (adopted): order cast by billing order… Evidence:
  `curation/validate_ladder.py`."* Billing order is now the shipped rule
  (`curation/build_rungs.py`).
- Do NOT re-run this script casually — it hits live TMDB and needs the key. It's a citation,
  not a test.

**What would falsify it:** a stress-set film where the *adopted* ordering (billing) also
produces a bad ladder — that would reopen the decision, and belongs as a new A/B run plus a
DESIGN note, not a silent code change.

---

## (b) Contract-first algorithm change

**When to use:** changing any algorithm whose behavior is a *contract* with users — here,
above all, the fuzzy matcher (`docs/match.js`), which decides whether the game feels fair.

**Steps:**
1. Find the spec table — the test file that enumerates input → expected-output pairs
   (`match.test.js` is a literal table of `[guess, answers, expected, label]`).
2. **Add your new case to the table FIRST** and run it. It must FAIL (red). If it already
   passes, the behavior exists and you're done — don't touch the algorithm.
3. Make the smallest change that turns it green.
4. Re-run the whole table. Every pre-existing row must still pass — that's the proof the
   change did what was intended *and nothing else*. A row you have to "fix" is a behavior
   change you must justify explicitly.
5. Leave the new row in the table permanently. The table only grows.

**Worked example — `match.test.js` + `docs/match.js`:** the table has 25 rows as of
2026-07-03, encoding accepts (foreign titles, typos, surname-only "Bardem" → "Javier Bardem")
AND rejects ("Roger Moore" vs Roger Deakins — right first name, wrong surname). CLAUDE.md
makes the rule explicit: *"`match.test.js` is the contract… Add a case there before touching
the algorithm."* The mechanism behind one row, computed against the live module:

```
$ node -e "import('./docs/match.js').then(({normalize,levenshtein,maxDist})=>{ ... })"
answer normalized: "no country for old men" len 22
levenshtein: 1 maxDist: 4
```

"No Country for Old Man" is accepted because it is 1 edit from the 22-char normalized answer
and `maxDist(22) = floor(22*0.2) = 4`. If you widened `maxDist`, only the reject rows can
prove you didn't just accept everything — that's why the table carries both kinds.

**What would falsify it:** any pre-existing row flipping without an explicit, argued decision;
or shipping a matcher change with no new red-first row (then you have no evidence the change
did anything at all).

---

## (c) Cross-language parity via a shared fixed vector

**When to use:** any behavior implemented twice (two languages, client + server, old + new
system) that must stay byte-identical. Here: `docs/cipher.js` ↔ `curation/cipher.py`.

**Steps:**
1. Produce one concrete input → output pair with implementation A. Freeze it.
2. Assert that exact pair in BOTH test suites, as literal strings — not "encode then decode",
   which each side can pass alone even when they disagree with each other.
3. Include at least one non-ASCII input (encoding drift is the classic divergence).
4. Mark the vector frozen: changing it is a breaking change to all data at rest.

**Worked example — the shared vector, quoted from both suites:**
- `cipher.test.js` (line 17–18): `decode(S + 'MA0CUiEEAUZPLUMPDgQZ')` must equal
  `'The Dark Knight'` — commented *"this exact payload was produced by curation/cipher.py.
  If either side's KEY/scheme drifts, this fails."* Plus a Unicode vector:
  `decode(S + 'JQik2wkMFg==')` → `'Amélie'`.
- `curation/cipher.test.py` (lines 33–36): `obfuscate("The Dark Knight")` must equal
  `SENTINEL + "MA0CUiEEAUZPLUMPDgQZ"` — commented *"fixed cross-language vector (also
  asserted in cipher.test.js)"*.
- Independent derivation (I recomputed the vector from first principles, not from either
  implementation):

```
$ python -c "import base64; KEY=b'degrees-of-film';
  xor=lambda d: bytes(b^KEY[i%len(KEY)] for i,b in enumerate(d));
  print(repr(chr(1)+base64.b64encode(xor('The Dark Knight'.encode())).decode()))"
'\x01MA0CUiEEAUZPLUMPDgQZ'
```

- Both suites green as of 2026-07-03: `node cipher.test.js` → `19 passed, 0 failed`;
  `python curation/cipher.test.py` → `22 passed, 0 failed`.

**Why a vector beats code inspection:** the two files *look* equivalent, but parity actually
depends on UTF-8 byte order, base64 alphabet, key bytes (`TextEncoder` vs a `b""` literal),
and sentinel placement. A pinned literal catches drift in ANY of those; a human diff of the
two implementations catches almost none reliably.

**What would falsify it:** either suite failing on the vector — that means published puzzle
files written by Python would no longer decode in players' browsers. The vector (and KEY
`"degrees-of-film"` + SENTINEL U+0001) are effectively frozen forever; see
degreesoffilm-config-and-flags.

---

## (d) Pure-core / IO-shell decomposition as a provability strategy

**When to use:** whenever logic worth proving is entangled with pixels, files, network, or
DOM. Split it: a pure core you can prove with hand-checkable inputs, and a thin shell whose
IO you exercise against temp resources.

**Steps:**
1. Extract the decision logic into a function of plain data (lists, dicts, numbers) with no
   imports of the IO layer. (House law: `docs/` game logic is DOM-free; `curation/images.py`
   keeps box/energy math Pillow-free.)
2. Prove the core on an input small enough to compute BY HAND. Write the hand arithmetic
   down; then run the function and compare.
3. For the shell, parameterize every path (no hard-coded repo paths) and test against
   `tempfile.TemporaryDirectory()` — never against committed content (that rule exists
   because a live-write test once moved committed puzzle 004; see
   degreesoffilm-failure-archaeology).

**Worked example 1 — `curation/images.py` `best_window` (summed-area table):** the claimed
property: after building the SAT, *any* window sum is 4 lookups (O(1)), so the whole scan is
O(cols·rows). SAT identity: `sum(window) = sat[r2][c2] − sat[r1][c2] − sat[r2][c1] + sat[r1][c1]`
(lines 61–62). Hand check on a 3×3 grid `[1,2,3, 4,5,6, 7,8,9]`, all 2×2 windows:

```
top-left (0,0): 1+2+4+5 = 12      top-right (1,0): 2+3+5+6 = 16
bot-left (0,1): 4+5+7+8 = 24      bot-right (1,1): 5+6+8+9 = 28  <- max
```

```
$ python -c "import sys; sys.path.insert(0,'curation'); from images import best_window;
  print(best_window([1,2,3,4,5,6,7,8,9],3,3,2,2)); print(best_window([5]*9,3,3,2,2))"
(1, 1)
(0, 0)
```

Matches the hand arithmetic, including the documented tie-break toward top-left (uniform grid
→ `(0, 0)`; the code uses strict `>` at line 63). Because `best_window` takes a plain list,
this proof needed no image, no Pillow, no OpenCV.

**Worked example 2 — `curation/publish.test.py`:** `publish.publish()` writes a puzzle file,
appends the ledger, and upserts the manifest — record-keeping that MUST be provable without a
network or the real `docs/` tree. It works because `publish()` takes `puzzles_dir=`,
`ledger_path=`, `manifest_path=` parameters; the test (lines 56–91) points all three into a
`TemporaryDirectory`, publishes twice, and asserts: first id is 1, the written rungs
`decode_rungs` back to the exact input, the ledger recorded film id 99 and deduped on
republish, and the manifest title is sentinel-prefixed on disk. Run: `python
curation/publish.test.py` → `36 passed, 0 failed` (2026-07-03), zero network, zero repo writes.

**What would falsify it:** a core function growing an IO import (it can no longer be proved
on plain data), or a shell function growing a hard-coded path (it can no longer be tested
against temp dirs — and someone will eventually test it against the live repo).

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
   (deterministic) scheme and compares against the shipped blob — an offline dictionary
   attack. Only a non-enumerable domain or a server-held secret survives.
4. Conclude honestly: label the mechanism for what it is, and name the real fix.

**Worked example — the answer obfuscation (`docs/cipher.js` / `curation/cipher.py`):**
- Kill shot 1 (step 2): the key ships. `docs/cipher.js` line 8:
  `const KEY = new TextEncoder().encode('degrees-of-film');` — every player downloads the
  decoder. Anyone can paste a puzzle blob into the shipped `decode()`.
- Kill shot 2 (step 3): even with a secret key, the domain is enumerable — every answer is a
  TMDB title or credited person, all public. Demonstrated against the real implementation:

```
$ python -c "import sys; sys.path.insert(0,'curation'); from cipher import obfuscate;
  target=obfuscate('The Dark Knight');
  print([c for c in ['Inception','Parasite','The Dark Knight','Heat'] if obfuscate(c)==target])"
['The Dark Knight']
```

  `obfuscate` is deterministic, so encode-candidates-and-compare identifies the plaintext
  without ever inverting the cipher. Scale the candidate list to all of TMDB and every puzzle
  falls. (This same argument kills "just hash the answers" — hashing is deterministic too.)
- The repo concludes correctly and says so in the source: `curation/cipher.py` docstring —
  *"a light cipher… NOT security. The key lives in the client too… the point is only to
  defeat 'open the JSON and read the answer.' The proper fix is server-side matching (v3)."*
  For executing that fix, see **degreesoffilm-server-move-campaign** (which also fences off
  "harden the XOR" and "hash the answers" as wrong paths, for exactly this reason).

**What would falsify it:** nothing in-browser. The only escape is changing the architecture:
answers held server-side, client sends guesses. Any proposal claiming otherwise must defeat
the enumeration argument above explicitly.

---

## (f) Idempotence + sentinel design proof

**When to use:** designing any in-place data migration or encoding that will meet **mixed
content** — some records already converted, some not, some hand-authored — and might be
re-run. Aim for "safe by construction": correctness follows from two properties you can
test, not from operator carefulness.

**The two properties (and where they're implemented):**
1. **Encode is idempotent** — `curation/cipher.py` lines 31–33: `obfuscate` returns its input
   unchanged if it already starts with SENTINEL. Encoding twice = encoding once; a re-run
   cannot double-encode.
2. **Decode is a passthrough** — lines 39–41: `deobfuscate` returns any non-sentinel string
   as-is. Decoding is always safe to run, on plaintext or ciphertext.

Both hinge on the sentinel being **unambiguous**: U+0001 appears in no real title/name AND is
never produced by base64 (its alphabet is `A–Za–z0–9+/=`), so "starts with SENTINEL" is a
perfect encoded/plaintext discriminator — stated in the `cipher.py` docstring, asserted in
both test suites (`encoded string carries the sentinel prefix`, `idempotent: encoding an
encoded string is a no-op`, `decode leaves plaintext untouched` — all PASS, 2026-07-03).

**Worked example — the live migration `curation/obfuscate_puzzles.py`:** v1 shipped puzzles
in plaintext; v2 had to encode them in place, on the live `docs/puzzles/` tree, while new
publishes were already writing encoded files. The script just maps `obfuscate` over every
answer/caption/title:
- Already-encoded strings? Untouched (property 1). Re-running after adding a puzzle by hand
  is explicitly supported — the docstring says so and offers `--dry-run`.
- Hand-authored plaintext puzzle 001? Keeps working forever, encoded or not, because the
  client's `decode()` passes plaintext through (property 2) — `docs/app.js` decodes every
  puzzle at load unconditionally, and half-migrated data is simply fine.
- No backup/restore choreography, no "did I already run this?" ledger. The safety is in the
  encoding's algebra, not in the runbook. (Do not actually run the migration casually — it
  writes to `docs/`; use `--dry-run`. As of 2026-07-03 all published content is migrated.)

**General recipe:** make the converted form self-identifying (sentinel/magic prefix outside
the value alphabet) → prove encode∘encode = encode and decode(plaintext) = plaintext in the
test suite → only then write the migration as a bare map over the data.

**What would falsify it:** a legitimate value that starts with the sentinel (breaks the
discriminator — impossible here by the alphabet argument), or an encode path that skips the
sentinel check.

---

## (g) Predict numbers before running

**When to use:** any formula, threshold, or curve. Derive the expected values by hand FIRST,
write them down, then run. If you run first, you'll rationalize whatever comes out — the
prediction is the experiment's integrity.

**Steps:**
1. From the formula/spec, compute the concrete expected values on paper. Commit to them
   (write them in the test or a note) before executing anything.
2. Run the real code. Compare against the written-down values, not your memory.
3. Freeze the numbers as a literal assertion so the property outlives you.

**Worked example — `docs/game.js` `scoreForRung` (lines 11–14):**
`score(n) = n + min(max(n−5, 0), 5)`. Hand derivation:

```
n=1..5 : bonus max(n-5,0)=0            -> 1, 2, 3, 4, 5
n=6    : bonus min(1,5)=1  -> 7        n=7: bonus 2 -> 9
n=8    : bonus 3 -> 11                 n=9: bonus 4 -> 13
n=10   : bonus 5 -> 15                 n=11,12: bonus capped at 5 -> 16, 17
```

Predicted curve for rungs 1–12: `1,2,3,4,5,7,9,11,13,15,16,17`. Confirmed against the module:

```
$ node -e "import('./docs/game.js').then(({scoreForRung})=>
  console.log([1,2,3,4,5,6,7,8,9,10,11,12].map(scoreForRung).join(',')))"
1,2,3,4,5,7,9,11,13,15,16,17
```

And frozen as a literal in `game.test.js` line 11–12:
`check('score curve rungs 1-12', curve, [1,2,3,4,5,7,9,11,13,15,16,17]);` — the assertion is
the *whole table*, not a re-implementation of the formula (which would just repeat the same
bug). The same discipline shaped recipe (a): validate_ladder predicted "leads top, director
early" before querying TMDB.

**What would falsify it:** the assertion being edited to match new output without a
derivation showing why the new curve is intended. Curve changes are game-balance changes —
route through degreesoffilm-change-control.

---

## (h) Fallback-chain failure analysis

**When to use:** before claiming "it degrades gracefully". A fallback you haven't traced is a
hope, not a design. For each hop: name the **trigger**, verify the trigger is **actually
detectable in code** (cite the line), and test the **terminal state** — the chain's floor is
what users hit on the worst day.

**Steps:**
1. Enumerate the chain hop by hop, ending at the terminal state (which may be "a human" or
   "hide it" — both fine, if explicit).
2. For each hop, find the exact code that detects the trigger. If detection is missing (e.g.
   an exception the caller never sees, a 404 with no handler), the "fallback" never fires —
   that's the bug this recipe exists to catch.
3. Test the terminal state directly, plus at least one mid-chain hop.

**Worked example 1 — auto-crop (`curation/images.py` `auto_crop_box`, lines 164–184):**

| Hop | Trigger | Detection (verified in code) |
|---|---|---|
| Face-centered box | ≥1 Haar face found | `if faces:` (line 170) |
| → edge-energy box | no faces | `detect_faces` returns `[]` on: cv2 import failure (145–146), missing/empty cascade (151–152), any cv2 exception (157–158), or zero detections — ALL collapse into the same `[]`, so the fallback trigger is one truthiness check |
| → curator re-drag | suggestion is bad | by design a human gate: docstring line 169 — *"A STARTING POINT the curator reviews and approves/re-drags — not final"*; the crop UI (`curation/static/index.html`) always shows the box before approve |

Consequence proved by the detection analysis: OpenCV is genuinely optional — every cv2
failure mode is swallowed into the edge-energy path, which is why
`curation/images.test.py` passes without cv2 installed (CLAUDE.md states this; the suite
exercises the pure edge-energy pieces `best_window`/`deweight_bands` directly).

**Worked example 2 — client credit image (`docs/frame.js` + `docs/app.js`):**

| Hop | Trigger | Detection |
|---|---|---|
| Rung's own image + caption | rung has `image` | `if (last && last.image)` — frame.js line 29 |
| → full frame (`images[last]`) | rung has no `image` field | frame.js line 30 return |
| → full frame (runtime swap) | image file 404s in the browser | `$('frame-img').onerror` — app.js lines 95–104; guarded by `!img.src.endsWith(...)` so a failing full frame can't loop |
| → hide the element | even the full frame fails (or no frames) | `img.style.display = 'none'` — app.js line 102; reset on next puzzle at line 109 |

Terminal + mid-chain states are tested in `frame.test.js` (16 checks green 2026-07-03):
imageless rung → full frame; single-tier puzzle 001 → same file at every tier; **no frames at
all → `{ src: null, caption: '' }`** (the floor). Honest gap: the `onerror` hop itself is DOM
glue and has NO automated test — it's covered only by the manual browser gate (see
degreesoffilm-validation-and-qa's coverage-gap list). Say so when you cite this chain.

**What would falsify it:** a new hop added without a detectable trigger (e.g. catching an
exception the image pipeline doesn't actually raise), or a terminal state that renders
broken UI (dangling broken-image icon) instead of an explicit floor.

---

## When NOT to use this skill

- Running/choosing the existing test suites, coverage gaps, how to add a test →
  **degreesoffilm-validation-and-qa**.
- Ready-made measurement scripts (content validator, puzzle report) and instrument inventory →
  **degreesoffilm-diagnostics-and-tooling**.
- A live symptom to triage right now → **degreesoffilm-debugging-playbook**.
- "Was this already investigated/rejected?" (don't re-fight settled battles) →
  **degreesoffilm-failure-archaeology**.
- The full idea lifecycle (parking lot → de-risk → slice → ship) and experiment hygiene rules →
  **degreesoffilm-research-methodology** (this skill supplies its proof techniques).
- Actually executing the server-side-matching fix that recipe (e) concludes with →
  **degreesoffilm-server-move-campaign**.
- Landing a change once proven → **degreesoffilm-change-control**.

## Reusing this pattern beyond this project

This is the most transferable skill in the library: none of the eight recipes is really about
film. To re-instantiate on another repo, keep the recipe skeletons (when / steps / falsifier)
and swap the worked examples for that repo's own artifacts: find its riskiest assumption (a),
its contract test table (b), any dual implementation (c), its most tangled logic (d), any
client-side "protection" (e), any in-place migration (f), any magic curve (g), and any
"degrades gracefully" claim (h). The discipline that transfers unchanged: state the criteria
before running, compute expected numbers by hand first, and record verdicts with the
falsifying evidence where the next person will look.

## Provenance and maintenance

- Written 2026-07-03. Every cited artifact was read in full; every number above was computed
  by actually running the shown command against this repo (outputs pasted verbatim).
  Commit `45b4085` verified via `git log --oneline -- curation/validate_ladder.py`.
- Test-suite counts observed 2026-07-03: cipher.test.js 19, cipher.test.py 22,
  publish.test.py 36, frame.test.js 16, match.test.js 25 cases, game.test.js curve assertion
  at line 12.
- One-line re-verification (all offline, read-only):
  - Cipher parity + vector: `node cipher.test.js && python curation/cipher.test.py`
  - Scoring curve: `node -e "import('./docs/game.js').then(({scoreForRung})=>console.log([1,2,3,4,5,6,7,8,9,10,11,12].map(scoreForRung).join(',')))"` → expect `1,2,3,4,5,7,9,11,13,15,16,17`
  - Matcher contract: `node match.test.js`
  - SAT hand check: `python -c "import sys; sys.path.insert(0,'curation'); from images import best_window; print(best_window([1,2,3,4,5,6,7,8,9],3,3,2,2))"` → expect `(1, 1)`
  - Temp-dir publish proof: `python curation/publish.test.py`
  - Fallback floors: `node frame.test.js`
- Drift-prone facts: line numbers cited into `curation/images.py`, `docs/app.js`,
  `docs/frame.js`, `curation/cipher.py` (re-grep after edits to those files); the "onerror
  hop untested" gap (delete that caveat if a test appears); the migration-complete claim
  ("all published content migrated as of 2026-07-03" — re-check with
  `python curation/obfuscate_puzzles.py --dry-run` if in doubt).
