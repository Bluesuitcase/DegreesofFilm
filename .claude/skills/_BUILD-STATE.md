# Skill-library build state — BUILD COMPLETE 2026-07-03

> **The build this file drove is FINISHED.** All 16 skills authored (Phase 2) and reviewed +
> fixed (Phase 3: FACTUAL / DOCTRINE / USABILITY passes — 3 BLOCKING, 7 IMPORTANT, 11 MINOR
> findings, all applied; deliberately-unfixed minors listed at the bottom of this file's
> Phase 3 section). This file is now a historical build record only — safe to delete, or
> keep as provenance. It is NOT a skill and nothing references it.
> Phase 3 deliberately left unfixed (cosmetic): build-and-env heading numbering;
> server-move-campaign's 514-line length; benign converging trigger overlaps; dated
> operational facts (guarded by re-verify probes by design).

## Mission

Build a complete skill library under `.claude/skills/` for the **Degrees of Film** repo
(`C:\Claude\DegreesofFilm`) so junior/mid-level engineers and Sonnet-class AI models can
debug, extend, validate, and advance this project at a principal-engineer standard.
16 skills total, then a 3-reviewer + 1-fixer review pass, then a final report to the user.

Preferred execution: multi-agent (one authoring agent per skill, general-purpose type,
run in parallel waves of ~4). **Fallback if agents fail or spend limits recur: author the
skills inline yourself, one at a time, in the priority order of the status table.**
Correctness beats speed; every fact must be verified against the repo before being written.

## Status (update this table as skills land)

| # | Skill | Status |
|---|-------|--------|
| 1 | degreesoffilm-build-and-env | **DONE 2026-07-02** (294-line SKILL.md, verified by its author against live commands) |
| 2 | degreesoffilm-architecture-contract | **DONE 2026-07-03** (331 lines; 13 invariants; found live QUOTES spoiler violation — chipped for owner) |
| 3 | degreesoffilm-change-control | **DONE 2026-07-03** (368 lines; all hashes re-verified; landing-mode nuance recorded) |
| 4 | degreesoffilm-run-and-operate | **DONE 2026-07-03** (~330 lines; found "accent undefined" approve-message bug — chipped for owner) |
| 5 | degreesoffilm-domain-reference | **DONE 2026-07-03** (411 + references/tmdb.md 129 lines; worked examples executed; stale frame.js comment noted for FACTUAL review) |
| 6 | degreesoffilm-config-and-flags | **DONE 2026-07-03** (370 lines; 11 zone tables; master re-verify block executed; QUOTES violation recorded) |
| 7 | degreesoffilm-debugging-playbook | **DONE 2026-07-03** (269 lines; all error strings + probes verified; 401-behind-500 nuance corrected) |
| 8 | degreesoffilm-failure-archaeology | **DONE 2026-07-03** (447 lines; 16 entries; corrected: reveal-mechanic remote branch is gone, collision was 003/004/005) |
| 9 | degreesoffilm-diagnostics-and-tooling | **DONE 2026-07-03** (288 lines + 2 working scripts, run against repo: 7 PASS groups, 1 WARN [quotes], runway 2, puzzle-5 rung-12 zero decoys noted) |
| 10 | degreesoffilm-validation-and-qa | **DONE 2026-07-03** (366 lines; all 16 counts re-measured; full coverage-gap list) |

**Phase 3 pre-logged defects** (found during authoring, for the FACTUAL reviewer/fixer):
- degreesoffilm-diagnostics-and-tooling/SKILL.md states "244 JS/Python-pure checks"; measured sum is 275 (137 JS + 138 Python-pure). Fix the arithmetic.
- degreesoffilm-domain-reference noted docs/frame.js's header comment still says "character still for cast" (stale wording from the removed picker; actual behavior = headshots for all credit rungs) — repo-side nit, NOT a skill defect; skills must describe actual behavior.
| 11 | degreesoffilm-docs-and-writing | **DONE 2026-07-03** (279 lines; all conventions corpus-quoted; found 3rd spoiler-leak commit 007b3e2) |
| 12 | degreesoffilm-external-positioning | **DONE 2026-07-03** (~300 lines; TMDB terms verified live; found footer-wording drift vs current TMDB terms — pre-launch re-check) |
| 13 | degreesoffilm-server-move-campaign | **DONE 2026-07-03** (515 lines; pure-module claim proven by Node execution; 4 numeric gates; 6 derived fences) |
| 14 | degreesoffilm-proof-and-analysis-toolkit | **DONE 2026-07-03** (435 lines; 8 recipes; all numbers computed live incl. an enumeration-attack demo) |
| 15 | degreesoffilm-research-frontier | **DONE 2026-07-03** (437 lines; 6 problems w/ falsifiable milestones; finding: Movie Buff is static-possible, not server-gated) |
| 16 | degreesoffilm-research-methodology | **DONE 2026-07-03** (316 lines; lifecycle honest about the character-stills de-risk skip; corrected the ~18-min-per-PR claim) |

**PHASE 2 COMPLETE 2026-07-03 — all 16 skills on disk. Next: Phase 3 (FACTUAL/DOCTRINE/USABILITY reviews + fixer), awaiting owner go-ahead.**

Then: **Phase 3** (three review passes + fixer), then the **final report**. Both specified
at the bottom.

## Hard constraints (apply to every skill, every agent, every inline edit)

- Write ONLY inside `.claude/skills/` (each skill in its own `degreesoffilm-<name>/SKILL.md`,
  optional `references/` or `scripts/` inside its own directory). The rest of the repo is
  READ-ONLY. NO mutating git commands (no add/commit/push/checkout/restore/reset).
  Read-only git (`log/show/diff/branch -a`) and read-only `gh` (`pr list/view`) are allowed
  and encouraged (gh works directly in this environment).
