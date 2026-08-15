---
name: degreesoffilm-docs-and-writing
description: >
  The docs of record for Degrees of Film, the update discipline, and the house writing style.
  Load at the END of every work session (updating project_state.md is mandatory before
  stopping); after shipping ANYTHING (which docs must the same change make true?); when
  writing a commit message or PR title/body (the "Area: imperative summary" convention + the
  spoiler rule — never name a future daily's chain); when unsure which doc owns a fact
  (CLAUDE.md vs project_state.md vs the historical DESIGN.md vs agents/*.md); when recording
  a decision or a rejected alternative; and when a code change invalidates something a skill
  under .claude/skills/ says (same-session update rule). Contains copy-paste templates for
  the session handoff, decision records, and commits/PRs. NOT for what may land where or
  rollback (degreesoffilm-change-control) or the full account of a concluded investigation
  (degreesoffilm-failure-archaeology).
---

# Degrees of Film — Docs of Record & House Writing Style

How this project stays maintainable by strangers: every session leaves the written record
right. **The one habit that matters:** AI sessions are stateless; a SessionStart hook in
`.claude/settings.json` injects `project_state.md` into **every** new session's context
(verified 2026-08-14: the hook runs `node -e "...readFileSync('project_state.md'...)"`).
Whatever you write there is literally what the next session knows.

---

## 1. Docs-of-record map

| Document | Role | Precedence |
|---|---|---|
| `CLAUDE.md` | **How the code works** (durable): architecture, ruleset, share grammar, content ops. Updated with the change that makes it true. | Current source of truth, with project_state.md. Wins over DESIGN.md and skills. |
| `project_state.md` | **Running handoff** (living) — "where we are right now", read FIRST each session. | Freshest authority on status; snapshot only — durable facts must also land in CLAUDE.md. Lands direct to `main`. |
| `DESIGN.md` | **HISTORICAL.** The retired dig's spec, with a superseding banner at its top: "This document describes a game that no longer exists" … "Current sources of truth: CLAUDE.md … and project_state.md". Kept for reasoning that carried over (pool floor §1, three-zone architecture §2, matcher fairness §3, the parking lot §6 that produced the current game). | **Never wins a conflict.** Closed to new material — don't update it, cite it. |
| `agents/issue-tracker.md` | Issue conventions: GitHub Issues via `gh`, auth per-command with `GH_TOKEN` from the cached git credential. | New 2026-08-14. |
| `agents/domain.md` | Domain-doc conventions: `CONTEXT.md` at the repo root + ADRs in `adr/` — **both created lazily; neither exists yet**, so CLAUDE.md + project_state.md carry vocabulary and decisions. Never under `docs/` (that's the deployed site). | New 2026-08-14. |
| `.claude/skills/*/SKILL.md` | Maintained operational docs (this library). | Must not contradict CLAUDE.md/project_state.md (see §6). |
| Commit messages / PR bodies | The public, permanent change narrative. | Public — spoiler rule applies (§4). |

**What does NOT belong in each:**

- `project_state.md` is **not a spec** — rules and constants live in CLAUDE.md;
  project_state.md points at them.
- `CLAUDE.md` is **not a changelog** — it describes current state; history lives in git and
  in project_state.md's dated records ("history, not instructions").
- `DESIGN.md` takes **no new content**. Deferred ideas now go to project_state.md's
  "Open items" list or GitHub Issues, not a parking lot.
- Skills are **not a second spec** — one home per fact; skills cite and cross-reference.

**Memory-mirror convention:** a condensed status mirror lives in the assistant's auto-memory.
Update it when project_state.md's status materially changes; **the repo file is the source of
truth**, the mirror a convenience copy.

---

## 2. The session-handoff discipline

**When:** before ending ANY session that changed code, content, docs, or plans. Commit direct
to `main` (or on the working branch if mid-PR). Real handoff subjects:
`Docs: session-end sweep — post-launch start-here + ordered open items` ·
`Docs: session-end handoff — rebuild committed, playtest is the open gate`.

**project_state.md's current shape** (keep it; rewrite in place, don't append a diary):

1. **Header + `_Last updated: YYYY-MM-DD, <session label>_`.**
2. **"▶ Start here next session"** — numbered; item 1 is the literal first action.
3. **"⏭ Open items (in order)"** — the canonical to-do. Completed items get struck through
   in place: `~~Restock by ~2026-09-06~~ **DONE 2026-08-14 (see the refresh record below)**`.
4. **Dated records, reverse-chronological** — one per significant session/event
   (`## 🔄 CORPUS REFRESHED + RESTOCKED — 2026-08-14…`), each self-contained: what happened,
   evidence (suites, browser checks), commit hashes in backticks. These are history — new
   sessions add a record on top rather than editing old ones (except strikethroughs).
5. Deeper down: **"Key decisions (why things are the way they are)"** and
   **"Workflow / gotchas"** — append new decisions (§5) and newly discovered traps.

**End-of-session pass:** rewrite Start-here + Open items to be true; add this session's
dated record; append any new decision/gotcha; then commit
`Docs: <what happened> — <state / next step>`.

---

## 3. House style guide (evidenced)

Every rule below is quoted from the current corpus — match it.

- **Bold the load-bearing phrase**, not whole sentences: "**Ship the whole graph once, not a
  puzzle at a time.**" · "**Suggestions are global, validation is contextual.**" ·
  "**Work happens on `main` now**".
- **Record the *why* next to the *what*, plus the rejected alternative.** Canonical current
  examples (project_state.md "Key decisions" / CLAUDE.md): "**Unrecognized input doesn't burn
  an attempt** … punishing them makes the game feel like a spelling test" · "An earlier
  prototype shipped a per-challenge subgraph and drew autocomplete from it, which handed the
  player the answer."
- **Status vocabulary:** strikethrough + `**DONE YYYY-MM-DD**` for completed open items;
  "**rejected**" bolded with the reason; "parked" / "gated on <evidence>" for deferred work
  ("gated on measured DNF rates + owner sign-off"); HISTORICAL / SUPERSEDED banners at the
  top of retired docs. Use these exact markers, not synonyms.
- **Dates are YYYY-MM-DD**, always.
- **Arrows for ordered progressions:** "`harvest.py` → `graph_build.py` →
  `challenge_gen.py`", "exact → typo → last-word".
- **Terse parentheticals** carry the qualifier: "(no PR needed for this file)",
  "(recoverable from git history)", "(owner, 2026-08-11)".
- **Backtick every path, route, identifier**: `docs/chain.js`, `?id=N`, `par_for_date`.
- **The spoiler rule applies to docs too** — see §4; it binds skills, issues, and
  project_state.md as much as commits.

---

## 4. Commit & PR writing

**Commit convention: `Area: imperative summary`** (aim ≤ 70 chars; an em-dash subtitle for
detail is the house idiom). Real post-rebuild examples:

| Area | Real examples |
|---|---|
| `Game:` (player-facing) | `Game: rebuild the site around degrees-of-separation, retire the dig` · `Game: Wave 3 — completion calendar, handicap, backup codes, curator's note` |
| `Curation:` (private tool) | `Curation: weekly difficulty arc — par 2 early week to par 4 Saturdays` |
| `Content:` (corpus + dailies) | `Content: corpus refresh + restock 30 dailies (runway through 2026-10-13)` |
| `Docs:` (docs of record, incl. handoffs and skills) | `Docs: record the launch — PR #29 merged, Comeback Loop live` · `Docs: agent-skills setup — GitHub issue tracker + domain-doc conventions` |

Older areas (`UX:`, `Polish:`, `Phase N:`, `v2:`, `State:`) are dig-era history — read
`git log --oneline` for the live corpus rather than trusting any list here. Coin a new area
only when none fits.

**The spoiler rule (recast 2026-08-14 — owner text in CLAUDE.md "Spoiler discipline" /
"Curator's notes"):** this repo is public, so commits, PR bodies, issues, docs, and skills
must **never name a future daily's chain** — no connector person or film on any geodesic.
The **endpoint pair is fine**: pairs ship publicly in `challenges.json` before their date
("the pair is the prompt, not the answer"). Solutions live only in the gitignored
`curation/challenge_solutions.json`. Curator's notes have their own hard version of this
rule, machine-enforced by `challenge_gen.py --check`.

**PR conventions** (all PRs MERGED via rebase-merge; branches now `claude/...`-prefixed and
pruned after merge):

- **Title** = the squash-subject, commit-style: #30 "Content: corpus refresh + restock 30
  dailies (runway through 2026-10-13)"; #29 "Rebuild the site around degrees-of-separation,
  retire the dig".
- **Body** (verified from #30): `## What` — intent + bulleted changes, bold the feature →
  `## Evidence` (older PRs: `## Changes` / `## Verification`) — what was actually run and
  observed ("9 suites (6 JS + 3 Python) all green … Browser-verified on :8010"), plus a
  spoiler attestation when content shipped ("nothing here names a future chain"). Footer:
  "🤖 Generated with [Claude Code](https://claude.com/claude-code)".
- **PR-vs-direct routing** is degreesoffilm-change-control's call, not this skill's.

---

## 5. Decision-record template

When a decision of consequence is made (or an alternative rejected), record it in this shape:

```markdown
- **<Decision topic>:** <what was decided, one line>. (<who>, YYYY-MM-DD)
  - **Why:** <the mechanism/observation that forced it>
  - **Rejected alternatives:** <alternative> — **rejected** because <reason>.
  - **Evidence:** <file / commit hash / PR # / test that proves it>
```

Gold-standard instance already in project_state.md "Key decisions": "**The surname rule is
asymmetric on purpose.** In context … 'Bardem' is unambiguous and accepted; globally (9,679
names) a bare surname is accepted **only if exactly one person in the pool has it**, or
'smith' would silently resolve to whichever Smith ranks highest."

**Placement:** every significant decision lands in project_state.md "Key decisions" (the
living copy) **and**, if it changes how the code works, in CLAUDE.md. Once `adr/` exists
(created lazily per `agents/domain.md`), durable decisions graduate to ADRs there. A
concluded *investigation* — dead end, rejected fix — additionally gets an entry in
degreesoffilm-failure-archaeology, so it is never re-fought.

---

## 6. Skill-library maintenance

`.claude/skills/` is a docs surface with the same discipline as CLAUDE.md:

1. **Same-session updates.** When a code change invalidates a fact a skill states (a
   constant, path, count, command), the session making the change updates that skill **and
   bumps its "Provenance and maintenance" date** — that section lists one-line re-verify
   commands; run the relevant one to confirm the fix.
2. **One home per fact.** If a fact lives in CLAUDE.md/project_state.md, skills cite it
   rather than fork it. Prefer deleting a cached fact over refreshing it.
3. **Skills follow this style guide** — including the spoiler rule (§4): skills are public.
4. Commit skill updates as `Docs: <what changed in which skill>`.
5. **Post-rebuild migration:** the seven skills that described deleted dig tooling were
   removed 2026-08-11; the survivors are being re-verified 2026-08-14. Cross-reference only
   skills that exist in `.claude/skills/` right now.

---

## When NOT to use this skill

- **What may land where, gates, non-negotiables, rollback** → degreesoffilm-change-control
  (this skill only covers how to *write* the commit/PR once routing is decided).
- **Recording a concluded investigation's full account** → degreesoffilm-failure-archaeology.
- **What tests to run / the evidence bar before writing "all green"** →
  degreesoffilm-validation-and-qa.
- **Architecture rules the docs describe** → degreesoffilm-architecture-contract.
- **Term definitions / domain theory** → degreesoffilm-domain-reference.
- **Public claims, attribution, announcement copy** → degreesoffilm-external-positioning.

## Provenance and maintenance

- **Re-verified 2026-08-14** after the degrees-of-separation rebuild (HEAD `71454d3`),
  by reading CLAUDE.md, project_state.md, DESIGN.md's banner, `.claude/settings.json`,
  `agents/issue-tracker.md`, `agents/domain.md`; `git log --oneline`;
  `gh pr list --state all` + `gh pr view 30 --json body`. Originally written 2026-07-03.
- Re-verify (drift-prone facts):
  - Hook still injects project_state.md: `cat .claude/settings.json`
  - Commit corpus / new areas: `git log --oneline | head -30`
  - PR conventions: `gh pr view <n> --json title,body` (GH_TOKEN per `agents/issue-tracker.md`)
  - Doc precedence + spoiler wording: top of `CLAUDE.md`, `project_state.md`, `DESIGN.md`
  - `CONTEXT.md` / `adr/` still lazy (update §1 and §5 when they first exist): `ls adr CONTEXT.md`
