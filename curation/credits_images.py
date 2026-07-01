"""Per-rung credit images: a character still for cast, a headshot for crew.

The image shown AFTER a rung is answered (client side: frame.js pickCreditFrame).
Cast rungs get a curator-picked character still; crew rungs default to the
person's TMDB profile headshot. This module has three jobs:

  - attach_person_meta(): map each drafted rung back to its TMDB person and stamp
    helper fields (character, person_id, profile URL, a default caption, and a
    pre-selected image_pick). Pure — takes the credits dict, no network.
  - candidate_stills() / tagged_still_urls(): best-effort still URLs to offer in
    the picker (the thin network layer).
  - finalize_rung_images(): at approve time, turn each rung's chosen image_pick
    into a saved file + image/caption fields, then strip every helper field so the
    published JSON keeps only the {role, prompt, answers, decoys, image, caption}
    schema. Pure orchestration via an injected save() callback.

The helper fields (character, person_id, profile, candidates, image_pick) ride
along in the draft and the approve payload but NEVER reach the published file.
"""
import sys

import build_rungs

IMG_BASE = "https://image.tmdb.org/t/p/original"

# Roles that show a character still (and get an "as Character" caption). Every
# other rung that gets an image is crew, shown as a headshot with a name caption.
CHARACTER_ROLES = {"Cast"}
# Rung role -> TMDB crew `job`, to match a crew rung back to its person.
CREW_JOBS = {role: spec["job"] for role, spec in build_rungs.ROLES.items()}
# Fields stamped for the picker that must be stripped before publishing.
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
    """Stamp each credit rung with the helper fields the image picker needs. Pure
    (dict in, dict mutated) — no network, so it unit-tests directly."""
    for rung in puzzle.get("rungs", []):
        if rung.get("role") == "Film":
            continue
        person = _find_person(rung, credits)
        name = (rung.get("answers") or [""])[0]
        is_char = rung["role"] in CHARACTER_ROLES
        character = person.get("character", "") if (person and is_char) else ""
        profile = _profile_url(person)
        rung["character"] = character or ""
        rung["person_id"] = (person or {}).get("id")
        rung["profile"] = profile
        rung["caption"] = caption_for(rung["role"], name, character)
        # Crew default to their headshot; cast start unset so the curator picks a
        # character still deliberately (falling back to the full frame if not).
        rung["image_pick"] = None if is_char else profile
    return puzzle


def tagged_still_urls(person_id, film_id, key, *, limit=8, get=None):
    """Best-effort stills of this person tagged in THIS film. Returns [] if the
    endpoint is unavailable or empty (the curator can still use movie backdrops).
    `get` defaults to tmdb.get; injectable so this stays unit-testable."""
    if not person_id:
        return []
    if get is None:
        import tmdb
        get = tmdb.get
    try:
        data = get(f"/person/{person_id}/tagged_images", key)
    except Exception:
        return []
    urls = []
    for im in data.get("results", []):
        media = im.get("media") or {}
        if media.get("id") == film_id and im.get("file_path"):
            urls.append(IMG_BASE + im["file_path"])
            if len(urls) >= limit:
                break
    return urls


def candidate_stills(rung, film_id, key, movie_stills, *, get=None):
    """Ordered, de-duped candidate image URLs for a rung's picker: for cast, the
    person's tagged stills first, then the movie backdrops, then their headshot as
    a last resort; for crew, just the headshot. Pure aside from tagged_still_urls."""
    urls = []
    if rung.get("role") in CHARACTER_ROLES:
        urls += tagged_still_urls(rung.get("person_id"), film_id, key, get=get)
        urls += list(movie_stills or [])
    if rung.get("profile"):
        urls.append(rung["profile"])
    seen, out = set(), []
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def finalize_rung_images(rungs, stem, save):
    """At approve: for each rung with a chosen image_pick, save it (via the
    injected save(url, filename) -> None) and set image/caption; otherwise drop any
    image/caption. Then strip every helper field, leaving publish-clean rungs.
    Mutates and returns rungs. Pure orchestration (IO is injected)."""
    for i, rung in enumerate(rungs, start=1):
        pick = rung.get("image_pick")
        if rung.get("role") != "Film" and pick:
            filename = rung_image_name(stem, i)
            save(pick, filename)
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


# --- thin CLI: show a draft's per-rung image picks/candidates for a film --------

def _main(argv):
    import argparse
    import decoys as decoys_mod
    import tmdb

    ap = argparse.ArgumentParser(description="Show per-rung credit-image options.")
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
    imgs = tmdb.get(f"/movie/{args.id}/images", key)
    stills = [IMG_BASE + b["file_path"] for b in imgs.get("backdrops", [])[:12]
              if b.get("file_path")]

    print(f"{movie.get('title')} — per-rung credit images:")
    for i, r in enumerate(puzzle["rungs"], start=1):
        if r["role"] == "Film":
            print(f"  rung {i:>2} [{r['role']:<19}] (film — full-frame reveal)")
            continue
        cands = candidate_stills(r, args.id, key, stills)
        pick = r.get("image_pick") or "(none — curator picks)"
        print(f"  rung {i:>2} [{r['role']:<19}] {r['caption']}")
        print(f"          default pick: {pick}")
        print(f"          {len(cands)} candidate(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
