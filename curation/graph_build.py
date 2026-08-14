"""Build the shipped film<->person corpus: docs/graph.json.

The Degrees rebuild plays against ONE cached graph instead of a per-challenge
subgraph. That inverts the old economics: the corpus costs ~171 KB gz once (less
than the Movie Buff people index the site used to ship), and every challenge after
it is ~50 bytes of {start, goal, par}. It also removes the subgraph-as-hint problem
— the shipped file is the whole pool, so it says nothing about today's answer.

Two size levers, both measured (see the module docstring history in project_state):
  1. PRUNE degree-1 people. A person credited on a single film can never be a chain
     step (you enter through a film and must leave through another, and closing on
     the goal needs the goal's credit too). 67% of people, ~0 gameplay value.
  2. INDEX-ENCODE. Parallel label arrays + per-film adjacency as delta-hex strings.

Ordering is meaningful: films keep the discover sweep's popularity order and people
are ordered by TMDB popularity, so the client's prefix suggestions surface the
famous entry first without shipping a rank field.

    python curation/graph_build.py            # build + report sizes
    python curation/graph_build.py --check     # validate the existing file only

Pure core (no network, no IO): connector_ids / rank_people / encode_deltas /
decode_deltas / build_corpus / validate. The CLI reads the two gitignored caches
(people_harvest_cache.jsonl, films_cache.jsonl — rebuildable by people_index.py and
graph_extract.py) and writes the asset.
"""
import argparse
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PEOPLE_CACHE = os.path.join(HERE, "people_harvest_cache.jsonl")
FILMS_CACHE = os.path.join(HERE, "films_cache.jsonl")
OUT = os.path.join(os.path.dirname(HERE), "docs", "graph.json")

CORPUS_VERSION = 1
MIN_FILMS_PER_PERSON = 2      # lever 1: a one-film person can never be a hop


def connector_ids(people_by_film, *, min_films=MIN_FILMS_PER_PERSON):
    """Person ids credited on at least `min_films` DISTINCT films. Pure."""
    seen = {}
    for fid, people in people_by_film.items():
        for pid, _name, _pop in people:
            seen.setdefault(pid, set()).add(fid)
    return {pid for pid, films in seen.items() if len(films) >= min_films}


def rank_people(people_by_film, keep):
    """[(pid, name)] for the kept ids, most popular first (ties: name, for a stable
    build). Popularity is per-credit in the harvest; a person's rank is their max. Pure."""
    best = {}
    for people in people_by_film.values():
        for pid, name, pop in people:
            if pid not in keep:
                continue
            if pid not in best or pop > best[pid][1]:
                best[pid] = (name, pop)
    return [(pid, best[pid][0])
            for pid in sorted(best, key=lambda p: (-best[p][1], best[p][0]))]


def encode_deltas(indices):
    """Ascending ints -> comma-separated hex gaps ("3,1,2b"). Smaller raw AND gz than
    a JSON int array, and the client decoder is four lines. Pure."""
    out, prev = [], 0
    for i in sorted(indices):
        out.append(format(i - prev, "x"))
        prev = i
    return ",".join(out)


def decode_deltas(s):
    """Inverse of encode_deltas — the Python mirror of corpus.js's decoder, so the
    round-trip is testable on this side too. Pure."""
    if not s:
        return []
    out, run = [], 0
    for part in s.split(","):
        run += int(part, 16)
        out.append(run)
    return out


