"""Harvest the raw material for the corpus: the pool's films and their key credits.

This is step 1 of the Degrees pipeline:

    harvest.py  ->  films_cache.jsonl + people_harvest_cache.jsonl   (this file, needs TMDB)
    graph_build.py  ->  docs/graph.json                              (pure)
    challenge_gen.py -> docs/challenges.json                         (pure)

The pool floor (DESIGN §1) is TMDB films with vote_count >= 800 AND vote_average >= 6.5
— roughly 3,700 films people have actually heard of. Beyond that floor, hops stop being
recognisable and the game stops being fun, so the floor is the corpus boundary.

Both caches are append-only jsonl and gitignored: re-running fetches only what's new,
so a refresh months later costs a few hundred calls, not thousands.

    python curation/harvest.py             # refresh both caches
    python curation/harvest.py --films     # films metadata only

Pure core (no network): extract_people. Everything else is the cached TMDB sweep.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tmdb  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FILMS_CACHE = os.path.join(HERE, "films_cache.jsonl")
PEOPLE_CACHE = os.path.join(HERE, "people_harvest_cache.jsonl")

POOL_MIN_VOTES = 800
POOL_MIN_AVG = 6.5
MAX_PAGES = 500
CAST_TOP = 12                        # top billing; 12 gives margin over the visible cast
CREW_JOBS = ("Director", "Director of Photography", "Original Music Composer",
             "Editor", "Production Design")


def extract_people(movie, cast_top=CAST_TOP, crew_jobs=CREW_JOBS):
    """(id, name, popularity) for a film's top-billed cast + key crew. Pure."""
    credits = movie.get("credits") or {}
    out = []
    for c in (credits.get("cast") or [])[:cast_top]:
        if c.get("id") and c.get("name"):
            out.append((c["id"], c["name"].strip(), c.get("popularity") or 0))
    for c in (credits.get("crew") or []):
        if c.get("job") in crew_jobs and c.get("id") and c.get("name"):
            out.append((c["id"], c["name"].strip(), c.get("popularity") or 0))
    return out


def pool_film_ids(key, *, sort_by="popularity.desc"):
    """Every film clearing the pool floor, in `sort_by` order. The order matters:
    graph_build keeps it as the corpus's rank, which drives autocomplete."""
    ids, page, total = [], 1, 1
    while page <= min(total, MAX_PAGES):
        data = tmdb.get("/discover/movie", key, sort_by=sort_by, include_adult="false",
                        page=page, **{"vote_count.gte": POOL_MIN_VOTES,
                                      "vote_average.gte": POOL_MIN_AVG})
        total = data.get("total_pages") or 1
        ids += [m["id"] for m in (data.get("results") or []) if m.get("id")]
        page += 1
    return ids


def _cached_ids(path, field):
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as fh:
        return {json.loads(line)[field] for line in fh}


def refresh_films(key):
    """films_cache.jsonl: {id, title, year} in popularity order."""
    have = _cached_ids(FILMS_CACHE, "id")
    ids, page, total, wrote = [], 1, 1, 0
    with open(FILMS_CACHE, "a", encoding="utf-8") as fh:
        while page <= min(total, MAX_PAGES):
            data = tmdb.get("/discover/movie", key, sort_by="popularity.desc",
                            include_adult="false", page=page,
                            **{"vote_count.gte": POOL_MIN_VOTES,
                               "vote_average.gte": POOL_MIN_AVG})
            total = data.get("total_pages") or 1
            for m in (data.get("results") or []):
                if not m.get("id") or m["id"] in have:
                    continue
                have.add(m["id"])
                fh.write(json.dumps({"id": m["id"], "title": m.get("title"),
                                     "year": int((m.get("release_date") or "0")[:4] or 0)}) + "\n")
                wrote += 1
            ids += [m["id"] for m in (data.get("results") or []) if m.get("id")]
            page += 1
    print(f"films: {len(ids)} in the pool, {wrote} new")
    return ids


def refresh_credits(key, film_ids):
    """people_harvest_cache.jsonl: {film_id, people:[[id,name,popularity]...]}."""
    have = _cached_ids(PEOPLE_CACHE, "film_id")
    fresh = [fid for fid in film_ids if fid not in have]
    print(f"credits: {len(film_ids) - len(fresh)} cached, {len(fresh)} to fetch")
    with open(PEOPLE_CACHE, "a", encoding="utf-8") as fh:
        for i, fid in enumerate(fresh, 1):
            movie = tmdb.get(f"/movie/{fid}", key, append_to_response="credits")
            fh.write(json.dumps({"film_id": fid, "people": extract_people(movie)}) + "\n")
            if i % 250 == 0:
                print(f"  fetched {i}/{len(fresh)} film credits…")
    return len(fresh)


def _main(argv):
    ap = argparse.ArgumentParser(description="Refresh the TMDB caches behind the corpus")
    ap.add_argument("--films", action="store_true", help="films metadata only")
    args = ap.parse_args(argv)
    key = tmdb.load_key()
    ids = refresh_films(key)
    if not args.films:
        refresh_credits(key, ids)
    print("\nnext: python curation/graph_build.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
