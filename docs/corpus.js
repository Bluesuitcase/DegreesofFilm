// The shipped film<->person graph: loading, lookup, and name resolution.
// Pure logic, no DOM — imports only the matcher, so Node tests and any future
// server replay run this exact file.
//
// graph.json is one cached download (~188 KB gz) covering the whole pool, so a
// challenge is just {start, goal, par} and the shipped data leaks nothing about
// today's answer. Built by curation/graph_build.py; the two ends of the delta-hex
// adjacency encoding are tested against each other in both languages.
//
// The division that makes the game a game:
//   SUGGESTIONS are global — you can type any film or person in the pool.
//   RESOLUTION is contextual — a guess is read first against the hops that are
//   actually valid here, then against the whole pool, so the caller can tell
//   "not a real person" from "real, but not in this film".
import { normalize, levenshtein, maxDist } from './match.js';

// "0,3,1,10" -> [0, 3, 4, 20]. Mirrors graph_build.decode_deltas.
export function decodeDeltas(s) {
  if (!s) return [];
  const out = [];
  let run = 0;
  for (const part of s.split(',')) {
    run += parseInt(part, 16);
    out.push(run);
  }
  return out;
}

// Index arrays share their order with the label arrays, and that order is rank
// (film popularity / person popularity), so "first hit wins" means "most famous
// hit wins" everywhere below without shipping a rank field.
function keyIndex(keys) {
  const m = new Map();
  for (let i = 0; i < keys.length; i++) {
    if (!keys[i]) continue;
    const at = m.get(keys[i]);
    if (at) at.push(i); else m.set(keys[i], [i]);
  }
  return m;
}

// Best (= highest ranked) index in `hits` that `allowed` permits, or -1.
function pick(hits, allowed) {
  if (!hits) return -1;
  for (const i of hits) if (!allowed || allowed.has(i)) return i;
  return -1;
}

// Surname / last-word rule. In context ('any') the candidate set is a handful of
// live hops, so "Bardem" or "Fiction" is unambiguous and the best-ranked hit wins.
// Globally ('unique') it only fires when exactly one name in the pool ends that
// way — otherwise "smith" would silently resolve to whichever Smith ranks highest.
function lastTokenMatch(g, keys, pool, mode) {
  if (!mode || g.includes(' ')) return -1;
  let found = -1;
  for (let i = 0; i < keys.length; i++) {
    if (pool && !pool.has(i)) continue;
    const tokens = keys[i].split(' ');
    if (tokens.length > 1 && tokens[tokens.length - 1] === g) {
      if (mode === 'any') return i;
      if (found >= 0) return -1;                 // ambiguous surname: refuse to guess
      found = i;
    }
  }
  return found;
}

function fuzzy(g, keys, allowed, { lastToken }) {
  let best = -1, bestDist = Infinity;
  const pool = allowed || null;
  for (let i = 0; i < keys.length; i++) {
    if (pool && !pool.has(i)) continue;
    const k = keys[i];
    if (!k) continue;
    if (Math.abs(k.length - g.length) > maxDist(k.length)) continue;  // cheap prefilter
    const d = levenshtein(g, k);
    if (d <= maxDist(k.length) && d < bestDist) { best = i; bestDist = d; if (d === 0) break; }
  }
  if (best >= 0) return best;
  return lastTokenMatch(g, keys, pool, lastToken);
}

export class Corpus {
  constructor(json) {
    if (json.v !== 1) throw new Error(`unsupported corpus version ${json.v}`);
    this.ids = json.ids;                 // TMDB film id per film index
    this.films = json.films;             // [[title, year], ...] popularity order
    this.people = json.people;           // [name, ...] popularity order
    this.cast = json.cast.map(decodeDeltas);          // film index -> person indices
    this.credits = this.people.map(() => []);         // person index -> film indices
    for (let f = 0; f < this.cast.length; f++) {
      for (const p of this.cast[f]) this.credits[p].push(f);
    }
    this.byTmdb = new Map(this.ids.map((id, i) => [id, i]));
    this.filmKeys = this.films.map(([title]) => normalize(title));
    this.peopleKeys = this.people.map(normalize);
    this.filmLookup = keyIndex(this.filmKeys);
    this.peopleLookup = keyIndex(this.peopleKeys);
  }

  filmIndex(tmdbId) {
    const i = this.byTmdb.get(tmdbId);
    return i === undefined ? -1 : i;
  }

  filmTitle(i) { return this.films[i][0]; }
  filmYear(i) { return this.films[i][1]; }
  filmLabel(i) { return `${this.films[i][0]} (${this.films[i][1]})`; }
  personName(i) { return this.people[i]; }
  castOf(filmIndex) { return this.cast[filmIndex] || []; }
  filmsOf(personIndex) { return this.credits[personIndex] || []; }
  isCredited(filmIndex, personIndex) { return this.cast[filmIndex].includes(personIndex); }

  // Resolve typed text to a person/film index. `within` (a Set of indices) is the
  // set of hops that are legal right now. Returns {index, scope} where scope is
  // 'here' (a legal hop) or 'elsewhere' (real, but not playable from here), or
  // null when the text names nothing in the pool.
  resolve(text, keys, lookup, within) {
    const g = normalize(text || '');
    if (!g) return null;
    if (within) {
      const hit = pick(lookup.get(g), within);
      if (hit >= 0) return { index: hit, scope: 'here' };
      const near = fuzzy(g, keys, within, { lastToken: 'any' });
      if (near >= 0) return { index: near, scope: 'here' };
    }
    const exact = pick(lookup.get(g), null);
    if (exact >= 0) return { index: exact, scope: 'elsewhere' };
    const near = fuzzy(g, keys, null, { lastToken: 'unique' });
    return near >= 0 ? { index: near, scope: 'elsewhere' } : null;
  }

  resolvePerson(text, within) {
    return this.resolve(text, this.peopleKeys, this.peopleLookup, within);
  }

  resolveFilm(text, within) {
    return this.resolve(text, this.filmKeys, this.filmLookup, within);
  }

  // Autocomplete over the WHOLE pool (never the local candidates — suggesting only
  // valid hops would hand over the answer). Prefix hits first, then word-boundary
  // hits, each in rank order. Returns indices.
  suggest(keys, query, limit = 8) {
    const q = normalize(query || '');
    if (q.length < 2) return [];
    const starts = [], contains = [];
    for (let i = 0; i < keys.length; i++) {
      if (starts.length >= limit) break;
      const k = keys[i];
      if (k.startsWith(q)) starts.push(i);
      else if (starts.length + contains.length < limit && k.includes(' ' + q)) contains.push(i);
    }
    return starts.concat(contains).slice(0, limit);
  }

  suggestFilms(query, limit) { return this.suggest(this.filmKeys, query, limit); }
  suggestPeople(query, limit) { return this.suggest(this.peopleKeys, query, limit); }
}
