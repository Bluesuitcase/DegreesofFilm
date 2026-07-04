---
name: degreesoffilm-docs-and-writing
description: >
  The docs of record for Degrees of Film, the update discipline, and the house writing style.
  Use at the END of every work session (updating project_state.md is mandatory before you
  stop); after shipping ANYTHING (which docs must the same change make true?); when writing
  a commit message or PR title/body (the "Area: imperative summary" convention + the
  spoiler-safe rule for content commits); when updating CLAUDE.md, DESIGN.md, or
  project_state.md and unsure which one owns a fact; when recording a decision or a rejected
  alternative; when a code change invalidates something a skill under .claude/skills/ says;
  and whenever you ask "where do I document X?". Contains copy-paste templates for the
  session handoff, decision records, and commits/PRs. NOT for the rules of what may land
  where (degreesoffilm-change-control) or how to publish a puzzle
  (degreesoffilm-run-and-operate).
---

# Degrees of Film — Docs of Record & House Writing Style

How this project stays maintainable by strangers: every session leaves the written record
right. Facts verified against the repo on **2026-07-03** (HEAD `10668ca`, clean tree, 18
merged PRs, 0 open). Corpus = CLAUDE.md, DESIGN.md, project_state.md, `git log --oneline`
(67 commits), `gh pr list/view`.

**The one habit that matters:** documentation here is not an afterthought — it is the
project's memory. AI sessions are stateless; a SessionStart hook in `.claude/settings.json`
injects `project_state.md` into **every** new session's context (verified: the hook runs
`node -e "...readFileSync('project_state.md'...)"`). Whatever you write there is literally
what the next session knows. Write it wrong and the next engineer starts wrong.

---

## 1. Docs-of-record map

| Document | Role | Update cadence | Lands how | Precedence |
|---|---|---|---|---|
| `DESIGN.md` | The full spec: ruleset → architecture → stack → schema → roadmap → §6 parking lot | When the *design* changes (new decision, item shipped/deferred/rejected) | With the change that makes it true (same commit/PR) | **Wins all conflicts.** CLAUDE.md itself says: "**DESIGN.md is the full spec and source of truth.** … when the two disagree, DESIGN.md wins." |
| `CLAUDE.md` | "How the code works" — durable working summary + file map + run/test instructions | When code structure/behavior it describes changes | With the change that makes it true | Below DESIGN.md |
| `project_state.md` | "Running handoff — current task, decisions, next steps. Read FIRST." The living where-are-we-now doc | **Every session that changes anything** | **Direct to `main`** — its own header says "keep it updated in place on `main` (no PR needed for this file)" | Snapshot only; durable facts must also live in CLAUDE.md/DESIGN.md |
| `.claude/skills/*/SKILL.md` | Maintained operational docs (runbooks, conventions, references) | When a code change invalidates a stated fact — same session (see §6) | With the change, or direct-to-main as docs-of-record | Must not contradict CLAUDE.md/DESIGN.md |
| Commit messages / PR bodies | The public, permanent change narrative | Every commit/PR | n/a | Public — spoiler rules apply (§4) |

**What does NOT belong in each:**

