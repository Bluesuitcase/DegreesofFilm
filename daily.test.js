import { pickPuzzle, todayISO } from './docs/daily.js';

let pass = 0, fail = 0;
function check(label, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  ok ? pass++ : fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${ok ? '' : `  (got ${JSON.stringify(got)}, want ${JSON.stringify(want)})`}`);
}

const manifest = [
  { date: '2026-06-28', id: 1, file: '001.json' },
  { date: '2026-06-30', id: 3, file: '003.json' },   // note: 06-29 intentionally missing (a gap)
  { date: '2026-06-29', id: 2, file: '002.json' },   // out of order on purpose
];

check('exact date match', pickPuzzle(manifest, '2026-06-29').id, 2);
check('after all dates -> latest', pickPuzzle(manifest, '2026-07-15').id, 3);
check('before all dates -> earliest', pickPuzzle(manifest, '2026-01-01').id, 1);

// a gap day (no 06-29 in this manifest) -> most recent on/before it
const gap = manifest.filter((e) => e.id !== 2);
check('gap day -> most recent prior', pickPuzzle(gap, '2026-06-29').id, 1);

check('empty manifest -> null', pickPuzzle([], '2026-06-29'), null);
check('non-array -> null', pickPuzzle(undefined, '2026-06-29'), null);

// todayISO formatting
check('todayISO zero-pads', todayISO(new Date(2026, 0, 5)), '2026-01-05');
check('todayISO month/day', todayISO(new Date(2026, 11, 31)), '2026-12-31');

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
