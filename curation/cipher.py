"""Light, reversible obfuscation for the answer strings served to players.

v1 shipped answers in plaintext in the puzzle JSON — one glance at devtools spoils
the game. This is the interim anti-snoop measure from DESIGN §6: a **light cipher**
(repeating-key XOR over the UTF-8 bytes, then base64), NOT security. The key lives
in the client too, so anyone determined can reverse it — the point is only to defeat
"open the JSON and read the answer." The proper fix is server-side matching (v3).

Every obfuscated string carries a one-char SENTINEL prefix (U+0001, which no real
title/name contains and which base64 never produces). That makes the scheme:
  - self-identifying — `deobfuscate` leaves any non-prefixed (plaintext) string
    untouched, so old files, hand-authored puzzles, and half-migrated data all work;
  - idempotent — `obfuscate` won't double-encode an already-encoded string.

The JS side (docs/cipher.js) mirrors this exactly; curation/cipher.test.py and
cipher.test.js share a fixed vector so the two implementations can't drift.
"""
import base64

SENTINEL = "\x01"
KEY = b"degrees-of-film"   # shared with docs/cipher.js — keep in sync


def _xor(data):
    return bytes(b ^ KEY[i % len(KEY)] for i, b in enumerate(data))


def obfuscate(s):
    """Plaintext -> SENTINEL + base64(xor(utf8)). Passes through None and
    already-encoded strings unchanged (idempotent)."""
    if s is None or (isinstance(s, str) and s.startswith(SENTINEL)):
        return s
    return SENTINEL + base64.b64encode(_xor(s.encode("utf-8"))).decode("ascii")


def deobfuscate(s):
    """Inverse of obfuscate. Any string without the SENTINEL prefix (i.e. still
    plaintext) is returned as-is, so decoding is always safe to run."""
    if not (isinstance(s, str) and s.startswith(SENTINEL)):
        return s
    return _xor(base64.b64decode(s[1:])).decode("utf-8")


def _map_rungs(rungs, fn):
    """Return new rung dicts with each answer + the caption passed through `fn`.
    Copies (never mutates the input); leaves decoys/prompts/role/image alone."""
    out = []
    for r in rungs or []:
        r2 = dict(r)
        if isinstance(r2.get("answers"), list):
            r2["answers"] = [fn(a) for a in r2["answers"]]
        if r2.get("caption"):
            r2["caption"] = fn(r2["caption"])
        out.append(r2)
    return out


def encode_rungs(rungs):
    """Obfuscate the answer strings + caption of every rung (for writing a file)."""
    return _map_rungs(rungs, obfuscate)


def decode_rungs(rungs):
    """Deobfuscate the answer strings + caption of every rung (after reading a file)."""
    return _map_rungs(rungs, deobfuscate)
