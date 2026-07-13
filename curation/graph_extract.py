"""Graph-mode Phase G1: extract the film<->person graph from the harvest cache and
measure everything the campaign's G1 gate needs (degreesoffilm-graph-mode-campaign).

The edge list already exists on disk — curation/people_harvest_cache.jsonl (built for
Movie Buff autocomplete) maps every pool-floor film to its top-billed cast + five rung
crew jobs. This module joins it with a films-metadata sweep (id -> title/year, cached
the same way) and answers, with numbers: corpus size, path-length distribution, and
per-challenge subgraph size.

    python curation/graph_extract.py                 # build caches if needed + report
    python curation/graph_extract.py --out PATH      # also write the corpus JSON
    python curation/graph_extract.py --pairs 500     # BFS sample size (default 300)

Pure core (no network): load_cache / build_graph / bfs_dist / neighborhood /
subgraph_json. The CLI is the only thing that touches TMDB (films sweep, cached).
"""
import gzip
import json
import os
import random
import sys
from collections import deque

import discover as discover_mod
import tmdb

HERE = os.path.dirname(os.path.abspath(__file__))
PEOPLE_CACHE = os.path.join(HERE, "people_harvest_cache.jsonl")
FILMS_CACHE = os.path.join(HERE, "films_cache.jsonl")
MAX_PAGES = 500


