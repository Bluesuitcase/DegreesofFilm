"""Curation crop tool — FastAPI backend + a localhost crop page.

PRIVATE: holds the TMDB key, runs on localhost only, and writes finished static
files into docs/. It is a thin layer over the framework-free modules (discover,
build_rungs, decoys, images, publish). Run from the repo root:

    .venv/Scripts/python -m uvicorn app:app --reload --app-dir curation --port 8001

(or use the "curation" entry in .claude/launch.json).
"""
import datetime
import io
import json
import os
import urllib.request

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import build_rungs
import credits_images as credits_images_mod
import decoys as decoys_mod
import discover as discover_mod
import images as images_mod
import manifest as manifest_mod
import publish as publish_mod
import tmdb
from ledger import load as load_ledger, used_ids

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_BASE = "https://image.tmdb.org/t/p/original"
IMG_DIR = os.path.join(publish_mod.PUZZLES_DIR, "images")

app = FastAPI(title="Degrees of Film — curation")


def _key():
    try:
        return tmdb.load_key()
    except SystemExit as e:
        raise HTTPException(500, str(e))


# --- shared helpers (used by discover/search + film/puzzle load + approve/update) --

def _film_id_for_puzzle(pid):
    """The TMDB film id a published puzzle came from, via the ledger."""
    for e in load_ledger():
        if e.get("puzzle") == pid:
            return e.get("id")
    return None


def _film_stills(movie, film_id, k):
    """Candidate source frames for the crop stage: the film's backdrops + poster."""
    imgs = tmdb.get(f"/movie/{film_id}/images", k)
    stills = [IMG_BASE + b["file_path"] for b in imgs.get("backdrops", [])[:12]
              if b.get("file_path")]
    if movie.get("poster_path"):
        stills.append(IMG_BASE + movie["poster_path"])
    return stills


def _download_rgb(url):
    """Fetch a TMDB image as an RGB PIL Image (rejects non-TMDB URLs)."""
    from PIL import Image
    if not url.startswith("https://image.tmdb.org/"):
        raise HTTPException(400, "image must be a TMDB image URL")
    with urllib.request.urlopen(url, timeout=30) as resp:
        return Image.open(io.BytesIO(resp.read())).convert("RGB")


def _credit_saver(img_dir=IMG_DIR):
    """A save(url, filename) that downloads a credit image, downscales to a sane
    width (client uses object-fit:contain), and writes it into the images dir."""
    def save(url, filename):
        im = _download_rgb(url)
        if im.width > 1000:
            im = im.resize((1000, max(1, round(im.height * 1000 / im.width))))
        os.makedirs(img_dir, exist_ok=True)
        im.save(os.path.join(img_dir, filename), quality=85)
    return save


def _crop_and_theme(image_url, box, accent, stem):
    """Download the source still, crop the reveal tiers, sample the theme, and save
    the tiers as NNN-{1,2,3}.jpg. Returns (image_files, theme)."""
    if len(box) != 4:
        raise HTTPException(400, "box must be [x, y, w, h]")
    src = _download_rgb(image_url)
    x, y, w, h = box
    px = (round(x * src.width), round(y * src.height),
          round((x + w) * src.width), round((y + h) * src.height))
    tiers = images_mod.crop_tiers(src, px)
    theme = {"accent": accent or images_mod.sample_accent(tiers[0]),
             **images_mod.derive_background(tiers[0])}
    names = images_mod.save_tiers(tiers, IMG_DIR, stem)
    return [f"images/{n}" for n in names], theme


@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(HERE, "static", "index.html"), encoding="utf-8") as fh:
        return fh.read()


@app.get("/api/next-date")
def api_next_date():
    # Default the crop UI's date to the next free day so publishes don't collide.
    return {"date": publish_mod.next_date(manifest_mod.load())}


@app.get("/api/schedule")
def api_schedule(days: int = 14):
    # The coming days flagged filled/empty, plus the runway (consecutive stocked
    # days from today) — the "curate a week ahead" view. No key needed.
    man = manifest_mod.load()
    return {"today": datetime.date.today().isoformat(),
            "runway": publish_mod.runway(man),
            "slots": publish_mod.upcoming_schedule(man, days=days)}


@app.get("/api/discover")
def api_discover(sort: str = "vote_count.desc", count: int = 12):
    k = _key()
    used = used_ids(load_ledger())
    found = []
    for page in range(1, 4):
        data = tmdb.get("/discover/movie", k, sort_by=sort, page=page,
                        include_adult="false",
                        **{"vote_count.gte": discover_mod.POOL_MIN_VOTES,
                           "vote_average.gte": discover_mod.POOL_MIN_AVG})
        found += discover_mod.candidates(data.get("results", []), used)
        if len(found) >= count:
            break
    return [{"id": m["id"], "title": m.get("title"),
             "year": (m.get("release_date") or "")[:4],
             "vote_average": round(m.get("vote_average", 0), 1),
             "vote_count": m.get("vote_count"),
             "backdrop": (IMG_BASE + m["backdrop_path"]) if m.get("backdrop_path") else None}
            for m in found[:count]]


