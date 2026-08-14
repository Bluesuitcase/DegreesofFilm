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
    history: {},                    // date -> { id, degrees, par, won[, playedOn] }
    archive: {},                    // id -> { degrees, par, won } — replays, isolated
  };
}

// A loss carries this penalty in the handicap — fixed and documented so the
// number can't be gamed by abandoning bad runs.
export const LOSS_PENALTY = 3;

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
export function recordResult(stats, { date, id, degrees, par, won, playedOn }) {
  const s = { ...stats, histogram: { ...stats.histogram }, history: { ...stats.history } };
  if (s.lastDate === date) return s;
  const gap = s.lastDate ? dayDiff(s.lastDate, date) : null;
  s.currentStreak = gap === 1 ? s.currentStreak + 1 : 1;   // consecutive day extends; else reset
  s.maxStreak = Math.max(s.maxStreak, s.currentStreak);
  s.played += 1;
  s.lastDate = date;
  const bucket = won ? relativeLabel(degrees, par) : 'x';
  s.histogram[bucket] = (s.histogram[bucket] || 0) + 1;
  // playedOn stamps day-of play (gold calendar cells); absent on legacy records,
  // which the calendar treats as day-of.
  s.history[date] = { id, degrees, par, won, ...(playedOn ? { playedOn } : {}) };
  if (won) {
    s.wins += 1;
    const rel = degrees - par;
    s.best = s.best === null ? rel : Math.min(s.best, rel);
  }
  return s;
}

// --- portable backup codes -------------------------------------------------
// The Wordle->NYT migration mechanism: the record serialized into a copyable
// code, user-triggered, no server. Version-prefixed so schema changes stay
// importable. Encoding is byte-safe (future titles may be non-Latin-1).

const EXPORT_PREFIX = 'DOF1.';

function b64encode(s) { return btoa(unescape(encodeURIComponent(s))); }
function b64decode(s) { return decodeURIComponent(escape(atob(s))); }

export function exportRecord(stats) {
  return EXPORT_PREFIX +
    b64encode(JSON.stringify({ history: stats.history || {}, archive: stats.archive || {} }));
}

// Which of two results for the SAME puzzle deserves the record: a win beats a
// loss, then fewer over par.
function better(a, b) {
  if (!b) return a;
  if (Boolean(a.won) !== Boolean(b.won)) return a.won ? a : b;
  return (a.degrees - a.par) <= (b.degrees - b.par) ? a : b;
}

// Merge a backup code into `stats`: union both histories/archives keeping the
// better run per day, then REBUILD every derived field — a max'd streak or a
// summed histogram would be inconsistent with the merged history. Returns the
// merged stats, or null when the code is corrupt or from an unknown version.
export function importRecord(stats, code) {
  if (typeof code !== 'string' || !code.trim().startsWith(EXPORT_PREFIX)) return null;
  let data;
  try {
    data = JSON.parse(b64decode(code.trim().slice(EXPORT_PREFIX.length)));
  } catch {
    return null;
  }
  if (!data || typeof data.history !== 'object' || data.history === null) return null;
  const history = { ...(stats.history || {}) };
  for (const [date, r] of Object.entries(data.history)) {
    if (!r || typeof r.degrees !== 'number' || typeof r.par !== 'number') continue;
    history[date] = history[date] ? better(history[date], r) : r;
  }
  const archive = { ...(stats.archive || {}) };
  for (const [id, r] of Object.entries(data.archive || {})) {
    if (!r || typeof r.degrees !== 'number' || typeof r.par !== 'number') continue;
    archive[id] = archive[id] ? better(archive[id], r) : r;
  }
  return rebuildStats(history, archive);
}

// Pass `today` (ISO) so the streak is settled at load — every render path then
// shows an honest number without each caller remembering to recompute.
// Fold a REPLAY result into the isolated archive channel: replays never touch
// the streak, the histogram, or the scorecard — they fill calendar cells. Keyed
// by puzzle id (a replay can happen on any date), keep-better: a win beats a
// loss, then fewer over par. Pure.
export function recordArchive(stats, { id, degrees, par, won }) {
  const s = { ...stats, archive: { ...(stats.archive || {}) } };
  const prev = s.archive[id];
  const better = !prev
    || (won && !prev.won)
    || (won === Boolean(prev.won) && degrees - par < prev.degrees - prev.par);
  if (better) s.archive[id] = { degrees, par, won };
  return s;
}

// The golfer's number: rolling average vs par across every recorded daily, one
// decimal. Losses count LOSS_PENALTY. Null until `min` rounds exist — a handicap
// over three data points is noise that teaches players to ignore it. Pure.
export function handicap(stats, min = 10) {
  const rows = Object.values(stats.history || {});
  if (!rows.length || rows.length < min) return null;
  const sum = rows.reduce((t, r) => t + (r.won ? r.degrees - r.par : LOSS_PENALTY), 0);
  return Math.round((sum / rows.length) * 10) / 10;
}

// Rebuild every derived field from the history map alone — the single source of
// truth after an import merge (a max'd streak or summed histogram would lie).
// Streaks are runs of consecutive dates; the current streak counts only if it
// ends at the newest recorded date. Pure.
export function rebuildStats(history, archive = {}) {
  const s = { ...defaultStats(), history: { ...history }, archive: { ...archive } };
  const dates = Object.keys(history).sort();
  let run = 0;
  for (let i = 0; i < dates.length; i++) {
    const r = history[dates[i]];
    s.played += 1;
    run = i > 0 && dayDiff(dates[i - 1], dates[i]) === 1 ? run + 1 : 1;
    s.maxStreak = Math.max(s.maxStreak, run);
    const bucket = r.won ? relativeLabel(r.degrees, r.par) : 'x';
    s.histogram[bucket] = (s.histogram[bucket] || 0) + 1;
    if (r.won) {
      s.wins += 1;
      const rel = r.degrees - r.par;
      s.best = s.best === null ? rel : Math.min(s.best, rel);
    }
  }
  s.lastDate = dates[dates.length - 1] || null;
  s.currentStreak = dates.length ? run : 0;
  return s;
}

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
