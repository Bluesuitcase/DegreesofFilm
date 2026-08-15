# Degrees of Film — brand & design brief

> Self-contained brief for designers and design tools. Everything needed to create
> logos, marks, social cards, and promotional art for this game is in this file.
> Written 2026-08-15, alongside the "Matinee" visual redesign.

## What the game is

**Degrees of Film** is a free daily browser puzzle about how films connect. Each day you
get **two films** — say *The Prestige* → *The Purge: Anarchy* — and you chain from one to
the other through the people who made them: name someone credited on the first film, then
another film that person worked on, and keep hopping until you name someone who also worked
on the target. Each person you route through is one **degree**.

Scoring is **golf**: *par* is the shortest chain that exists, and your brag is your degrees
against par — Birdie, Par, Bogey. Three wrong links on one step ends the run. When the run
ends, the game reveals a shortest route, your own chain stays on screen for comparison, and
you get a spoiler-free share string built for group chats:

```
Degrees of Film #12 — 3° (par 2, +1)
The Prestige (2006) → The Purge: Anarchy (2014)
🔗🟥🔗🔗 · obscurity 36 · streak 4
https://bluesuitcase.github.io/DegreesofFilm/
```

One puzzle a day. No accounts, no ads, no images, no app — a ~200 KB static website that
loads instantly and keeps your streak on your device.

## Purpose and positioning

- **The daily-ritual game for film lovers.** Same cultural slot as Wordle or NYT
  Connections — a two-minute morning habit you share with a group chat — but the subject
  is the connective tissue of cinema: who worked with whom.
- **Heritage:** the "six degrees of separation" tradition (Six Degrees of Kevin Bacon, the
  Oracle of Bacon), rebuilt as a daily puzzle with golf scoring and a share loop.
- **The social loop is accountless.** Scores travel as text into group chats; the share
  string's first line is machine-parseable so communities can run leagues with bots. No
  logins, no leaderboards — your rivals are your friends.
- **Tone of competition:** golf, not esports. Par is a handshake, not a gate. Beating par
  is possible and delightful; a loss still pays off (the game shows you the route you
  were hunting).

## Brand personality

- **Warm, literate, cinephile-but-welcoming.** The voice of a friend who runs a repertory
  cinema — knows everything, gatekeeps nothing.