- `project_state.md` is **not a spec**. Rules, schemas, and constants belong in
  DESIGN.md/CLAUDE.md; project_state.md points at them ("Full v2/v3 backlog is in
  `DESIGN.md` §6", "full details in CLAUDE.md").
- `CLAUDE.md` is **not a changelog**. It describes the current state of the code, not the
  path there. History lives in git and in degreesoffilm-failure-archaeology.
- `DESIGN.md` §6 (the "v2 / v3 parking lot (deliberately deferred)") is **the only home for
  deferred ideas** — each parked item states its gate ("v2 — stays static / no architecture
  change" vs "v3 — needs the backend / scale (the server move)"). Don't scatter TODOs
  through code or other docs.
- Skills are **not a second spec**. One home per fact; skills cite and cross-reference.

**The memory-mirror convention:** project_state.md's header notes that a condensed mirror of
the status also lives in the assistant's auto-memory. If you have such a memory surface,
update the mirror when project_state.md's status materially changes; if you don't, ignore it
— **the file in the repo is the source of truth**, the mirror is a convenience copy.

---

## 2. The session-handoff discipline

**Why:** sessions are stateless; the hook makes project_state.md the next session's opening
context. **When:** before ending ANY session that changed code, content, docs, or plans.
Commit it direct to `main` — the corpus shows a dedicated handoff commit is normal even
mid-feature: `f1119c7 Docs: session handoff — v2 in progress, reveal in open PR #18, paused`
and `f2ffe28 Update project_state: session pause — status recorded`.

**What a good update contains** — the structure of project_state.md itself (keep these
sections; rewrite their contents in place, don't append a diary):

1. **Header + `_Last updated: YYYY-MM-DD_`** with a one-line "Resume with: …" pointer.
2. **Status at a glance** — bullet per track (v1/v2/v3, content runway, tests green?).
3. **What's shipped** — grouped player-facing vs curation, each item with its commit
   hash(es) in brackets, e.g. "**Randomize** [`afec469`]", "**Auto-crop** [`7957b19`,
   `4496c81`, `388e645`]".
4. **Next steps** — numbered, ranked; step 1 is what to literally do first.
5. **Key decisions (why things are the way they are)** — decision + why + rejected
   alternative (see §5).
6. **Workflow / gotchas** — traps the next session would otherwise re-hit (e.g. "Dev cache
   gotcha", the `git checkout --` restore line for live-write tests).
7. **Run & test (quick)** — commands only, pointing at CLAUDE.md for detail.

**Copy-paste template** for the end-of-session pass (edit the existing file to match; don't
duplicate sections):

```markdown
_Last updated: YYYY-MM-DD. <one-line state>. **Resume with: <next action>.**_

## Status at a glance
- <track>: <COMPLETE / IN PROGRESS / NOT STARTED — one line each>
- **Tests:** <suites run this session> — <all green / what's red and why>

## What's shipped (this session's additions, merged into the existing list)
- **<Feature>** [`<hash>`] — <one line: what it does + where it lives>.

## Next steps (pick up here)
1. <most important next action, with the exact command if there is one>
2. <second>

## Key decisions (append any new ones)
- **<Topic>:** <what was decided>. <Why>. <Rejected alternative> was **rejected** — <reason>.

## Workflow / gotchas (append any new trap discovered this session)
- <trap + the recovery/avoidance command>
```

Then commit: `State: <what happened>; next = <next step>` (see §4) or
`Docs: session handoff — <state>`.

---

## 3. House style guide (evidenced)

Every rule below is quoted from the corpus — match it.

- **Bold the load-bearing phrase**, not whole sentences: "the answer is **depth** — how many
  rungs deep you got"; "**Pool is thin past 07-04**"; "**bone text stays fixed** for
  legibility".
- **Record the *why* next to the *what*, plus the rejected alternative.** The canonical
  example (DESIGN §5, Phase 2 de-risk): "Result: **pure popularity-sort fails** — it buried
  Heath Ledger's Joker at rung 13 … because TMDB `popularity` is a rolling/current metric,
  not fame-for-this-film. **Fix (adopted):** order cast by billing order … Evidence:
  `curation/validate_ladder.py`." Decision, mechanism, adoption, evidence pointer — all in
  one place.
- **Status vocabulary:** `*(DONE)*` on shipped parking-lot items ("**Practice / endless
  mode** — *(DONE)*…"); "**rejected**" bolded with the reason ("Popularity-sort was
  **rejected** — it buried Heath Ledger's Joker at rung 13"); "deliberately deferred" /
  "parked" for §6 items; roadmap checkboxes `- [x]` / `- [ ]`; completed-then-superseded
  gets strikethrough: "~~Not v2/v3, just undone: deploy to GitHub Pages.~~ **DONE** — live
  at …". Use these exact markers, not synonyms.
- **Dates are YYYY-MM-DD**, always: "_Last updated: 2026-07-02_", "dated
  **2026-06-28 .. 07-04**", "(from playtesting 2026-06-30)".
- **Arrows for ordered progressions:** "famous → obscure", "tight → wider → full",
  "branch → PR → rebase-merge → delete branch", "`date` → puzzle file".
- **Terse parentheticals** carry the qualifier: "(popularity only as a tiebreaker)",
  "(strictly-future)", "(no PR needed for this file)", "(key ships to client)".
- **Backtick every path, route, identifier**: `docs/cipher.js`, `?play&mode=poser`,
  `publish.next_date`.
- **The spoiler rule applies to docs too.** This repo is public; its docs are
  player-visible. **The film title of any puzzle whose date has not passed must not appear
  anywhere public** — not in docs, commit messages, PR bodies, or skills. Reference puzzles
  by number/date ("puzzle 007", "dated 2026-07-04"). Past-dated titles are fine (CLAUDE.md
  freely names puzzle 001's film). Full rule + incident history: degreesoffilm-change-control.

---

## 4. Commit & PR writing

**Commit convention: `Area: imperative summary`.** Corpus median subject length is 57 chars
(max 86); aim ≤ 70. Real examples by area:

| Area | Real examples |
|---|---|
| `Phase N:` (roadmap work) | `Phase 3: TMDB attribution footer (ship-blocker)` · `Phase 2 de-risk: validate the credit-ordering assumption` · `Phase 1: core game loop, fuzzy matcher, tests, and puzzle 001` |
| `Curation:` (private tool) | `Curation: auto-crop is now face-first (OpenCV), with edge-energy fallback` · `Curation: add a Randomize button (preview a random unused film)` · `Curation: week-ahead scheduling view (v2)` |
| `Docs:` (docs of record) | `Docs: refresh project_state + CLAUDE.md for a clean handoff (v2 complete)` · `Docs: v1 complete + deployed live to GitHub Pages` |
| `UX:` (player-facing polish) | `UX: add hover tooltip explaining the Skip -1 cost` · `UX: show current mode label above the still in-game` |
| `Polish:` (post-v1 finish) | `Polish: mobile-responsive layout` · `Polish: savage end-of-round mode roast` |
| `State:` (project_state.md updates) | `State: PR #6 merged — Poser mode on main; next = pick next v2 item` · `State: per-rung credit images built (PRs #12 & #13 open); next = merge + backfill` |

Note the `State:` idiom: **what landed; `next = <next step>`** — the subject alone tells a
reader where the project stands. Feature commits may also use the feature name as the prefix
(`Light answer obfuscation: cipher the in-JSON answers (v2)`, `Reveal mechanic: widen the
film-rung crop on wrong guesses (v2)`) — the constant is *prefix-colon-imperative-summary*,
with a `(v2)` tag for parking-lot items as they ship.

**Content commits — the spoiler-safe template:** `Add puzzle NNN (YYYY-MM-DD)` — number and
date only, **never the film title until the date passes**. The counter-example lesson: two
commits violated this — `bdca151` named puzzle 006's film in its subject, and `3d7d17e`
named puzzle 007's film before its date (both future-dated when committed; `007b3e2` then
repeated the leak in a `State:` subject — leaks propagate into handoff commits, so keep
those clean too).
History was **deliberately not rewritten** (shared main; the damage is done) — cite these as
the reason the rule exists, don't repeat them. The compliant shape exists in the corpus:
`772f4f7 Add curated puzzles 004/005 + recover the manifest`.

**PR conventions** (all 18 PRs MERGED via rebase-merge, kebab-case branches —
`reveal-mechanic`, `ux-skip-tooltip`, `credit-images-curation` — deleted after merge):

- **Title** = commit-subject style, e.g. #18 "Reveal mechanic: widen the film-rung crop on
  wrong guesses (v2)", #13 "Per-rung credit images: curation authoring".
- **Body structure** (verified from PRs #13 and #18): `## What` (the intent, one short
  paragraph, bold the feature name) → `## Changes` (bullet per file: `**\`frame.js\`** —
  what changed and why) → `## Verification` / `## Tests / verification` (what was actually
  run and observed: #18 lists a live walkthrough "Start → `004-1.jpg` (tightest); miss 1 →
  `004-2.jpg`…" plus "All suites green (6 JS + 7 Python)"). Optional `## Follow-up` for
  work the PR deliberately leaves (#13: the manual backfill pass). Bodies end with the
  "🤖 Generated with [Claude Code](https://claude.com/claude-code)" footer.
- Stacked PRs get a bold callout in What ("**Stacked on #12**…") — but prefer sequential;
  see the stacked-PR incident in degreesoffilm-failure-archaeology.

**PR vs direct-to-main routing** (one line — full rules in degreesoffilm-change-control):
player-facing `docs/` work goes branch → PR → rebase-merge (historical default — in late v2
the owner sometimes chose direct-to-main for player-facing work too; ask per change, see
degreesoffilm-change-control); curation-only and docs-of-record changes have landed direct
to `main` per the owner's per-change choice — **confirm with the owner**.

---

## 5. Decision-record template

When a decision of consequence is made (or an alternative rejected), record it in this
shape:

```markdown
- **<Decision topic>:** <what was decided, one line>.
  - **Date:** YYYY-MM-DD
  - **Why:** <the mechanism/observation that forced it>
  - **Rejected alternatives:** <alternative> — **rejected** because <reason>.
  - **Evidence:** <file / commit hash / PR # / test that proves it>
  - **Where recorded:** <project_state.md "Key decisions" + DESIGN.md §N / CLAUDE.md §…>
```

Gold-standard instance (already in the corpus, compressed to project_state.md's one-bullet
form): "**Credit ordering:** cast by TMDB **billing order** (popularity only a tiebreaker)…
Popularity-sort was **rejected** — it buried Heath Ledger's Joker at rung 13." with the full
account + evidence pointer (`curation/validate_ladder.py`) in DESIGN §5.

**Placement rule:** every significant decision lands in project_state.md "Key decisions"
(the living copy) **and**, if durable, in DESIGN.md (if it changes the spec) or CLAUDE.md
(if it changes how the code works). A concluded *investigation* — dead end, rejected fix,
dropped non-issue — additionally gets an entry appended to
degreesoffilm-failure-archaeology using that skill's entry template, so it is never
re-fought.

---

## 6. Skill-library maintenance

`.claude/skills/` is a docs surface with the same discipline as CLAUDE.md:

1. **Same-session updates.** When a code change invalidates a fact a skill states (a
   constant, path, endpoint, count, command), the session making the change updates the
   affected lines in that skill **and bumps the date in its "Provenance and maintenance"
   section** — that section is the update contract (it lists one-line re-verify commands;
   run the relevant one to confirm your fix).
2. **One home per fact.** If a fact lives in CLAUDE.md/DESIGN.md, skills cite it rather
   than fork it. Cross-reference sibling skills by exact name.
3. **Skills follow this style guide** — bolded decisions, why-next-to-what, YYYY-MM-DD,
   status vocabulary, spoiler discipline (skills are in the public repo: no future-dated
   film titles). Historical spoiler incidents are cited by hash and puzzle number, never
   by film title, until the puzzle's date has passed.
4. Commit skill updates as docs-of-record: `Docs: <what changed in which skill>`.

---

## When NOT to use this skill

- **What may land where, gates, non-negotiables, rollback** → degreesoffilm-change-control
  (this skill only covers how to *write* the commit/PR once routing is decided).
- **Publishing/editing puzzles, running the tools** → degreesoffilm-run-and-operate.
- **Recording a concluded investigation's full account** → degreesoffilm-failure-archaeology
  (it owns the entry template and the settled-battles index).
- **What tests to run / the evidence bar before you write "all green"** →
  degreesoffilm-validation-and-qa.
- **Architecture rules the docs describe** → degreesoffilm-architecture-contract.
- **Environment setup** → degreesoffilm-build-and-env.

## Reusing this pattern beyond this project

The transferable core: (1) a three-doc split — durable spec (wins conflicts) / how-the-code-
works summary / living session-handoff file — with the handoff auto-injected into every AI
session by a SessionStart hook; (2) "docs land in the same commit as the change that makes
them true"; (3) `Area: imperative summary` commits with a `State:` handoff idiom; (4)
decision records that always carry the rejected alternative + evidence pointer. Project-
specific: the exact doc names, the area prefixes, and the spoiler rule (an artifact of
publishing future-dated game content from a public repo).

## Provenance and maintenance

- **Written 2026-07-03** against HEAD `10668ca` (clean tree, 18 merged PRs, 0 open).
- Verified by: reading CLAUDE.md/DESIGN.md/project_state.md/.claude/settings.json in full;
  `git log --oneline` (67 subjects, lengths measured: median 57, max 86);
  `gh pr list --state all --limit 50`; `gh pr view 13` and `gh pr view 18` bodies.
- Re-verify (drift-prone facts):
  - Hook still injects project_state.md: `cat .claude/settings.json`
  - Commit corpus / new areas: `git log --oneline | head -30`
  - PR conventions: `gh pr list --state all --limit 10` and `gh pr view <n> --json title,body`
  - Precedence + division-of-labor wording: top of `CLAUDE.md` and `project_state.md`
  - Parking-lot status markers: `grep -n "DONE\|rejected\|deferred" DESIGN.md`
