---
name: degreesoffilm-worker-ops
description: >
  Operate the LIVE /match Cloudflare Worker for Degrees of Film — deploy/redeploy,
  KV answer sync after publishes, auth via the scoped token in curation/.env,
  verification probes, reading usage metrics as the project's only (privacy-preserving)
  demand signal, rate-limit facts, rollback, and the §6 step 5 cutover runbook (stop
  embedding answers in new puzzles — earliest ~2026-07-25). Load when: deploying or
  redeploying the Worker; a publish batch needs its answers pushed to KV; "wrangler"
  anything; the live site's server matching seems broken or slow; someone asks "how many
  players do we have"; executing or rolling back §6 step 5; or rotating/replacing the
  Cloudflare token. NOT for building new server features (degreesoffilm-server-move-campaign)
  or static-site/curation ops (degreesoffilm-run-and-operate).
---

# Degrees of Film — /match Worker operations

The Worker went LIVE 2026-07-11: deployed, GATE 1 passed, and the client default is ON
(`MATCH_API` in `docs/app.js` = the Worker origin). This skill is the day-2 runbook.
Facts verified live 2026-07-11.

## 1. The standing facts

| Fact | Value (2026-07-11) |
|---|---|
| Worker | `dof-match`, `https://dof-match.bluesuitcase.workers.dev` |
| Code | `server/worker.js` — imports `docs/match.js` UNCHANGED (parity by reuse) |
| KV namespace | `ANSWERS`, id `c6672c863072425f9b94d6b0501e2b03` (in `server/wrangler.toml`) |
| KV contents | `answers:<puzzleId>` → `{"rungs":[{"answers":[...]},...]}` PLAINTEXT |
| Auth | `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` in gitignored `curation/.env` — scoped token (Workers Scripts Edit + Workers KV Storage Edit + reads). NO interactive `wrangler login` needed; export both as env vars before any wrangler command |
| CORS | pinned to `https://bluesuitcase.github.io` (worker.js `ALLOWED_ORIGIN`) |
| Rate limit | 60 req/min/IP (`wrangler.toml` unsafe binding; CONFIRMED working on the free plan — a 429 was observed under load) |
| Answers cache | 5-min per-isolate TTL in worker.js — an edited puzzle's answers can be stale server-side up to 5 min after a KV update |
| Client fallback | 2 s timeout → local matching on ANY failure; `?servermatch=0` forces local |
| Cost | $0 — free tier (100k req/day; legit game ≈ 36 calls) |
| GATE 1 evidence | contract 9/9, parity 25/25 vs match.cases.js, warm p50=34ms/p95=41ms/max=88ms, fallback drill 55ms |

## 2. Routine ops

**Every command starts the same way** (PowerShell shown; adapt for bash):
```powershell
$envFile = 'curation/.env'
$env:CLOUDFLARE_API_TOKEN  = ((Select-String $envFile -Pattern '^CLOUDFLARE_API_TOKEN=').Line.Split('=',2)[1]).Trim()
$env:CLOUDFLARE_ACCOUNT_ID = ((Select-String $envFile -Pattern '^CLOUDFLARE_ACCOUNT_ID=').Line.Split('=',2)[1]).Trim()
cd server
```

**THE TRAP (cost us a silent no-op on day 1): wrangler 4 defaults every `kv` command to a
LOCAL simulator.** Always pass `--remote`. `server/.wrangler/` is that simulator's litter
(gitignored). A bulk put that prints `Resource location: local` did nothing real.

- **Push answers after a publish batch** (the publish sink keeps gitignored
  `server/answers-bulk.json` current):
  `npx wrangler kv bulk put answers-bulk.json --namespace-id <id> --remote`
- **Rebuild the artifact from scratch** (cutover/rollback/drift):
  `python curation/backfill_answers.py` then the bulk put above.
- **List what KV actually holds:**
  `npx wrangler kv key list --namespace-id <id> --remote`
- **Redeploy after editing worker.js/wrangler.toml:** `npx wrangler deploy` (from `server/`).
  Run `node worker.test.js` FIRST (in-process suite incl. full matcher parity).
