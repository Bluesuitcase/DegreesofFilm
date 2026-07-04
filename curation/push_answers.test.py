"""Tests for the /match answers artifact (v3 Phase 1). Pure file ops, no network.

Run:  python curation/push_answers.test.py
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cipher  # noqa: E402
import push_answers  # noqa: E402
import backfill_answers  # noqa: E402

passed = failed = 0


def check(label, got, want):
    global passed, failed
    ok = got == want
    passed, failed = passed + (1 if ok else 0), failed + (0 if ok else 1)
    print(f"{'PASS' if ok else 'FAIL'}  {label}"
          + ("" if ok else f"\n        got:  {got!r}\n        want: {want!r}"))


RUNGS = [
    {"role": "Film", "prompt": "Name the film.", "answers": ["Test Film", "Le Film"],
     "decoys": ["A", "B"], "image": "images/007-r1.jpg", "caption": "x"},
    {"role": "Cast", "answers": ["Jane Doe"]},
]

# --- payload shape: answers only, ladder order, nothing else ---
p = push_answers.answers_payload(RUNGS)
check("payload keeps every rung in order",
      p, {"rungs": [{"answers": ["Test Film", "Le Film"]}, {"answers": ["Jane Doe"]}]})
check("payload strips decoys/images/captions",
      any(k in p["rungs"][0] for k in ("decoys", "image", "caption", "prompt")), False)
check("payload survives empty rungs", push_answers.answers_payload(None), {"rungs": []})
check("payload tolerates a rung without answers",
      push_answers.answers_payload([{"role": "x"}]), {"rungs": [{"answers": []}]})

# --- bulk entry: wrangler `kv bulk put` shape (value is a JSON STRING) ---
e = push_answers.bulk_entry(7, RUNGS)
check("bulk key", e["key"], "answers:7")
check("bulk value is a string", isinstance(e["value"], str), True)
check("bulk value round-trips", json.loads(e["value"]), p)

# --- upsert: replace same key, append new ---
entries = [push_answers.bulk_entry(1, RUNGS), push_answers.bulk_entry(2, RUNGS)]
updated = push_answers.upsert_bulk(entries, push_answers.bulk_entry(1, [{"answers": ["New"]}]))
check("upsert keeps one entry per key", sorted(x["key"] for x in updated),
      ["answers:1", "answers:2"])
check("upsert replaced the value",
      json.loads([x for x in updated if x["key"] == "answers:1"][0]["value"]),
      {"rungs": [{"answers": ["New"]}]})
check("upsert appends unseen keys",
      len(push_answers.upsert_bulk(entries, push_answers.bulk_entry(3, RUNGS))), 3)
check("upsert does not mutate its input", len(entries), 2)

# --- file sink: load/save/upsert against a temp file ---
with tempfile.TemporaryDirectory() as d:
    path = os.path.join(d, "server", "answers-bulk.json")
    check("load of a missing file -> []", push_answers.load_bulk(path), [])
    sink = push_answers.file_sink(path)
    sink(7, RUNGS)
    sink(8, [{"answers": ["Other"]}])
    sink(7, [{"answers": ["Edited"]}])          # re-publish upserts, no dupe
    on_disk = push_answers.load_bulk(path)
    check("sink wrote both puzzles, deduped", sorted(x["key"] for x in on_disk),
          ["answers:7", "answers:8"])
    check("sink upserted the edit",
          json.loads([x for x in on_disk if x["key"] == "answers:7"][0]["value"]),
          {"rungs": [{"answers": ["Edited"]}]})

# --- backfill: manifest + obfuscated puzzle files -> decoded bulk entries ---
with tempfile.TemporaryDirectory() as d:
    puzzle = {"id": 4, "rungs": cipher.encode_rungs(RUNGS)}
    with open(os.path.join(d, "004.json"), "w", encoding="utf-8") as fh:
        json.dump(puzzle, fh)
    man = [{"id": 4, "file": "004.json"},
           {"id": 9, "file": "009.json"}]       # missing file -> skipped, not fatal
    entries = backfill_answers.build_entries(man, d)
    check("backfill built one entry (missing file skipped)", len(entries), 1)
    check("backfill decoded the obfuscated answers",
          json.loads(entries[0]["value"]),
          {"rungs": [{"answers": ["Test Film", "Le Film"]}, {"answers": ["Jane Doe"]}]})
    check("backfill keys by puzzle id", entries[0]["key"], "answers:4")

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
