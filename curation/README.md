# curation/ — the PRIVATE zone (your machine only)

This is Phase 2 of Degrees of Film: the tooling that holds the **TMDB API key** and
manufactures puzzles. **Nothing here is served to players** — players only ever fetch the
finished static files under `docs/`. The key lives only in `curation/.env` (gitignored).

## Setup

1. `cp .env.example .env` (or copy it in your editor).
2. Open `curation/.env` and paste your TMDB **v3 API Key** in place of the placeholder.
   Do not paste the key into chat or commit it — `.env` is gitignored.

## What's here so far

- **`validate_ladder.py`** — a throwaway de-risk script (stdlib only, no installs). It pulls
  several known films from TMDB, sorts their credits by popularity, and prints the resulting
  ladder so we can eyeball the project's riskiest assumption: *does popularity-sorting yield a
  sane famous→obscure ladder?* Prove this before building any curation UI (DESIGN.md §5).

  ```
  python curation/validate_ladder.py
  ```

The real tool (Flask/FastAPI endpoints, Pillow cropping, the used-films ledger, decoy + accent
generation, the `manifest.json` writer) gets built only once the ladder assumption checks out.
