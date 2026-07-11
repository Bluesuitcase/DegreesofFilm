// Movie Buff autocomplete core (prototype behind ?buff=1). Pure logic, no DOM.
// Filters the prebaked title index (title-index.json: [[title, year], ...],
// popularity-ordered) using the SAME normalize() the matcher applies to guesses,
// so any suggested title survives matching by construction. The index adapts to
// the matcher, never the reverse.
import { normalize } from './match.js';

// Precomputed normalized keys, aligned by index with the entries array.
export function indexKeys(entries) {
  return entries.map(([title]) => normalize(title));
}

// Top suggestions for a partial guess: prefix matches first (index order =
// popularity order), then word-boundary substring matches. Queries under 2
// normalized characters suggest nothing (too noisy).
export function suggest(entries, keys, query, limit = 7) {
  const q = normalize(query || '');
  if (q.length < 2) return [];
  const starts = [], contains = [];
  for (let i = 0; i < keys.length; i++) {
    if (starts.length >= limit) break;
    const k = keys[i];
    if (k.startsWith(q)) starts.push(entries[i]);
    else if (starts.length + contains.length < limit && k.includes(' ' + q)) contains.push(entries[i]);
  }
  return starts.concat(contains).slice(0, limit);
}
