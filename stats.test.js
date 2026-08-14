// Stats/streak tests (node stats.test.js). recordResult is pure — no localStorage.
import { defaultStats, recordResult, relativeLabel,
         recomputeStreak, streakState, verdictName,
         recordArchive, handicap, rebuildStats,
         exportRecord, importRecord } from './docs/stats.js';

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

// --- named golf verdicts ---
check('even is Par', verdictName(2, 2), 'Par');
check('one under is Birdie', verdictName(2, 3), 'Birdie');
check('two under is Eagle', verdictName(1, 3), 'Eagle');
check('three under is Albatross', verdictName(1, 4), 'Albatross');
check('one over is Bogey', verdictName(3, 2), 'Bogey');
check('two over is Double bogey', verdictName(4, 2), 'Double bogey');
check('past double bogey the number speaks', verdictName(6, 2), null);

// --- streakState drives the at-risk nudge ---
check('played today reads safe', streakState(r, '2026-08-11'), 'safe');
check('played yesterday reads at-risk', streakState(r, '2026-08-12'), 'at-risk');
check('a dead streak reads none', streakState(r, '2026-08-13'), 'none');
check('no history reads none', streakState(defaultStats(), '2026-08-11'), 'none');

// --- the archive channel: replays fill cells, never the scorecard ---
let a = recordArchive(defaultStats(), { id: 3, degrees: 4, par: 3, won: true });
check('replay lands in the archive map', a.archive[3], { degrees: 4, par: 3, won: true });
check('  ... and touches nothing else',
      [a.played, a.wins, a.currentStreak, a.lastDate], [0, 0, 0, null]);
a = recordArchive(a, { id: 3, degrees: 3, par: 3, won: true });
check('a better replay takes the cell', a.archive[3].degrees, 3);
a = recordArchive(a, { id: 3, degrees: 5, par: 3, won: true });
check('a worse replay is ignored', a.archive[3].degrees, 3);
a = recordArchive(a, { id: 9, degrees: 1, par: 2, won: false });
check('a loss records', a.archive[9].won, false);
a = recordArchive(a, { id: 9, degrees: 4, par: 2, won: true });
check('any win beats any loss', a.archive[9], { degrees: 4, par: 2, won: true });

// --- handicap: the golfer's number, hidden until it means something ---
let h = defaultStats();
for (let i = 1; i <= 9; i++) h = recordResult(h, win(`2026-09-${String(i).padStart(2, '0')}`, 3, 2, i));
check('nine rounds is not yet a handicap', handicap(h), null);
check('  ... unless the minimum is tuned down (9 bogeys average +1)', handicap(h, 5), 1);
h = recordResult(h, { date: '2026-09-10', id: 10, degrees: 1, par: 3, won: false });
check('ten rounds: 9 bogeys + 1 loss (+3) averages +1.2', handicap(h), 1.2);
check('an empty record never grades', handicap(defaultStats(), 0), null);

// --- rebuildStats: derived fields from history alone ---
const hist = {
  '2026-08-11': { id: 1, degrees: 2, par: 2, won: true },
  '2026-08-12': { id: 2, degrees: 5, par: 3, won: true },
  '2026-08-14': { id: 4, degrees: 1, par: 3, won: false },
};
const rb = rebuildStats(hist);
check('rebuild counts plays and wins', [rb.played, rb.wins], [3, 2]);
check('rebuild finds the streak runs (max 2, current 1)',
      [rb.maxStreak, rb.currentStreak], [2, 1]);
check('rebuild recomputes best and lastDate', [rb.best, rb.lastDate], [0, '2026-08-14']);
check('rebuild rebuilds the histogram', rb.histogram, { E: 1, '+2': 1, x: 1 });

// --- backup codes: export -> import round-trips and merges honestly ---
const code = exportRecord(rb);
check('codes carry the version prefix', code.startsWith('DOF1.'), true);
check('import into empty stats restores everything',
      JSON.stringify(importRecord(defaultStats(), code).history), JSON.stringify(hist));
const other = recordResult(defaultStats(), win('2026-08-13', 3, 3, 3));
const merged = importRecord(other, code);
check('merge unions both devices', merged.played, 4);
check('merge RECOMPUTES the streak across the union (13 bridges 12 -> 14: a 4-run neither device had)',
      [merged.maxStreak, merged.currentStreak], [4, 4]);
const clash = recordResult(defaultStats(), { date: '2026-08-12', id: 2, degrees: 3, par: 3, won: true });
check('conflicting dates keep the better run', importRecord(clash, code).history['2026-08-12'].degrees, 3);
check('garbage is rejected, not merged', importRecord(rb, 'DOF1.@@@not-base64@@@'), null);
check('a foreign prefix is rejected', importRecord(rb, 'WORDLE.abc'), null);
check('non-Latin titles survive the encoding',
      importRecord(defaultStats(),
        exportRecord(rebuildStats({ '2026-08-11': { id: 1, degrees: 2, par: 2, won: true, note: '寄生虫' } })))
        .history['2026-08-11'].note, '寄生虫');

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