def build_corpus(film_order, films, people_by_film, *, version=CORPUS_VERSION):
    """Assemble the shipped corpus. Pure.

    film_order: [tmdb_id] in popularity order (the sweep order).
    films:      {tmdb_id: (title, year)}.
    people_by_film: {tmdb_id: [(pid, name, popularity)]}.

    Films are kept only if they still carry a connector; people only if they connect.
    Film ids are TMDB ids, NOT array positions — challenges reference them, so a
    rebuild that reorders the arrays must not silently repoint an old daily.
    """
    keep = connector_ids(people_by_film)
    ranked = rank_people(people_by_film, keep)
    pindex = {pid: i for i, (pid, _n) in enumerate(ranked)}

    ids, labels, cast = [], [], []
    for fid in film_order:
        if fid not in films or fid not in people_by_film:
            continue
        mine = {pindex[pid] for pid, _n, _p in people_by_film[fid] if pid in pindex}
        if not mine:
            continue                      # isolated film: nothing to hop through
        ids.append(fid)
        title, year = films[fid]
        labels.append([title, year])
        cast.append(encode_deltas(mine))
    return {"v": version, "ids": ids, "films": labels,
            "people": [name for _pid, name in ranked], "cast": cast}


def validate(corpus):
    """Raise ValueError on anything that would break the client. Pure."""
    n_films, n_people = len(corpus["films"]), len(corpus["people"])
    if corpus.get("v") != CORPUS_VERSION:
        raise ValueError(f"corpus version {corpus.get('v')} != {CORPUS_VERSION}")
    if not (len(corpus["ids"]) == n_films == len(corpus["cast"])):
        raise ValueError("ids/films/cast arrays are not the same length")
    if len(set(corpus["ids"])) != n_films:
        raise ValueError("duplicate film ids")
    degree = [0] * n_people
    for i, enc in enumerate(corpus["cast"]):
        people = decode_deltas(enc)
        if not people:
            raise ValueError(f"film index {i} has an empty cast")
        if any(p < 0 or p >= n_people for p in people):
            raise ValueError(f"film index {i} references a person out of range")
        if len(set(people)) != len(people):
            raise ValueError(f"film index {i} lists a person twice")
        for p in people:
            degree[p] += 1
    orphans = [i for i, d in enumerate(degree) if d < MIN_FILMS_PER_PERSON]
    if orphans:
        raise ValueError(f"{len(orphans)} people are not connectors "
                         f"(e.g. {corpus['people'][orphans[0]]!r})")
    return True


def _load_caches():
    films, order = {}, []
    with open(FILMS_CACHE, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            if rec["id"] not in films:
                order.append(rec["id"])
            films[rec["id"]] = (rec.get("title"), rec.get("year"))
    people_by_film = {}
    with open(PEOPLE_CACHE, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            people_by_film[rec["film_id"]] = [tuple(p) for p in rec["people"]]
    return order, films, people_by_film


def _sizes(path):
    raw = open(path, "rb").read()
    return len(raw) / 1024, len(gzip.compress(raw, 9)) / 1024


def _main(argv):
    ap = argparse.ArgumentParser(description="Build docs/graph.json (the Degrees corpus)")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--check", action="store_true", help="validate the existing file, don't build")
    args = ap.parse_args(argv)

    if args.check:
        with open(args.out, encoding="utf-8") as fh:
            corpus = json.load(fh)
        validate(corpus)
        raw, gz = _sizes(args.out)
        print(f"OK  {len(corpus['films'])} films / {len(corpus['people'])} people "
              f"/ {raw:.0f} KB raw / {gz:.0f} KB gz")
        return 0

    for path in (FILMS_CACHE, PEOPLE_CACHE):
        if not os.path.exists(path):
            print(f"missing cache: {path}\n"
                  "  rebuild with: python curation/people_index.py --source credits\n"
                  "                python curation/graph_extract.py", file=sys.stderr)
            return 1
    order, films, people_by_film = _load_caches()
    corpus = build_corpus(order, films, people_by_film)
    validate(corpus)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(corpus, fh, ensure_ascii=False, separators=(",", ":"))
    raw, gz = _sizes(args.out)
    edges = sum(len(decode_deltas(c)) for c in corpus["cast"])
    print(f"wrote {args.out}")
    print(f"  {len(corpus['films'])} films / {len(corpus['people'])} people / {edges} edges")
    print(f"  {raw:.1f} KB raw / {gz:.1f} KB gz")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
