"""Tests for decoy selection (the pure core). No network.

Run:  python curation/decoys.test.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decoys import pick_decoys  # noqa: E402

passed = failed = 0


def check(label, got, want):
    global passed, failed
    ok = got == want
    passed, failed = passed + (1 if ok else 0), failed + (0 if ok else 1)
    print(f"{'PASS' if ok else 'FAIL'}  {label}"
          + ("" if ok else f"\n        got:  {got!r}\n        want: {want!r}"))


POOL = ["Christopher Nolan", "Denis Villeneuve", "Denis Villeneuve",
        "Steven Spielberg", "Greta Gerwig"]

# --- excludes the correct answer (case-insensitively), keeps pool order ---
check("answer excluded, order preserved",
      pick_decoys(["denis villeneuve"], POOL, n=3),
      ["Christopher Nolan", "Steven Spielberg", "Greta Gerwig"])

# --- de-dupes the pool ---
check("duplicates collapsed",
      pick_decoys(["Greta Gerwig"], POOL, n=4),
      ["Christopher Nolan", "Denis Villeneuve", "Steven Spielberg"])

# --- respects n ---
check("returns at most n", len(pick_decoys([], POOL, n=2)), 2)

# --- exclude set (e.g. people actually in this film) is filtered out ---
check("exclude set removed",
      pick_decoys([], POOL, n=3, exclude=["Christopher Nolan"]),
      ["Denis Villeneuve", "Steven Spielberg", "Greta Gerwig"])

# --- short pool: return what we can, no error ---
check("pool smaller than n",
      pick_decoys(["a"], ["a", "b"], n=3), ["b"])

# --- empty / blank names are skipped ---
check("blank names skipped",
      pick_decoys([], ["", "  ", "Real Name"], n=3), ["Real Name"])

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
