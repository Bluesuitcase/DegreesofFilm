#!/usr/bin/env python3
"""
Phase 2 de-risk script (THROWAWAY) for Degrees of Film.

Tests the single riskiest assumption in the whole project (DESIGN.md §5):
    does sorting a film's credits by TMDB popularity produce a sane
    "famous -> obscure" ladder?

If the lead actors and director sit near the top and it descends gracefully
into obscure crew, the core premise holds and Phase 2 is worth building. If the
ordering is nonsense, we found out for the price of one script instead of a
whole curation tool.

Usage:
    1. Put your key in curation/.env  (TMDB_API_KEY=...). It is gitignored.
    2. python curation/validate_ladder.py

Stdlib only -- no pip installs. The key is read from .env / the environment and
is never printed (request URLs that carry it are never logged).
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.themoviedb.org/3"
KEY = ""  # filled by load_env() via main()

# Crew jobs a player could plausibly be asked about -> display role.
# (Cast is handled separately.) Kept deliberately tight to mirror the rungs.
ASKABLE_JOBS = {
    "Director": "Director",
    "Director of Photography": "Cinematographer",
    "Original Music Composer": "Composer",
    "Editor": "Editor",
    "Production Design": "Production Designer",
    "Writer": "Writer",
    "Screenplay": "Writer",
    "Story": "Writer",
    "Novel": "Writer",
}

# A spread to stress the assumption: ensemble, blockbuster, two foreign-language.
# No Country cross-checks hand-authored puzzle 001.
FILMS = [
    ("No Country for Old Men", 2007),
    ("Pulp Fiction", 1994),
    ("The Dark Knight", 2008),
    ("Parasite", 2019),
    ("Pan's Labyrinth", 2006),
]

ROWS_PER_FILM = 18


def load_env():
    """Minimal .env loader so we need no python-dotenv dependency."""
    here = os.path.dirname(os.path.abspath(__file__))
    for path in (os.path.join(here, ".env"), "curation/.env", ".env"):
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            return


def get(path, **params):
    """GET a TMDB endpoint. Never logs the URL (it carries the api key)."""
    params["api_key"] = KEY
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        # path only -- the query string holds the key, so we drop it.
        msg = "401 (check your TMDB_API_KEY)" if e.code == 401 else str(e.code)
        raise RuntimeError(f"HTTP {msg} on {path}") from None


def search_movie(title, year):
    data = get("/search/movie", query=title, year=year, include_adult="false")
    results = data.get("results") or []
    return results[0] if results else None


def build_ladder(credits):
    """Combine cast + askable crew, dedupe by person, sort by popularity."""
    people = {}

    def add(pid, name, pop, role, detail):
        e = people.get(pid)
        if e is None:
            people[pid] = {"name": name, "pop": pop, "roles": [role], "detail": detail}
        else:
            if role not in e["roles"]:
                e["roles"].append(role)
            if detail and not e["detail"]:
                e["detail"] = detail
            e["pop"] = max(e["pop"], pop)

    for c in credits.get("cast", []):
        add(c["id"], c["name"], c.get("popularity", 0.0), "Cast", c.get("character", ""))
    for c in credits.get("crew", []):
        role = ASKABLE_JOBS.get(c.get("job", ""))
        if role:
            add(c["id"], c["name"], c.get("popularity", 0.0), role, "")

    return sorted(people.values(), key=lambda e: e["pop"], reverse=True)


CREW_PRIORITY = ["Director", "Cinematographer", "Composer", "Editor",
                 "Production Designer", "Writer"]


def billing_ladder(credits):
    """Cast by billing order (lead=0), then key crew by role priority."""
    cast = sorted(credits.get("cast", []), key=lambda c: c.get("order", 9999))
    seen, crew = set(), []
    for c in sorted(credits.get("crew", []),
                    key=lambda c: CREW_PRIORITY.index(ASKABLE_JOBS[c["job"]])
                    if c.get("job") in ASKABLE_JOBS and ASKABLE_JOBS[c["job"]] in CREW_PRIORITY
                    else 99):
        role = ASKABLE_JOBS.get(c.get("job", ""))
        if role and c["id"] not in seen:
            seen.add(c["id"])
            crew.append((c["name"], role, c.get("popularity", 0.0)))
    rows = [(c["name"], "Cast", c.get("character", ""), c.get("popularity", 0.0))
            for c in cast]
    rows += [(n, r, "", p) for (n, r, p) in crew]
    return rows


def report(title, year):
    hit = search_movie(title, year)
    if not hit:
        print(f"\n### {title} ({year}) -- NOT FOUND on TMDB")
        return
    mid = hit["id"]
    movie = get(f"/movie/{mid}", append_to_response="credits")
    credits = movie.get("credits", {})
    rel = (movie.get("release_date") or "----")[:4]

    print(f"\n### {movie.get('title')} ({rel}) -- TMDB id {mid}, "
          f"film popularity {movie.get('popularity', 0):.1f}")

    pop = build_ladder(credits)
    print("  [A] by PERSON POPULARITY (current draft):")
    for i, e in enumerate(pop[:12], start=2):
        roles = "/".join(e["roles"])
        detail = f"  as {e['detail']}" if e["detail"] and "Cast" in e["roles"] else ""
        print(f"      rung {i:>2}  pop {e['pop']:6.1f}  {e['name']:<24} [{roles}]{detail}")

    bill = billing_ladder(credits)
    print("  [B] by BILLING ORDER (cast lead->bit), then key crew:")
    for i, (name, role, detail, p) in enumerate(bill[:12], start=2):
        d = f"  as {detail}" if detail and role == "Cast" else ""
        print(f"      rung {i:>2}  pop {p:6.1f}  {name:<24} [{role}]{d}")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # names carry diacritics
    except Exception:
        pass
    load_env()
    global KEY
    KEY = os.environ.get("TMDB_API_KEY", "").strip()
    if not KEY or KEY == "PASTE_YOUR_KEY_HERE":
        print("TMDB_API_KEY is not set.\n"
              "  -> Open curation/.env and replace PASTE_YOUR_KEY_HERE with your TMDB v3 key.\n"
              "     (curation/.env is gitignored; do not paste the key into chat.)",
              file=sys.stderr)
        sys.exit(2)

    print("Degrees of Film -- ladder validation (credits sorted by TMDB popularity)")
    print("EYEBALL TEST: do recognizable stars + the director sit at the top,")
    print("descending smoothly into obscure crew? Watch for anyone wildly out of place.")
    for title, year in FILMS:
        try:
            report(title, year)
        except RuntimeError as e:
            print(f"  ! {title}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
