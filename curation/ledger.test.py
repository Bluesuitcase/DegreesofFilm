"""Tests for the used-films ledger. Pure file I/O, no network.

Run:  python curation/ledger.test.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger  # noqa: E402

passed = failed = 0


def check(label, got, want):
    global passed, failed
    ok = got == want
    passed, failed = passed + (1 if ok else 0), failed + (0 if ok else 1)
    print(f"{'PASS' if ok else 'FAIL'}  {label}"
          + ("" if ok else f"\n        got:  {got!r}\n        want: {want!r}"))


# --- load: missing file is an empty ledger ---
check("missing file -> []", ledger.load(os.path.join(tempfile.gettempdir(),
                                                      "nope_does_not_exist.json")), [])

# --- add + dedupe by id ---
led = []
ledger.add(led, {"id": 1, "title": "Alpha"})
ledger.add(led, {"id": 1, "title": "Alpha again"})   # same id -> ignored
ledger.add(led, {"id": 2, "title": "Bravo"})
check("dedupe keeps first record only", len(led), 2)
check("used_ids", ledger.used_ids(led), {1, 2})
check("is_used true", ledger.is_used(led, 1), True)
check("is_used false", ledger.is_used(led, 99), False)

# --- a record must carry an id ---
raised = False
try:
    ledger.add(led, {"title": "no id"})
except ValueError:
    raised = True
check("add without id raises", raised, True)

# --- save + reload round-trips ---
with tempfile.TemporaryDirectory() as d:
    path = os.path.join(d, "used_films.json")
    ledger.save(led, path)
    check("round-trip equals", ledger.load(path), led)
    # appending across a reload still dedupes
    reloaded = ledger.load(path)
    ledger.add(reloaded, {"id": 2, "title": "Bravo dup"})
    check("reload + add dup is a no-op", len(reloaded), 2)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
