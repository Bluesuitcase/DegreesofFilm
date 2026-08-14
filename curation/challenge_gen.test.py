"""Tests for the Degrees daily generator. Pure logic, no network, no corpus file.

Run:  python curation/challenge_gen.test.py
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import challenge_gen as cg  # noqa: E402

passed = failed = 0


def check(label, got, want):
    global passed, failed
    ok = got == want
    passed, failed = passed + (1 if ok else 0), failed + (0 if ok else 1)
    print(f"{'PASS' if ok else 'FAIL'}  {label}"
          + ("" if ok else f"\n        got:  {got!r}\n        want: {want!r}"))


# Heat --De Niro--> Casino --Pesci--> Goodfellas, and the parallel
# Heat --Kilmer--> Dead End --Liotta--> Goodfellas: two par-2 routes.
# "Island" hangs off the graph entirely (unreachable), "Heat 2" is a sequel trap.
CORPUS = {
    "v": 1,
    "ids": [1, 2, 3, 4, 5, 6],
    "films": [["Heat", 1995], ["Casino", 1995], ["Goodfellas", 1990],
              ["The Godfather Part II", 1974], ["Dead End Movie", 2001], ["Island", 2015]],
    "people": ["Al Pacino", "Robert De Niro", "Joe Pesci", "Val Kilmer", "Ray Liotta",
               "Solo A", "Solo B"],
    "cast": ["0,1,2", "1,1", "2,2", "0,1", "3,1", "5,1"],
}
ADJ = cg.adjacency(CORPUS)

# --- adjacency, both directions ---
check("film -> people decoded", ADJ[0][0], [0, 1, 3])
check("person -> films inverted", ADJ[1][1], [0, 1, 3])

# --- shortest chains ---
path = cg.bfs_path(ADJ, 0, 2)
check("path alternates film/person and ends at the goal",
      [k for k, _ in path], ["f", "p", "f", "p", "f"])
check("par is the person-step count", cg.degrees_between(ADJ, 0, 2), 2)
check("adjacent films are one degree apart", cg.degrees_between(ADJ, 0, 1), 1)
check("a film is zero degrees from itself", cg.degrees_between(ADJ, 0, 0), 0)
check("unreachable pair -> None", cg.degrees_between(ADJ, 0, 5), None)
check("depth cap refuses a longer answer", cg.bfs_path(ADJ, 0, 2, max_degrees=1), None)

# --- fairness proxy: how many distinct people can close the chain ---
check("both par-2 closers found", cg.count_routes(ADJ, 0, 2, 2), 2)
check("one-degree pair counts its shared credits", cg.count_routes(ADJ, 0, 1, 1), 1)

# --- franchise filter ---
check("sequel pair rejected",
      cg.too_similar("Avengers: Infinity War", "Avengers: Endgame"), True)
check("numbered sequel rejected",
      cg.too_similar("The Godfather", "The Godfather Part II"), True)
check("unrelated pair kept", cg.too_similar("Heat", "Casino"), False)
check("shared stopwords are not similarity",
      cg.too_similar("The Ring", "The Others"), False)

# --- pair picking ---
rng = random.Random(11)
got = cg.pick_pair(CORPUS, ADJ, rng, 2, top=6)
check("picks a pair at exactly the requested par",
      cg.degrees_between(ADJ, got[0], got[1]), 2)
check("endpoints differ", got[0] != got[1], True)
check("avoid list is honoured",
      cg.pick_pair(CORPUS, ADJ, random.Random(3), 2, top=6, avoid=(0, 1, 3, 4, 5)), None)
check("a par nothing satisfies -> None",
      cg.pick_pair(CORPUS, ADJ, random.Random(3), 5, top=6), None)
check("needle pairs filtered out by min_routes",
      cg.pick_pair(CORPUS, ADJ, random.Random(3), 2, top=6, min_routes=99), None)

# --- scheduling ---
check("empty schedule starts today",
      cg.next_dates([], 3, today="2026-08-11"),
      ["2026-08-11", "2026-08-12", "2026-08-13"])
check("continues the day after the last daily",
      cg.next_dates([{"date": "2026-08-20"}], 2, today="2026-08-11"),
      ["2026-08-21", "2026-08-22"])
check("a lapsed schedule resumes today, never in the past",
      cg.next_dates([{"date": "2026-07-01"}], 1, today="2026-08-11"), ["2026-08-11"])
check("explicit start skips days already taken",
      cg.next_dates([{"date": "2026-08-11"}, {"date": "2026-08-13"}], 2, start="2026-08-11"),
      ["2026-08-12", "2026-08-14"])

print(f"\n{passed} passed, {failed} failed")
raise SystemExit(1 if failed else 0)
