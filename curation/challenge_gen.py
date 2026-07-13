"""Graph-mode challenge generator (campaign phase G2). Picks a film pair A->B at an
exact target par from the extracted graph, emits a decoy-padded challenge JSON
(subgraph radius sized to the par, so over-par wandering is possible but bounded),
ASSERTS the par survives inside the shipped subgraph, and writes the solution chain
to a separate curator-only spoiler file.

    python curation/challenge_gen.py --par 2 --seed 7 --out CH.json --solution SOL.json
        [--top 1200]   # endpoints drawn from the N most-voted pool films (recognizable)

Pure core: bfs_path / pick_pair / build_challenge. Only the CLI touches disk, and
nothing here touches the network (the graph comes from the G1 caches).
"""
import json
import random
import sys
from collections import deque

import graph_extract as gx


def bfs_path(g, src, dst, max_depth=12):
    """Shortest alternating path [srcFilm, p1, f1, ..., pN, dstFilm] or None. Pure."""
    if src == dst:
        return [src]
    parent = {("f", src): None}
    q = deque([("f", src, 0)])
    while q:
        kind, node, d = q.popleft()
        if d >= max_depth:
            continue
        if kind == "f":
            for p in g["film_people"].get(node, []):
                if ("p", p) not in parent:
                    parent[("p", p)] = ("f", node)
                    q.append(("p", p, d + 1))
        else:
            for f in g["person_films"].get(node, []):
                if f == dst:
                    path, cur = [dst], ("p", node)
                    while cur:
                        path.append(cur[1])
                        cur = parent[cur]
                    return path[::-1]
                if ("f", f) not in parent:
                    parent[("f", f)] = ("p", node)
                    q.append(("f", f, d + 1))
    return None


def pick_pair(g, rng, ranked_fids, par, tries=4000):
    """A film pair whose shortest distance is EXACTLY 2*par edges, endpoints drawn
    from ranked_fids. Returns (a, b, path) or None. Pure given rng."""
    want = 2 * par
    for _ in range(tries):
        a, b = rng.sample(ranked_fids, 2)
        path = bfs_path(g, a, b, max_depth=want)
        if path and len(path) - 1 == want:
            return a, b, path
    return None


def _subgraph_adjacency(challenge):
    """Rebuild a gx-shaped graph dict from a challenge payload (for assertions). Pure."""
    film_people, person_films = {}, {}
    for f, p in challenge["edges"]:
        film_people.setdefault(f, []).append(p)
        person_films.setdefault(p, []).append(f)
    return {"films": {int(k): tuple(v) for k, v in challenge["films"].items()},
            "film_people": film_people, "person_films": person_films,
            "person_names": {int(k): v for k, v in challenge["people"].items()}}


def _dists_from(g, src_fid, max_depth):
    """Edge-distance maps ({fid: d}, {pid: d}) from a source film. Pure."""
    df, dp = {src_fid: 0}, {}
    q = deque([("f", src_fid, 0)])
    while q:
        kind, node, d = q.popleft()
        if d >= max_depth:
            continue
        if kind == "f":
            for p in g["film_people"].get(node, []):
                if p not in dp:
                    dp[p] = d + 1
                    q.append(("p", p, d + 1))
        else:
            for f in g["person_films"].get(node, []):
                if f not in df:
                    df[f] = d + 1
                    q.append(("f", f, d + 1))
    return df, dp


def build_challenge(g, cid, a, b, par, slack=2, ranked=None, fringe_cap=6):
    """Decoy-padded challenge dict, sized by GEODESIC ELLIPSE, not radius balls
    (measured 2026-07-13: radius balls at par 3 swallow 95% of the small-world
    corpus). Core = every node on a SHORTEST path (dA + dB == 2*par) — always
    kept in full — plus over-par detour nodes (<= 2*par + slack) kept only when
    `ranked` says the film is recognizable (obscure detours are dead bytes).
    Decoy fringe = up to fringe_cap extra people per core film beyond its core
    people (billing order — plausible wrong turns, mostly dead ends inside the
    subgraph). Asserts the subgraph preserves par (raises if it ever breaks). Pure."""
    exact, budget = 2 * par, 2 * par + slack
    daf, dap = _dists_from(g, a, budget)
    dbf, dbp = _dists_from(g, b, budget)

    def keep_film(f, total):
        return total <= exact or (total <= budget and (ranked is None or f in ranked))

    core_f = {f for f, d in daf.items() if f in dbf and keep_film(f, d + dbf[f])}
    films = core_f | {a, b}
    core_p = {p for p, d in dap.items() if p in dbp and d + dbp[p] <= budget
              and any(f in films for f in g["person_films"].get(p, []))}
    people = set(core_p)
    for f in films:                       # capped decoy fringe, billing order
        extra = 0
        for p in g["film_people"].get(f, []):
            if p in people:
                continue
            if extra >= fringe_cap:
                break
            people.add(p)
            extra += 1
    sub = gx.subgraph_json(g, films, people)
    ta, tb = g["films"][a], g["films"][b]
    ch = {"id": cid,
          "start": {"id": a, "title": ta[0], "year": ta[1]},
          "goal": {"id": b, "title": tb[0], "year": tb[1]},
          "par": par, **sub}
    got = gx.bfs_dist(_subgraph_adjacency(ch), a, b, max_depth=2 * par + 2)
    if got != 2 * par:
        raise AssertionError(f"subgraph broke the par: shipped distance {got}, want {2*par}")
    return ch


def solution_labels(g, path):
    """The replayable solution: alternating person/film LABELS between the endpoints.
    (Spoiler — never ships; the curator-only sidecar.) Pure."""
    out = []
    for i, node in enumerate(path[1:-1], start=1):
        out.append(g["person_names"][node] if i % 2 == 1 else g["films"][node][0])
    return out


def _main(argv):
    par = int(argv[argv.index("--par") + 1]) if "--par" in argv else 2
    seed = int(argv[argv.index("--seed") + 1]) if "--seed" in argv else 7
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 1200
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    sol_out = argv[argv.index("--solution") + 1] if "--solution" in argv else None

    films, order = {}, []
    with open(gx.FILMS_CACHE, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            films[rec["id"]] = (rec["title"], rec["year"])
            order.append(rec["id"])
    g = gx.build_graph(films, gx.load_people_cache(gx.PEOPLE_CACHE))
    ranked = [f for f in order if f in g["film_people"]][:top]

    picked = pick_pair(g, random.Random(seed), ranked, par)
    if not picked:
        print(f"no pair found at par {par} within tries — loosen --top or change --seed")
        return 1
    a, b, path = picked
    ch = build_challenge(g, 1, a, b, par, ranked=set(ranked))
    raw = json.dumps(ch, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    import gzip
    print(f"challenge: {ch['start']['title']} ({ch['start']['year']}) -> "
          f"{ch['goal']['title']} ({ch['goal']['year']}), par {par}")
    print(f"payload: {len(ch['films'])} films, {len(ch['people'])} people, "
          f"{len(ch['edges'])} edges — {len(raw)/1024:.0f} KB raw / "
          f"{len(gzip.compress(raw, 9))/1024:.0f} KB gz")
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(ch, fh, ensure_ascii=False, separators=(",", ":"))
        print(f"wrote {out}")
    if sol_out:
        with open(sol_out, "w", encoding="utf-8") as fh:
            json.dump(solution_labels(g, path), fh, ensure_ascii=False)
        print(f"wrote SPOILER solution -> {sol_out}")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
