"""Tests for the light answer-obfuscation cipher. Pure logic, no network.

Run:  python curation/cipher.test.py
Prints PASS/FAIL lines; exits non-zero on any failure (mirrors the JS tests).
The fixed vector below is shared with cipher.test.js so the two implementations
can't drift.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cipher import (  # noqa: E402
    obfuscate, deobfuscate, encode_rungs, decode_rungs, SENTINEL,
)

try:                       # so Unicode test labels print on Windows' cp1252 stdout
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

passed = failed = 0


def check(label, got, want):
    global passed, failed
    ok = got == want
    passed, failed = passed + (1 if ok else 0), failed + (0 if ok else 1)
    print(f"{'PASS' if ok else 'FAIL'}  {label}"
          + ("" if ok else f"\n        got:  {got!r}\n        want: {want!r}"))


# --- fixed cross-language vector (also asserted in cipher.test.js) ---
check("obfuscate('The Dark Knight') is the shared vector",
      obfuscate("The Dark Knight"), SENTINEL + "MA0CUiEEAUZPLUMPDgQZ")
check("deobfuscate reverses the vector",
      deobfuscate(SENTINEL + "MA0CUiEEAUZPLUMPDgQZ"), "The Dark Knight")

# --- round trip (ASCII, Unicode, punctuation, empty) ---
for s in ["Javier Bardem", "No Country for Old Men", "Amélie", "WALL·E",
          "Harry Potter and the Philosopher's Stone", "", "東京物語"]:
    check(f"round-trips {s!r}", deobfuscate(obfuscate(s)), s)

# --- it actually obfuscates + carries the sentinel ---
check("encoded differs from plaintext", obfuscate("Heath Ledger") != "Heath Ledger", True)
check("encoded carries the sentinel prefix", obfuscate("Heath Ledger")[0], SENTINEL)

# --- passthrough + idempotency + None handling ---
check("deobfuscate leaves plaintext untouched", deobfuscate("Christian Bale"), "Christian Bale")
check("obfuscate is idempotent", obfuscate(obfuscate("Toy Story")), obfuscate("Toy Story"))
check("obfuscate(None) -> None", obfuscate(None), None)
check("deobfuscate(None) -> None", deobfuscate(None), None)

# --- encode_rungs / decode_rungs: answers + caption only, copies not mutations ---
rungs = [
    {"role": "Film", "prompt": "Name the film.", "answers": ["The Dark Knight"],
     "decoys": ["The Batman", "Batman Begins"]},
    {"role": "Cast", "prompt": "Who played Joker?", "answers": ["Heath Ledger"],
     "caption": "Heath Ledger as Joker", "decoys": ["Tom Hardy"], "image": "images/004-r3.jpg"},
]
enc = encode_rungs(rungs)
check("encode_rungs does not mutate the input", rungs[0]["answers"], ["The Dark Knight"])
check("encoded film answer carries sentinel", enc[0]["answers"][0][0], SENTINEL)
check("encoded caption carries sentinel", enc[1]["caption"][0], SENTINEL)
check("decoys left untouched by encode", enc[0]["decoys"], ["The Batman", "Batman Begins"])
check("prompt/image left untouched by encode",
      (enc[1]["prompt"], enc[1]["image"]), ("Who played Joker?", "images/004-r3.jpg"))

dec = decode_rungs(enc)
check("decode_rungs round-trips answers", dec[1]["answers"], ["Heath Ledger"])
check("decode_rungs round-trips caption", dec[1]["caption"], "Heath Ledger as Joker")

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
