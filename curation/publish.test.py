"""Tests for the publish step. Pure assembly + file writes, no network/Pillow.

Run:  python curation/publish.test.py
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import publish  # noqa: E402

passed = failed = 0


def check(label, got, want):
    global passed, failed
    ok = got == want
    passed, failed = passed + (1 if ok else 0), failed + (0 if ok else 1)
    print(f"{'PASS' if ok else 'FAIL'}  {label}"
          + ("" if ok else f"\n        got:  {got!r}\n        want: {want!r}"))


# --- stem + next_id ---
check("stem zero-pads", publish.puzzle_stem(1), "001")
check("stem keeps width", publish.puzzle_stem(142), "142")

with tempfile.TemporaryDirectory() as d:
    check("empty dir -> id 1", publish.next_id(d), 1)
    open(os.path.join(d, "001.json"), "w").close()
    open(os.path.join(d, "002.json"), "w").close()
    open(os.path.join(d, "notes.txt"), "w").close()   # ignored
    check("scans NNN.json files", publish.next_id(d), 3)
    check("manifest ids counted too",
          publish.next_id(d, manifest=[{"id": 9}]), 10)

# --- assemble shape ---
MOVIE = {"id": 99, "title": "Test Film", "release_date": "2020-05-01"}
RUNGS = [{"role": "Film", "prompt": "Name the film.",
          "answers": ["Test Film"], "decoys": ["A", "B", "C"]}]
puz = publish.assemble_puzzle(MOVIE, RUNGS, puzzle_id=7, date="2026-07-01",
                              theme={"accent": "#abc123"}, image_files=["images/007-1.jpg"])
check("assembled id", puz["id"], 7)
check("assembled date", puz["date"], "2026-07-01")
check("assembled accent", puz["theme"], {"accent": "#abc123"})
check("assembled images", puz["images"], ["images/007-1.jpg"])
check("assembled rungs carry decoys", puz["rungs"][0]["decoys"], ["A", "B", "C"])

# --- full publish into temp dirs ---
with tempfile.TemporaryDirectory() as d:
    pdir = os.path.join(d, "puzzles")
    led = os.path.join(d, "used_films.json")
    man = os.path.join(d, "manifest.json")
    res = publish.publish(MOVIE, RUNGS, theme={"accent": "#abc123"},
                          image_files=["images/001-1.jpg"], date="2026-07-01",
                          puzzles_dir=pdir, ledger_path=led, manifest_path=man)
    check("first publish gets id 1", res["id"], 1)

    with open(res["puzzle_path"], encoding="utf-8") as fh:
        written = json.load(fh)
    check("puzzle file has accent", written["theme"]["accent"], "#abc123")
    check("puzzle file has rungs", written["rungs"], RUNGS)

    with open(led, encoding="utf-8") as fh:
        ledger_data = json.load(fh)
    check("ledger recorded the film id", ledger_data[0]["id"], 99)

    with open(man, encoding="utf-8") as fh:
        manifest_data = json.load(fh)
    check("manifest entry written",
          {k: manifest_data[0][k] for k in ("date", "id", "file", "title")},
          {"date": "2026-07-01", "id": 1, "file": "001.json", "title": "Test Film"})

    # republishing the same film: ledger dedupes, next id advances past 001.json
    res2 = publish.publish(MOVIE, RUNGS, theme={"accent": "#abc123"},
                           image_files=["images/002-1.jpg"], date="2026-07-02",
                           puzzles_dir=pdir, ledger_path=led, manifest_path=man)
    check("second publish gets id 2", res2["id"], 2)
    with open(led, encoding="utf-8") as fh:
        check("ledger still has one entry (deduped by film id)",
              len(json.load(fh)), 1)

# --- next_date: queues onto the day after the latest puzzle (no collisions) ---
check("next_date empty -> today", publish.next_date([], today="2026-07-05"), "2026-07-05")
check("next_date -> latest + 1 day",
      publish.next_date([{"date": "2026-06-28"}, {"date": "2026-07-02"}], today="2026-06-01"),
      "2026-07-03")
check("next_date ignores undated entries",
      publish.next_date([{"id": 1}, {"date": "2026-06-30"}], today="2026-06-01"), "2026-07-01")

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