- **Matinee, not midnight.** Since the 2026-08 redesign the game is deliberately
  **light-mode-first**: warm cream paper, espresso ink, marquee gold. Cozy afternoon
  cinema lobby, not a darkened theater. (The owner's explicit stance: "I don't do dark
  mode." Inviting > moody.)
- **Golf-clubhouse patience.** Verdict names come from golf (Albatross, Eagle, Birdie,
  Par, Bogey). A daily may carry a one-sentence **curator's note** — a human voice on the
  end card, texture rather than trivia.
- **Playful, never snarky.** Errors don't punish spelling; feedback explains *why* a hop
  failed. The design never makes the player feel dumb.

## Visual identity — the "Matinee" theme

The entire UI derives from nine CSS variables. Hex values are canonical:

| Role | Var | Hex | Use |
|---|---|---|---|
| Paper (page ground) | `--paper` | `#f5efe3` | Warm cream — the whole page |
| Card (panels) | `--card` | `#fcf8ef` | Inputs, pills, tiles — slightly lighter than paper |
| Ink (text) | `--ink` | `#2e2620` | Espresso — all primary text |
| Muted | `--muted` | `#7a6f60` | Secondary text, labels |
| Amber (fills) | `--amber` | `#e09b28` | Marquee gold — buttons, tiles, tooltip, confetti |
| Deep gold (text accent) | `--amber-deep` | `#96660a` | Accent text, big numerals, hovers |
| On-accent | `--on-accent` | `#241a06` | Text sitting on amber fills |
| Signal red | `--red` | `#b5462e` | Burned attempts, losses — terracotta, not alarm-red |
| Line | `--line` | `#ddd2bc` | Borders, dividers — soft parchment |

**Why these choices** (the psychology the redesign was built on):

- Warm off-white cuts glare and eye strain versus pure white while keeping text contrast —
  the "book paper" effect. The game should feel like settling in, not squinting.
- Warm hues (cream, gold) read as inviting and approachable — the comfort that makes a
  daily habit stick.
- Gold is the cinema thread: marquee bulbs, ticket foil, award statues — without using any
  actual film imagery.
- Accent discipline: vivid gold for *fills* (with dark text on top), deep gold for
  *text* — every text/background pair clears WCAG AA contrast on cream.

## Typography

- **System sans stack** (`-apple-system, "Segoe UI", Helvetica…`) — fast, neutral,
  invisible. The brand lives in *treatment*, not typeface:
  - The wordmark is set **UPPERCASE, letterspaced** (`letter-spacing: .28em`), small and
    quiet: `D E G R E E S   O F   F I L M`.
  - Section eyebrows are uppercase, letterspaced, deep gold.
  - Numerals are **tabular** everywhere; the end-card degree count is a huge (84px)
    deep-gold numeral with the degree symbol: **2°**.
- **Monospace** for the share string block (it's presented as copyable text).

## Marks, motifs, iconography

- **The chain** is the core motif: film → person → film as linked pills. The current
  favicon is original art: two **gold open chain links** joined by a solid **ink
  connector bar**, on a rounded cream square. Rounded-rectangle "pills" are the game's
  signature shape (border-radius 999 pills in the UI).
- **The degree symbol (°)** is the scoring mark — "3°" is how a score is written. A logo
  may lean on it.
- **Glyph vocabulary** (used in shares, may inspire art): 🔗 a completed degree ·
  🟥 a burned attempt · ↩ backing up · 💔 a broken chain (loss).
- **Golf iconography** is fair game in moderation (par, scorecards) — the completion
  calendar already uses gold/silver day tiles.

## What a logo needs to do

- Work at **favicon size** (16px) and as a standalone app-icon-style mark.
- Sit on **cream** (`#f5efe3`) primarily; a variant that sits on **ink** (`#2e2620`) is
  needed for the dark social card (og.png is currently a dark design — acceptable
  contrast against the light site, may be redesigned to match).
- Use the palette above — ideally gold + ink on paper, terracotta as a rare accent.
- **SVG-first, tiny.** The whole site is ~200 KB; assets must stay featherweight.
- Feel: **warm matinee cinema + linked chain + a wink of golf.** Not: neon, noir,
  cyberpunk, streaming-service gradients.

## Hard constraints (non-negotiable)

1. **No film imagery, ever.** No stills, posters, headshots, or recognizable likenesses —
   the game ships zero images by design, and TMDB imagery must never appear in any brand
   asset. All art must be original.
2. **No real film or person references in art.** A logo or promo card must never name or
   depict an actual film/actor (spoiler discipline: future puzzles are film pairs, and
   endpoint pairs are public but chains are not — art stays generic).
3. **Clichés to avoid:** film reels, clapperboards, popcorn — the ecosystem default.
   The chain/degrees idea is the distinctive asset; lean on it.
4. **TMDB attribution** lives in the site footer (data source credit). Brand assets don't
   need it, but nothing may imply TMDB endorsement.
5. **The share string's first line is a frozen grammar** — if art incorporates a sample
   share, copy the format exactly as shown above.

## Current assets (adopted 2026-08-15 from the "Movie Trivia Game Graphics" design project)

The logo concept is **"chain into degree"**: an open gold chain link, an ink connector bar
climbing at 30°, resolving into a gold degree ring. Play, connection, and score in one mark.

- `docs/favicon.svg` — the mark on a rounded card tile (browser tab).
- `docs/logo-mark.svg` — the bare mark (masthead, next to the wordmark).
- `docs/logo-lockup.svg` — mark over the letterspaced wordmark (external/promo use).
- `docs/og.png` — 1200×630 social card, cream ground, mark + tagline
  ("Two films. Chain them. Beat par.") + a Film → ? → ? → Film pill chain.
- `docs/badges/badge-{albatross,eagle,birdie,par,bogey,double-bogey,broken-chain}.svg` —
  rank-tiered ticket-stub verdict badges for the end card: gold fills under par, quiet
  card stubs at/over par, terracotta for a lost chain. Notches assume the cream ground.
- `docs/confetti.svg` — chain-and-ring confetti scatter, shown on under-par end cards.
- `docs/invite.gif` — 68 KB animated invite card (chain assembles → final link pops →
  confetti; 1000×525, ~4 s loop). Attached by the in-game "Share this game" button via
  the Web Share API where the platform allows files.
- Live site: https://bluesuitcase.github.io/DegreesofFilm/
