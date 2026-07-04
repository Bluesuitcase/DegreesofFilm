"""Answers artifact for the /match Worker (v3 Phase 1, server-side matching).

The Worker matches guesses against PLAINTEXT answers stored in Cloudflare KV,
keyed `answers:<puzzleId>`. This module builds that artifact locally as a
`wrangler kv bulk put` file (a JSON array of {key, value-string} entries):

    server/answers-bulk.json   (GITIGNORED — plaintext answers never get committed)

Upload (once the Cloudflare account exists):
    wrangler kv bulk put server/answers-bulk.json --namespace-id <ANSWERS id>

publish.publish() feeds new puzzles in via its answers_sink hook (file_sink);
backfill_answers.py rebuilds the whole file from the published puzzles. Pure
file ops — no network, no key — so it unit-tests against temp dirs.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(ROOT, "server", "answers-bulk.json")


def kv_key(puzzle_id):
    return f"answers:{puzzle_id}"


def answers_payload(rungs):
    """The KV value for one puzzle: just each rung's plaintext answers, in
    ladder order. (Phase 3's replay validator will want decoys too — extend
    then, not now.)"""
    return {"rungs": [{"answers": list(r.get("answers") or [])} for r in rungs or []]}


def bulk_entry(puzzle_id, rungs):
    """One `wrangler kv bulk put` entry. KV values are strings, hence the dump."""
    return {"key": kv_key(puzzle_id),
            "value": json.dumps(answers_payload(rungs), ensure_ascii=False)}


def load_bulk(path=DEFAULT_PATH):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_bulk(entries, path=DEFAULT_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(entries, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def upsert_bulk(entries, entry):
    """Replace the entry with the same key, else append. Returns a new list."""
    out = [e for e in entries if e.get("key") != entry["key"]]
    out.append(entry)
    return out


def file_sink(path=DEFAULT_PATH):
    """An answers_sink for publish.publish(): upserts the puzzle's plaintext
    answers into the local bulk file on every approve/update."""
    def sink(puzzle_id, rungs):
        save_bulk(upsert_bulk(load_bulk(path), bulk_entry(puzzle_id, rungs)), path)
    return sink
