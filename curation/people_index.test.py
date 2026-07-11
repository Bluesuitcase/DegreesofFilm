"""Tests for people_index.py's pure core (build_names / rung_coverage).
No network, no key. Run: python curation/people_index.test.py"""
import sys

sys.path.insert(0, "curation")
import people_index  # noqa: E402

FAILS = 0


def check(label, got, expected):
    global FAILS
    ok = got == expected
    print(("PASS " if ok else "FAIL ") + label + ("" if ok else f"  got={got!r} expected={expected!r}"))
    if not ok:
        FAILS += 1


P = [
    {"id": 1, "name": "Javier Bardem"},
    {"id": 2, "name": "Roger Deakins"},
    {"id": 1, "name": "Javier Bardem"},        # dup id
    {"id": 3, "name": ""},                      # no name
    {"id": 4, "name": "javier bardem"},         # dup name, different id
    {"id": 5, "name": "Carter Burwell"},
]

N = people_index.build_names(P, 10)
check("build: dedupes by id AND name, skips empties", N,
      ["Javier Bardem", "Roger Deakins", "Carter Burwell"])
check("build: truncates to n", people_index.build_names(P, 2), ["Javier Bardem", "Roger Deakins"])
check("build: empty input", people_index.build_names([], 5), [])

RUNGS = [
    {"role": "Film", "answers": ["No Country for Old Men"]},           # rung 0 ignored
    {"role": "Cast", "answers": ["Javier Bardem"]},
    {"role": "Director", "answers": ["Coen brothers", "Joel Coen"]},
    {"role": "Cinematographer", "answers": ["Roger Deakins", "Roger A. Deakins"]},
    {"role": "Production Designer", "answers": ["Jess Gonchor"]},
]
per_role, misses = people_index.rung_coverage([(1, RUNGS)], N + ["Joel Coen"])
check("coverage: film rung excluded", "Film" in per_role, False)
check("coverage: exact-name hit", per_role["Cast"], [1, 1])
check("coverage: ANY answer form counts (Joel Coen covers the Coens)", per_role["Director"], [1, 1])
check("coverage: alternate form matches case-insensitively", per_role["Cinematographer"], [1, 1])
check("coverage: obscure crew missed + reported spoiler-safe (role only)",
      (per_role["Production Designer"], misses), ([0, 1], ["puzzle 1 · Production Designer"]))

print(f"\n{8 - FAILS} passed, {FAILS} failed")
sys.exit(1 if FAILS else 0)
