# TMDB endpoint reference — as consumed by this repo

Companion to `../SKILL.md` §2. Everything here is either (a) read from this repo's
code (file cited), or (b) checked against the public TMDB docs at
developer.themoviedb.org on **2026-07-03** (no API key used), or (c) labeled
"as of training data". TMDB's API evolves — re-verify (b)/(c) items before relying
on them for new work.

## Client basics (`curation/tmdb.py`)

- Base: `https://api.themoviedb.org/3` (`API` constant).
- Auth: **v3 query-parameter style** — `get()` injects `api_key=<key>` into every
  request's query string. TMDB's current docs foreground a v4 bearer-token header
  instead; both work for v3 endpoints (header form: as of training data — verify).
- Key loading: `load_key()` reads `TMDB_API_KEY` from `curation/.env` (first hit
  among `curation/.env`, `./curation/.env`, `./.env`), falling back to the process
  environment. Missing/placeholder key → `SystemExit("TMDB_API_KEY not set — put
  your key in curation/.env (gitignored; do not paste it in chat).")`.
- Timeout: 20 s per request (`urllib.request.urlopen(url, timeout=20)`).
- **Never log URLs** — they carry the key. Errors report the path only:
  `RuntimeError("HTTP 401 (check your TMDB_API_KEY) on {path}")` for 401, bare
  status code otherwise. Preserve this in any new TMDB code.
- No retry, no rate-limit handling: usage is one curator clicking a local tool, a
  handful of requests per puzzle. TMDB rate limits are generous at this scale
  (as of training data — verify if usage pattern changes).

## Endpoints in use

### `GET /discover/movie` — the film pool

Callers: `curation/discover.py` (`_discover_page`, CLI), `curation/app.py`
(`api_discover`, `api_random`).

| Param as sent | Value here | Meaning |
|---|---|---|
| `sort_by` | `popularity.desc` default; the tool's sort dropdown can change it | Result ordering (TMDB default is also `popularity.desc` — verified 2026-07-03) |
| `page` | 1..3 for Discover; random 1..min(total_pages,500) for Randomize | 20 results/page |
| `include_adult` | `"false"` | Excludes adult titles (TMDB default false — verified 2026-07-03) |
| `vote_count.gte` | 800 | Pool floor: "is it known" |
| `vote_average.gte` | 6.5 | Pool floor: "is it good" |

Fields consumed from `results[]`: `id`, `title`, `release_date`, `vote_count`,
`vote_average`, `popularity`, `backdrop_path`; plus top-level `total_pages`.
**Paging is hard-capped at 500 pages** — `api_random` clamps
(`min(probe.get("total_pages", 1) or 1, 500)`, `curation/app.py`); the cap is also
TMDB-documented (as of training data). Note `.gte` filters are *server-side*, but
`discover.py`'s pure `candidates()` re-checks the floor locally so the logic
unit-tests offline and survives odd API responses.

### `GET /search/movie` — free-text title search

Callers: `curation/tmdb.py` `search_movie` (CLIs; takes `query`, optional `year`,
`include_adult="false"`, returns first result), `curation/app.py` `api_search`
(returns up to `count=18` results; each hit flagged `used` + `puzzle` id via the
ledger so the UI routes already-made films to the edit flow).

### `GET /movie/{id}?append_to_response=credits` — film + credits in one call

Caller: `curation/tmdb.py` `movie_with_credits`. `append_to_response` is TMDB's
mechanism for bundling sub-resources into one response (here the `/movie/{id}/credits`
payload appears under a `credits` key) — one request instead of two.

Movie fields consumed: `title`, `original_title` (seeded as an alternate answer if
it differs — `build_rungs.film_rung`), `release_date`, `poster_path`, `popularity`.

`credits.cast[]` fields:

| Field | Used for |
|---|---|
| `order` | **Billing order** — the cast sort key (0 = lead). Missing → treated as 9999 (`build_rungs.order_cast`) |
| `popularity` | Tiebreaker only (descending); also sorts decoy pools |
| `name` | The rung's answer; person matching in `credits_images._find_person` |
| `character` | The prompt ("Who played X?") and the caption ("Name as Character") |
| `id` | De-dup key |
| `profile_path` | The headshot (see image URLs below) |

`credits.crew[]` fields: `job` (exact-string matched: `Director`, `Director of
Photography`, `Original Music Composer`, `Editor`, `Production Design` —
`build_rungs.ROLES`), plus `name`/`id`/`popularity`/`profile_path` as above.
People with other `job` strings are invisible to the ladder. Multiple people with
the same job (e.g. co-editors) all become answers on one rung
(`build_rungs._people_for_job`, billing-stable order).

### `GET /movie/{id}/images` — crop-source stills

Caller: `curation/app.py` `_film_stills`. Takes `backdrops[].file_path` for the
first **12** backdrops, appends the movie's `poster_path` if present. Backdrops
are wide (~16:9) frames/promo shots; the poster is the vertical one-sheet, offered
last. TMDB also returns `posters[]` and `logos[]` arrays here — unused. Note: no
`include_image_language` filter is sent, so TMDB's default language filtering
applies (as of training data — verify if stills come back sparse).

### `GET /movie/{id}/recommendations` → `GET /movie/{id}/similar` — decoy sources

Caller: `curation/decoys.py` `_source_films`. Recommendations first (TMDB's
curated "if you liked X" list, generally better neighbours), `similar` (metadata
matching: genres/keywords — as of training data) only if recommendations don't
fill `source_limit=8`. Both page-1 only. Films need `vote_count >= 400`; results
are popularity-sorted so decoy pools lead with recognizable names. Each neighbour
then gets a `movie_with_credits` call: top `cast_per_film=5` billed cast feed the
Cast pool; crew feed per-role pools by the same exact `job` strings. Anyone
actually credited in *this* film is excluded (a decoy must never be accidentally
correct).

## Image URLs

Composition: `base + size + file_path` → this repo always builds
`https://image.tmdb.org/t/p/original` + `file_path` (`IMG_BASE` in
`curation/credits_images.py`, `curation/app.py`). Verified against
developer.themoviedb.org/docs/image-basics 2026-07-03: valid sizes (e.g. `w500`,
`original`) and canonical base URL come from the `/configuration` endpoint; the
documented example is `https://image.tmdb.org/t/p/w500/1E5baAaEse26fej7uHcjOgEE2t2.jpg`.
This repo skips `/configuration` and hardcodes `original` because every image is
downloaded once at curation time, then locally cropped/resized (tiers to width
1000, JPEG q85) — the player never loads from TMDB directly.

Security note: `curation/app.py` `_download_rgb` refuses non-TMDB URLs
(HTTP 400 `"image must be a TMDB image URL"`) so the local tool can't be used as a
generic image proxy.

## What this repo deliberately does NOT use

No TV endpoints, no `/person/{id}` detail calls (headshots come from
`profile_path` already present in credits), no `/movie/{id}/alternative_titles`
(only `original_title` seeds alternates — additional forms are typed by the
curator), no sessions/accounts/v4 lists, no `/configuration`, no webhooks. If you
add an endpoint: call it only from `curation/` (never `docs/`), route it through
`tmdb.get()` to inherit key hygiene, and keep any filtering logic in a pure,
offline-testable function per the existing pattern.
