# curation/ — the PRIVATE zone (your machine only)

The tooling that holds the **TMDB API key** and builds the game's data. **Nothing here is
served to players** — they only ever fetch the finished static files under `docs/`. The key
lives only in `curation/.env` (gitignored).

**No dependencies.** Everything here is Python stdlib — there is no `.venv`, no `pip install`,
no Pillow/FastAPI/OpenCV. (The old crop-and-publish tool that needed those was deleted with the
dig game on 2026-08-11.)

## Setup

1. `cp .env.example .env` (or copy it in your editor).
2. Paste your TMDB **v3 API Key** in place of the placeholder. Never commit it or paste it
   into chat — `.env` is gitignored.

## The pipeline

Three steps, and only the first touches the network:

```bash
python curation/harvest.py                    # 1. TMDB -> the two local caches
python curation/graph_build.py                # 2. caches -> docs/graph.json  (the corpus)
python curation/challenge_gen.py --days 30    # 3. corpus -> docs/challenges.json (dailies)
```

- **`harvest.py`** sweeps every film clearing the pool floor (`vote_count >= 800` and
  `vote_average >= 6.5` — about 3,700 films people have actually heard of) and caches each
  one's top-billed cast plus five key crew jobs. Both caches (`films_cache.jsonl`,
  `people_harvest_cache.jsonl`) are gitignored and append-only, so re-running months later
  fetches only what's new.
- **`graph_build.py`** turns the caches into `docs/graph.json`: it drops people credited on a
  single film (they can never be a hop — 67% of them), ranks films and people by popularity so
  autocomplete surfaces the famous entry first, index-encodes the adjacency, and validates the
  result. `--check` re-validates the shipped file without rebuilding.
- **`challenge_gen.py`** picks film pairs at an exact par *from the shipped corpus*, so a par
  written into a daily is a par the player can actually reach. It draws endpoints from the most
  popular films, rejects franchise pairs (*Infinity War* → *Endgame* is not a puzzle), requires
  more than one shortest route so the answer isn't a needle, and asserts par at build time.
  `--check` re-derives every published daily's par.

## Spoilers

`challenge_gen.py` writes the solution chains to **`curation/challenge_solutions.json`**, which
is **gitignored and must stay that way — this repo is public**. Don't name a future daily's
chain in a commit message either.

## Tests

Pure logic, no network, no fixtures to install:

```bash
python curation/harvest.test.py
python curation/graph_build.test.py
python curation/challenge_gen.test.py
```
