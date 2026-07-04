#!/usr/bin/env python3
"""SPOILER-REVEALING puzzle inspector — CURATOR-ONLY. Decodes and prints every
answer, caption, and the film title of ONE puzzle in plaintext. Never paste its
output anywhere player-visible (commits, PR bodies, public issues, the live site).

READ-ONLY (opens files for reading only; no network, no writes, no curation/.env).

Run from the repo root:
    python .claude/skills/degreesoffilm-diagnostics-and-tooling/scripts/puzzle_report.py 4

Prints: manifest entry (date, decoded title, accent), theme, tier images with
on-disk existence marks, then per rung: index, role, decoded answer(s), decoded
caption, decoy count, image file + existence mark.

Exit codes: 0 = printed, 2 = puzzle id not found.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "curation"))
import cipher  # noqa: E402

PUZZLES_DIR = ROOT / "docs" / "puzzles"

try:  # Unicode names/titles on Windows' cp1252 stdout
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def mark(rel):
    """'[ok]' / '[MISSING]' existence mark for a puzzles-relative image path."""
    return "[ok]" if (PUZZLES_DIR / rel).is_file() else "[MISSING]"


def main():
    ap = argparse.ArgumentParser(
        description="SPOILER-REVEALING (curator-only): decode and print one puzzle "
                    "— answers, captions, and title in PLAINTEXT.")
    ap.add_argument("id", type=int, help="puzzle id, e.g. 4 for docs/puzzles/004.json")
    args = ap.parse_args()
    pid = args.id

    # Manifest entry (may be absent for an orphaned file — report either way).
    manifest_path = PUZZLES_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) \
        if manifest_path.is_file() else []
    entry = next((e for e in manifest if e.get("id") == pid), None)

    path = PUZZLES_DIR / (entry["file"] if entry else f"{pid:03d}.json")
    if not path.is_file():
        print(f"no such puzzle: id {pid} ({path.name} not found"
              f"{' and not in manifest' if not entry else ''})")
        sys.exit(2)
    pz = json.loads(path.read_text(encoding="utf-8"))

    print("=" * 72)
    print(f"SPOILERS BELOW — puzzle {pid} ({path.name}) — curator eyes only")
    print("=" * 72)
    if entry:
        print(f"manifest : date {entry.get('date')}  "
              f"title {cipher.deobfuscate(entry.get('title'))!r}  "
              f"accent {entry.get('accent')}")
    else:
        print("manifest : NOT IN MANIFEST (orphaned file)")
    if pz.get("date") and entry and pz["date"] != entry.get("date"):
        print(f"WARNING  : puzzle file date {pz['date']} != manifest date "
              f"{entry.get('date')}")
    print(f"theme    : {pz.get('theme')}")
    print(f"images   : {len(pz.get('images', []))} tier(s)")
    for rel in pz.get("images", []):
        print(f"           {rel} {mark(rel)}")

    rungs = pz.get("rungs", [])
    print(f"rungs    : {len(rungs)}")
    for i, r in enumerate(rungs, start=1):
        answers = [cipher.deobfuscate(a) for a in r.get("answers", [])]
        caption = cipher.deobfuscate(r.get("caption")) if r.get("caption") else None
        image = r.get("image")
        print(f"\n  r{i:<2} {r.get('role')}")
        print(f"      prompt : {r.get('prompt')}")
        print(f"      answers: {' | '.join(repr(a) for a in answers) or '(NONE)'}")
        if caption:
            print(f"      caption: {caption!r}")
        print(f"      decoys : {len(r.get('decoys', []))}")
        if image:
            print(f"      image  : {image} {mark(image)}")
        else:
            print("      image  : (none — client holds the full frame)")
    sys.exit(0)


if __name__ == "__main__":
    main()
