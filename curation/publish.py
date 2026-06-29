"""Publish step: assemble the final puzzle file and record it.

Once a curator approves, this writes docs/puzzles/NNN.json, appends the
used-films ledger, and upserts the daily manifest. (The tier images are written
by images.save_tiers separately.) Assembly + record-keeping are pure/file ops,
so they unit-test against temp dirs — no network, no Pillow.
"""
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


def assemble_puzzle(movie, rungs, *, puzzle_id, date, accent, image_files):
    """The puzzle JSON: id, date, theme.accent, images[], rungs[] (with decoys)."""
    puzzle = {"id": puzzle_id}
    if date:
        puzzle["date"] = date
    if accent:
        puzzle["theme"] = {"accent": accent}
    puzzle["images"] = list(image_files)
    puzzle["rungs"] = rungs
    return puzzle


def publish(movie, rungs, *, accent, image_files, date,
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
                             accent=accent, image_files=image_files)
    os.makedirs(puzzles_dir, exist_ok=True)
    with open(os.path.join(puzzles_dir, file), "w", encoding="utf-8") as fh:
        json.dump(puzzle, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    year = (movie.get("release_date") or "")[:4] or None
    ledger_mod.add(led, {"id": movie["id"], "title": movie.get("title"),
                         "year": year, "puzzle": pid})
    ledger_mod.save(led, ledger_path)

    man = manifest_mod.upsert(man, manifest_mod.make_entry(
        date=date, id=pid, file=file, title=movie.get("title"), accent=accent))
    manifest_mod.save(man, manifest_path)

    return {"id": pid, "file": file, "puzzle_path": os.path.join(puzzles_dir, file)}
