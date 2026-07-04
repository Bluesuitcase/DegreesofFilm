"""Rebuild the /match Worker's answers artifact from the published puzzles.

Reads every puzzle in docs/puzzles/manifest.json, decodes its (obfuscated)
answers with cipher.py, and writes the whole set as a `wrangler kv bulk put`
file. Re-runnable and idempotent — needed once at Phase 1 cutover, and again
in any rollback that re-publishes puzzles. No network, no TMDB key.

    python curation/backfill_answers.py                # writes server/answers-bulk.json
    python curation/backfill_answers.py --out PATH     # elsewhere (still gitignore it!)
    python curation/backfill_answers.py --dry-run      # count + list, write nothing

Upload after (needs the Cloudflare account):
    wrangler kv bulk put server/answers-bulk.json --namespace-id <ANSWERS id>
"""
import json
import os
import sys

import cipher
import manifest as manifest_mod
import push_answers


def build_entries(manifest, puzzles_dir):
    """Bulk entries for every manifest puzzle whose file exists. Pure."""
    entries = []
    for e in manifest:
        path = os.path.join(puzzles_dir, e.get("file") or "")
        if not e.get("file") or not os.path.exists(path):
            print(f"  skip id={e.get('id')} — no file {e.get('file')}")
            continue
        with open(path, encoding="utf-8") as fh:
            puzzle = json.load(fh)
        rungs = cipher.decode_rungs(puzzle.get("rungs") or [])
        entries.append(push_answers.bulk_entry(puzzle.get("id") or e.get("id"), rungs))
    return entries


def _main(argv):
    out = push_answers.DEFAULT_PATH
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    dry = "--dry-run" in argv

    puzzles_dir = os.path.join(push_answers.ROOT, "docs", "puzzles")
    man = manifest_mod.load()
    entries = build_entries(man, puzzles_dir)
    for e in entries:
        rungs = len(json.loads(e["value"])["rungs"])
        print(f"  {e['key']}: {rungs} rungs")
    if dry:
        print(f"dry run — {len(entries)} entries, nothing written")
        return 0
    push_answers.save_bulk(entries, out)
    print(f"wrote {len(entries)} entries -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
