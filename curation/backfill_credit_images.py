"""Backfill headshot credit images onto already-published puzzles.

Every credit rung (cast + crew) gets the person's TMDB profile headshot — cast
character stills on TMDB are too sparse to rely on, so headshots are the uniform
default (a curator can still override a specific rung with an in-character still
via the crop tool's picker). For each puzzle it maps back to its TMDB film via
the ledger, fetches credits, and (reusing credits_images) saves each person's
headshot as docs/puzzles/images/NNN-rK.jpg and sets that rung's image + caption.

Re-runnable and idempotent-ish: it re-derives images from TMDB each time and
rewrites the same NNN-rK.jpg files, so running twice just refreshes them.

Run (needs the repo-root .venv + curation/.env):
  .venv/Scripts/python curation/backfill_credit_images.py             # all puzzles
  .venv/Scripts/python curation/backfill_credit_images.py --ids 4 5   # just some
  .venv/Scripts/python curation/backfill_credit_images.py --dry-run   # no writes
"""
import argparse
import io
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import credits_images as ci  # noqa: E402
import ledger as ledger_mod  # noqa: E402
import publish as publish_mod  # noqa: E402
import tmdb  # noqa: E402

IMG_DIR = os.path.join(publish_mod.PUZZLES_DIR, "images")


def film_id_for(puzzle_id, led):
    for e in led:
        if e.get("puzzle") == puzzle_id:
            return e.get("id")
    return None


def make_saver(dry_run):
    from PIL import Image

    def save(url, filename):
        if dry_run:
            print(f"      would save {filename}  <-  {url}")
            return
        with urllib.request.urlopen(url, timeout=30) as r:
            im = Image.open(io.BytesIO(r.read())).convert("RGB")
        if im.width > 1000:
            im = im.resize((1000, max(1, round(im.height * 1000 / im.width))))
        os.makedirs(IMG_DIR, exist_ok=True)
        im.save(os.path.join(IMG_DIR, filename), quality=85)
        print(f"      saved  {filename}")

    return save


def backfill_one(puzzle_path, film_id, key, save):
    """Add cast + crew headshots to one puzzle file. Returns (done, missing)."""
    with open(puzzle_path, encoding="utf-8") as fh:
        puzzle = json.load(fh)

    credits = tmdb.movie_with_credits(film_id, key).get("credits", {})
    ci.attach_person_meta(puzzle, credits)   # every credit rung defaults to its headshot

    people = [r for r in puzzle["rungs"] if r.get("role") != "Film"]
    missing = [r["answers"][0] for r in people if not r.get("image_pick")]

    stem = os.path.splitext(os.path.basename(puzzle_path))[0]
    ci.finalize_rung_images(puzzle["rungs"], stem, save)

    done = [(r["role"], r.get("caption"), r["image"])
            for r in puzzle["rungs"] if r.get("image")]
    with open(puzzle_path, "w", encoding="utf-8") as fh:
        json.dump(puzzle, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return done, missing


def _main(argv):
    ap = argparse.ArgumentParser(description="Backfill crew headshots onto puzzles.")
    ap.add_argument("--ids", type=int, nargs="*", help="puzzle ids (default: all)")
    ap.add_argument("--dry-run", action="store_true", help="don't download or write")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    key = tmdb.load_key()
    led = ledger_mod.load()
    save = make_saver(args.dry_run)

    files = sorted(fn for fn in os.listdir(publish_mod.PUZZLES_DIR)
                   if re.match(r"^\d+\.json$", fn))
    total_done = 0
    for fn in files:
        pid = int(fn[:-5])
        if args.ids and pid not in args.ids:
            continue
        film_id = film_id_for(pid, led)
        if not film_id:
            print(f"puzzle {pid}: no ledger entry (skipped)")
            continue
        print(f"puzzle {pid} (TMDB {film_id}):")
        done, missing = backfill_one(
            os.path.join(publish_mod.PUZZLES_DIR, fn), film_id, key, save)
        for role, caption, image in done:
            print(f"   {role:<19} {caption}  ->  {image}")
        if missing:
            print(f"   (no headshot on TMDB for: {', '.join(missing)})")
        total_done += len(done)
    verb = "would write" if args.dry_run else "wrote"
    print(f"\n{verb} {total_done} credit image(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