- Never read or print `curation/.env`. Never call TMDB or use the API key. Don't start
  servers. Don't run anything that writes to `docs/` or `curation/used_films.json`
  (POST /api/approve, /api/update, /api/clear-schedule, `backfill_credit_images.py`,
  `obfuscate_puzzles.py`) — document them from the code instead. Running the OFFLINE test
  suites is allowed/encouraged: `node <name>.test.js` (repo root), `python curation/<name>.test.py`,
  `.venv/Scripts/python curation/images.test.py` (they write only temp dirs).
- GROUND TRUTH ONLY: verify every command, flag, path, constant, hash, and claim against
  the repo before stating it. Unverifiable ⇒ omit or label "unverified — check before relying".
- Repo-relative paths only as load-bearing facts. Date-stamp volatile facts ("as of 2026-07-02").
  No oversell: unproven things stay labeled open/candidate. Nothing may contradict
  CLAUDE.md / DESIGN.md; no skill may advise routing around change control.

## Required per-skill structure

1. YAML frontmatter: `name: <exact dir name>` + trigger-rich `description:` (third person;
   states exactly WHEN a model should load it, with concrete symptoms/tasks — the model
   decides from the description alone).
2. Body per that skill's outline (below).
3. "When NOT to use this skill" section routing to sibling skills BY EXACT NAME.
4. "Reusing this pattern beyond this project" (2–6 lines: what transfers as a template to a
   future project vs what is project-specific — the owner wants the library reusable).
5. Final "Provenance and maintenance": date, how facts were verified, one-line
   re-verification commands for anything drift-prone.

Audience & voice: zero-context mid-level engineer or Sonnet-class model. Imperative runbook
voice. Copy-pasteable commands (forward-slash repo-relative paths work in PowerShell and
Git Bash; give dual forms where platforms diverge, e.g. `.venv/Scripts/python` vs
`.venv/bin/python`). Define each jargon term once (or point to the domain-reference glossary).
Tables and numbered checklists over prose. SKILL.md ≲ 450–500 lines; overflow → `references/`.

## Canonical inventory (cross-reference siblings by these exact names)

1. **degreesoffilm-change-control** — how changes are classified/gated/land (PR vs direct-to-main); non-negotiables with rationale + incident history.
2. **degreesoffilm-debugging-playbook** — symptom→triage tables for known failure modes; costliest traps with stories; discriminating experiments.
3. **degreesoffilm-failure-archaeology** — chronicle of investigations/dead ends/rejected fixes: symptom → root cause → evidence → status; settled battles index.
4. **degreesoffilm-architecture-contract** — load-bearing design decisions, testable invariants, known weak points stated plainly.
5. **degreesoffilm-domain-reference** — TMDB data model, fuzzy-matching theory, image/color math, daily-game conventions as used HERE; the glossary.
6. **degreesoffilm-config-and-flags** — catalog of every configuration axis with values/locations/change-gates + re-verification one-liners.
7. **degreesoffilm-build-and-env** — recreate the environment from scratch; known traps. (DONE)
8. **degreesoffilm-run-and-operate** — run the game + curation tool; the puzzle-publishing runbook; artifact/deploy conventions.
9. **degreesoffilm-diagnostics-and-tooling** — measure instead of eyeball; ships working scripts + interpretation guides.
10. **degreesoffilm-validation-and-qa** — the evidence bar; test inventory; how to add tests; content QA checklist; golden inventory.
11. **degreesoffilm-docs-and-writing** — docs of record, session-handoff discipline, house style, commit/PR conventions, templates.
12. **degreesoffilm-external-positioning** — TMDB terms/attribution, content-rights posture (not legal advice), ecosystem novelty analysis, claim standards.
13. **degreesoffilm-server-move-campaign** — executable, decision-gated campaign for the v3 server move (the owner-designated hardest live problem).
14. **degreesoffilm-proof-and-analysis-toolkit** — first-principles analysis recipes, each with a worked example from this repo's history.
15. **degreesoffilm-research-frontier** — open problems where this project can advance SOTA (owner-picked tracks: automated curation, novel modes, scale & integrity); first steps + falsifiable milestones.
16. **degreesoffilm-research-methodology** — the discipline turning a hunch into an accepted result here; evidence bar; idea lifecycle; experiment hygiene.

## Verified facts pack (verified 2026-07-02 — spot-check anything you rely on)

