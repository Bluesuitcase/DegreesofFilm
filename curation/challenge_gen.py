"""Generate Degrees dailies: film pairs at an exact par, against the SHIPPED corpus.

The generator reads docs/graph.json — the same bytes the client plays — so a par
written here is a par the player can actually reach. (Generating from the raw caches
would let pruning or a rebuild quietly shift distances.)

A daily is ~50 bytes: {id, date, start, goal, par} with TMDB film ids. They all live
in docs/challenges.json; the solution chains are written to a gitignored curator file
and never committed, because this repo is public.

    python curation/challenge_gen.py --days 30                 # append 30 dailies
    python curation/challenge_gen.py --days 7 --par 3 --seed 4
    python curation/challenge_gen.py --check                    # re-verify every daily

Pure core (no IO): adjacency / bfs_path / degrees_between / count_routes /
too_similar / pick_pair / next_dates.
"""
import argparse
import datetime as dt
import json
import os
import random
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graph_build as gb  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(os.path.dirname(HERE), "docs")
CORPUS = os.path.join(DOCS, "graph.json")
CHALLENGES = os.path.join(DOCS, "challenges.json")
SOLUTIONS = os.path.join(HERE, "challenge_solutions.json")   # gitignored: spoilers

CHALLENGES_VERSION = 1
DEFAULT_TOP = 900        # endpoints drawn from the N most popular films
MIN_ROUTES = 2           # more than one shortest path = a fair daily, not a needle
TITLE_STOPWORDS = {"the", "a", "an", "of", "and", "part", "ii", "iii", "iv", "2", "3"}

# The weekly difficulty arc (NYT-crossword convention): gentle early week, a real
# reach on the weekend. Without par spread, day 14 feels identical to day 3 —
# monotony, not difficulty, is what kills a daily. Mon..Sun by weekday().
WEEKLY_ARC = {0: 2, 1: 2, 2: 2, 3: 3, 4: 3, 5: 4, 6: 3}


def par_for_date(iso, arc=None):
    """The arc's par for an ISO date (Mon=2 … Sat=4). Pure."""
    arc = arc or WEEKLY_ARC
    return arc[dt.date.fromisoformat(iso).weekday()]


def adjacency(corpus):
    """(film -> [person], person -> [film]) over array indices. Pure."""
    film_people = [gb.decode_deltas(c) for c in corpus["cast"]]
    person_films = [[] for _ in corpus["people"]]
    for f, people in enumerate(film_people):
        for p in people:
            person_films[p].append(f)
    return film_people, person_films


def bfs_path(adj, src, dst, max_degrees=6):
    """Shortest alternating path [("f",src), ("p",x), ("f",y), ..., ("f",dst)] or
    None. Degrees = person steps = (len(path)-1)//2. Pure."""
    film_people, person_films = adj
    if src == dst:
        return [("f", src)]
    parent = {("f", src): None}
    q = deque([(("f", src), 0)])
    while q:
        node, d = q.popleft()
        kind, idx = node
        if kind == "f":
            if d >= max_degrees * 2:
                continue
            for p in film_people[idx]:
                if ("p", p) not in parent:
                    parent[("p", p)] = node
                    q.append((("p", p), d + 1))
        else:
            for f in person_films[idx]:
                if ("f", f) in parent:
                    continue
                parent[("f", f)] = node
                if f == dst:
                    path, cur = [], ("f", f)
                    while cur is not None:
                        path.append(cur)
                        cur = parent[cur]
                    return path[::-1]
                q.append((("f", f), d + 1))
    return None


def degrees_between(adj, src, dst, max_degrees=6):
    """Par: the number of person steps on a shortest chain, or None. Pure."""
    path = bfs_path(adj, src, dst, max_degrees)
    return None if path is None else (len(path) - 1) // 2


def count_routes(adj, src, dst, par, cap=50):
    """How many DISTINCT people close a par chain (a fairness proxy: one single
    connector is a needle, several is a game). Counts closers at the final step. Pure."""
    film_people, person_films = adj
    if par < 1:
        return 0
    reach = {src}
    for _ in range(par - 1):
        nxt = set()
        for f in reach:
            for p in film_people[f]:
                for f2 in person_films[p]:
                    if f2 != dst:
                        nxt.add(f2)
        reach = nxt
        if not reach:
            return 0
    goal_cast = set(film_people[dst])
    closers = set()
    for f in reach:
        for p in film_people[f]:
            if p in goal_cast:
                closers.add(p)
                if len(closers) >= cap:
                    return cap
    return len(closers)


def too_similar(title_a, title_b):
    """Reject sequels/franchise pairs — "Avengers: Infinity War" -> "Avengers: Endgame"
    is a connection nobody has to think about. Pure."""
    def words(t):
        return {w for w in "".join(ch.lower() if ch.isalnum() else " " for ch in t).split()
                if w not in TITLE_STOPWORDS and len(w) > 2}
    return bool(words(title_a) & words(title_b))


def pick_pair(corpus, adj, rng, par, *, top=DEFAULT_TOP, avoid=(), tries=3000,
              min_routes=MIN_ROUTES):
    """A film pair at EXACTLY `par` degrees, both endpoints among the `top` most
    popular films and neither in `avoid`. Returns (a_idx, b_idx, path) or None.
    Pure given rng."""
    pool = [i for i in range(min(top, len(corpus["films"]))) if i not in set(avoid)]
    if len(pool) < 2:
        return None
    for _ in range(tries):
        a, b = rng.sample(pool, 2)
        if too_similar(corpus["films"][a][0], corpus["films"][b][0]):
            continue
        path = bfs_path(adj, a, b, max_degrees=par)
        if path is None or (len(path) - 1) // 2 != par:
            continue
        if count_routes(adj, a, b, par) < min_routes:
            continue
        return a, b, path
    return None


