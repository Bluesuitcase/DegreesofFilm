"""Tests for the manifest writer. Pure JSON-list ops, no network.

Run:  python curation/manifest.test.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import manifest  # noqa: E402

passed = failed = 0


def check(label, got, want):
    global passed, failed
    ok = got == want
    passed, failed = passed + (1 if ok else 0), failed + (0 if ok else 1)
    print(f"{'PASS' if ok else 'FAIL'}  {label}"
          + ("" if ok else f"\n        got:  {got!r}\n        want: {want!r}"))


# --- missing file -> [] ---
check("missing file -> []",
      manifest.load(os.path.join(tempfile.gettempdir(), "no_manifest_here.json")), [])

# --- make_entry shape ---
e1 = manifest.make_entry(date="2026-06-25", id=1, file="001.json",
                         title="No Country for Old Men", accent="#c98a3d")
check("entry has the five fields", sorted(e1), sorted(manifest.FIELDS))

# --- upsert appends and keeps date order ---
m = []
m = manifest.upsert(m, manifest.make_entry(date="2026-06-26", id=2, file="002.json", title="B"))
m = manifest.upsert(m, manifest.make_entry(date="2026-06-25", id=1, file="001.json", title="A"))
check("sorted by date ascending", [e["date"] for e in m], ["2026-06-25", "2026-06-26"])

# --- upsert replaces same-date entry (one puzzle per day) ---
m = manifest.upsert(m, manifest.make_entry(date="2026-06-25", id=1,
                                           file="001.json", title="A (fixed)", accent="#abc123"))
check("same date replaced, not duplicated", len(m), 2)
check("replacement won", next(e for e in m if e["date"] == "2026-06-25")["title"], "A (fixed)")

# --- upsert moves a puzzle to a new date without leaving a stale entry (reschedule) ---
r = [manifest.make_entry(date="2026-06-25", id=1, file="001.json", title="A"),
     manifest.make_entry(date="2026-06-26", id=2, file="002.json", title="B")]
r = manifest.upsert(r, manifest.make_entry(date="2026-06-28", id=1, file="001.json", title="A"))
check("reschedule drops the old-date entry for that id", len(r), 2)
check("puzzle 1 now lives on the new date only",
      sorted((e["id"], e["date"]) for e in r), [(1, "2026-06-28"), (2, "2026-06-26")])

# --- clear_scheduled: drop strictly-future entries, keep today + past ---
SCHED = [
    manifest.make_entry(date="2026-06-30", id=1, file="001.json", title="Past"),
    manifest.make_entry(date="2026-07-02", id=2, file="002.json", title="Today"),
    manifest.make_entry(date="2026-07-03", id=3, file="003.json", title="Future A"),
    manifest.make_entry(date="2026-07-10", id=4, file="004.json", title="Future B"),
]
kept, removed = manifest.clear_scheduled(SCHED, "2026-07-02")
check("clear keeps today + past", [e["id"] for e in kept], [1, 2])
check("clear removes strictly-future entries", [e["id"] for e in removed], [3, 4])
check("clear on an empty manifest is a no-op", manifest.clear_scheduled([], "2026-07-02"), ([], []))
check("clear when nothing is scheduled ahead removes nothing",
      manifest.clear_scheduled(SCHED[:2], "2026-07-02"), (SCHED[:2], []))

# --- a date is required ---
raised = False
try:
    manifest.upsert(m, {"id": 9, "file": "x.json", "title": "no date"})
except ValueError:
    raised = True
check("upsert without date raises", raised, True)

# --- save + reload round-trips ---
with tempfile.TemporaryDirectory() as d:
    path = os.path.join(d, "sub", "manifest.json")   # save makes parent dirs
    manifest.save(m, path)
    check("round-trip equals", manifest.load(path), m)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
