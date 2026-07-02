// Light, reversible de-obfuscation for the answer strings in puzzle JSON.
// Mirrors curation/cipher.py EXACTLY (same SENTINEL + KEY + scheme). See that
// file for the rationale: this is an interim anti-snoop measure (repeating-key
// XOR + base64), NOT security — the key ships to the client, so it only defeats
// "open the JSON and read the answer." Pure logic, no DOM — node-testable.

const SENTINEL = String.fromCharCode(1);   // U+0001 — matches cipher.py; no title/name contains it
const KEY = new TextEncoder().encode('degrees-of-film');   // keep in sync with cipher.py

function xor(bytes) {
  const out = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i++) out[i] = bytes[i] ^ KEY[i % KEY.length];
  return out;
}

// SENTINEL + base64(xor(utf8)) -> plaintext. Any string without the sentinel
// (i.e. still plaintext) is returned untouched, so decoding is always safe.
export function decode(s) {
  if (typeof s !== 'string' || s[0] !== SENTINEL) return s;
  const bin = atob(s.slice(1));
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new TextDecoder().decode(xor(bytes));
}

// Inverse — provided for parity/tests; the client rarely needs to encode.
export function encode(s) {
  if (typeof s !== 'string' || s[0] === SENTINEL) return s;
  const enc = xor(new TextEncoder().encode(s));
  let bin = '';
  for (let i = 0; i < enc.length; i++) bin += String.fromCharCode(enc[i]);
  return SENTINEL + btoa(bin);
}

// Decode a puzzle's rungs in place: the answer strings + caption (the spoilers).
// Decoys/prompts stay as-is (they're player-facing and aren't the answer).
export function decodeRungs(rungs) {
  for (const r of rungs || []) {
    if (Array.isArray(r.answers)) r.answers = r.answers.map(decode);
    if (r.caption) r.caption = decode(r.caption);
  }
  return rungs;
}
