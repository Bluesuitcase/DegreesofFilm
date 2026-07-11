"""Movie Buff title index: a prebaked top-N popular-title list for client-side
autocomplete (research-frontier 2b). Static-only by design — the index ships as a
plain JSON file so the browser never calls TMDB (the key-leak ban).

Anti-leak invariant: the index is built from TMDB-WIDE vote_count order, NEVER from
the ledger or manifest, so membership carries ~no signal about eligible answers.
The ledger is used only as an ASSERTION input: every ledger film's title must be
present (absence would both leak by omission and break autocomplete on its day).

Index format (compact, client-side normalize() at load): [[title, year], ...]
ordered by TMDB vote_count descending.

    python curation/title_index.py --n 5000 --out PATH   # fetch + build + assert
    python curation/title_index.py --n 5000 --out PATH --report-only
                                                         # sizes/coverage, no exit-1
"""
import gzip
import json
import os
import sys

import ledger as ledger_mod
import tmdb

PAGE_SIZE = 20          # TMDB discover page size (fixed)
MAX_PAGES = 500         # TMDB hard paging cap


def build_entries(movies, n):
    """Dedupe raw discover results (by id), keep input order, shape to
    [title, year] pairs, truncate to n. Pure."""
    seen, entries = set(), []
    for m in movies:
        mid, title = m.get("id"), (m.get("title") or "").strip()
        if not mid or not title or mid in seen:
            continue
        seen.add(mid)
        year = (m.get("release_date") or "")[:4]
        entries.append([title, int(year) if year.isdigit() else 0])
        if len(entries) >= n:
            break
    return entries


def coverage_gaps(entries, ledger):
    """Ledger films whose (title, year) is absent from the index. Pure."""
    have = {(t.casefold(), str(y)) for t, y in entries}
    return [f"{r.get('title')} ({r.get('year')})" for r in ledger
            if (str(r.get('title', '')).casefold(), str(r.get('year'))) not in have]


def _sizes(entries):
    raw = json.dumps(entries, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return len(raw), len(gzip.compress(raw, 9))


def _main(argv):
    n = int(argv[argv.index("--n") + 1]) if "--n" in argv else 5000
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    report_only = "--report-only" in argv

    key = tmdb.load_key()
    pages = min(-(-n // PAGE_SIZE), MAX_PAGES)
    movies = []
    for p in range(1, pages + 1):
        data = tmdb.get("/discover/movie", key, sort_by="vote_count.desc",
                        include_adult="false", page=p)
        movies += data.get("results") or []
        if p % 50 == 0:
            print(f"  fetched {p}/{pages} pages…")
    entries = build_entries(movies, n)

    raw, gz = _sizes(entries)
    print(f"{len(entries)} titles: {raw/1024:.1f} KB raw, {gz/1024:.1f} KB gzip "
          f"({raw/max(1,len(entries)):.1f} B/title raw)")

    gaps = coverage_gaps(entries, ledger_mod.load())
    if gaps:
        print(f"LEDGER COVERAGE GAPS ({len(gaps)}):")
        for g in gaps:
            print(f"  MISSING {g}")
    else:
        print("ledger coverage: every ledger film is in the index")

    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(entries, fh, ensure_ascii=False, separators=(",", ":"))
        print(f"wrote {out}")
    return 1 if (gaps and not report_only) else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