def next_dates(existing, count, start=None, today=None):
    """The next `count` free ISO dates: the day after the last scheduled daily, or
    today if the schedule has lapsed. Pure."""
    today = today or dt.date.today().isoformat()
    if start:
        cursor = dt.date.fromisoformat(start)
    else:
        latest = max((e["date"] for e in existing), default=None)
        after = (dt.date.fromisoformat(latest) + dt.timedelta(days=1)).isoformat() if latest else today
        cursor = dt.date.fromisoformat(max(after, today))
    taken = {e["date"] for e in existing}
    out = []
    while len(out) < count:
        iso = cursor.isoformat()
        if iso not in taken:
            out.append(iso)
        cursor += dt.timedelta(days=1)
    return out


def _load(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _write(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"))


def _labels(corpus, path):
    return [corpus["people"][i] if kind == "p" else corpus["films"][i][0]
            for kind, i in path]


def _main(argv):
    ap = argparse.ArgumentParser(description="Generate Degrees dailies")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--par", default=None,
                    help="pars to draw from, comma separated; default = the weekly arc "
                         "(Mon-Wed 2, Thu-Fri 3, Sat 4, Sun 3)")
    ap.add_argument("--top", type=int, default=DEFAULT_TOP)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--start", help="first date (YYYY-MM-DD); default = next free day")
    ap.add_argument("--check", action="store_true", help="re-verify every existing daily")
    args = ap.parse_args(argv)

    corpus = _load(CORPUS, None)
    if corpus is None:
        print(f"no corpus at {CORPUS} — run: python curation/graph_build.py", file=sys.stderr)
        return 1
    gb.validate(corpus)
    adj = adjacency(corpus)
    by_id = {tid: i for i, tid in enumerate(corpus["ids"])}
    doc = _load(CHALLENGES, {"v": CHALLENGES_VERSION, "daily": []})
    daily = doc["daily"]

    if args.check:
        bad = 0
        for e in daily:
            a, b = by_id.get(e["start"]), by_id.get(e["goal"])
            if a is None or b is None:
                print(f"FAIL  #{e['id']} {e['date']}: endpoint missing from the corpus")
                bad += 1
                continue
            got = degrees_between(adj, a, b)
            labels_ok = (e.get("from") == corpus["films"][a]
                         and e.get("to") == corpus["films"][b])
            ok = got == e["par"] and labels_ok
            why = "" if ok else (f" but the corpus says {got}" if got != e["par"]
                                 else " — cached titles drifted from the corpus")
            print(f"{'OK  ' if ok else 'FAIL'}  #{e['id']} {e['date']}  "
                  f"{corpus['films'][a][0]} -> {corpus['films'][b][0]}  par {e['par']}{why}")
            bad += 0 if ok else 1
        print(f"\n{len(daily)} dailies, {bad} broken")
        return 1 if bad else 0

    rng = random.Random(args.seed)
    pars = [int(p) for p in args.par.split(",")] if args.par else None
    used = {by_id[e[k]] for e in daily for k in ("start", "goal") if e[k] in by_id}
    dates = next_dates(daily, args.days, start=args.start)
    solutions = _load(SOLUTIONS, {})
    next_id = max((e["id"] for e in daily), default=0) + 1

    for date in dates:
        par = rng.choice(pars) if pars else par_for_date(date)
        picked = pick_pair(corpus, adj, rng, par, top=args.top, avoid=used)
        # A high-par day the popular pool can't satisfy steps down rather than
        # aborting the whole run — a par-3 Saturday beats no Saturday.
        while picked is None and not pars and par > 2:
            par -= 1
            print(f"  {date}: no par-{par + 1} pair in the pool — stepping down to {par}",
                  file=sys.stderr)
            picked = pick_pair(corpus, adj, rng, par, top=args.top, avoid=used)
        if picked is None:
            print(f"could not find a par-{par} pair for {date} "
                  f"(try a larger --top or fewer --days)", file=sys.stderr)
            return 1
        a, b, path = picked
        assert degrees_between(adj, a, b) == par, "par assertion failed"
        used.update({a, b})
        # The two titles ride along so home/archive render without the 188 KB corpus;
        # the ids stay authoritative (--check re-derives par and labels from them).
        entry = {"id": next_id, "date": date, "start": corpus["ids"][a],
                 "goal": corpus["ids"][b], "par": par,
                 "from": corpus["films"][a], "to": corpus["films"][b]}
        daily.append(entry)
        solutions[str(next_id)] = {"date": date, "par": par,
                                   "routes": count_routes(adj, a, b, par),
                                   "chain": _labels(corpus, path)}
        print(f"#{next_id} {date}  par {par}  "
              f"{corpus['films'][a][0]} ({corpus['films'][a][1]}) -> "
              f"{corpus['films'][b][0]} ({corpus['films'][b][1]})")
        next_id += 1

    daily.sort(key=lambda e: e["date"])
    _write(CHALLENGES, {"v": CHALLENGES_VERSION, "daily": daily})
    _write(SOLUTIONS, solutions)
    print(f"\nwrote {CHALLENGES} ({len(daily)} dailies)")
    print(f"solutions (gitignored, spoilers): {SOLUTIONS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
