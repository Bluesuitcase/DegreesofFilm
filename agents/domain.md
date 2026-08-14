# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the
codebase.

> **Path note for this repo:** the usual `docs/adr/` location is NOT used here, because `docs/`
> is the deployed GitHub Pages site (the game itself). ADRs live in **`adr/` at the repo root**
> instead. Never put agent/process docs under `docs/`.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root (single-context repo — no `CONTEXT-MAP.md`).
- **`adr/`** at the repo root — read ADRs that touch the area you're about to work in.
- This repo also has richer, older docs of record: `CLAUDE.md` (how the code works),
  `project_state.md` (where we are right now — read FIRST each session), `DESIGN.md`, and the
  `degreesoffilm-*` skills under `.claude/skills/`. Where `CONTEXT.md`/ADRs and those disagree,
  `project_state.md` is the freshest authority; flag the conflict rather than silently picking.

If `CONTEXT.md` or `adr/` don't exist yet, **proceed silently**. Don't flag their absence;
don't suggest creating them upfront. The `/domain-modeling` skill (reached via
`/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or
decisions actually get resolved.

## File structure

Single-context repo:

```
/
├── CONTEXT.md            ← glossary (lazily created)
├── adr/                  ← decision records (lazily created)
│   └── 0001-….md
├── agents/               ← this folder: agent-workflow config
├── docs/                 ← THE DEPLOYED GAME — never put process docs here
└── curation/             ← private content-generation tooling
```

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis,
a test name), use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary
explicitly avoids. (Until `CONTEXT.md` exists, the canonical vocabulary is CLAUDE.md's — e.g.
*degree*, *par*, *chain*, *hop*, *corpus*, *daily*, *pool*.)

If the concept you need isn't in the glossary yet, that's a signal — either you're inventing
language the project doesn't use (reconsider) or there's a real gap (note it for
`/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently
overriding:

> _Contradicts ADR-0007 (…) — but worth reopening because…_

The same applies to decisions recorded in `project_state.md` and the `degreesoffilm-*` skills
(settled battles, owner decisions): surface the conflict, cite the record, and route through
`degreesoffilm-change-control` before acting against it.
