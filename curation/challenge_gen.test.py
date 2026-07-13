"""Tests for challenge_gen.py's pure core. No network, no key, no disk.
Run: python curation/challenge_gen.test.py"""
import random
import sys

sys.path.insert(0, "curation")
import challenge_gen as cg  # noqa: E402
import graph_extract as gx  # noqa: E402

FAILS = 0


def check(label, got, expected):
    global FAILS
    ok = got == expected
    print(("PASS " if ok else "FAIL ") + label + ("" if ok else f"  got={got!r} expected={expected!r}"))
    if not ok:
        FAILS += 1


# Same tiny world as graph_extract.test.py: F1-{P1,P2}, F2-{P2,P3}, F3-{P3}, F4-{P9}.
FILMS = {1: ("Heat", 1995), 2: ("The Godfather Part II", 1974),
         3: ("Casino", 1995), 4: ("Island", 2020)}
CACHE = {1: [(101, "Al Pacino", 90), (102, "Robert De Niro", 95)],
         2: [(102, "Robert De Niro", 95), (103, "Joe Pesci", 40)],
         3: [(103, "Joe Pesci", 40)],
         4: [(109, "Loner", 1)]}
G = gx.build_graph(FILMS, CACHE)

check("bfs_path: alternating shortest path", cg.bfs_path(G, 1, 3), [1, 102, 2, 103, 3])
check("bfs_path: adjacent films", cg.bfs_path(G, 1, 2), [1, 102, 2])
check("bfs_path: disconnected -> None", cg.bfs_path(G, 1, 4), None)

P = cg.pick_pair(G, random.Random(1), [1, 2, 3], par=2)
check("pick_pair: finds the exact-par pair", (P[0], P[1]) in {(1, 3), (3, 1)}, True)

CH = cg.build_challenge(G, 1, 1, 3, par=2)
check("challenge: endpoints labeled", (CH["start"]["title"], CH["goal"]["title"]), ("Heat", "Casino"))
check("challenge: par recorded", CH["par"], 2)
check("challenge: subgraph contains the solution spine",
      all(str(f) in CH["films"] for f in (1, 2, 3)) and all(str(p) in CH["people"] for p in (102, 103)), True)
check("solution labels alternate person/film between endpoints",
      cg.solution_labels(G, [1, 102, 2, 103, 3]),
      ["Robert De Niro", "The Godfather Part II", "Joe Pesci"])

# build_challenge must raise if the subgraph cannot honor the par (force it by
# asking for a par the graph can't deliver between these endpoints)
try:
    cg.build_challenge(G, 1, 1, 4, par=2)   # film 4 is disconnected
    check("challenge: broken par raises", "no exception", "AssertionError")
except AssertionError:
    check("challenge: broken par raises", "AssertionError", "AssertionError")

print(f"\n{9 - FAILS} passed, {FAILS} failed")
sys.exit(1 if FAILS else 0)
