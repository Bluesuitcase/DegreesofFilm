// Fuzzy answer matching for Degrees of Film.
// Pure logic, no DOM — runs in the browser (as an ES module) and in Node tests.

export function normalize(s) {
  return s
    .toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '') // strip diacritics
    .replace(/&/g, ' and ')                           // & -> and
    .replace(/[^a-z0-9\s]/g, ' ')                      // punctuation -> space
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/^(the|a|an)\s+/, '');                    // drop leading article
}

export function levenshtein(a, b) {
  const m = a.length, n = b.length;
  if (m === 0) return n;
  if (n === 0) return m;
  let prev = Array.from({ length: n + 1 }, (_, i) => i);
  let curr = new Array(n + 1);
  for (let i = 1; i <= m; i++) {
    curr[0] = i;
    for (let j = 1; j <= n; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      curr[j] = Math.min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost);
    }
    [prev, curr] = [curr, prev];
  }
  return prev[n];
}

// How many typo-edits to forgive, scaled to the target answer's length.
export function maxDist(len) {
  if (len <= 3) return 0;
  if (len <= 6) return 1;
  if (len <= 10) return 2;
  return Math.floor(len * 0.2);
}

// Does `guess` match any accepted answer for a rung?
export function matchGuess(guess, answers) {
  const g = normalize(guess);
  if (!g) return false;
  for (const ans of answers) {
    const a = normalize(ans);
    if (!a) continue;
    if (g === a) return true;                                  // exact (post-normalize)
    if (levenshtein(g, a) <= maxDist(a.length)) return true;   // typos
    const tokens = a.split(' ');                               // surname / last-token
    if (tokens.length > 1 && !g.includes(' ') && g === tokens[tokens.length - 1]) {
      return true;
    }
  }
  return false;
}
