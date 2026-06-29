"""Tiny TMDB v3 client for the curation tools. Stdlib only — no pip installs.

The API key lives in curation/.env (gitignored) and is read here; it is never
logged (request URLs that carry it are not printed).
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.themoviedb.org/3"


def load_key():
    """Load TMDB_API_KEY from curation/.env (or the environment)."""
    here = os.path.dirname(os.path.abspath(__file__))
    for path in (os.path.join(here, ".env"), "curation/.env", ".env"):
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            break
    key = os.environ.get("TMDB_API_KEY", "").strip()
    if not key or key == "PASTE_YOUR_KEY_HERE":
        raise SystemExit("TMDB_API_KEY not set — put your key in curation/.env "
                         "(gitignored; do not paste it in chat).")
    return key


def get(path, key, **params):
    """GET a TMDB endpoint. Never logs the URL (it carries the key)."""
    params["api_key"] = key
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        msg = "401 (check your TMDB_API_KEY)" if e.code == 401 else str(e.code)
        raise RuntimeError(f"HTTP {msg} on {path}") from None


def search_movie(title, key, year=None):
    data = get("/search/movie", key, query=title,
               year=(year or ""), include_adult="false")
    results = data.get("results") or []
    return results[0] if results else None


def movie_with_credits(film_id, key):
    return get(f"/movie/{film_id}", key, append_to_response="credits")
