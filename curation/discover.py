"""Discover an unused film clearing the pool floor.

Pool floor (DESIGN §1): TMDB films with `vote_count >= 800 AND vote_average >= 6.5`.
(Score = "is it good", vote count = "is it known" — the fame proxy.) A discovered
film must also not already be in the used-films ledger.

The filtering is a pure function (`pick_unused` / `candidates`) so it unit-tests
offline; `discover_unused` is the thin network wrapper around TMDB /discover.
"""
import sys

import tmdb
from ledger import load as load_ledger, used_ids

POOL_MIN_VOTES = 800
POOL_MIN_AVG = 6.5


def clears_floor(movie, *, min_votes=POOL_MIN_VOTES, min_avg=POOL_MIN_AVG):
    return (movie.get("vote_count", 0) >= min_votes
            and movie.get("vote_average", 0.0) >= min_avg)


def candidates(results, used, *, min_votes=POOL_MIN_VOTES, min_avg=POOL_MIN_AVG):
    """All results that clear the floor and aren't already used. Pure."""
    return [m for m in results
            if m.get("id") not in used
            and clears_floor(m, min_votes=min_votes, min_avg=min_avg)]


def pick_unused(results, used, **floor):
    """First valid candidate, or None. Pure."""
    found = candidates(results, used, **floor)
    return found[0] if found else None


def _discover_page(key, page, sort_by, min_votes, min_avg):
    return tmdb.get("/discover/movie", key,
                    sort_by=sort_by,
                    page=page,
                    include_adult="false",
                    **{"vote_count.gte": min_votes, "vote_average.gte": min_avg})


def discover_unused(key, used, *, pages=3, sort_by="popularity.desc",
                    min_votes=POOL_MIN_VOTES, min_avg=POOL_MIN_AVG):
    """Page through TMDB /discover and return the first unused film, or None."""
    for page in range(1, pages + 1):
        data = _discover_page(key, page, sort_by, min_votes, min_avg)
        hit = pick_unused(data.get("results", []), used,
                          min_votes=min_votes, min_avg=min_avg)
        if hit:
            return hit
    return None


def _main(argv):
    import argparse
    ap = argparse.ArgumentParser(
        description="Suggest unused films that clear the pool floor.")
    ap.add_argument("--count", type=int, default=8, help="how many to list")
    ap.add_argument("--sort", default="popularity.desc", help="TMDB sort_by")
    ap.add_argument("--pages", type=int, default=3, help="discover pages to scan")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    key = tmdb.load_key()
    used = used_ids(load_ledger())

    found = []
    for page in range(1, args.pages + 1):
        data = _discover_page(key, page, args.sort, POOL_MIN_VOTES, POOL_MIN_AVG)
        found += candidates(data.get("results", []), used)
        if len(found) >= args.count:
            break

    print(f"Unused films clearing the floor "
          f"(votes >= {POOL_MIN_VOTES}, avg >= {POOL_MIN_AVG}); sort={args.sort}:")
    for m in found[:args.count]:
        yr = (m.get("release_date") or "----")[:4]
        print(f"  id {m['id']:>7}  {m.get('vote_average', 0):>4.1f}*  "
              f"{m.get('vote_count', 0):>6} votes  {m.get('title')} ({yr})")
    print(f"\n{len(used)} film(s) already in the ledger. "
          f"Next: python curation/build_rungs.py --id <id>")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