**Project**: "Degrees of Film" — daily browser game: name a film from a cropped frame, dig its
credits famous→obscure; brag stat = depth. Three zones: (1) PRIVATE curation tool (`curation/`,
FastAPI, TMDB v3 key in gitignored `curation/.env` — the key must NEVER reach a player);
(2) STATIC hosting (`docs/` = the entire site; GitHub Pages serves `main` `/docs`; live at
https://bluesuitcase.github.io/DegreesofFilm/; any push to main touching docs/ auto-deploys);
(3) player browser (vanilla ES modules, no backend, localStorage stats). v1+v2 complete and
live; v3 ("the server move") not started. Remote: github.com/Bluesuitcase/DegreesofFilm.
Docs precedence (stated in CLAUDE.md): DESIGN.md is the spec and wins conflicts; CLAUDE.md =
how the code works; project_state.md = living session handoff (injected into sessions by a
SessionStart hook in .claude/settings.json).

**Tests** (all green 2026-07-02; PASS/FAIL lines, non-zero exit; no framework, no npm test;
package.json = only `{"type":"module"}`): JS from repo root — match 25 / game 34 / daily 11 /
theme 15 / stats 17 / frame 16 / cipher 19. Pure Python — build_rungs 16 / ledger 12 /
discover 11 / decoys 6 / manifest 13 / publish 36 / credits_images 22 / cipher 22 (run with any
Python, zero pip deps). Pillow suite: `.venv/Scripts/python curation/images.test.py` (32;
degrades gracefully without cv2; without Pillow fails `ModuleNotFoundError: No module named 'PIL'`).

**Toolchain**: Node v24.17.0; Python 3.14.6; venv at repo root `.venv` with pillow 11.3.0,
fastapi 0.138.2, uvicorn 0.49.0, opencv-python-headless 4.13.0.92. Pins
(curation/requirements.txt): pillow>=10,<12 · fastapi>=0.110 · uvicorn>=0.29 ·
opencv-python-headless>=4.9,<5 (**<5 is load-bearing: OpenCV 5.0 dropped bundled Haar
cascades**; cv2 optional at runtime — detect_faces returns [] and auto-crop falls back to
edge energy).

**Content**: puzzles 001–007 dated 2026-06-28..2026-07-04 (runway thin); manifest
docs/puzzles/manifest.json entries {date,id,file,title,accent} with titles obfuscated; ledger
curation/used_films.json has the 7 films {id,title,year,puzzle}; 92 files in docs/puzzles/images/
(tiers NNN-{1,2,3}.jpg, credit headshots NNN-rK.jpg). Puzzle 001 is hand-authored (single image
tier; verify its current on-disk state before claiming more).

**OWNER'S UNWRITTEN RULES (2026-07-02 — encode wherever relevant)**:
(1) **IMMUTABLE PAST** — never modify a published puzzle dated ≤ today (players played it);
edits only for future-dated puzzles. The tooling allows editing any id; the rule is discipline.
(2) **SPOILER DISCIPLINE** — nothing player-visible may leak an answer: archive shows no
titles; manifest/puzzle answers obfuscated; home QUOTES only from films NOT in the puzzle set;
commit messages are public — content commits reference puzzle NUMBER/date only ("Add puzzle
NNN (YYYY-MM-DD)"), never the film title until the date passes. Two historical commits violated
this (bdca151 named Toy Story, 3d7d17e named Avatar) — cite as the lesson; history NOT rewritten.

**OWNER'S ANSWERS (2026-07-02)**: hardest live problem = **the v3 server move** (campaign
skill targets it). Costliest failures = manifest collision/orphans, character-stills dead end,
dev-cache verification traps (weight these deepest). "Beyond SOTA" = automated curation,
novel modes, scale & integrity (explicitly NOT matcher craft).

**Key incidents** (hashes verified via `git log --oneline`): popularity-sort ladder REJECTED
after de-risk 45b4085 (TMDB rolling popularity buried Heath Ledger's Joker at rung 13; evidence
curation/validate_ladder.py; billing order adopted). Manifest date-collision 2026-06-30
orphaned puzzles 003/004 (recovered 772f4f7; prevented by publish.next_date auto-assign
257bcff; mechanism: manifest.upsert replaces by date). Character-stills picker built (PRs
#12/#13) then REMOVED 3e2cfbb (TMDB tagged images too sparse — mostly generic backdrops;
ALL credit rungs now auto TMDB headshots; do NOT rebuild). OpenCV pinned <5 (388e645).
Reveal mechanic: cut from v1 but tiers authored ahead; shipped v2 via PR #18 → rebase-merged
995c01e. (CORRECTED 2026-07-03: the remote branch origin/reveal-mechanic no longer exists —
`git ls-remote --heads origin` shows only main; 22c07e4 survives only as a dangling local object.
Also: the 2026-06-30 manifest collision involved THREE puzzles — 003/004/005 all dated 06-30,
only 005 survived; see the failure-archaeology skill for the verified account.)
"Exclude scheduled-but-unpublished from Discover" investigated and DROPPED as non-issue
(ledger already excludes at approve). Live-write reschedule test moved committed puzzle 004 —
rule: never point live-write tests at committed content; restore =
`git checkout -- docs/puzzles/manifest.json curation/used_films.json` (recorded account in
project_state.md). Stale ES-module cache on python http.server = recurring trap → verify on
a fresh port. Other landmarks: practice 811ee40, tooltips 314b98f, obfuscation 8be6434,
Randomize afec469, Auto-crop 7957b19, slider+sort 4496c81, face-first 388e645, Clear-scheduled
125c4a5 + frees-films c0329a2. All 18 PRs MERGED via rebase-merge, branches deleted,
kebab-case names; player-facing work via PR, curation-only/docs often direct-to-main per
owner's per-change choice. Commit convention: "Area: imperative summary" (Phase N:/Curation:/
Docs:/UX:/Polish:/State:).

**Architecture invariants**: key never in docs/; layering law — docs/match.js imports nothing,
docs/game.js imports only match.js, docs/app.js does ALL DOM; daily/theme/stats/frame/cipher
pure (stats load/save touch localStorage only); cipher parity docs/cipher.js ↔ curation/cipher.py
(repeating-key XOR, KEY "degrees-of-film", SENTINEL U+0001, base64; idempotent encode;
plaintext passthrough decode; shared fixed vector asserted in BOTH cipher suites — anti-snoop
only, NOT security); manifest = sole daily index; ledger = never-repeat; archive hides titles;
archived/poser/practice runs never touch daily stats (app.js showEnd guards); TMDB attribution
footer mandatory (shipped c2f59c3; DESIGN §5 calls it a ship-blocker). KNOWN SPEC/CODE
DIVERGENCE: DESIGN §4 says daily rollover is a "single global" date, but docs/daily.js
todayISO() uses the DEVICE-LOCAL date — accepted in practice; flag, don't fix without
change control.

