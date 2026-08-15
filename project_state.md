# Project State — Degrees of Film

> **Running handoff doc. Read this first each session, and keep it updated.** Division of labor:
> `CLAUDE.md` = how the code works (durable); **this file = where we are right now** (living).

_Last updated: **2026-08-15, session end (launch eve — owner shares the game 2026-08-16)**._

## ▶ Start here next session (2026-08-15 version)

1. **The owner shared the game with a group on 2026-08-16** — the first real players.
   Everything below this line was built and merged for that moment. First questions next
   session: how did the launch land? Any bug reports? **Does anyone come back on day 3?**
2. **Current state:** corpus 6,566 films / 16,379 people / 80,767 edges (floor 500/6.0);
   **74 dailies through 2026-10-13** (+10 backdated archive games); Matinee light theme +
   brand identity live; share-the-game button live and **owner-verified sharing the
   animated GIF correctly from mobile** after three same-evening fixes (PRs #36–#38:
   tooltip tap-trap + gesture-window prefetch, TDZ hotfix, prefetch race).
3. **Docs and skills are current** — CLAUDE.md, BRAND.md, the re-verified skill library
   (+ failure-archaeology entries 18–23), and the global mirror all updated same-session.
4. **Open items:** watch the launch (evidence for the gated soft-fail caddy accrues from
   real players now); restock by **~2026-10-06** (harvest picks up the 500/6.0 floor
   automatically); TMDB-terms re-read stays a gate before any *public* (beyond
   friends) push; parked: role glyphs, PWA manifest, in-game rules from `?play`.

## 🎞 GIF-SHARE RACE FIX — MERGED 2026-08-15 (PR #38, `a947ebd`)

Owner report: shares arrived as the static PNG. Cause: a fast tap beat the 68 KB
invite.gif prefetch → silent fallback to text+url → the chat rendered the og.png unfurl.
The tap now races the in-flight prefetch against a 700 ms beat (inside the gesture
window; the earlier bug was an UNBOUNDED await) before choosing which share to send.
Platform floor stays: no file-share support → text+link+og unfurl. If a platform
rejects GIF files specifically, the next lever is an MP4 card variant (not built).
**OWNER-VERIFIED on device: "it works now, the gif is sharing correctly."**

## 🚑 HOTFIX — TDZ regression from PR #36, MERGED 2026-08-15 (PR #37, `6370e99`)

PR #36 declared `let inviteFile` mid-module, below the top-of-file `boot()` call —
`renderHome()` hit the temporal dead zone and the LIVE home card showed "Couldn't load
today's connection. Cannot access 'inviteFile' before initialization" until the hotfix
landed (~30 min exposure). Why verification missed it: the error was caught into the
today-card and the check looked at the BUTTON under test, not the card beside it.
**Rule adopted: browser verification asserts the page's primary content, not just the
feature under change.** Recorded as failure-archaeology entry 23. Fix: state hoisted to
the module-state block above `boot()`.

## 🩹 MOBILE SHARE FIX — MERGED 2026-08-15 (PR #36, `d089f39`)

Owner reported the share button flaky on mobile. Root causes, both fixed: **(1) expired
user gesture** — the handler awaited the invite.gif download before `navigator.share()`;
mobile Safari's transient-activation window closed and the sheet silently refused. The
card is now **prefetched when a share button appears** and the tap shares instantly with
whatever is ready. **(2) tooltip tap-trap** — `data-tip` hover bubbles ate the first tap
on touch (iOS hover-before-click); tooltips are now `display:none` under
`@media (hover:none)`, sitewide. Verified under mobile emulation (first tap fires, no
overflow at 375px). Merged directly given launch timing (owner-reported launch-day bug);
PR #36 carries the full evidence.

## 🔗 SHARE-THE-GAME BUTTON — MERGED 2026-08-15 (PR #35, `a423a33`)

The game shares itself: "Share this game" on the home CTA row + "Share the game" on the
end card (tooltip: "Send the game itself, not your score"). Web Share API with
`docs/invite.gif` (68 KB animated Matinee invite card, fetched only on tap) attached
where the platform allows files; text+url sheet otherwise; clipboard fallback with
button-label feedback in every path (including copy-blocked). Dismissed sheet = non-event.
BRAND.md documents the asset. Browser-verified both buttons + worst-case fallback; 6 JS
suites green.

## 🚪 LAUNCH PREP — the owner shares the game 2026-08-16 (PR #34, MERGED 2026-08-15 as `891a6fe`)

