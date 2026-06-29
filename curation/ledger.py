"""Used-films ledger — the rule that we never repeat a film.

A version-controlled JSON list in the repo (DESIGN §2/§3): usage history can't
silently corrupt because it's just a committed file. Each record is
`{ id, title, year, puzzle }`; only `id` matters for the never-repeat check.

Pure file I/O + set membership, so it unit-tests with a temp path (no network).
"""
import json
import os

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "used_films.json")


def load(path=DEFAULT_PATH):
    """Return the ledger as a list of records ([] if the file is absent)."""
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else data.get("films", [])


def used_ids(ledger):
    return {rec["id"] for rec in ledger if "id" in rec}


def is_used(ledger, film_id):
    return film_id in used_ids(ledger)


def add(ledger, record):
    """Append a film record unless its id is already present. Returns ledger."""
    if "id" not in record:
        raise ValueError("ledger record needs an 'id'")
    if not is_used(ledger, record["id"]):
        ledger.append(record)
    return ledger


def save(ledger, path=DEFAULT_PATH):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(ledger, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