**Game constants**: MAX_ATTEMPTS 3, MAX_SKIPS 5, MAX_HELPS 3 (docs/game.js); scoreForRung =
n + min(max(n−5,0),5) → curve 1,2,3,4,5,7,9,11,13,15,16,17; POSER_RUNGS 7, MODE_LABELS,
QUOTES (must be from films NOT in the puzzle set), ROASTS tiers (thresholds 0.6/0.3) in
docs/app.js; localStorage 'dof-stats-v1'; routes `?` home / `?modes` / `?play` / `?play&mode=poser`
/ `?id=N` / `?archive` / `?practice` / `?practice&mode=cinephile|poser`; manifest fetch
cache-busted `?d=<todayISO>`; matcher maxDist thresholds 0(≤3)/1(≤6)/2(≤10)/floor(len*0.2);
surname rule = single-token guess equals answer's LAST token.

**Curation constants**: pool floor vote_count≥800 & vote_average≥6.5 (discover.py); cast by
billing order (cast[].order), popularity tiebreak; director_after=2; Writer deliberately NOT a
rung; deep crew order DP("Director of Photography")/Composer("Original Music Composer")/
Editor/Production Designer("Production Design"); build_rungs default max_cast=8 BUT app.py
api_film passes max_cast=6; decoys n=3 from neighbour films (recommendations→similar,
source_limit=8, cast_per_film=5, min_votes=400, popularity-sorted, people-in-this-film
excluded); tiers factors (1.0, 1.8, None), out_width 1000, quality 85; auto-crop scale default
0.5, API clamp 0.2–0.9, UI slider 0.25–0.85; edge-energy sample_w 160, deweight_bands top
0.12 / bottom 0.18 / factor 0.35; Haar scaleFactor 1.1, minNeighbors 5, min face min(w,h)//12;
accent clamp min_sat 0.45 / min_val 0.45 / max_val 0.92; TMDB base https://api.themoviedb.org/3,
images https://image.tmdb.org/t/p/original, 20s timeout, discover paging cap 500, search
count 18, stills = backdrops[:12]+poster.

**Curation endpoints** (curation/app.py): GET / (crop page) · GET /api/next-date ·
GET /api/schedule?days=14 (slots+runway) · GET /api/clear-schedule (dry count) ·
POST /api/clear-schedule (LIVE-WRITE: unschedules strictly-future + frees films) ·
GET /api/discover · GET /api/random (preview candidate; does NOT auto-load; 404 after 6 tries)
· GET /api/search?q= (used films flagged → edit route) · GET /api/autocrop?url=&scale= ·
GET /api/film/{id} (draft: rungs+decoys+auto headshot meta+stills) · GET /api/puzzle/{pid}
(edit-load, decodes answers) · POST /api/approve (LIVE-WRITE: puzzle JSON + tiers + headshots
+ ledger append + manifest upsert) · POST /api/update (LIVE-WRITE: rewrite in place, optional
re-crop, moves manifest entry; ledger untouched). Key handling is PER-REQUEST: the server
starts key-less; exactly 7 endpoints 500 without a key (discover/random/search/film/puzzle/
approve/update); autocrop/schedule/next-date/clear-schedule work without it.

