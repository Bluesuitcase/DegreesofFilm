"""Phase 2 data layer: turn a TMDB film + credits into an ordered rung draft.

This is the auto-generated *draft* a human curator then reviews/reorders. The
ordering rules (decided in the Phase 2 de-risk; see DESIGN.md §1/§5):

  - rung 1 is the film itself ("name the film").
  - CAST is ordered by TMDB billing order (`cast[].order`, lead first), with
    person popularity only as a tiebreaker. (Rolling popularity buries
    posthumous legends — it put the Joker at rung 13 — so it is NOT the sort.)
  - the DIRECTOR floats early: just after the top `director_after` lead cast.
  - the technical crew (cinematographer, composer, editor, production designer)
    are the DEEPEST rungs, in a fixed role order.

The functions that do the ordering are pure (dict in, dict out) so they unit-
test without a network or key — see build_rungs.test.py. `theme.accent` and per-
rung `decoys` are added by *later* curation steps, not here.
"""
import json
import sys

# Crew roles that become rungs, mapped to their TMDB `job` string, the player
# prompt, and where they sit. (Writer is deliberately NOT a rung — matches the
# §1 spec and hand-authored puzzle 001.)
DIRECTOR = "Director"
ROLES = {
    DIRECTOR:              {"job": "Director",
                            "prompt": "Who directed it?"},
    "Cinematographer":     {"job": "Director of Photography",
                            "prompt": "Who was the cinematographer?"},
    "Composer":            {"job": "Original Music Composer",
                            "prompt": "Who composed the score?"},
    "Editor":              {"job": "Editor",
                            "prompt": "Who edited the film?"},
    "Production Designer":  {"job": "Production Design",
                            "prompt": "Who was the production designer?"},
}
# Technical crew, deepest-rung order (director is placed separately, early).
DEEP_ROLES = ["Cinematographer", "Composer", "Editor", "Production Designer"]


def film_rung(movie):
    answers = [movie["title"]]
    original = (movie.get("original_title") or "").strip()
    if original and original != movie["title"]:
        answers.append(original)
    return {"role": "Film", "prompt": "Name the film.", "answers": answers}


def cast_rung(member):
    character = (member.get("character") or "").strip()
    prompt = f"Who played {character}?" if character else "Name this cast member."
    return {"role": "Cast", "prompt": prompt, "answers": [member["name"]]}


def _people_for_job(credits, job):
    """All crew with this job, deduped by person id, billing-stable order."""
    seen, names = set(), []
    for c in credits.get("crew", []):
        if c.get("job") == job and c["id"] not in seen:
            seen.add(c["id"])
            names.append(c["name"])
    return names


def crew_rung(credits, role):
    names = _people_for_job(credits, ROLES[role]["job"])
    if not names:
        return None
    return {"role": role, "prompt": ROLES[role]["prompt"], "answers": names}


def order_cast(credits, max_cast):
    """Cast by billing order (lead=0), popularity as the tiebreaker, trimmed."""
    cast = sorted(
        credits.get("cast", []),
        key=lambda c: (c.get("order", 9999), -c.get("popularity", 0.0)),
    )
    return cast[:max_cast]


def order_rungs(movie, credits, *, max_cast=8, director_after=2):
    """Assemble the ordered list of rung dicts (the draft)."""
    cast = [cast_rung(c) for c in order_cast(credits, max_cast)]
    director = crew_rung(credits, DIRECTOR)

    rungs = [film_rung(movie)]
    rungs += cast[:director_after]          # top lead cast
    if director:
        rungs.append(director)              # director floats early
    rungs += cast[director_after:]          # remaining cast
    for role in DEEP_ROLES:                 # technical crew, deepest
        rung = crew_rung(credits, role)
        if rung:
            rungs.append(rung)
    return rungs


def build_puzzle(movie, credits, *, puzzle_id, date=None, images=None, **opts):
    """Full puzzle-JSON skeleton. `theme.accent` and `decoys` come later."""
    puzzle = {"id": puzzle_id}
    if date:
        puzzle["date"] = date
    puzzle["images"] = list(images or [])
    puzzle["rungs"] = order_rungs(movie, credits, **opts)
    return puzzle


# --- thin CLI: print a real draft for a film (needs a key) -------------------

def _main(argv):
    import argparse
    from tmdb import load_key, movie_with_credits, search_movie

    ap = argparse.ArgumentParser(description="Print a rung draft for a film.")
    ap.add_argument("--title", help="film title to search")
    ap.add_argument("--year", type=int, help="release year (disambiguates)")
    ap.add_argument("--id", type=int, help="TMDB movie id (skips search)")
    ap.add_argument("--max-cast", type=int, default=8)
    ap.add_argument("--json", action="store_true", help="emit puzzle JSON")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    key = load_key()
    film_id = args.id
    if not film_id:
        if not args.title:
            ap.error("give --id or --title")
        hit = search_movie(args.title, key, year=args.year)
        if not hit:
            print(f"Not found: {args.title} ({args.year})", file=sys.stderr)
            return 1
        film_id = hit["id"]

    movie = movie_with_credits(film_id, key)
    credits = movie.get("credits", {})
    puzzle = build_puzzle(movie, credits, puzzle_id=film_id,
                          date=(movie.get("release_date") or None),
                          max_cast=args.max_cast)

    if args.json:
        print(json.dumps(puzzle, ensure_ascii=False, indent=2))
        return 0

    rel = (movie.get("release_date") or "----")[:4]
    print(f"{movie.get('title')} ({rel}) — TMDB id {film_id} — draft ladder:")
    for i, r in enumerate(puzzle["rungs"], start=1):
        ans = " / ".join(r["answers"])
        print(f"  rung {i:>2}  [{r['role']:<19}] {ans}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
