"""Tests for the per-rung credit-image layer. Pure logic, no network/key.

Run:  python curation/credits_images.test.py
Prints PASS/FAIL lines; exits non-zero on any failure (mirrors the JS tests).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from credits_images import (  # noqa: E402
    caption_for, rung_image_name, attach_person_meta,
    finalize_rung_images, IMG_BASE, HELPER_KEYS,
)

passed = failed = 0


def check(label, got, want):
    global passed, failed
    ok = got == want
    passed, failed = passed + (1 if ok else 0), failed + (0 if ok else 1)
    print(f"{'PASS' if ok else 'FAIL'}  {label}"
          + ("" if ok else f"\n        got:  {got!r}\n        want: {want!r}"))


# --- caption_for ---
check("cast caption is 'Name as Character'",
      caption_for("Cast", "Heath Ledger", "Joker"), "Heath Ledger as Joker")
check("crew caption is name only",
      caption_for("Director", "Christopher Nolan", ""), "Christopher Nolan")
check("cast with no character falls back to name",
      caption_for("Cast", "Some Actor", ""), "Some Actor")
check("film rung has no caption", caption_for("Film", "The Dark Knight", ""), "")
check("blank character whitespace ignored",
      caption_for("Cast", "A B", "   "), "A B")

# --- rung_image_name ---
check("credit image filename uses r-prefix", rung_image_name("004", 2), "004-r2.jpg")

# --- attach_person_meta ---
CREDITS = {
    "cast": [
        {"id": 1, "name": "Christian Bale", "order": 0, "character": "Bruce Wayne",
         "profile_path": "/bale.jpg"},
        {"id": 2, "name": "Heath Ledger", "order": 1, "character": "Joker",
         "profile_path": "/ledger.jpg"},
    ],
    "crew": [
        {"id": 9, "name": "Christopher Nolan", "job": "Director", "profile_path": "/nolan.jpg"},
        {"id": 8, "name": "Wally Pfister", "job": "Director of Photography"},  # no profile
    ],
}
puzzle = {"rungs": [
    {"role": "Film", "answers": ["The Dark Knight"]},
    {"role": "Cast", "answers": ["Christian Bale"]},
    {"role": "Cast", "answers": ["Heath Ledger"]},
    {"role": "Director", "answers": ["Christopher Nolan"]},
    {"role": "Cinematographer", "answers": ["Wally Pfister"]},
]}
attach_person_meta(puzzle, CREDITS)
r = puzzle["rungs"]

check("film rung is left untouched (no helper fields)",
      any(k in r[0] for k in HELPER_KEYS), False)
check("cast rung gets character", r[1]["character"], "Bruce Wayne")
check("cast rung caption", r[1]["caption"], "Christian Bale as Bruce Wayne")
check("cast rung profile url is its headshot (uniform with crew)",
      r[1]["profile"], IMG_BASE + "/bale.jpg")
check("crew rung caption is name only", r[3]["caption"], "Christopher Nolan")
check("crew rung profile url is its headshot",
      r[3]["profile"], IMG_BASE + "/nolan.jpg")
check("crew rung with no profile has no headshot", r[4]["profile"], None)
check("crew rung with no profile has no character", r[4]["character"], "")
check("no image_pick/candidates fields are stamped anymore",
      any(k in rung for rung in r for k in ("image_pick", "candidates")), False)

# --- finalize_rung_images (injected fake save) ---
saved = []
def fake_save(url, filename):
    saved.append((url, filename))

# An approve payload: the film rung, a cast rung + crew rung that each have a
# headshot, and a cast rung whose person has no TMDB headshot (holds the frame).
payload = [
    {"role": "Film", "answers": ["The Dark Knight"], "profile": None},
    {"role": "Cast", "answers": ["Heath Ledger"], "character": "Joker",
     "caption": "Heath Ledger as Joker", "profile": IMG_BASE + "/ledger.jpg"},
    {"role": "Director", "answers": ["Christopher Nolan"], "character": "",
     "caption": "Christopher Nolan", "profile": IMG_BASE + "/nolan.jpg"},
    {"role": "Cast", "answers": ["Aaron Eckhart"], "character": "Harvey Dent",
     "caption": "Aaron Eckhart as Harvey Dent", "profile": None},
]
finalize_rung_images(payload, "004", fake_save)

check("saved exactly the two headshots (film + headshot-less rung skipped)",
      saved, [(IMG_BASE + "/ledger.jpg", "004-r2.jpg"), (IMG_BASE + "/nolan.jpg", "004-r3.jpg")])
check("cast rung gets image + caption",
      (payload[1].get("image"), payload[1].get("caption")),
      ("images/004-r2.jpg", "Heath Ledger as Joker"))
check("crew rung gets image + caption",
      (payload[2].get("image"), payload[2].get("caption")),
      ("images/004-r3.jpg", "Christopher Nolan"))
check("headshot-less cast rung has no image or caption",
      ("image" in payload[3] or "caption" in payload[3]), False)
check("film rung stays imageless", ("image" in payload[0]), False)
check("all helper fields stripped from every rung",
      any(k in rung for rung in payload for k in HELPER_KEYS), False)
check("published rungs keep only schema keys",
      sorted(payload[1].keys()), ["answers", "caption", "image", "role"])

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