Three owner-requested moves for tomorrow's share: **(1) easy first daily** — tomorrow's
slot (2026-08-16) was regenerated as a **par-2 between two top-200-popularity films**
(`--par 2 --top 200`) so newcomers' first game is warm; the old par-3 pair was discarded
unplayed. **(2) archive stocked for day one** — ten backdated games (#80–#89,
2026-08-01 → 2026-08-10, pars 2,2,3 mix) fill the archive so a hooked newcomer has
**15 games** to keep playing. These were never live dailies — they're archive filler by
design, replay-channel only, no streak impact. **(3) personal share card** — 1200×630
Matinee-brand invite PNG (Pillow one-off via the main-checkout `.venv`; script in the
session scratchpad; no real film/person names per BRAND.md) delivered to the owner —
it is NOT in the repo; the og.png unfurl still covers pasted links. `--check`: **74
dailies, 0 broken**; affected suites green; archive browser-verified (15 rows).

## 📈 CORPUS EXPANDED — pool floor widened 800/6.5 → 500/6.0 (PR #33, MERGED 2026-08-15 as `7dc07b3`)

Owner-directed ("pull more movies in for autofill + connections"). **Measured before
building** (one `discover` call per candidate floor; throwaway probe, deleted): a grid of
floors was priced and the owner picked **500 votes / 6.0 avg** from real numbers. Result:
**6,566 films / 16,379 people / 80,767 edges, 345 KB gz** (was 3,682 / 9,791 / 42,948 @
190 KB) — 1.8× films, 1.9× edges; the newly admitted famous-but-middling blockbusters are
prime connective tissue. Harvest fetched 2,925 new credit sets (append-only cache).
**Schedule repair:** the denser graph shortened 14 future dailies' pars (12 par-3→2,
2 par-4→shorter; **all five past dailies survived untouched** — immutable past never came
into play). The 14 broken were deleted and regenerated at their same dates on the weekly
arc (ids #65–#78; Saturdays kept par 4). Final `--check`: **64 dailies, 0 broken.**
The harvest.test.py floor tripwire was moved to (500, 6.0) with the decision documented.
Worst-case matcher scan at 16,379 names: **~3 ms** (measured in-browser). challenges.json
still 8.2 KB. Docs + skills (domain-reference, validation-and-qa, external-positioning)
updated to the new numbers; caches + 64-entry sidecar copied back to the main checkout's
`curation/`. Note the site is now **~360 KB total** (was ~200 KB) — the owner accepted the
trade explicitly when picking the floor.

## 🎨 MERGED — the "Matinee" light-theme redesign + brand identity (PR #32, 2026-08-15)

**Merged as `888402c` on the owner's "merge it" — the light theme, BRAND.md, and the
adopted brand identity are live.** The identity came from the owner's Claude Design
project ("Movie Trivia Game Graphics", imported via the design MCP): the
**chain-into-degree mark** (favicon + masthead `logo-mark.svg` + `logo-lockup.svg`),
**seven ticket-stub verdict badges** on the end card (mapped from score-vs-par; terracotta
broken-chain on a loss), an **under-par confetti scatter** (static — reduced-motion players
finally get a celebration), and a **light 1200×630 og.png** replacing the dark card. The
import also caught and fixed a real bug: the dead-CSS sweep had cut the bare `.eyebrow`
rule, but app.js builds that class dynamically on the end card — restored. BRAND.md's
asset section documents the adopted identity. Record below kept for the design rationale:

The owner asked for a lighter, more inviting look ("I don't do dark mode"). Researched color
psychology (warm off-whites cut glare vs pure white while keeping contrast; warm hues read
inviting; NYT-games register), mocked **three directions** (Matinee cream+gold /
Ticket-Stub cream+teal / Sunny-Marquee white+yellow) on a comparison page, owner picked
**A · Matinee: warm cream paper + marquee gold**. Implemented in `docs/style.css`:
`:root` swapped to the Matinee palette and the vars **semantically renamed**
(`--ink`→`--paper` ground, `--ink2`→`--card`, `--bone`→`--ink` text — old names would lie
in a light theme); text-role accents moved amber→`--amber-deep` (#96660a) for WCAG contrast
on cream; hovers darken instead of brighten; tooltip/shadow/calendar-silver retuned;
confetti retoned in `app.js`; `favicon.svg` rethemed (paper ground, gold links). Also swept
**dead dig-era CSS** (.frame/.mark/.rail/.rung/.roast/.quote/.modes cards/.again + more —
verified unreferenced by index.html+app.js): style.css 367→300 lines. Verified in the
browser via computed styles (pane hidden → screenshots unavailable, per the gotcha):
body/paper/ink/amber correct on home + play, **today's daily #5 played end-to-end through
the real UI to a win** — end card fully themed (deep-gold hero, cream share box, countdown,
obscurity, reveal). 6 JS suites green. **og.png stays dark for now** (regenerating needs a
Pillow one-off; a dark social card is acceptable — follow-up if wanted).

## ~~Start here next session~~ (2026-08-14 version — SUPERSEDED by the top of this file)

1. **The game is LIVE** at https://bluesuitcase.github.io/DegreesofFilm/ — the
   degrees-of-separation rebuild WITH the complete Comeback Loop (Waves 1–3, all built and
   merged 2026-08-14), **plus the corpus refresh + restock (PR #30, merged and verified live
   the same night — Pages serves 64 dailies / the 3,682-film graph).** Work happens on
   `main`. **Worktrees/branches pruned 2026-08-14 late evening:** all stale worktrees
   deregistered + emptied (four zero-byte root folders remain pinned as other sessions'
   CWDs — they'll rmdir once those close or after a reboot), all merged local branches and
   the remote rebuild branch deleted. Only `main` + the corpus-refresh session's worktree
   (`project-state-review-0347aa`) remain.
2. **Read `CLAUDE.md` next** — it is current for the rebuilt game (ruleset, share grammar,
   content ops, curator's-note rule, immutable past). The `degreesoffilm-*` skill library
   was **re-verified 2026-08-14** (10 skills, every fact checked against the repo) — it is
   trustworthy again; if a code change invalidates a skill fact, update the skill the same
   session.
3. **Run everything from the repo root:** serve `docs/` on any port to play locally; suites
   are `node {match,daily,stats,corpus,chain,solve}.test.js` + `python
   curation/{harvest,graph_build,challenge_gen}.test.py` — **9 suites, 268 assertions, all
   green at session end.** Publishing content = `python curation/challenge_gen.py --days N`
   (weekly par arc is the default; `--check` re-verifies everything incl. curator notes).
4. **The canonical to-do is the OPEN ITEMS list below.** Nothing is blocked on code.

## ⏭ Open items (in order)

1. ~~Share the game~~ **HAPPENING 2026-08-16** — launch prep merged (easy opener,
   15-game archive, share buttons + invite cards). Watch: does anyone come back on day 3?
2. **Watch the first par-4 Saturday land** (2026-08-15, pilot curator's note attached) —
   the first live test of the difficulty arc.
3. ~~Restock by ~2026-09-06~~ **DONE 2026-08-14 (see the refresh record below)** — corpus
   refreshed + 30 dailies appended. **Runway is now 64 dailies through 2026-10-13; next
   restock by ~2026-10-06.**
4. **Soft-fail caddy** (the only unbuilt Comeback Loop item) — gated on measured DNF rates
   from real players (<~10% → skip forever) + owner sign-off (rules change).
5. ~~Skill-library re-verification pass~~ **DONE 2026-08-14 (see the record below)** — 10
   skills recast for the rebuilt game; graph-mode-campaign retired (campaign complete).
6. Wave-2-era follow-ups parked in the plan: role glyphs in the share (needs a harvest
   schema change + corpus rebuild), PWA manifest, in-game rules access from `?play`.

**Cloudflare: fully torn down 2026-08-14** (owner-requested) — the orphaned `dof-match`
Worker and its `ANSWERS` KV namespace were deleted via the API; the endpoint 404s. The
project is now purely static files. `curation/.env` still holds the TMDB key (needed for
harvests) and the now-unused Cloudflare token (rotate/revoke at leisure).

**The launch, the plan, and the build record follow below in reverse order — history, not
instructions.**

## 📚 SKILL LIBRARY RE-VERIFIED — 2026-08-14, late evening (after the corpus refresh)

Open item 5 done: the 10 surviving `degreesoffilm-*` skills were recast for the rebuilt
game (one editing agent per skill, every kept fact verified against this repo; net −800
lines). Pattern per `writing-for-agents`: dig-era content cut, environment-caches (test
counts, file lists) replaced with pointers to CLAUDE.md/the code, descriptions retargeted
to live triggers, worked examples swapped for current ones (corpus-size table, small-world
experiment, match.cases.js contract, par `--check`). **Deleted:** `graph-mode-campaign`
(campaign complete — its subject became the product) and `_BUILD-STATE.md` (historical).
**failure-archaeology grew** (453→585) with five rebuild-era entries: the dig retirement,
the subgraph-autocomplete leak, the small-world falsification, the "one-off" verdict → the
Comeback Loop, and the KILLED list. Side fixes the pass surfaced: CLAUDE.md gained
`solve.js`/`solve.test.js` (previously unlisted), the **immutable-past rule** (now formally
stated), and dropped its mid-migration banner; stale comments fixed in `match.cases.js`
(dead worker.test.js reference) and `docs/app.js:637` (frozen grammar now cites CLAUDE.md).
Noted for the owner (from external-positioning's re-verification): shipping the full
TMDB-derived credits graph in a public repo is **bulk redistribution the old rights posture
never evaluated** — flagged in that skill as an open TMDB-terms question, with terms
re-reading kept as a going-public gate. The global mirror `~/.claude/skills/` was synced to
match. Suites all green after the pass.

## 🔄 CORPUS REFRESHED + RESTOCKED — 2026-08-14, late evening (after launch)

Open item "restock by ~09-06" done early, on branch `claude/project-state-review-0347aa`:
`harvest.py` (44 new films crossed the pool floor since 2026-07-11, 46 credit sets fetched) →
`graph_build.py` (**3,682 films / 9,791 people / 42,948 edges, 190 KB gz** — was
3,637/9,679/42,367 @ 188 KB) → `--check` on the rebuilt corpus (**all 34 published dailies
survive, pars unchanged**) → `challenge_gen.py --days 30` (**64 dailies through 2026-10-13**,
8.2 KB raw / 2.8 KB gz) → final `--check` 64/64 green. All 9 suites pass; browser-verified on
:8010 (finished-state restore of daily #4 re-runs the route reveal against the NEW graph —
zero console errors; all 9 scheduled Saturdays hold par 4). Diff is exactly
`docs/graph.json` + `docs/challenges.json` plus these doc updates. CLAUDE.md corpus numbers
refreshed to match. **Gitignored curation assets** (`films_cache.jsonl`,
`people_harvest_cache.jsonl`, `challenge_solutions.json` — now 64 entries) were copied back
to the **main checkout's `curation/`, their canonical home** — the old worktrees held the
only sidecar copies and can now be pruned safely.

## 🚀 MERGED AND LIVE — 2026-08-14, end of the same evening

**PR #29 was rebase-merged into `main` (`87699a9` → `ce6b4dd`) on the owner's explicit
"merge", and GitHub Pages deployed within a minute.** The LIVE site at
https://bluesuitcase.github.io/DegreesofFilm/ now serves the rebuilt degrees-of-separation
game **with the complete Comeback Loop (Waves 1–3)** — verified live: home renders today's
daily #4, zero console errors, new OG meta present. The old dig is retired from production.
The rebuild worktree/branch (`claude/session-context-634bc2`) is merged and can be cleaned up;
**work now happens from `main`.** Still open, in order: (1) **share the game** — the loop is
built for a group chat, it needs one; (2) watch the first par-4 Saturday (2026-08-15, pilot
curator's note attached) land with real players; (3) ~~delete the orphaned Cloudflare Worker~~ **DONE
2026-08-14 late evening, owner-requested:** `dof-match` script + its `ANSWERS` KV namespace
deleted via the API (scoped token in `curation/.env`, which the account still holds along
with the TMDB key); endpoint verified 404. Nothing remains on Cloudflare; (4) corpus refresh
(caches from 2026-07-11) then `graph_build` + `challenge_gen --check`; (5) the soft-fail caddy
stays gated on measured DNF rates + owner sign-off; (6) skill-library re-verification pass
(post-rebuild staleness). Runway: 34 dailies through 2026-09-13 — restock by ~09-06.

_Previous update: **2026-08-14, second session (evening)**. **THE OWNER PLAYTEST HAPPENED — the
gate is passed with a verdict:** "I like it, but it's missing something… feels like a one-off
rather than I-need-to-come-back-and-play-this-again-asap." That verdict was put through a
12-agent research workflow + 3 adversarial critics, merged with the owner's brief (Wordle is
the model; end felt flat; wants beating-friends/route-comparison + film discovery; share-based
social, NO accounts/leaderboards), and produced **THE COMEBACK LOOP plan** — see "Next phases"
below (it replaces the old 'Next up' ordering) and the published report at
https://claude.ai/code/artifact/83fee604-32dd-4373-885a-af1a4176b856 . Core diagnosis: **the
game ends at the wrong moment** — no countdown, no solution reveal, own chain hidden at end,
share link unfurls bare (no OG/favicon), zero @keyframes, all 30 pars are 2–3. Session
side-effects: agent-skills setup committed to this branch as `3cc45ba` (agents/issue-tracker.md,
agents/domain.md, CLAUDE.md "Agent skills" block — GitHub Issues tracker; ADRs will live in
root `adr/`, NEVER under docs/). **OPEN DECISION for next session: build Wave 1 on this branch
then merge once (recommended), or merge PR #29 now and fast-follow.** Owner paused before
deciding. Everything below remains the accurate rebuild handoff; where the old 'Next up' list
disagrees with the Comeback Loop plan, the plan wins._

### ⭐ WAVE 3 BUILT — same evening (commit `dcafaac`). THE COMEBACK LOOP PLAN IS COMPLETE.

Three of four Wave 3 items shipped: **(1) completion calendar + handicap** — ?history now
renders a month-grid calendar (gold day-of ≤par / silver late-or-over / red broken / dashed
replay-filled / dotted future); replays record into an isolated `archive` channel (`stats.js
recordArchive`, by id, keep-better — the anticipated per-mode stats design, streak untouched);
handicap = rolling avg vs par (losses +3, hidden until 10 rounds); day-of stamped via
`playedOn`; **(2) backup codes** — `exportRecord`/`importRecord` (`DOF1.` prefix, byte-safe),
merge = union keep-better then `rebuildStats` recomputes ALL derived fields from the merged
history (tested: a bridged date gap yields a streak neither device had); Back up / Restore UI
on the scorecard; **(3) curator's note** — optional `note` per daily on the end card;
`challenge_gen --check` HARD-enforces "texture only, never a connector" against all closers +
the sidecar; pilot note live on an upcoming daily; rule documented in CLAUDE.md. **(4) The
soft-fail caddy was deliberately NOT built** — its own gate requires measured DNF rates (no
players yet) + owner sign-off (rules change). **Suites: 268 assertions all green** (stats 62,
challenge_gen 33). Browser-verified: calendar classes {gold 1, empty 3, future 30}, backup
export→wipe→restore round-trip byte-identical. **PR #29 = rebuild + Waves 1+2+3. Merge =
launch — the only remaining step.**

### ⭐ WAVE 2 BUILT TOO — same evening (commit `a1c4c12`)

All three Wave 2 items shipped on this branch: **(1) near-miss feedback** — burned guesses
return graph temperature via `chain.js nearMiss` ("one degree away (a shared 2010 film)" /
"two degrees off" / "stone cold"); the small-world worry was measured and FALSIFIED first
(6,800 samples: d=1 27%, d=2 60%, d=3+ 15% — the experiment script is in the session
scratchpad, prediction written before running); **(2) the juice pass** — first @keyframes
ever (pill entrances, shake-vs-dot-crack two-tier errors, hero pop, staggered win re-trace,
theme-toned under-par confetti on fresh finishes), all inert under prefers-reduced-motion,
plus named golf verdicts (`stats.js verdictName`: Albatross→Double bogey) on the endline;
**(3) the obscurity score** — `solve.js obscurity()` 0–99 (percentile×log geometric blend,
calibrated: hubs 0, floor 88, textbook routes median 19), on the end card with tooltip and
in share line 3 (grammar doc updated, line 1 untouched). **Suites now 241 assertions, all
green** (chain 51, stats 40, solve 20). Browser-verified on a replay end-to-end. Wave 3
remains: calendar+handicap, curator's note, backup codes, evidence-gated soft-fail caddy.

### ⭐ WAVE 1 BUILT — 2026-08-14 evening, same session as the plan

**All four Wave 1 items are implemented, tested, and committed on this branch** (two
commits after the plan handoff): **(1) the ritual end card** — own chain kept visible,
client-BFS shortest-route reveal via new pure `docs/solve.js` (loss now pays off; win
compares; "N distinct ways" geodesic count), first-ever render of the stats histogram,
streak line, countdown to midnight (only when tomorrow's daily exists); **(2) durable
record** — finished-state restore (`dof-run-v1`), mid-run persistence (`dof-live-v1` via
`chain.js toJSON/fromJSON`, portable TMDB-ids+names, discard-on-mismatch), streak
recomputed at load + at-risk nudges on home/scorecard; **(3) share overhaul** — line-1
grammar FROZEN (see CLAUDE.md "Share grammar"), glyph trail 🔗/🟥/↩, share text rendered
on-page, favicon.svg + OG/Twitter meta + original-art og.png (Pillow one-off, repo-root
.venv still has it); **(4) weekly difficulty arc** — `par_for_date` in challenge_gen.py
(Mon–Wed 2, Thu–Fri 3, Sat 4, Sun 3, step-down fallback), future dailies restocked: 34
total, 5 Saturdays all par 4, `--check` 34/34 green. **Suites: 9 (was 8), 224 assertions
(match 25, daily 11, stats 33, corpus 35, chain 46, solve 15; harvest 8, graph_build 23,
challenge_gen 28), all green.** In-browser verified end-to-end on :8010 (burn → hop →
mid-run reload → finish → revisit; zero console errors). **NOT yet merged — PR #29 now
carries the rebuild + Wave 1; merge = launch.** Wave 2 next (near-miss feedback, juice
pass, obscurity score), then Wave 3 — see the plan below.

### The Comeback Loop (2026-08-14 plan — critic-verified, owner-briefed)

**Wave 1, ship as ONE unit (~1–2 sessions):** (1) **Ritual end card** — own-chain recap stays
visible, client-BFS shortest-route reveal (loss = the payoff, not "stays hidden"), render the
already-recorded histogram (dead .hist CSS exists), streak, countdown to local midnight (only
when tomorrow's entry exists), Share. New pure `docs/solve.js` + tests; count distinct routes
via path-DP over BFS layers, not node counting. (2) **Durable record** — finished-state restore,
mid-run persistence (serialize by TMDB ids/names, NOT corpus indices), streak recomputed at
load + at-risk state; defer streak freezes. (3) **Share loop fix** — favicon + OG/Twitter meta
FIRST (bare-URL unfurl kills the loop; og:image must be original art, never TMDB), render share
text on page, glyph-trail share (🔗 + 🟥 burn pips + ↩, zero-data version; role glyphs 🎭🎬🎼
need a harvest-schema change — later), freeze the line-1 grammar in DESIGN.md (enables Discord-
bot leagues, no server). (4) **Difficulty arc** (curation) — NYT-crossword weekly par shape
(2 early week → 4–5 weekend) + anti-hub pairs; use the discarded `count_routes`. Critics: this
matters more than everything except the end card. **Wave 2:** near-miss feedback (validate
distance distribution offline first — small-world risk), juice pass (staged reveals, named
verdicts Eagle/Birdie/Par/Bogey, theme-toned), obscurity score 0–99 (calibrate vs bottom-heavy
degree distribution). **Wave 3 (when streaks exist):** calendar+handicap, curator's note (hard
rule: never identify a geodesic film/person; generator assert), backup codes, soft-fail caddy
(ONLY if DNF >~10% measured; rules change = owner sign-off). **KILLED:** spoiler-gated challenge
links (leaky funnel), community-pulse Worker (needs server AND a crowd; revival trigger =
organic strangers sharing + min-N gate + owner sign-off), accounts/leaderboards (owner's call).
Full research + verdicts: workflow run `wf_3e3c18d6-60e` in session
`0198cf19-ed05-46a2-ab23-0a01aeb96843` (12 agents, ~1.07M tokens).

**THE GAME WAS REBUILT.** The vertical-dig daily (name the film
from a still, then dig through its credits) was **retired and deleted** at the owner's direction —
"I just don't find it very fun" — and the site is now built entirely around
**degrees-of-separation: connect two films through the people who made them**. All work is
**committed as `3da6a94`** on branch `claude/session-context-634bc2` (368 files, +2,080/−13,703)
— **pushed as [PR #29](https://github.com/Bluesuitcase/DegreesofFilm/pull/29), NOT merged, NOT live.**_

## ~~Start here next session~~ (2026-08-11 version — SUPERSEDED by the top of this file)

The rebuild-era checklist that lived here (playtest gate → merge decision) completed on
2026-08-14: playtest done, verdict acted on, PR #29 merged, site live. The gitignored TMDB
caches referenced below now matter only for the next corpus refresh — copies live in the
repo root's `curation/` after the merge.

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
- **Gitignored curation assets live in the MAIN checkout's `curation/`**
  (`films_cache.jsonl`, `people_harvest_cache.jsonl`, `challenge_solutions.json`, `.env`).
  A worktree doesn't inherit them — copy all four in before running content ops, and copy
  refreshed caches + the sidecar back after.
