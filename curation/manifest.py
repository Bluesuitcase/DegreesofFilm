"""Writer for docs/puzzles/manifest.json — the daily index the client reads.

Each entry is `{ date, id, file, title, accent }`. The client fetches this list,
picks the entry whose `date` matches today's canonical date, then fetches
`file`; the archive browser is just a render of the list (decided in DESIGN §4).

Pure JSON-list operations, so it unit-tests against a temp path (no network).
"""
import json
import os

DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs", "puzzles", "manifest.json")

FIELDS = ("date", "id", "file", "title", "accent")


def load(path=DEFAULT_PATH):
    """Return the manifest as a list of entries ([] if the file is absent)."""
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else data.get("puzzles", [])


def make_entry(*, date, id, file, title, accent=None):
    return {"date": date, "id": id, "file": file, "title": title, "accent": accent}


def upsert(manifest, entry):
    """Insert or replace by `date` (one puzzle per day). Returns a new list,
    sorted by date so 'today' lookups and the archive read in order."""
    if not entry.get("date"):
        raise ValueError("manifest entry needs a 'date'")
    kept = [e for e in manifest if e.get("date") != entry["date"]]
    kept.append(entry)
    kept.sort(key=lambda e: e.get("date") or "")
    return kept


def save(manifest, path=DEFAULT_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
