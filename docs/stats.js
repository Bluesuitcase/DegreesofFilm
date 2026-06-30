// Player stats + daily streak, persisted in localStorage. The streak/histogram
// math (recordResult) is pure and node-testable; load/save touch localStorage.

const KEY = 'dof-stats-v1';

export function defaultStats() {
  return {
    played: 0, wins: 0, bestDepth: 0,
    currentStreak: 0, maxStreak: 0,
    lastDate: null, lastDepth: 0,
    histogram: {},                 // depth -> times reached
  };
}

// Whole days from a -> b for 'YYYY-MM-DD' strings (UTC-safe, DST-proof).
function dayDiff(a, b) {
  return Math.round((Date.parse(b + 'T00:00:00Z') - Date.parse(a + 'T00:00:00Z')) / 86400000);
}

// Fold one finished run into stats. Idempotent per date: replaying the same day
// (e.g. "Play again") doesn't double-count or move the streak.
export function recordResult(stats, { date, depth, won }) {
  const s = { ...stats, histogram: { ...stats.histogram } };
  if (s.lastDate === date) return s;
  const gap = s.lastDate ? dayDiff(s.lastDate, date) : null;
  s.currentStreak = gap === 1 ? s.currentStreak + 1 : 1;   // consecutive day extends; else reset
  s.maxStreak = Math.max(s.maxStreak, s.currentStreak);
  s.played += 1;
  if (won) s.wins += 1;
  s.bestDepth = Math.max(s.bestDepth, depth);
  s.lastDepth = depth;
  s.lastDate = date;
  s.histogram[depth] = (s.histogram[depth] || 0) + 1;
  return s;
}

export function loadStats() {
  try {
    return { ...defaultStats(), ...JSON.parse(localStorage.getItem(KEY) || '{}') };
  } catch {
    return defaultStats();
  }
}

export function saveStats(stats) {
  try { localStorage.setItem(KEY, JSON.stringify(stats)); } catch { /* ignore */ }
}
