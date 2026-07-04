"""Tests for the publish step. Pure assembly + file writes, no network/Pillow.

Run:  python curation/publish.test.py
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cipher  # noqa: E402
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
check("assembled rungs carry decoys (plaintext)", puz["rungs"][0]["decoys"], ["A", "B", "C"])
check("assembled rungs obfuscate answers",
      puz["rungs"][0]["answers"][0].startswith(cipher.SENTINEL), True)
check("obfuscated answers decode back to plaintext",
      cipher.deobfuscate(puz["rungs"][0]["answers"][0]), "Test Film")
check("assemble does not mutate the caller's rungs", RUNGS[0]["answers"], ["Test Film"])

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
    check("puzzle file rungs decode back to the input",
          cipher.decode_rungs(written["rungs"]), RUNGS)

    with open(led, encoding="utf-8") as fh:
        ledger_data = json.load(fh)
    check("ledger recorded the film id", ledger_data[0]["id"], 99)

    with open(man, encoding="utf-8") as fh:
        manifest_data = json.load(fh)
    check("manifest entry written (title obfuscated in the file)",
          {**{k: manifest_data[0][k] for k in ("date", "id", "file")},
           "title": cipher.deobfuscate(manifest_data[0]["title"])},
          {"date": "2026-07-01", "id": 1, "file": "001.json", "title": "Test Film"})
    check("manifest title is actually obfuscated on disk",
          manifest_data[0]["title"].startswith(cipher.SENTINEL), True)

    # republishing the same film: ledger dedupes, next id advances past 001.json
    res2 = publish.publish(MOVIE, RUNGS, theme={"accent": "#abc123"},
                           image_files=["images/002-1.jpg"], date="2026-07-02",
                           puzzles_dir=pdir, ledger_path=led, manifest_path=man)
    check("second publish gets id 2", res2["id"], 2)
    with open(led, encoding="utf-8") as fh:
        check("ledger still has one entry (deduped by film id)",
              len(json.load(fh)), 1)

# --- answers_sink (v3 Phase 1): the optional fourth artifact ---
with tempfile.TemporaryDirectory() as d:
    pdir = os.path.join(d, "puzzles")
    led = os.path.join(d, "used_films.json")
    man = os.path.join(d, "manifest.json")
    fed = []
    res = publish.publish(MOVIE, RUNGS, theme=None, image_files=[], date="2026-07-01",
                          puzzles_dir=pdir, ledger_path=led, manifest_path=man,
                          answers_sink=lambda pid, rungs: fed.append((pid, rungs)))
    check("answers_sink fed once", len(fed), 1)
    check("answers_sink gets the puzzle id", fed[0][0], res["id"])
    check("answers_sink gets PLAINTEXT rungs (not obfuscated)",
          fed[0][1][0]["answers"], ["Test Film"])
    # default None = no sink, publish still works (proven by every case above)

# --- next_date: queues onto the day after the latest puzzle (no collisions) ---
check("next_date empty -> today", publish.next_date([], today="2026-07-05"), "2026-07-05")
check("next_date -> latest + 1 day",
      publish.next_date([{"date": "2026-06-28"}, {"date": "2026-07-02"}], today="2026-06-01"),
      "2026-07-03")
check("next_date ignores undated entries",
      publish.next_date([{"id": 1}, {"date": "2026-06-30"}], today="2026-06-01"), "2026-07-01")

# --- upcoming_schedule: the week-ahead view ---
MAN = [
    {"date": "2026-07-01", "id": 4, "title": "The Dark Knight", "accent": "#6d733f"},
    {"date": "2026-07-02", "id": 5, "title": "Harry Potter", "accent": "#73563f"},
    {"date": "2026-07-04", "id": 6, "title": "Toy Story", "accent": "#877b4a"},  # gap on 07-03
]
sched = publish.upcoming_schedule(MAN, today="2026-07-01", days=5)
check("schedule spans the window", [s["date"] for s in sched],
      ["2026-07-01", "2026-07-02", "2026-07-03", "2026-07-04", "2026-07-05"])
check("today flagged only on the first slot",
      [s["is_today"] for s in sched], [True, False, False, False, False])
check("filled/empty tracks the manifest (07-03 is a gap)",
      [s["filled"] for s in sched], [True, True, False, True, False])
check("filled slot carries its puzzle", sched[0]["title"], "The Dark Knight")
check("filled slot carries id + accent",
      (sched[3]["id"], sched[3]["accent"]), (6, "#877b4a"))
check("empty slot is blank", (sched[2]["id"], sched[2]["title"]), (None, None))
check("weekday label present", sched[0]["weekday"], "Wed")   # 2026-07-01 is a Wednesday
check("days=0 -> empty schedule", publish.upcoming_schedule(MAN, today="2026-07-01", days=0), [])

# --- runway: consecutive stocked days from today until the first gap ---
check("runway counts to the first gap (07-01,02 then 03 empty)",
      publish.runway(MAN, today="2026-07-01"), 2)
check("runway 0 when today itself is empty",
      publish.runway(MAN, today="2026-06-30"), 0)
check("runway on a later stocked day past the gap",
      publish.runway(MAN, today="2026-07-04"), 1)
check("runway 0 on empty manifest", publish.runway([], today="2026-07-01"), 0)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