@app.get("/api/search")
def api_search(q: str = "", count: int = 18):
    """Free-text title search across ALL of TMDB (not just the discover shortlist).
    Films already made into puzzles are flagged `used` and carry their `puzzle` id
    so the UI can route them to editing instead of a duplicate authoring."""
    if not q.strip():
        return []
    k = _key()
    used_puzzle = {e["id"]: e.get("puzzle") for e in load_ledger() if e.get("id")}
    data = tmdb.get("/search/movie", k, query=q, include_adult="false")
    out = []
    for m in data.get("results", []):
        if not m.get("id") or not m.get("title"):
            continue
        out.append({"id": m["id"], "title": m.get("title"),
                    "year": (m.get("release_date") or "")[:4],
                    "vote_average": round(m.get("vote_average", 0), 1),
                    "vote_count": m.get("vote_count"),
                    "backdrop": (IMG_BASE + m["backdrop_path"]) if m.get("backdrop_path") else None,
                    "used": m["id"] in used_puzzle,
                    "puzzle": used_puzzle.get(m["id"])})
        if len(out) >= count:
            break
    return out


@app.get("/api/film/{film_id}")
def api_film(film_id: int):
    k = _key()
    movie = tmdb.movie_with_credits(film_id, k)
    credits = movie.get("credits", {})
    puzzle = build_rungs.build_puzzle(movie, credits, puzzle_id=film_id, max_cast=6)
    decoys_mod.attach_decoys(puzzle, film_id, credits, k)
    stills = _film_stills(movie, film_id, k)
    credits_images_mod.attach_person_meta(puzzle, credits)   # auto headshot per credit rung
    return {"id": film_id, "title": movie.get("title"),
            "release_date": movie.get("release_date"),
            "stills": stills, "rungs": puzzle["rungs"]}


@app.get("/api/puzzle/{pid}")
def api_puzzle(pid: int):
    """Load an already-published puzzle for editing: its existing rungs/date/theme,
    plus fresh film stills + per-rung picker options so it can be re-authored."""
    k = _key()
    film_id = _film_id_for_puzzle(pid)
    if not film_id:
        raise HTTPException(404, f"no ledger entry for puzzle {pid}")
    path = os.path.join(publish_mod.PUZZLES_DIR, f"{publish_mod.puzzle_stem(pid)}.json")
    if not os.path.isfile(path):
        raise HTTPException(404, f"puzzle file {pid} not found")
    with open(path, encoding="utf-8") as fh:
        existing = json.load(fh)
    movie = tmdb.movie_with_credits(film_id, k)
    credits = movie.get("credits", {})
    stills = _film_stills(movie, film_id, k)
    # Re-stamp each EXISTING rung with its headshot + caption (preserving human edits
    # to the rung text). Headshots are automatic — no per-rung picking.
    credits_images_mod.attach_person_meta(existing, credits)
    return {"id": pid, "film_id": film_id, "editing": True,
            "title": movie.get("title"), "release_date": movie.get("release_date"),
            "date": existing.get("date"),
            "accent": (existing.get("theme") or {}).get("accent"),
            "images": existing.get("images", []),
            "stills": stills, "rungs": existing["rungs"]}


class Approve(BaseModel):
    film_id: int
    image_url: str
    box: list[float]            # normalized [x, y, w, h] in 0..1
    rungs: list
    date: str
    accent: str | None = None


@app.post("/api/approve")
def api_approve(body: Approve):
    if not body.image_url.startswith("https://image.tmdb.org/"):
        raise HTTPException(400, "image_url must be a TMDB image URL")

    k = _key()
    movie = tmdb.movie_with_credits(body.film_id, k)

    pid = publish_mod.next_id()
    stem = publish_mod.puzzle_stem(pid)
    image_files, theme = _crop_and_theme(body.image_url, body.box, body.accent, stem)
    credits_images_mod.finalize_rung_images(body.rungs, stem, _credit_saver())

    res = publish_mod.publish(movie, body.rungs, theme=theme,
                              image_files=image_files, date=body.date, puzzle_id=pid)
    res["theme"] = theme
    return res


class Update(BaseModel):
    puzzle_id: int
    rungs: list
    date: str
    accent: str | None = None
    image_url: str | None = None    # supplied only when re-cropping the frame
    box: list[float] | None = None


@app.post("/api/update")
def api_update(body: Update):
    """Re-author an existing puzzle in place: rewrite its file, optionally re-crop
    the frame (regenerating tiers + theme), re-save its credit images, and move its
    manifest entry to the (possibly new) date. Does not touch the ledger."""
    k = _key()
    pid = body.puzzle_id
    film_id = _film_id_for_puzzle(pid)
    if not film_id:
        raise HTTPException(404, f"no ledger entry for puzzle {pid}")
    stem = publish_mod.puzzle_stem(pid)
    path = os.path.join(publish_mod.PUZZLES_DIR, f"{stem}.json")
    if not os.path.isfile(path):
        raise HTTPException(404, f"puzzle file {pid} not found")
    with open(path, encoding="utf-8") as fh:
        existing = json.load(fh)
    movie = tmdb.movie_with_credits(film_id, k)

    theme = existing.get("theme")
    image_files = existing.get("images", [])
    if body.image_url and body.box:          # re-crop only if a new still + box came in
        image_files, theme = _crop_and_theme(body.image_url, body.box, body.accent, stem)
    elif body.accent:                        # accent-only override, keep the frame
        theme = {**(theme or {}), "accent": body.accent}

    credits_images_mod.finalize_rung_images(body.rungs, stem, _credit_saver())

    puzzle = publish_mod.assemble_puzzle(movie, body.rungs, puzzle_id=pid,
                                         date=body.date, theme=theme, image_files=image_files)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(puzzle, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    # upsert is keyed by id+date, so changing the date moves the entry cleanly.
    man = manifest_mod.upsert(manifest_mod.load(), manifest_mod.make_entry(
        date=body.date, id=pid, file=f"{stem}.json",
        title=movie.get("title"), accent=(theme or {}).get("accent")))
    manifest_mod.save(man)
    return {"id": pid, "file": f"{stem}.json", "date": body.date, "theme": theme, "updated": True}
