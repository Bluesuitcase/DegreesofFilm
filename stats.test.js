import { defaultStats, recordResult } from './docs/stats.js';

let pass = 0, fail = 0;
function check(label, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  ok ? pass++ : fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${ok ? '' : `  (got ${JSON.stringify(got)}, want ${JSON.stringify(want)})`}`);
}

// --- first finished run ---
let s = recordResult(defaultStats(), { date: '2026-06-28', depth: 5, won: false });
check('played counts', s.played, 1);
check('first streak is 1', s.currentStreak, 1);
check('best depth set', s.bestDepth, 5);
check('histogram records depth', s.histogram, { 5: 1 });
check('not a win', s.wins, 0);

// --- consecutive day extends the streak ---
s = recordResult(s, { date: '2026-06-29', depth: 8, won: false });
check('consecutive day -> streak 2', s.currentStreak, 2);
check('max streak tracks', s.maxStreak, 2);
check('best depth keeps the max', s.bestDepth, 8);

// --- replaying the same day is idempotent ---
let again = recordResult(s, { date: '2026-06-29', depth: 11, won: true });
check('same date does not double-count played', again.played, s.played);
check('same date does not change streak', again.currentStreak, s.currentStreak);
check('same date does not change best depth', again.bestDepth, s.bestDepth);

// --- a missed day resets the streak but keeps maxStreak ---
let gapped = recordResult(s, { date: '2026-07-02', depth: 3, won: false });
check('gap day resets streak to 1', gapped.currentStreak, 1);
check('maxStreak preserved through a reset', gapped.maxStreak, 2);
check('played still increments after a gap', gapped.played, 3);

// --- a win on a consecutive day counts ---
let won = recordResult(s, { date: '2026-06-30', depth: 12, won: true });
check('win increments wins', won.wins, 1);
check('win extends streak to 3', won.currentStreak, 3);

// --- input is not mutated (pure) ---
const before = defaultStats();
const snapshot = JSON.stringify(before);
recordResult(before, { date: '2026-06-28', depth: 4, won: false });
check('recordResult does not mutate its input', JSON.stringify(before), snapshot);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
