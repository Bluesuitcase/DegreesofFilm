"""Publish step: assemble the final puzzle file and record it.

Once a curator approves, this writes docs/puzzles/NNN.json, appends the
used-films ledger, and upserts the daily manifest. (The tier images are written
by images.save_tiers separately.) Assembly + record-keeping are pure/file ops,
so they unit-test against temp dirs — no network, no Pillow.
"""
import datetime
import json
import os
import re

import ledger as ledger_mod
import manifest as manifest_mod

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUZZLES_DIR = os.path.join(ROOT, "docs", "puzzles")


def puzzle_stem(puzzle_id):
    return f"{puzzle_id:03d}"           # 1 -> "001"


def next_id(puzzles_dir=PUZZLES_DIR, manifest=None):
    """Next free puzzle id: 1 + max of existing NNN.json files and manifest ids.
    Scanning the files means we never clobber a hand-authored puzzle (e.g. 001)
    even before it's in the manifest."""
    ids = set()
    if os.path.isdir(puzzles_dir):
        for fn in os.listdir(puzzles_dir):
            m = re.match(r"^(\d+)\.json$", fn)
            if m:
                ids.add(int(m.group(1)))
    if manifest:
        ids.update(e.get("id", 0) for e in manifest)
    return (max(ids) + 1) if ids else 1


def next_date(manifest, today=None):
    """The next free publish date: the day after the latest puzzle in the manifest
    (so back-to-back publishes queue onto distinct days instead of colliding on
    'today'), or today if the manifest is empty. Pure."""
    today = today or datetime.date.today().isoformat()
    dates = [e["date"] for e in manifest if e.get("date")]
    if not dates:
        return today
    return (datetime.date.fromisoformat(max(dates)) + datetime.timedelta(days=1)).isoformat()


def upcoming_schedule(manifest, today=None, days=14):
    """The coming `days` days from today, each flagged filled/empty against the
    manifest — the data behind the 'curate a week ahead' view. Pure.

    Each slot: { date, weekday, is_today, filled, id, title, accent }. Empty slots
    (no puzzle for that date) carry id/title/accent = None."""
    today = today or datetime.date.today().isoformat()
    d0 = datetime.date.fromisoformat(today)
    by_date = {e["date"]: e for e in manifest if e.get("date")}
    slots = []
    for i in range(max(0, days)):
        d = d0 + datetime.timedelta(days=i)
        iso = d.isoformat()
        e = by_date.get(iso)
        slots.append({
            "date": iso,
            "weekday": d.strftime("%a"),
            "is_today": i == 0,
            "filled": e is not None,
            "id": e.get("id") if e else None,
            "title": e.get("title") if e else None,
            "accent": e.get("accent") if e else None,
        })
    return slots


def runway(manifest, today=None):
    """How many consecutive days are stocked starting today, until the first gap.
    0 means today itself has no puzzle. This is the 'days until the daily repeats'
    number the schedule view leads with. Pure."""
    n = 0
    for slot in upcoming_schedule(manifest, today, days=366):
        if not slot["filled"]:
            break
        n += 1
    return n


def assemble_puzzle(movie, rungs, *, puzzle_id, date, theme, image_files):
    """The puzzle JSON: id, date, theme {accent, bg, bg2}, images[], rungs[]."""
    puzzle = {"id": puzzle_id}
    if date:
        puzzle["date"] = date
    if theme:
        puzzle["theme"] = theme
    puzzle["images"] = list(image_files)
    puzzle["rungs"] = rungs
    return puzzle


def publish(movie, rungs, *, theme, image_files, date,
            puzzles_dir=PUZZLES_DIR,
            ledger_path=ledger_mod.DEFAULT_PATH,
            manifest_path=manifest_mod.DEFAULT_PATH,
            puzzle_id=None):
    """Write the puzzle file, append the ledger, upsert the manifest.
    Returns a small summary dict. Image files must already be written."""
    led = ledger_mod.load(ledger_path)
    man = manifest_mod.load(manifest_path)
    pid = puzzle_id or next_id(puzzles_dir, man)
    file = f"{puzzle_stem(pid)}.json"

    puzzle = assemble_puzzle(movie, rungs, puzzle_id=pid, date=date,
                             theme=theme, image_files=image_files)
    os.makedirs(puzzles_dir, exist_ok=True)
    with open(os.path.join(puzzles_dir, file), "w", encoding="utf-8") as fh:
        json.dump(puzzle, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    year = (movie.get("release_date") or "")[:4] or None
    ledger_mod.add(led, {"id": movie["id"], "title": movie.get("title"),
                         "year": year, "puzzle": pid})
    ledger_mod.save(led, ledger_path)

    man = manifest_mod.upsert(man, manifest_mod.make_entry(
        date=date, id=pid, file=file, title=movie.get("title"),
        accent=(theme or {}).get("accent")))
    manifest_mod.save(man, manifest_path)

    return {"id": pid, "file": file, "puzzle_path": os.path.join(puzzles_dir, file)}
