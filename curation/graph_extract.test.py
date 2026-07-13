"""Tests for graph_extract.py's pure core. No network, no key.
Run: python curation/graph_extract.test.py"""
import sys

sys.path.insert(0, "curation")
import graph_extract as gx  # noqa: E402

FAILS = 0


def check(label, got, expected):
    global FAILS
    ok = got == expected
    print(("PASS " if ok else "FAIL ") + label + ("" if ok else f"  got={got!r} expected={expected!r}"))
    if not ok:
        FAILS += 1


# Tiny world: F1(Heat)-{P1,P2}, F2(Godfather II)-{P2,P3}, F3(Casino)-{P3},
# F4(Island)-{P9} (disconnected). Chain F1->P2->F2->P3->F3.
FILMS = {1: ("Heat", 1995), 2: ("The Godfather Part II", 1974),
         3: ("Casino", 1995), 4: ("Island", 2020), 5: ("Orphan Meta", 1999)}
CACHE = {1: [(101, "Al Pacino", 90), (102, "Robert De Niro", 95)],
         2: [(102, "Robert De Niro", 95), (103, "Joe Pesci", 40)],
         3: [(103, "Joe Pesci", 40)],
         4: [(109, "Loner", 1)],
         9: [(110, "Ghost", 1)]}          # film 9 has no metadata -> dropped

G = gx.build_graph(FILMS, CACHE)
check("build: films joined with metadata only", sorted(G["film_people"]), [1, 2, 3, 4])
check("build: person->films inverted", sorted(G["person_films"][102]), [1, 2])
check("build: labels kept", (G["films"][1], G["person_names"][103]), (("Heat", 1995), "Joe Pesci"))

check("bfs: same film = 0", gx.bfs_dist(G, 1, 1), 0)
check("bfs: one shared person = 2 edges (1 degree)", gx.bfs_dist(G, 1, 2), 2)
check("bfs: two-bridge chain = 4 edges (2 degrees)", gx.bfs_dist(G, 1, 3), 4)
check("bfs: disconnected -> None", gx.bfs_dist(G, 1, 4), None)

f1, p1 = gx.neighborhood(G, 1, 1)
check("neighborhood k=1: film + its people only", (sorted(f1), sorted(p1)), ([1], [101, 102]))
f2, p2 = gx.neighborhood(G, 1, 2)
check("neighborhood k=2: reaches films one bridge away", sorted(f2), [1, 2])

SUB = gx.subgraph_json(G, {1, 2}, {102})
check("subgraph: only edges inside the node set",
      sorted(SUB["edges"]), [[1, 102], [2, 102]])
check("subgraph: labels serialized compactly",
      (SUB["films"]["1"], SUB["people"]["102"]), (["Heat", 1995], "Robert De Niro"))

print(f"\n{11 - FAILS} passed, {FAILS} failed")
sys.exit(1 if FAILS else 0)
