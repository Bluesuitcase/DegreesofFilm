"""Movie Buff people index: a prebaked top-N popular-people list for client-side
autocomplete on credit rungs (the all-rungs extension of title_index.py).

Same anti-leak posture as the title index: built from TMDB-WIDE popularity order
(/person/popular), NEVER from puzzle data — seeding from answers would turn the
dropdown into an answer oracle. Deep-crew answers may therefore be absent; the
CLI's coverage report against the published puzzles is the shipping evidence.

Index format: ["Name", ...] ordered by TMDB popularity.

    python curation/people_index.py --n 10000 --out PATH   # fetch + build + report
"""
import gzip
import json
import os
import sys

import cipher
import manifest as manifest_mod
import tmdb

PAGE_SIZE = 20
MAX_PAGES = 500


def build_names(people, n):
    """Dedupe raw /person/popular results (by id, then by name), keep popularity
    order, truncate to n names. Pure."""
    seen_ids, seen_names, names = set(), set(), []
    for p in people:
        pid, name = p.get("id"), (p.get("name") or "").strip()
        if not pid or not name or pid in seen_ids or name.casefold() in seen_names:
            continue
        seen_ids.add(pid)
        seen_names.add(name.casefold())
        names.append(name)
        if len(names) >= n:
            break
    return names


def rung_coverage(puzzles_rungs, names):
    """Coverage of credit-rung answers against the index: a rung is covered when
    ANY of its accepted answer forms is present. Returns (per_role, misses).
    per_role: {role: [covered, total]}. Pure."""
    have = {n.casefold() for n in names}
    per_role, misses = {}, []
    for pid, rungs in puzzles_rungs:
        for r in rungs[1:]:                       # rung 0 is the film — title index's job
            role = r.get("role") or "?"
            per_role.setdefault(role, [0, 0])
            per_role[role][1] += 1
            if any((a or "").strip().casefold() in have for a in (r.get("answers") or [])):
                per_role[role][0] += 1
            else:
                misses.append(f"puzzle {pid} · {role}")
    return per_role, misses


def _sizes(names):
    raw = json.dumps(names, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return len(raw), len(gzip.compress(raw, 9))


def _load_puzzles_rungs():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = []
    for e in manifest_mod.load():
        path = os.path.join(root, "docs", "puzzles", e.get("file") or "")
        if not e.get("file") or not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            puzzle = json.load(fh)
        out.append((puzzle.get("id") or e.get("id"), cipher.decode_rungs(puzzle.get("rungs") or [])))
    return out


def _main(argv):
    n = int(argv[argv.index("--n") + 1]) if "--n" in argv else 10000
    out = argv[argv.index("--out") + 1] if "--out" in argv else None

    key = tmdb.load_key()
    pages = min(-(-n // PAGE_SIZE), MAX_PAGES)
    people = []
    for p in range(1, pages + 1):
        data = tmdb.get("/person/popular", key, page=p)
        people += data.get("results") or []
        if p % 100 == 0:
            print(f"  fetched {p}/{pages} pages…")
    names = build_names(people, n)

    raw, gz = _sizes(names)
    print(f"{len(names)} names: {raw/1024:.1f} KB raw, {gz/1024:.1f} KB gzip "
          f"({raw/max(1,len(names)):.1f} B/name raw)")

    per_role, misses = rung_coverage(_load_puzzles_rungs(), names)
    total_c = sum(c for c, _ in per_role.values())
    total_t = sum(t for _, t in per_role.values())
    print(f"credit-rung coverage: {total_c}/{total_t} ({100*total_c/max(1,total_t):.0f}%)")
    for role, (c, t) in sorted(per_role.items(), key=lambda kv: kv[1][1], reverse=True):
        print(f"  {role:<22} {c}/{t}")
    if misses:
        print(f"uncovered rungs ({len(misses)}, roles only — no names, spoiler-safe):")
        for m in misses:
            print(f"  {m}")

    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(names, fh, ensure_ascii=False, separators=(",", ":"))
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
