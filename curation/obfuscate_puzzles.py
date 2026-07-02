"""One-off (but re-runnable) migration: obfuscate the answers already published.

v1 shipped puzzle files + the manifest with plaintext answers/titles. This walks
every docs/puzzles/NNN.json and the manifest, running the shared cipher over the
rung answers/captions and the manifest titles. It's idempotent — the cipher's
sentinel prefix means already-encoded strings are left alone — so re-running (e.g.
after adding a puzzle by hand) is safe and only touches what's still plaintext.

Going forward the crop tool encodes on publish/update automatically; this is just
to migrate what already exists.

Run (no network / key needed):
  python curation/obfuscate_puzzles.py            # encode all puzzle files + manifest
  python curation/obfuscate_puzzles.py --dry-run  # report what would change, write nothing
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cipher  # noqa: E402
import manifest as manifest_mod  # noqa: E402
import publish as publish_mod  # noqa: E402


def _plaintext_answers(rungs):
    """The rung answers/captions that are still plaintext (no sentinel) — i.e. what
    a migration would newly encode. Used for reporting."""
    hits = []
    for r in rungs or []:
        for a in (r.get("answers") or []):
            if isinstance(a, str) and not a.startswith(cipher.SENTINEL):
                hits.append(a)
        cap = r.get("caption")
        if isinstance(cap, str) and cap and not cap.startswith(cipher.SENTINEL):
            hits.append(cap)
    return hits


def migrate_puzzle(path, dry_run):
    with open(path, encoding="utf-8") as fh:
        puzzle = json.load(fh)
    newly = _plaintext_answers(puzzle.get("rungs", []))
    if not newly:
        return 0
    if not dry_run:
        puzzle["rungs"] = cipher.encode_rungs(puzzle["rungs"])
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(puzzle, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    return len(newly)


def migrate_manifest(dry_run):
    man = manifest_mod.load()
    newly = [e.get("title") for e in man
             if isinstance(e.get("title"), str)
             and not e["title"].startswith(cipher.SENTINEL)]
    if newly and not dry_run:
        for e in man:
            e["title"] = cipher.obfuscate(e.get("title"))
        manifest_mod.save(man)
    return newly


def _main(argv):
    ap = argparse.ArgumentParser(description="Obfuscate already-published answers.")
    ap.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    verb = "would encode" if args.dry_run else "encoded"
    total = 0
    files = sorted(fn for fn in os.listdir(publish_mod.PUZZLES_DIR)
                   if re.match(r"^\d+\.json$", fn))
    for fn in files:
        n = migrate_puzzle(os.path.join(publish_mod.PUZZLES_DIR, fn), args.dry_run)
        total += n
        print(f"  {fn}: {verb} {n} answer/caption string(s)"
              + ("" if n else "  (already obfuscated)"))

    titles = migrate_manifest(args.dry_run)
    print(f"  manifest.json: {verb} {len(titles)} title(s)"
          + (f"  ({', '.join(titles)})" if titles else "  (already obfuscated)"))

    print(f"\n{verb} {total} puzzle string(s) across {len(files)} file(s)"
          f" + {len(titles)} manifest title(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
