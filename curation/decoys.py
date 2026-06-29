"""Per-rung decoys: ~3 plausible, same-category wrong answers (DESIGN §4).

Selection is pure (`pick_decoys`). The candidate pools are sourced from the
credits of the film's *similar* movies — genre/era-appropriate wrong answers
(other directors for a director rung, other actors for a cast rung, other
cinematographers for a DP rung, ...). That sourcing is the thin network layer.

Decoys feed I Need Help's multiple choice in Cinephile, and all of Poser later.
"""
import sys

import tmdb

# rung role -> the TMDB crew `job` whose people make plausible decoys for it.
DEEP_JOBS = {
    "Director": "Director",
    "Cinematographer": "Director of Photography",
    "Composer": "Original Music Composer",
    "Editor": "Editor",
    "Production Designer": "Production Design",
}


def _norm(name):
    return " ".join((name or "").lower().split())


def pick_decoys(answers, pool, *, n=3, exclude=()):
    """Up to n names from `pool`, excluding the rung's answer(s) and `exclude`,
    de-duplicated, preserving pool order (so a popularity-sorted pool stays so).
    Pure — the unit-tested core."""
    blocked = {_norm(a) for a in answers} | {_norm(x) for x in exclude}
    out, seen = [], set()
    for name in pool:
        key = _norm(name)
        if not key or key in blocked or key in seen:
            continue
        seen.add(key)
        out.append(name)
        if len(out) >= n:
            break
    return out


def _people_in(credits):
    return {_norm(c.get("name", ""))
            for c in credits.get("cast", []) + credits.get("crew", [])}


def _source_films(film_id, key, *, limit, min_votes):
    """Plausible neighbour films: TMDB recommendations first (the curated "if you
    liked X" list), then `similar` as a fallback; filtered to reasonably-known
    films (vote floor) and popularity-sorted so pools lead with recognizable names."""
    out, seen = [], set()
    for endpoint in (f"/movie/{film_id}/recommendations", f"/movie/{film_id}/similar"):
        for m in tmdb.get(endpoint, key, page=1).get("results", []):
            if (m.get("id") and m["id"] not in seen and m.get("title")
                    and m.get("vote_count", 0) >= min_votes):
                seen.add(m["id"])
                out.append(m)
        if len(out) >= limit:
            break
    out.sort(key=lambda m: -m.get("popularity", 0.0))
    return out[:limit]


def gather_pools(film_id, credits, key, *, source_limit=8, cast_per_film=5, min_votes=400):
    """Build same-category candidate pools from the film's neighbour movies.

    Returns { "Film": [titles], "Cast": [names], "Director": [...], ... } with
    each person pool sorted by popularity, de-duped, and with anyone actually in
    THIS film removed (so a decoy can't be accidentally correct).
    """
    sims = _source_films(film_id, key, limit=source_limit, min_votes=min_votes)
    pools = {"Film": [m["title"] for m in sims]}
    scored = {role: [] for role in (["Cast"] + list(DEEP_JOBS))}

    for m in sims:
        cr = tmdb.movie_with_credits(m["id"], key).get("credits", {})
        for c in sorted(cr.get("cast", []), key=lambda c: c.get("order", 999))[:cast_per_film]:
            scored["Cast"].append((c.get("popularity", 0.0), c["name"]))
        for c in cr.get("crew", []):
            for role, job in DEEP_JOBS.items():
                if c.get("job") == job:
                    scored[role].append((c.get("popularity", 0.0), c["name"]))

    here = _people_in(credits)
    for role, items in scored.items():
        seen, names = set(), []
        for _, name in sorted(items, key=lambda t: -t[0]):
            k = _norm(name)
            if k and k not in seen and k not in here:
                seen.add(k)
                names.append(name)
        pools[role] = names
    return pools


def attach_decoys(puzzle, film_id, credits, key, *, n=3):
    """Set `rung["decoys"]` on every rung of an already-built puzzle draft."""
    pools = gather_pools(film_id, credits, key)
    for rung in puzzle["rungs"]:
        rung["decoys"] = pick_decoys(rung["answers"], pools.get(rung["role"], []), n=n)
    return puzzle


def _main(argv):
    import argparse
    import build_rungs

    ap = argparse.ArgumentParser(description="Show a puzzle draft with decoys.")
    ap.add_argument("--id", type=int, help="TMDB movie id")
    ap.add_argument("--title", help="film title to search")
    ap.add_argument("--year", type=int)
    ap.add_argument("--max-cast", type=int, default=6)
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    key = tmdb.load_key()
    film_id = args.id
    if not film_id:
        if not args.title:
            ap.error("give --id or --title")
        hit = tmdb.search_movie(args.title, key, year=args.year)
        if not hit:
            print("Not found.", file=sys.stderr)
            return 1
        film_id = hit["id"]

    movie = tmdb.movie_with_credits(film_id, key)
    credits = movie.get("credits", {})
    puzzle = build_rungs.build_puzzle(movie, credits, puzzle_id=film_id,
                                      max_cast=args.max_cast)
    attach_decoys(puzzle, film_id, credits, key)

    print(f"{movie.get('title')} — draft with decoys:")
    for i, r in enumerate(puzzle["rungs"], start=1):
        ans = " / ".join(r["answers"])
        decoys = ", ".join(r["decoys"]) or "(none found)"
        print(f"  rung {i:>2} [{r['role']:<19}] {ans}")
        print(f"          decoys: {decoys}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
