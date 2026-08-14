// Stats/streak tests (node stats.test.js). recordResult is pure — no localStorage.
import { defaultStats, recordResult, relativeLabel,
         recomputeStreak, streakState } from './docs/stats.js';

let pass = 0, fail = 0;
function check(label, got, want) {
  const g = JSON.stringify(got), w = JSON.stringify(want);
  const ok = g === w;
  ok ? pass++ : fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${ok ? '' : `  (got ${g}, want ${w})`}`);
}

const win = (date, degrees, par = 2, id = 1) => ({ date, id, degrees, par, won: true });

// --- golf labels ---
check('matching par reads as even', relativeLabel(2, 2), 'E');
check('over par is signed', relativeLabel(4, 2), '+2');
check('under par is signed', relativeLabel(1, 2), '−1');

// --- first result ---
let s = recordResult(defaultStats(), win('2026-08-11', 2));
check('played counted', s.played, 1);
check('win counted', s.wins, 1);
check('streak opens at 1', [s.currentStreak, s.maxStreak], [1, 1]);
check('history keyed by date', s.history['2026-08-11'], { id: 1, degrees: 2, par: 2, won: true });
check('histogram keyed by the golf label', s.histogram, { E: 1 });
check('best is degrees over par', s.best, 0);

// --- consecutive days extend the streak ---
s = recordResult(s, win('2026-08-12', 3, 2, 2));
check('next day extends', [s.currentStreak, s.maxStreak], [2, 2]);
check('best keeps the lower score', s.best, 0);
s = recordResult(s, win('2026-08-13', 1, 3, 3));
check('under par improves best', s.best, -2);
check('histogram accumulates buckets', s.histogram, { E: 1, '+1': 1, '−2': 1 });

// --- a gap resets the current streak but not the max ---
s = recordResult(s, win('2026-08-20', 2, 2, 4));
check('gap resets current streak', s.currentStreak, 1);
check('max streak remembered', s.maxStreak, 3);

// --- a broken chain still counts as played, and still keeps the streak alive ---
s = recordResult(s, { date: '2026-08-21', id: 5, degrees: 1, par: 3, won: false });
check('loss counted as played', s.played, 5);
check('loss not counted as a win', s.wins, 4);
check('showing up keeps the streak', s.currentStreak, 2);
check('failed runs bucket under x', s.histogram.x, 1);
check('a loss never becomes your best score', s.best, -2);

// --- idempotent per date (replaying the same day changes nothing) ---
const before = JSON.stringify(s);
check('same date is a no-op', JSON.stringify(recordResult(s, win('2026-08-21', 1, 3, 5))), before);

// --- defaults are safe ---
check('fresh stats have no best yet', defaultStats().best, null);

// --- recomputeStreak: the display is honest even before today's play ---
let r = recordResult(defaultStats(), win('2026-08-11', 2));
check('streak survives same-day recompute', recomputeStreak(r, '2026-08-11').currentStreak, 1);
check('streak survives into the next day (still playable)',
      recomputeStreak(r, '2026-08-12').currentStreak, 1);
check('a missed day zeroes the displayed streak',
      recomputeStreak(r, '2026-08-13').currentStreak, 0);
check('  ... without touching the original object', r.currentStreak, 1);
check('  ... and maxStreak is untouched', recomputeStreak(r, '2026-08-13').maxStreak, 1);
check('recompute is a no-op when nothing changes', recomputeStreak(r, '2026-08-12') === r, true);
check('fresh stats recompute safely', recomputeStreak(defaultStats(), '2026-08-11').currentStreak, 0);

// --- streakState drives the at-risk nudge ---
check('played today reads safe', streakState(r, '2026-08-11'), 'safe');
check('played yesterday reads at-risk', streakState(r, '2026-08-12'), 'at-risk');
check('a dead streak reads none', streakState(r, '2026-08-13'), 'none');
check('no history reads none', streakState(defaultStats(), '2026-08-11'), 'none');

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
