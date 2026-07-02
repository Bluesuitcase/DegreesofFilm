"""Per-rung credit images: the person's TMDB headshot, for cast and crew alike.

The image shown AFTER a rung is answered (client side: frame.js pickCreditFrame).
Every credit rung — cast or crew — uses that person's TMDB profile headshot,
chosen automatically with no manual per-rung picking. (Cast character stills on
TMDB are too sparse to rely on, so headshots are the uniform default; a rung whose
person has no headshot simply holds the full frame.) This module has two jobs:

  - attach_person_meta(): map each drafted rung back to its TMDB person and stamp
    helper fields (character, profile headshot URL, and a caption). Pure — takes
    the credits dict, no network.
  - finalize_rung_images(): at approve time, save each rung's headshot into a file
    + image/caption fields, then strip every helper field so the published JSON
    keeps only the {role, prompt, answers, decoys, image, caption} schema. Pure
    orchestration via an injected save() callback.

The helper fields (character, profile) ride along in the draft and the approve
payload but NEVER reach the published file.
"""
import sys

import build_rungs

IMG_BASE = "https://image.tmdb.org/t/p/original"

# Cast rungs get an "as Character" caption; every other credit rung is crew, whose
# caption is just the name. (Both show the person's headshot — see the module doc.)
CHARACTER_ROLES = {"Cast"}
# Rung role -> TMDB crew `job`, to match a crew rung back to its person.
CREW_JOBS = {role: spec["job"] for role, spec in build_rungs.ROLES.items()}
# Helper fields stamped onto a draft rung that must be stripped before publishing.
# (person_id/candidates/image_pick are legacy from the old picker; kept in the
# strip list so any stale draft can't leak them into a published file.)
HELPER_KEYS = ("character", "person_id", "profile", "candidates", "image_pick")


def _norm(name):
    return " ".join((name or "").lower().split())


def caption_for(role, name, character):
    """'Name as Character' for cast, 'Name' for crew, '' for the film rung. Pure."""
    if role == "Film":
        return ""
    name = name or ""
    if role in CHARACTER_ROLES and (character or "").strip():
        return f"{name} as {character.strip()}"
    return name


def rung_image_name(stem, n):
    """Credit-image filename for rung n (1-based): '004' -> '004-r2.jpg'. The 'r'
    keeps these distinct from the reveal-tier files ('004-1.jpg'). Pure."""
    return f"{stem}-r{n}.jpg"


def _profile_url(person):
    pp = (person or {}).get("profile_path")
    return (IMG_BASE + pp) if pp else None


def _find_person(rung, credits):
    """The TMDB credit dict this rung names, matched by answer name + role/job."""
    names = {_norm(a) for a in rung.get("answers", [])}
    role = rung.get("role")
    if role in CHARACTER_ROLES:
        for c in credits.get("cast", []):
            if _norm(c.get("name")) in names:
                return c
    elif role in CREW_JOBS:
        for c in credits.get("crew", []):
            if c.get("job") == CREW_JOBS[role] and _norm(c.get("name")) in names:
                return c
    return None


def attach_person_meta(puzzle, credits):
    """Stamp each credit rung with its headshot + caption. Every credit rung — cast
    and crew alike — uses the person's TMDB profile headshot, automatically (no
    per-rung choice). Pure (dict in, dict mutated) — no network, unit-tests directly."""
    for rung in puzzle.get("rungs", []):
        if rung.get("role") == "Film":
            continue
        person = _find_person(rung, credits)
        name = (rung.get("answers") or [""])[0]
        is_char = rung["role"] in CHARACTER_ROLES
        character = person.get("character", "") if (person and is_char) else ""
        rung["character"] = character or ""
        rung["profile"] = _profile_url(person)   # the headshot the rung will show
        rung["caption"] = caption_for(rung["role"], name, character)
    return puzzle


def finalize_rung_images(rungs, stem, save):
    """At approve: for each credit rung with a headshot, save it (via the injected
    save(url, filename) -> None) and set image/caption; a rung with no headshot
    drops any image/caption and holds the full frame. Then strip every helper field,
    leaving publish-clean rungs. Mutates and returns rungs (IO is injected)."""
    for i, rung in enumerate(rungs, start=1):
        headshot = rung.get("profile")
        if rung.get("role") != "Film" and headshot:
            filename = rung_image_name(stem, i)
            save(headshot, filename)
            rung["image"] = f"images/{filename}"
            if not (rung.get("caption") or "").strip():
                rung["caption"] = caption_for(rung.get("role"),
                                              (rung.get("answers") or [""])[0],
                                              rung.get("character"))
        else:
            rung.pop("image", None)
            rung.pop("caption", None)
        for k in HELPER_KEYS:
            rung.pop(k, None)
    return rungs


# --- thin CLI: show a draft's per-rung credit headshots for a film --------------

def _main(argv):
    import argparse
    import tmdb

    ap = argparse.ArgumentParser(description="Show per-rung credit headshots.")
    ap.add_argument("--id", type=int, required=True, help="TMDB movie id")
    ap.add_argument("--max-cast", type=int, default=6)
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    key = tmdb.load_key()
    movie = tmdb.movie_with_credits(args.id, key)
    credits = movie.get("credits", {})
    puzzle = build_rungs.build_puzzle(movie, credits, puzzle_id=args.id,
                                      max_cast=args.max_cast)
    attach_person_meta(puzzle, credits)

    print(f"{movie.get('title')} — per-rung credit headshots:")
    for i, r in enumerate(puzzle["rungs"], start=1):
        if r["role"] == "Film":
            print(f"  rung {i:>2} [{r['role']:<19}] (film — full-frame reveal)")
            continue
        shot = r.get("profile") or "(no TMDB headshot — holds full frame)"
        print(f"  rung {i:>2} [{r['role']:<19}] {r['caption']}")
        print(f"          headshot: {shot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
