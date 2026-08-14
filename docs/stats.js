// Player stats + daily streak for Degrees, persisted in localStorage. The streak
// and histogram math (recordResult) is pure and node-testable; load/save touch
// localStorage.
//
// Scoring is golf: a run is graded by degrees against par, so the histogram is
// keyed by that difference ('-1', '0', '+1', …) with 'x' for a failed run.

const KEY = 'dof-degrees-v1';

export function defaultStats() {
  return {
    played: 0, wins: 0,
    currentStreak: 0, maxStreak: 0,
    lastDate: null, best: null,     // best = lowest degrees-over-par ever scored
    histogram: {},                  // '-1' | '0' | '+1' | … | 'x' -> count
    history: {},                    // date -> { id, degrees, par, won }
  };
}

// Whole days from a -> b for 'YYYY-MM-DD' strings (UTC-safe, DST-proof).
function dayDiff(a, b) {
  return Math.round((Date.parse(b + 'T00:00:00Z') - Date.parse(a + 'T00:00:00Z')) / 86400000);
}

// '+2' / 'E' / '−1' — how a finished run reads on a scorecard, golf convention.
export function relativeLabel(degrees, par) {
  const d = degrees - par;
  if (d === 0) return 'E';
  return d > 0 ? `+${d}` : `−${Math.abs(d)}`;
}

// The golf verdict as a NAME — vocabulary players carry into group chats
// ("birdied it through the composer"). Null past double bogey; the signed label
// does the talking out there.
export function verdictName(degrees, par) {
  const d = degrees - par;
  if (d <= -3) return 'Albatross';
  return { '-2': 'Eagle', '-1': 'Birdie', 0: 'Par', 1: 'Bogey', 2: 'Double bogey' }[d] || null;
}

// Settle the streak against today BEFORE displaying it. recordResult only touches
// the streak when a result lands, so after missed days the stored number is stale
// until this runs — the honest-accounting fix. Pure; returns a new object only
// when something changed.
export function recomputeStreak(stats, today) {
  if (!stats.lastDate || stats.currentStreak === 0) return stats;
  const gap = dayDiff(stats.lastDate, today);
  if (gap <= 1) return stats;            // played today, or yesterday (still alive)
  return { ...stats, currentStreak: 0 };
}

// How the streak stands right now: 'safe' (played today), 'at-risk' (alive on
// yesterday's play — today still unplayed), or 'none'. Drives the UI nudge. Pure.
export function streakState(stats, today) {
  if (!stats.lastDate || stats.currentStreak === 0) return 'none';
  const gap = dayDiff(stats.lastDate, today);
  if (gap === 0) return 'safe';
  return gap === 1 ? 'at-risk' : 'none';
}

// Fold one finished daily into stats. Idempotent per date: replaying the same day
// doesn't double-count or move the streak.
export function recordResult(stats, { date, id, degrees, par, won }) {
  const s = { ...stats, histogram: { ...stats.histogram }, history: { ...stats.history } };
  if (s.lastDate === date) return s;
  const gap = s.lastDate ? dayDiff(s.lastDate, date) : null;
  s.currentStreak = gap === 1 ? s.currentStreak + 1 : 1;   // consecutive day extends; else reset
  s.maxStreak = Math.max(s.maxStreak, s.currentStreak);
  s.played += 1;
  s.lastDate = date;
  const bucket = won ? relativeLabel(degrees, par) : 'x';
  s.histogram[bucket] = (s.histogram[bucket] || 0) + 1;
  s.history[date] = { id, degrees, par, won };
  if (won) {
    s.wins += 1;
    const rel = degrees - par;
    s.best = s.best === null ? rel : Math.min(s.best, rel);
  }
  return s;
}

// Pass `today` (ISO) so the streak is settled at load — every render path then
// shows an honest number without each caller remembering to recompute.
export function loadStats(today = null) {
  let s;
  try {
    s = { ...defaultStats(), ...JSON.parse(localStorage.getItem(KEY) || '{}') };
  } catch {
    s = defaultStats();
  }
  return today ? recomputeStreak(s, today) : s;
}

export function saveStats(stats) {
  try { localStorage.setItem(KEY, JSON.stringify(stats)); } catch { /* ignore */ }
}