def load_people_cache(path):
    """{film_id: [(pid, name, popularity), ...]} from the harvest jsonl. Pure-ish (IO only)."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            out[rec["film_id"]] = [tuple(p) for p in rec["people"]]
    return out


def build_graph(films, people_by_film):
    """Adjacency + labels. films: {fid: (title, year)}. Pure.
    Returns dict with film_people/person_films adjacency and label maps; films with
    no metadata (fell out of the pool between sweeps) are dropped for consistency."""
    film_people, person_films, person_names = {}, {}, {}
    for fid, people in people_by_film.items():
        if fid not in films:
            continue
        pids = []
        for pid, name, _pop in people:
            pids.append(pid)
            person_names[pid] = name
            person_films.setdefault(pid, []).append(fid)
        film_people[fid] = pids
    return {"films": {fid: films[fid] for fid in film_people},
            "film_people": film_people, "person_films": person_films,
            "person_names": person_names}


def bfs_dist(g, src_fid, dst_fid, max_depth=12):
    """Shortest edge-distance between two films (film->person->film alternation).
    Returns edge count (2 per film 'degree') or None. Pure."""
    if src_fid == dst_fid:
        return 0
    seen_f, seen_p = {src_fid}, set()
    frontier, dist = [src_fid], 0
    while frontier and dist < max_depth:
        nxt_people = []
        for fid in frontier:
            for pid in g["film_people"].get(fid, []):
                if pid not in seen_p:
                    seen_p.add(pid)
                    nxt_people.append(pid)
        dist += 1
        frontier = []
        for pid in nxt_people:
            for fid in g["person_films"].get(pid, []):
                if fid == dst_fid:
                    return dist + 1
                if fid not in seen_f:
                    seen_f.add(fid)
                    frontier.append(fid)
        dist += 1
    return None


def neighborhood(g, fid, k):
    """Film + person ids within k edges of a film. Pure."""
    films, people = {fid}, set()
    frontier_f, frontier_p = [fid], []
    for depth in range(k):
        if depth % 2 == 0:      # film -> people
            frontier_p = []
            for f in frontier_f:
                for p in g["film_people"].get(f, []):
                    if p not in people:
                        people.add(p)
                        frontier_p.append(p)
        else:                    # person -> films
            frontier_f = []
            for p in frontier_p:
                for f in g["person_films"].get(p, []):
                    if f not in films:
                        films.add(f)
                        frontier_f.append(f)
    return films, people


def subgraph_json(g, film_ids, person_ids):
    """Compact challenge-shaped payload for a node set: labels + edges. Pure."""
    films = {str(f): list(g["films"][f]) for f in film_ids if f in g["films"]}
    people = {str(p): g["person_names"][p] for p in person_ids if p in g["person_names"]}
    edges = [[f, p] for f in film_ids for p in g["film_people"].get(f, []) if p in person_ids]
    return {"films": films, "people": people, "edges": edges}


def _sizes(obj):
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return len(raw), len(gzip.compress(raw, 9))


def _ensure_films_cache(key):
    if os.path.exists(FILMS_CACHE):
        return
    print("films cache missing — one discover sweep…")
    page, total = 1, 1
    with open(FILMS_CACHE, "w", encoding="utf-8") as fh:
        while page <= min(total, MAX_PAGES):
            data = tmdb.get("/discover/movie", key, sort_by="vote_count.desc",
                            include_adult="false", page=page,
                            **{"vote_count.gte": discover_mod.POOL_MIN_VOTES,
                               "vote_average.gte": discover_mod.POOL_MIN_AVG})
            total = data.get("total_pages") or 1
            for m in data.get("results") or []:
                if m.get("id") and m.get("title"):
                    year = (m.get("release_date") or "")[:4]
                    fh.write(json.dumps({"id": m["id"], "title": m["title"],
                                         "year": int(year) if year.isdigit() else 0}) + "\n")
            page += 1


def _main(argv):
    pairs = int(argv[argv.index("--pairs") + 1]) if "--pairs" in argv else 300
    out = argv[argv.index("--out") + 1] if "--out" in argv else None

    _ensure_films_cache(tmdb.load_key())
    films = {}
    with open(FILMS_CACHE, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            films[rec["id"]] = (rec["title"], rec["year"])
    g = build_graph(films, load_people_cache(PEOPLE_CACHE))

    n_edges = sum(len(v) for v in g["film_people"].values())
    print(f"graph: {len(g['film_people'])} films, {len(g['person_names'])} people, {n_edges} edges")
    deg = sorted(len(v) for v in g["person_films"].values())
    print(f"person degree: median {deg[len(deg)//2]}, p95 {deg[int(len(deg)*0.95)]}, max {deg[-1]}")

    corpus_raw, corpus_gz = _sizes(subgraph_json(g, set(g["film_people"]), set(g["person_names"])))
    print(f"whole corpus: {corpus_raw/1024:.0f} KB raw, {corpus_gz/1024:.0f} KB gzip")

    rng = random.Random(42)
    fids = list(g["film_people"])
    dists, unreachable = [], 0
    for _ in range(pairs):
        a, b = rng.sample(fids, 2)
        d = bfs_dist(g, a, b)
        if d is None:
            unreachable += 1
        else:
            dists.append(d)
    dists.sort()
    hist = {}
    for d in dists:
        hist[d] = hist.get(d, 0) + 1
    print(f"path lengths over {pairs} random pairs (edges; 2 edges = 1 degree):")
    for d, c in sorted(hist.items()):
        print(f"  {d} edges ({d//2} degree{'s' if d//2 != 1 else ''}): {c}")
    if dists:
        print(f"  median {dists[len(dists)//2]} edges · p95 {dists[int(len(dists)*0.95)]} edges"
              f" · unreachable {unreachable}/{pairs}")

    sub_sizes = []
    for _ in range(20):
        a, b = rng.sample(fids, 2)
        fa, pa = neighborhood(g, a, 2)
        fb, pb = neighborhood(g, b, 2)
        raw, gz = _sizes(subgraph_json(g, fa | fb, pa | pb))
        sub_sizes.append((raw, gz))
    sub_sizes.sort()
    mid, hi = sub_sizes[len(sub_sizes)//2], sub_sizes[-1]
    print(f"2-hop pair subgraph (20 samples): median {mid[0]/1024:.0f} KB raw / {mid[1]/1024:.0f} KB gz,"
          f" max {hi[0]/1024:.0f} KB raw / {hi[1]/1024:.0f} KB gz")

    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(subgraph_json(g, set(g["film_people"]), set(g["person_names"])), fh,
                      ensure_ascii=False, separators=(",", ":"))
        print(f"wrote corpus -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
