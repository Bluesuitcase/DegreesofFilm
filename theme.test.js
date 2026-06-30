import { parseHex, luminance, onAccentText } from './docs/theme.js';

let pass = 0, fail = 0;
function check(label, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  ok ? pass++ : fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${ok ? '' : `  (got ${JSON.stringify(got)}, want ${JSON.stringify(want)})`}`);
}

// --- parseHex ---
check('parse 6-digit', parseHex('#eba53c'), [235, 165, 60]);
check('parse 3-digit shorthand', parseHex('#abc'), [170, 187, 204]);
check('parse without hash', parseHex('734621'), [115, 70, 33]);
check('reject garbage', parseHex('nope'), null);
check('reject wrong length', parseHex('#12345'), null);
check('reject non-string', parseHex(null), null);

// --- luminance ordering ---
check('white brighter than black', luminance([255, 255, 255]) > luminance([0, 0, 0]), true);
check('white luminance ~1', Math.round(luminance([255, 255, 255])), 1);
check('black luminance 0', luminance([0, 0, 0]), 0);

// --- onAccentText: dark ink on light accents, bone on dark accents ---
check('amber accent -> dark ink text', onAccentText('#eba53c'), '#1a1206');
check('white accent -> dark ink text', onAccentText('#ffffff'), '#1a1206');
check('No Country brown -> bone text', onAccentText('#734621'), '#ece7dd');
check('Forrest Gump olive -> bone text', onAccentText('#735d3f'), '#ece7dd');
check('near-black accent -> bone text', onAccentText('#111111'), '#ece7dd');
check('unparseable accent -> dark fallback', onAccentText('???'), '#1a1206');

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