**Servers**: game `python -m http.server 8000 --directory docs` (file:// won't work);
curation `.venv/Scripts/python -m uvicorn app:app --app-dir curation --port 8001`;
.claude/launch.json entries "docs"/"curation". Client error strings (docs/app.js): manifest
fetch fail → 'Could not load — are you running a local server?'; puzzle fetch fail → 'Could
not load the puzzle.'; unknown ?id → 'No such puzzle.'; empty practice pool → 'No puzzles to
practice yet.'. tmdb.py: missing key → SystemExit("TMDB_API_KEY not set — put your key in
curation/.env …"); bad key → RuntimeError "HTTP 401 (check your TMDB_API_KEY)". Non-TMDB
image URL → HTTP 400 "image must be a TMDB image URL".

## Per-skill outlines (author from these + the facts pack; verify everything)

### 2. degreesoffilm-architecture-contract
Read: CLAUDE.md, project_state.md, DESIGN.md, all docs/*.js, docs/puzzles/004.json,
curation/{publish,manifest,ledger,cipher,tmdb}.py.
Content: (a) the one load-bearing fact (key never reaches a player) + three zones + ASCII
diagram + consequences; (b) numbered TESTABLE invariants (key confinement w/ grep check,
layering law from real imports, pure/no-DOM rule, self-contained puzzles, manifest sole index,
ledger never-repeat, cipher parity/sentinel/idempotence/passthrough, one-puzzle-per-day upsert,
archive hides titles, stats isolation, attribution mandatory, IMMUTABLE PAST, SPOILER
DISCIPLINE) each with why + what-breaks + verify one-liner; (c) data-contract tables (puzzle/
manifest/ledger schemas + which fields obfuscated + image naming); (d) the date-semantics
divergence (DESIGN global rollover vs device-local todayISO) stated plainly as accepted;
(e) known weak points honestly (obfuscation≠security, localStorage-only stats, pool-dry silent
repeat, no CI, single curator, Haar limits, plaintext decoys) each with why-accepted + what
would change it; (f) "before you add X" decision table (new mode/rung type/stat/curation step/
secret/runtime-write → zone, invariants touched, static-v2 vs v3-server shaped).

### 3. degreesoffilm-change-control
Read: CLAUDE.md, project_state.md "Workflow / gotchas", git log, gh pr list/view.
Content: (a) change classification table (player-facing docs/ code · game rules/matcher
[test-first gate] · content publish · content edit [future-dated only] · curation-only ·
docs-of-record · meta) × (deploys-live? · landing path · required tests · post-land
verification); (b) non-negotiables each with rationale + incident (immutable past, spoiler
discipline incl. commits, key confinement, tests-green-before-push-because-no-CI, layering,
matcher test-first, never-repeat film, attribution, one-puzzle-per-day, stats isolation,
live-write-with-restore-plan); (c) landing checklists: player-facing (branch→tests→PR→
rebase-merge→delete→verify Pages), curation-only (owner confirms; direct-to-main precedent),
content publish (gates here, workflow in run-and-operate), docs-of-record (project_state
direct to main); (d) commit/PR conventions with real examples + spoiler-safe template +
stacked-PR warning (#13-on-#12 rebase dance — prefer sequential); (e) what needs owner
sign-off (destructive ops, past content, scoring/matcher changes, mass TMDB usage,
force-push); (f) rollback (git revert preferred on shared main; manifest+ledger git-tracked).

### 4. degreesoffilm-run-and-operate
Read: CLAUDE.md run sections, project_state.md, curation/app.py (ALL endpoints),
curation/static/index.html (verify UI behavior claims from its JS), curation/{publish,
manifest,ledger,build_rungs,decoys,credits_images,discover}.py CLIs, docs/app.js init.
Content: (a) run the game (commands, routes table, fresh-port rule); (b) curation tool tour
verified from static/index.html (schedule strip semantics — click empty day targets date,
click filled day opens editor; search/Discover/Randomize — Randomize previews only, "Use this
film →" commits; crop + Auto-crop + slider; rungs review — billing draft, human reorders edge
cases, decoys shown, headshots automatic; date auto next-free; Approve); (c) THE PUBLISHING
RUNBOOK — one numbered end-to-end checklist from start-tool to confirmed-live, including
verify-before-push (validator + play `?id=N` on fresh port), exact files produced, spoiler-safe
commit template, point-of-no-return marked; (d) edit/reschedule flow (future-only; /api/update
semantics; ledger untouched); (e) clear-scheduled flow (two-click; frees films; restore
command); (f) CLI alternates (which print vs write — verify: they don't write); (g) operational
cadence (runway; pool-dry = silent repeat, not crash).

### 5. degreesoffilm-domain-reference
Read: docs/match.js line-by-line, match.test.js, docs/{theme,daily,stats,frame,cipher}.js,
curation/{tmdb,build_rungs,discover,decoys,credits_images,images,cipher}.py,
curation/validate_ladder.py. May WebFetch public TMDB docs (no key) — date-stamp.
Content: (a) GLOSSARY table (rung, ladder, depth, score, tier, reveal, decoy, lifeline,
strike-out, manifest, ledger, runway, poser/cinephile/movie-buff, billing order, pool floor,
sentinel, headshot vs still vs backdrop vs poster); (b) TMDB data model as used here (endpoint
table → purpose → fields → calling file; the billing-vs-popularity boxed warning; image URL
composition; paging cap; attribution pointer to external-positioning; key hygiene);
(c) fuzzy-matching theory (normalization pipeline with an ACTUALLY-EXECUTED worked example —
run node one-liners; Levenshtein two-row DP; maxDist length-scaling rationale; surname rule
tradeoffs — "Joel" does NOT match "Joel Coen", verify; what the matcher deliberately does NOT
do; alternates live in answers[]); (d) image/saliency math (concentric tier expansion + aspect
coupling; FIND_EDGES as saliency; summed-area table O(1) window sums; band de-weighting for
title cards; Haar in 2 paragraphs + why curator approves + the OpenCV 5 pin story); (e) color
math (WCAG luminance/contrast as coded; HSV clamps; why bone text is fixed); (f) daily-game
conventions (manifest index, rollover + local-date divergence note, streak idempotence,
spoiler-safe share). Each section ends with "where this bites you" → sibling pointer.

### 6. degreesoffilm-config-and-flags
Read: every file in the constants list (facts pack "Game constants" + "Curation constants" +
env/launch/settings/package/requirements) — RE-VERIFY EVERY VALUE yourself.
Content: (a) "how configuration works here" (no flag system; the 6 mechanisms: module
constants, keyword defaults, query params, CSS vars, env vars, pip pins); (b) catalog tables
by zone with columns Name | Value (as of date) | Defined in | What it does | Change gate |
Re-verify one-liner; (c) boxed traps (max_cast 6-vs-8 override; cipher KEY/SENTINEL sync pair
— changing the key breaks all published puzzles, effectively frozen; opencv <5 pin; QUOTES
spoiler constraint; scoring curve asserted by game.test.js); (d) "add a config axis" checklist
(one module, param-threaded for testability, test asserting default, document here +
CLAUDE.md, re-verify line, change-control); (e) master re-verification block (one pasteable
sequence printing every value).

### 7. degreesoffilm-debugging-playbook
Read: project_state.md gotchas, docs/app.js error branches + onerror chain, docs/daily.js
fallbacks, docs/cipher.js, curation/tmdb.py + app.py error paths, images.py detect_faces,
manifest.json. Quote error strings EXACTLY from source.
Content: (a) first-five-minutes universal triage (what changed? which zone? is it cache?
run the relevant suite); (b) symptom→triage tables for Player client / Curation tool /
Content-data / Deploy-e2e (columns: Symptom | First probe | Likely causes ranked | Fix |
Incident ref) covering at minimum: blank page + each client error string; wrong/old daily
(pool-dry vs date bug); earliest-puzzle-shown (clock/manifest); gibberish text (forgot decode)
vs plaintext-in-devtools (unmigrated, by design); broken/missing credit image (onerror chain →
NNN-rK.jpg missing); reveal not widening (single-tier 001 = correct); theme wrong; stats/streak
idempotence; poser/practice not counting (by design); curation 500 (per-endpoint key) /401/
search empty/Randomize 404/auto-crop off-center (cv2 present? Haar miss? deweight bands)/
approve date surprise (next_date)/edit stale; manifest-ledger drift (→ diagnostics validator);
pushed-but-live-unchanged (Pages lag vs never-pushed; client only cache-busts the MANIFEST);
(c) trap hall of fame — the 3 costliest as half-page stories (cache trap, manifest collision,
character stills) with the discriminating experiment each; (d) discriminating-experiment pairs
(stale cache vs regression [fresh port]; pool-dry vs date bug; cv2-missing vs Haar-miss vs
faceless; obfuscation-drift vs forgot-decode; deploy-lag vs never-pushed); (e) escalation map
to siblings.

### 8. degreesoffilm-failure-archaeology
Mine: git log --oneline --all + git show, gh pr list/view (18 PRs), project_state.md
bottom-to-top, CLAUDE.md/DESIGN.md decision language, curation/validate_ladder.py.
Content: (a) "Settled battles — do not re-fight" one-line index at top; (b) chronicle entries
in uniform format Symptom/Idea → Investigation (dated) → Root cause/finding → Evidence
(verified hash/PR/file/doc; label project_state-only stories "recorded account") → Status
(SETTLED-REJECTED/FIXED/RULE-CREATED/PARKED/OPEN) → Do not → Unless (what would reopen).
Entries: popularity-sort rejection; manifest collision; character stills; OpenCV 5 pin;
reveal cut-then-shipped (author-ahead pattern; stale origin/reveal-mechanic branch note);
"exclude scheduled" dropped non-issue; live-write test incident; stale-cache trap;
Score History deferred to v3; poser/practice stat isolation (settled design); spoiler leak in
commits bdca151/3d7d17e (convention adopted, history not rewritten); stacked-PR dance; UX
playtest batch #7–#11 (playtest-driven pattern); commercial TMDB agreement parked. Sweep for
more. (c) patterns section (de-risk-before-building, author-ahead, data-reality-beats-plan,
silent-overwrite-by-key, pin-with-rationale, verification-environment traps) cross-ref
research-methodology; (d) entry template + raw-source map.

### 9. degreesoffilm-diagnostics-and-tooling  ← must SHIP AND RUN scripts
Content: SKILL.md + scripts/validate_content.py + scripts/puzzle_report.py, both WRITTEN,
RUN against the real repo, real output pasted into the skill as interpretation guide.
validate_content.py (stdlib + import curation/cipher.py via sys.path; READ-ONLY; runnable
from repo root by deriving repo root from its own file path): manifest parses/sorted/dates
unique; every entry's file exists+parses; puzzle id matches entry; every referenced image
exists (tiers + rung images); every obfuscated answer/caption/title decodes (sentinel round-
trip); every rung ≥1 answer; film rung first; ledger↔manifest cross-check (FIRST investigate
whether hand-authored 001 is in the ledger — build the check to match reality and report
reality); decoy coverage counts (informational); runway report. House style: PASS/FAIL lines +
summary + non-zero exit. puzzle_report.py <id>: decode and print one puzzle (date/theme/
images; per rung: index, role, decoded answers, caption, decoy count, image + exists-mark);
clearly marked SPOILER-REVEALING curator-only. If the validator finds a real repo discrepancy:
do NOT fix the repo; record it in the skill under "known findings as of <date>". SKILL.md
also: philosophy (measure > eyeball; what healthy means numerically); instrument inventory
(16 suites table; the two scripts with interpretation guides; SAFE-READ-ONLY vs LIVE-WRITE
endpoint table per app.py; browser probes + fresh-port trick + screenshots-time-out note;
git forensics one-liners); evidence-before-conclusions protocol cross-ref validation-and-qa +
research-methodology.

### 10. degreesoffilm-validation-and-qa
Read: ALL test files (characterize each suite from content, not guesswork), CLAUDE.md test
sections, docs/puzzles/001.json, find the shared cipher vector in both cipher suites (quote
exactly), game.test.js scoring assertions. Run all 16 suites to confirm counts.
Content: (a) the evidence bar (relevant suites green + NEW test red→green for changed behavior
+ fresh-port browser verification for player-visible + content validator for content; "tests
pass" ≠ proof for uncovered behavior — name the gaps: app.js DOM glue, curation/app.py
endpoints, static/index.html UI have NO automated tests, manual gate only; find others);
(b) test inventory table (file | modules | property guarded | count as of date | command) +
reverse map "changed file X → run suites Y" derived from the import graph (cipher changes →
BOTH languages' suites); (c) how to add a test (house pattern with real skeleton quoted from
one JS + one Python suite; pure-module placement rule; matcher contract-first boxed;
network-free requirement, temp dirs like publish.test.py); (d) golden inventory (shared cipher
vector — frozen, changing it breaks published content; puzzle 001 as plaintext-passthrough +
single-tier golden; scoring curve table; validate_ladder 5-film stress set — describe, don't
run); (e) content QA checklist pre-publish (rung order sane w/ human reorder of edge cases;
answers + variants; decoys plausible/not-accidentally-correct; crop reveals no title; tiers
2–3 don't spoil; headshots present-or-fallback; intended date; spoiler-safe commit planned;
validator green); (f) acceptance thresholds (all suites green ALWAYS; no weakened assertions
without change-control; count drift up fine, down suspicious).

### 11. degreesoffilm-docs-and-writing
Read: CLAUDE.md, DESIGN.md, project_state.md (as style corpora), .claude/settings.json hook,
git log (commit corpus), 2–3 gh pr view bodies.
Content: (a) docs-of-record map (document | role | cadence | lands how | precedence; what
does NOT belong in each; .claude/skills/ as a docs surface whose Provenance sections are the
update contract); (b) session-handoff discipline (why: stateless sessions + the SessionStart
hook; when; the structure reverse-engineered from project_state.md; copy-paste TEMPLATE);
(c) house style with real quoted examples (decision + why + rejected alternative + evidence;
DONE/REJECTED/parked vocabulary; YYYY-MM-DD; bolding; no-spoiler rule in public docs);
(d) commit/PR writing ("Area: summary" ≥6 real examples; spoiler-safe content template;
rebase-merge + kebab branches; PR body conventions from real PRs; one-line PR-vs-direct
pointer to change-control); (e) decision-record template (Decision/Date/Why/Rejected/
Evidence/Where-recorded) + rule that concluded investigations append a failure-archaeology
entry; (f) skill-library maintenance (code changes that invalidate a skill fact update the
skill + its Provenance date in the same session).

### 12. degreesoffilm-external-positioning
Read: DESIGN §5 attribution item + §6 commercial-agreement item, docs/index.html (quote the
shipped TMDB footer exactly), docs/app.js shareText. May WebSearch/WebFetch public TMDB
terms + comparable games' pages — every external claim sourced+dated or labeled "as of
training data". MUST NOT read as legal advice — open risks + questions-for-a-lawyer framing.
Content: (a) TMDB relationship (integration shape — curation-time only; attribution obligation
+ quoted footer + never-comes-off rule; key confidentiality; non-commercial vs commercial line;
modest usage pattern); (b) content-rights posture NOT-legal-advice (what's re-hosted — cropped
stills, headshots; TMDB terms cover API access, underlying images remain rights-holders';
fair-use-shaped POSTURE not cleared right; concrete lawyer questions before monetization);
(c) ecosystem map table (Framed, Cine2Nerdle, Actorle, Wordle-share culture — labeled) +
honest novelty analysis (NOVEL: vertical credit-dig depth mechanic, billing-order famous→
obscure ladder, per-puzzle sampled theming, curated reveal tiers; KNOWN ART: daily cadence,
guess-from-still, emoji share, streaks); "first/only" claims BANNED unless verified at claim
time; (d) claim standards (behavior claims reproducible from repo; superiority needs metric +
comparison; NO analytics exists today — player-count claims impossible; "provable today" vs
"not provable" two-column table); (e) going-public checklist (attribution everywhere; repo
history spoiler-check citing bdca151/3d7d17e; terms re-read; quota sanity; no-key grep;
claim-standard copy; spoiler-free share).

### 13. degreesoffilm-server-move-campaign  ← the owner-designated hardest problem
Read: DESIGN §6 v3 list, architecture facts above, docs/cipher.js rationale comments,
docs/game.js+match.js (note: pure ES modules — they can run server-side in Node UNCHANGED,
a major asset), docs/stats.js (schema to migrate).
Content — an EXECUTABLE, decision-gated campaign (numbered phases, exact steps, EXPECTED
observations at every gate, "if you see X instead → branch Y", ranked option menus with
theory obligations, fenced wrong paths, promotion through change-control, numeric success
criteria; label everything unbuilt CANDIDATE):
- Phase 0 baseline & constraints: keep static play working end-to-end; TMDB key stays
  server-side only; archive must keep working; don't lose players' localStorage stats;
  target cost ceiling ~$0–5/mo (owner's hobby scale — label assumption). Record baseline
  facts (puzzle count, obfuscation scheme, stats schema 'dof-stats-v1').
- Phase 1 server-side matching spike (retires the plaintext/obfuscation wart — the clean fix
  DESIGN names): design menu RANKED with obligations: (A) Cloudflare Pages/Workers + KV
  (static-adjacent, generous free tier — verify tier facts before relying); (B) small FastAPI
  service (reuses the team's Python; hosting on Fly.io/VPS); (C) Vercel/Netlify functions;
  (D) any-API-behind-CORS on a separate origin (CORS + latency obligations). The endpoint
  contract: POST /match {puzzleId, rungIndex, guess} → {correct, canonical} with answers
  living ONLY server-side; client falls back to local matching if the endpoint is down
  (availability gate). Gate: archive + daily play unchanged for a client with the feature off;
  with it on, devtools shows NO answers in any payload. Publishing pipeline change: publish.py
  gains a server-artifact step (answers file/KV push) — the curation tool stays private.
- Phase 2 accounts + DB (menu: Supabase/Firebase/self-Postgres; magic-link vs OAuth; data
  minimalism — store the minimum for cross-device stats). Gate: stats round-trip across two
  devices; localStorage migration path (import-on-first-login, never destroy local).
- Phase 3 leaderboard + integrity: DESIGN's asterisk rule (flag totals mostly from easier
  modes); anti-cheat reality: depth is client-computed today — a leaderboard requires
  server-validated runs (transcript replay against the same pure game.js/match.js running
  server-side — the repo's biggest asset for this); rate limiting; Gate: a forged transcript
  is rejected, a legit one accepted, synthetic cohort ranks correctly.
- Migration/compat protocol: old clients keep decoding obfuscated JSON until N+2 versions;
  REMOVING answers from static files is the LAST, least-reversible step — gate: server
  matching stable ≥14 days + owner sign-off; NEVER delete past puzzle files (immutable past).
- FENCED WRONG PATHS (each with the reason): client-side answer hashing (answer space is
  enumerable from public TMDB — offline dictionary attack defeats it; show the reasoning);
  hardening the XOR cipher (arms race, same enumerability); exposing a TMDB proxy carelessly
  (quota abuse, key-adjacent risk); rewriting the client in a framework as part of this
  (scope creep — the vanilla client is an asset); putting the leaderboard before server-side
  matching (unvalidatable scores).
- Rollback plan per phase; all promotions via degreesoffilm-change-control; keep
  external-service facts labeled verify-at-execution-time.

### 14. degreesoffilm-proof-and-analysis-toolkit
Read: curation/validate_ladder.py (whole), match.test.js, both cipher suites, images.py
best_window, publish.test.py, game.test.js, docs/frame.js+app.js fallback chains.
Content — first-principles analysis RECIPES, each: when to use → steps → worked example from
THIS repo (cited): (a) throwaway de-risk script before building (validate_ladder.py's A/B
popularity-vs-billing protocol; 5-film stress set; decision recorded in DESIGN §5);
(b) contract-first algorithm change (match.test.js as spec table; red→green); (c) cross-
language parity via shared fixed vector (cipher suites; why a vector beats inspection);
(d) pure-core/IO-shell decomposition (best_window summed-area correctness argument;
publish() unit-tested against temp dirs); (e) enumerable-domain security analysis (why XOR
obfuscation is anti-snoop only: key ships AND the answer space is public TMDB — derive the
attack; conclusion = server-side matching, cross-ref the campaign); (f) idempotence/sentinel
design proof (cipher passthrough properties enabling safe migration-by-construction);
(g) predict-numbers-before-running template (scoring curve derived from formula then asserted);
(h) fallback-chain failure analysis (face→edge→curator; rung image→full frame→hidden — how
to enumerate and test each hop).

### 15. degreesoffilm-research-frontier
Owner's tracks (2026-07-02): automated curation, novel modes, scale & integrity — NOT matcher
craft. For each open problem: why current SOTA fails → this project's specific asset → first
THREE concrete steps IN THIS REPO → falsifiable "you have a result when…" milestone → "do not
start here" fences. Problems to cover:
(a) AUTOMATED CURATION: auto-crop acceptance (asset: curator approve/re-drag flow could log
final-vs-suggested boxes = free labeled data; instrumenting that logging is step 1; milestone
e.g. "suggested box accepted unmodified in ≥70% of 20 consecutive puzzles"); difficulty
calibration (asset: rung-level TMDB stats + future depth histograms; milestone: prediction
correlates with observed depth distribution); decoy quality scoring (asset: decoys.py pools +
popularity distances). Fence: don't train custom models before exhausting FaceDetectorYN/
heuristics; opencv>=5 migration is a deliberate step.
(b) NOVEL MODES: true degrees-of-separation graph play, static-first (asset: the curation
pipeline can prebake a film↔person graph; steps: graph extractor CLI in curation/, size
budget measurement, pathfinding prototype offline); Movie Buff via prebaked popular-title
index (static-possible: top-N title index + client autocomplete, no key; steps: index builder,
size/latency budget, matcher integration; milestone: autocomplete works offline on the
archive page without leaking eligible answers). Fence: DESIGN says a live TMDB call from the
browser is banned (key leak).
(c) SCALE & INTEGRITY: verifiable runs/anti-cheat (asset: game.js/match.js are pure ES modules
— the SAME code replays server-side; steps: define run-transcript format, offline replay
validator in Node, tamper tests; milestone: forged transcript rejected, legit accepted) —
feeds the campaign's Phase 3. Everything labeled OPEN/CANDIDATE; route promotions through
change-control; cross-ref server-move-campaign + research-methodology.

### 16. degreesoffilm-research-methodology
Mine: the project's own history for the discipline it already practices (validate_ladder
de-risk; match.test.js contract-first; character-stills retirement; "exclude scheduled"
investigate-and-drop; playtest-driven UX batch #7–#11; author-ahead tiers).
Content: (a) the evidence bar (one mechanism must explain ALL observations including
negatives; conclusions get an assigned adversarial-refutation pass — in agent sessions, spawn
a red-team reviewer; solo, write the strongest counter-argument before concluding);
(b) hypothesis-predicts-numbers-before-running (worked: scoring curve; ladder validation
predicted "leads top, director early" before querying); (c) the idea lifecycle HERE: idea →
DESIGN §6 parking lot with v2/v3 gate → de-risk (throwaway script or investigation) → smallest
buildable slice → test-first → ship via change-control → project_state record; OR documented
retirement (character stills; "exclude scheduled" drop) — retirement REQUIRES writing the why
into failure-archaeology so it isn't re-fought; (d) where ideas historically came from
(playtests → UX batch; curation pain → Randomize/Auto-crop/Clear-scheduled; spec-time
foresight → authored-ahead tiers); (e) experiment hygiene (never against live/committed data
— the puzzle-004 incident; git-reversible by construction; name the falsifier before starting);
(f) a hypothesis-card template (Claim / Predicted numbers / Experiment / Falsifier / Status)
+ where cards live (project_state or the relevant skill).

## Phase 3 — review and fix (after ALL 16 exist)

Three review passes over the COMPLETE set (parallel agents if available, else sequential
inline), then one fix pass:
- **FACTUAL**: re-verify every command/flag/path/constant/hash/count in every skill against
  the repo (run the read-only ones); flag anything invented or stale; severity by "would it
  send an engineer down a wrong path?" (BLOCKING / IMPORTANT / MINOR).
- **DOCTRINE**: contradictions with CLAUDE.md/DESIGN.md/owner rules or BETWEEN skills;
  overstated claims (oversell); anything that changes behavior without routing through
  degreesoffilm-change-control; spoiler-discipline violations inside the skills themselves.
- **USABILITY**: frontmatter description trigger quality (would a model load the right skill
  from the description alone?); duplication (one home per fact — others must cross-reference);
  self-containedness; scannability; presence of all required sections.
Fixer applies all BLOCKING + IMPORTANT fixes (edits only inside .claude/skills/), notes
MINOR ones unfixed. Reviewers must check the diagnostics scripts by RUNNING them.

## Final report to the user (end of Phase 3)

1. Skill inventory: 16 rows, name + one-line description + line count.
2. What was verified by spot-check (commands actually run, values actually re-read).
3. What remains uncertain (labeled items, external facts, anything time-sensitive).
4. Reminder: this file (_BUILD-STATE.md) should then be deleted (or converted into a short
   README index for the library), and the new `.claude/skills/` tree committed via the
   project's change-control conventions (owner decides landing mode; suggested commit:
   "Docs: add the project skill library (.claude/skills)").