- **Verify the live endpoint** (safe, no auth needed):
  ```
  curl -s -X POST https://dof-match.bluesuitcase.workers.dev/match \
    -H "Content-Type: application/json" \
    -d '{"puzzleId":1,"rungIndex":0,"guess":"zzz"}'        # expect {"correct":false}
  ```
  A wrong guess must be EXACTLY `{"correct":false}` — anything more is an answer leak.

## 3. Metrics = the project's only demand signal (privacy-preserving)

The project deliberately ships **no client analytics**. But with server matching ON, the
Worker's request volume ≈ engaged cinephile/buff players (≈36 requests per completed game,
plus partial games). The Cloudflare dashboard (Workers & Pages → dof-match → Metrics) shows
requests/day for free — **check it before any Phase 2/3 (accounts/leaderboard) scope
discussion**; GATE 0 parked those phases explicitly for lack of demand evidence, and this
is now the evidence source. Divide daily requests by ~36 for a rough player count. Caveats:
poser players don't call /match; local-fallback activations don't either; bots inflate it.

## 4. §6 step 5 — the final cutover (stop embedding answers in NEW puzzles)

**Gates (ALL required, campaign §6):** flag-ON stable **≥14 days** (from 2026-07-11 →
earliest **~2026-07-25**) with zero known fallback incidents; **owner sign-off** recorded in
project_state.md; a **rehearsed rollback** (below) on a future-dated puzzle first.

Execution sketch (route through degreesoffilm-change-control; player-facing):
1. `curation/publish.py` gains an answers-omitting mode for NEW puzzles (past puzzles keep
   theirs forever — R5). The client already handles answer-less rungs? VERIFY first: the
   local fallback needs answers; an answers-absent puzzle makes the server REQUIRED for
   that day (the one place R1 softens — why this step is last and gated).
2. Rehearse rollback on a future-dated puzzle: re-enable embedding, re-publish it
   (backfill path), confirm local matching works again.
3. Ship, then watch the Worker error rate + fallback behavior for the first live day.

## 5. Failure triage

| Symptom | Likely cause | Fix |
|---|---|---|
| Live guesses all take ~2 s then work | Worker down/unreachable → every guess rides the timeout into fallback | `curl` probe (§2); redeploy; if persistent, flip `MATCH_API=''` (one-line PR) — play is never blocked either way |
| New puzzle's guesses fall back locally | Its `answers:<id>` never pushed to KV (or pushed without `--remote`) | §2 bulk put with `--remote`; verify with `key list --remote` |
| Edited puzzle matches stale answers server-side | 5-min isolate cache (worker.js) | wait ≤5 min, or `wrangler deploy` to cycle isolates |
| 429s during testing | The 60/min/IP limit working as designed | pace probes ≥1.1 s apart |
| `wrangler whoami` says not authenticated | env vars not exported in THIS shell | §2 preamble; the token itself lives in curation/.env |
| Token compromised/lost | — | dash.cloudflare.com → My Profile → API Tokens: revoke, re-create (Workers Scripts Edit + Workers KV Storage Edit + reads), update curation/.env |

## When NOT to use this skill

- Designing/building new server phases (accounts, leaderboard, transcripts) →
  **degreesoffilm-server-move-campaign** (owns gates + fenced wrong paths).
- Publishing puzzles / static-site ops → **degreesoffilm-run-and-operate** (its step 14 is
  the KV-sync hook that points here).
- Matching semantics / why a guess matched → **degreesoffilm-domain-reference**.
- Landing rules for any change here → **degreesoffilm-change-control**.

## Provenance and maintenance

- Written 2026-07-11, the day the Worker went live; every § 1 fact observed that day
  (deploy logs, GATE 1 runs, the 429, the `--remote` trap, live curl probes).
- Re-verify quickly: the § 2 curl probe; `npx wrangler kv key list ... --remote | measure`
  (count should equal published puzzles); `grep -n "MATCH_API = " docs/app.js`.
- Update this file in the same session as: any wrangler.toml change, a token rotation,
  executing §6 step 5, or a rate-limit/plan change.
