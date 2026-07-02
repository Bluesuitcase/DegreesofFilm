// Tests for the light answer-obfuscation cipher (docs/cipher.js).
// Run: node cipher.test.js  — prints PASS/FAIL, non-zero exit on any failure.
import { decode, encode, decodeRungs } from './docs/cipher.js';

let pass = 0, fail = 0;
function check(label, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  if (ok) pass++; else fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}`
    + (ok ? '' : `\n        got:  ${JSON.stringify(got)}\n        want: ${JSON.stringify(want)}`));
}

const S = String.fromCharCode(1);   // the U+0001 sentinel

// --- cross-language vector: this exact payload was produced by curation/cipher.py.
// If either side's KEY/scheme drifts, this fails. ---
check('decodes the Python-produced vector for "The Dark Knight"',
  decode(S + 'MA0CUiEEAUZPLUMPDgQZ'), 'The Dark Knight');
check('decodes the Python vector for a Unicode title (Amélie)',
  decode(S + 'JQik2wkMFg=='), 'Amélie');

// --- round trip (ASCII + Unicode + punctuation) ---
for (const s of ['Javier Bardem', 'No Country for Old Men', 'Amélie', 'WALL·E',
                 "Harry Potter and the Philosopher's Stone", '', '東京物語']) {
  check(`round-trips ${JSON.stringify(s)}`, decode(encode(s)), s);
}

// --- the encoded form is not the plaintext (i.e. it actually obfuscates) ---
check('encoded string differs from plaintext', encode('Heath Ledger') !== 'Heath Ledger', true);
check('encoded string carries the sentinel prefix', encode('Heath Ledger')[0], S);

// --- passthrough: plaintext (no sentinel) decodes to itself, so old/plain files work ---
check('decode leaves plaintext untouched', decode('Christian Bale'), 'Christian Bale');
check('idempotent: encoding an encoded string is a no-op',
  encode(encode('Toy Story')), encode('Toy Story'));
check('non-string decode passes through', decode(undefined), undefined);

// --- decodeRungs: answers + caption decoded in place; decoys/prompt untouched ---
const rungs = [
  { role: 'Film', prompt: 'Name the film.', answers: [encode('The Dark Knight')],
    decoys: ['The Batman', 'Batman Begins'] },
  { role: 'Cast', prompt: 'Who played Joker?', answers: [encode('Heath Ledger')],
    caption: encode('Heath Ledger as Joker'), decoys: ['Tom Hardy'] },
];
decodeRungs(rungs);
check('film rung answer decoded', rungs[0].answers, ['The Dark Knight']);
check('decoys left as-is (not the answer)', rungs[0].decoys, ['The Batman', 'Batman Begins']);
check('prompt left as-is', rungs[1].prompt, 'Who played Joker?');
check('cast rung answer decoded', rungs[1].answers, ['Heath Ledger']);
check('caption decoded', rungs[1].caption, 'Heath Ledger as Joker');

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
