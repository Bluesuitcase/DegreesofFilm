"""Curation crop tool — FastAPI backend + a localhost crop page.

PRIVATE: holds the TMDB key, runs on localhost only, and writes finished static
files into docs/. It is a thin layer over the framework-free modules (discover,
build_rungs, decoys, images, publish). Run from the repo root:

    .venv/Scripts/python -m uvicorn app:app --reload --app-dir curation --port 8001

(or use the "curation" entry in .claude/launch.json).
"""
import io
import os
import urllib.request

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import build_rungs
import decoys as decoys_mod
import discover as discover_mod
import images as images_mod
import manifest as manifest_mod
import publish as publish_mod
import tmdb
from ledger import load as load_ledger, used_ids

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_BASE = "https://image.tmdb.org/t/p/original"

app = FastAPI(title="Degrees of Film — curation")


def _key():
    try:
        return tmdb.load_key()
    except SystemExit as e:
        raise HTTPException(500, str(e))


@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(HERE, "static", "index.html"), encoding="utf-8") as fh:
        return fh.read()


@app.get("/api/next-date")
def api_next_date():
    # Default the crop UI's date to the next free day so publishes don't collide.
    return {"date": publish_mod.next_date(manifest_mod.load())}


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


@app.get("/api/film/{film_id}")
def api_film(film_id: int):
    k = _key()
    movie = tmdb.movie_with_credits(film_id, k)
    credits = movie.get("credits", {})
    puzzle = build_rungs.build_puzzle(movie, credits, puzzle_id=film_id, max_cast=6)
    decoys_mod.attach_decoys(puzzle, film_id, credits, k)
    imgs = tmdb.get(f"/movie/{film_id}/images", k)
    stills = [IMG_BASE + b["file_path"] for b in imgs.get("backdrops", [])[:12]
              if b.get("file_path")]
    if movie.get("poster_path"):
        stills.append(IMG_BASE + movie["poster_path"])
    return {"id": film_id, "title": movie.get("title"),
            "release_date": movie.get("release_date"),
            "stills": stills, "rungs": puzzle["rungs"]}


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
    if len(body.box) != 4:
        raise HTTPException(400, "box must be [x, y, w, h]")

    k = _key()
    movie = tmdb.movie_with_credits(body.film_id, k)

    from PIL import Image
    with urllib.request.urlopen(body.image_url, timeout=30) as resp:
        src = Image.open(io.BytesIO(resp.read())).convert("RGB")

    x, y, w, h = body.box
    box = (round(x * src.width), round(y * src.height),
           round((x + w) * src.width), round((y + h) * src.height))
    tiers = images_mod.crop_tiers(src, box)
    accent = body.accent or images_mod.sample_accent(tiers[0])

    pid = publish_mod.next_id()
    stem = publish_mod.puzzle_stem(pid)
    names = images_mod.save_tiers(tiers, os.path.join(publish_mod.PUZZLES_DIR, "images"), stem)
    res = publish_mod.publish(movie, body.rungs, accent=accent,
                              image_files=[f"images/{n}" for n in names],
                              date=body.date, puzzle_id=pid)
    res["accent"] = accent
    return res
