# TMDB endpoint reference — as consumed by this repo

Companion to `../SKILL.md` §2, re-verified against the code on **2026-08-14**
(after the degrees rebuild). Everything here is either (a) read from this repo's
code (file cited), or (b) checked against the public TMDB docs at
developer.themoviedb.org on **2026-07-03** (no API key used), or (c) labeled
"as of training data". TMDB's API evolves — re-verify (b)/(c) items before
relying on them for new work.

Since the rebuild the whole TMDB surface is `curation/tmdb.py` (the client) +
`curation/harvest.py` (the only caller). **No images, no decoys, no search UI,
no recommendations** — those endpoints left with the retired dig game.

## Client basics (`curation/tmdb.py` — stdlib only)

- Base: `https://api.themoviedb.org/3` (`API` constant).
- Auth: **v3 query-parameter style** — `get()` injects `api_key=<key>` into
  every request. TMDB's current docs foreground a v4 bearer-token header; both
  work for v3 endpoints (header form: as of training data — verify).
- Key loading: `load_key()` reads `TMDB_API_KEY` from the first of
  `curation/.env`, `./curation/.env`, `./.env`, falling back to the process
  environment. Missing/placeholder key → `SystemExit("TMDB_API_KEY not set —
  put your key in curation/.env (gitignored; do not paste it in chat).")`.
- Timeout: 20 s per request (`urllib.request.urlopen(url, timeout=20)`).
- **Never log URLs** — they carry the key. Errors report the path only:
  `RuntimeError("HTTP 401 (check your TMDB_API_KEY) on {path}")` for 401, bare
  status code otherwise. Preserve this in any new TMDB code.
- No retry, no rate-limit handling: usage is one curator running a refresh; the
  append-only caches mean a refresh months later costs a few hundred calls.
- `search_movie()` and `movie_with_credits()` are defined here but currently
  have **no callers** — `harvest.py` calls `tmdb.get()` directly.

## Endpoints in use (both called only by `curation/harvest.py`)

### `GET /discover/movie` — the pool sweep

Callers: `harvest.refresh_films` (and the pure-order helper `pool_film_ids`).

| Param as sent | Value | Meaning |
|---|---|---|
| `sort_by` | `popularity.desc` | The sweep order **is** the corpus's film rank — `graph_build.py` preserves it, and the client's "first hit wins" resolution and autocomplete depend on it |
| `include_adult` | `"false"` | Excludes adult titles |
| `vote_count.gte` | 500 (`POOL_MIN_VOTES`) | Pool floor: "is it known" |
| `vote_average.gte` | 6.0 (`POOL_MIN_AVG`) | Pool floor: "is it good" |
| `page` | 1..min(total_pages, 500) | 20 results/page; `MAX_PAGES = 500` matches TMDB's hard paging cap (as of training data) |

Fields consumed from `results[]`: `id`, `title`, `release_date` (year only);
plus top-level `total_pages`. Written to append-only `films_cache.jsonl` as
`{id, title, year}` — `backdrop_path` and every other image field are ignored.

### `GET /movie/{id}?append_to_response=credits` — key credits

Caller: `harvest.refresh_credits`, once per film not already in
`people_harvest_cache.jsonl`. `append_to_response` is TMDB's mechanism for
bundling the `/movie/{id}/credits` payload into the same response under a
`credits` key — one request instead of two.

Fields consumed (`harvest.extract_people`, pure):

| Field | Used for |
|---|---|
| `credits.cast[:12]` (`CAST_TOP`) | The film's key cast. The slice trusts TMDB's array order = **billing order** (lead first); position 13+ never enters the corpus |
| `credits.crew[]` where `job` ∈ `Director`, `Director of Photography`, `Original Music Composer`, `Editor`, `Production Design` (`CREW_JOBS`, exact strings) | The film's key crew; any other `job` spelling is invisible |
| `id`, `name` | The person's identity; `name` is the string players must match |
| `popularity` | Kept per credit; becomes the corpus **rank** (a person's rank = max popularity across their credits — `graph_build.rank_people`). Not used for ordering within a film |

Cached as `{film_id, people: [[id, name, popularity], …]}` — nothing else from
the movie object (no `profile_path`, no `poster_path`, no images of any kind).

## What this repo deliberately does NOT use

No image endpoints or image fields (the game ships no images), no
`/search/movie` calls, no `/movie/{id}/recommendations` or `/similar`, no
`/person/{id}`, no `/configuration`, no TV endpoints, no sessions/accounts/v4
lists, no webhooks. If you add an endpoint: call it only from `curation/`
(never `docs/`), route it through `tmdb.get()` to inherit key hygiene, and keep
any filtering logic in a pure, offline-testable function per the existing
pattern (`harvest.extract_people` is the model).

Attribution obligations and TMDB terms live in
`degreesoffilm-external-positioning`.
