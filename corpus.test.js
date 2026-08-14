// Corpus tests (node corpus.test.js) — the shipped graph's loader, name resolution
// and suggestions. Two halves: a synthetic fixture that pins the contract, then
// structural checks against the REAL docs/graph.json (invariants only, never a
// specific title, so a corpus rebuild can't break the suite).
import { readFileSync } from 'node:fs';
import { Corpus, decodeDeltas } from './docs/corpus.js';

let pass = 0, fail = 0;
function check(label, got, want) {
  const g = JSON.stringify(got), w = JSON.stringify(want);
  const ok = g === w;
  ok ? pass++ : fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${ok ? '' : `  (got ${g}, want ${w})`}`);
}

// Rank order matters: index order IS popularity order in a real corpus.
// people: 0 Al Pacino, 1 Robert De Niro, 2 Joe Pesci, 3 Val Kilmer, 4 Chris Evans, 5 Luke Evans
// "Heat" appears twice (1995 at rank 0, 1986 at rank 4) to pin duplicate-title handling.
const FIXTURE = {
  v: 1,
  ids: [1, 2, 3, 4, 5],
  films: [['Heat', 1995], ['The Godfather Part II', 1974], ['Casino', 1995],
          ['Dead End Movie', 2001], ['Heat', 1986]],
  people: ['Al Pacino', 'Robert De Niro', 'Joe Pesci', 'Val Kilmer', 'Chris Evans', 'Luke Evans'],
  cast: ['0,1,2', '0,1', '1,1', '2,1,1', '2,1,2'],
};
const c = new Corpus(FIXTURE);

// --- adjacency encoding ---
check('decodeDeltas is the hex-gap inverse', decodeDeltas('0,3,1,10'), [0, 3, 4, 20]);
check('empty adjacency decodes to []', decodeDeltas(''), []);
check('cast decoded per film', c.castOf(0), [0, 1, 3]);
check('adjacency inverted to person -> films', c.filmsOf(1), [0, 1, 2]);
check('isCredited reads the graph', [c.isCredited(0, 0), c.isCredited(2, 0)], [true, false]);

// --- stable ids, labels ---
check('film looked up by TMDB id, not position', c.filmIndex(3), 2);
check('unknown TMDB id -> -1', c.filmIndex(999), -1);
check('label carries the year (duplicate titles need it)', c.filmLabel(4), 'Heat (1986)');

// --- resolution: in context ---
const inHeat = new Set(c.castOf(0));
check('exact person in context', c.resolvePerson('Al Pacino', inHeat), { index: 0, scope: 'here' });
check('typo tolerated in context', c.resolvePerson('Al Pacnio', inHeat), { index: 0, scope: 'here' });
check('surname alone works in context', c.resolvePerson('kilmer', inHeat), { index: 3, scope: 'here' });
check('person real but not in this film -> elsewhere',
      c.resolvePerson('Joe Pesci', inHeat), { index: 2, scope: 'elsewhere' });
check('nobody by that name -> null', c.resolvePerson('Tom Hanks', inHeat), null);
check('empty guess -> null', c.resolvePerson('   ', inHeat), null);

// --- resolution: the surname line (the deliberate asymmetry) ---
check('unique surname resolves globally', c.resolvePerson('pesci', null),
      { index: 2, scope: 'elsewhere' });
check('ambiguous surname refuses to guess globally', c.resolvePerson('evans', null), null);
check('but an ambiguous surname is fine in context',
      c.resolvePerson('evans', new Set([5])), { index: 5, scope: 'here' });

// --- resolution: films, duplicate titles, article handling ---
check('duplicate title resolves to the higher-ranked film',
      c.resolveFilm('heat', null), { index: 0, scope: 'elsewhere' });
check('context beats rank for duplicate titles',
      c.resolveFilm('heat', new Set([4])), { index: 4, scope: 'here' });
check('matcher drops the leading article',
      c.resolveFilm('godfather part ii', null), { index: 1, scope: 'elsewhere' });
check('last-word rule applies to titles in context too',
      c.resolveFilm('casino', new Set([2])), { index: 2, scope: 'here' });

// --- suggestions are GLOBAL (suggesting only valid hops would give away the hop) ---
check('prefix suggestions, rank ordered', c.suggestFilms('heat'), [0, 4]);
check('suggestions ignore the leading article', c.suggestFilms('the god'), [1]);
check('word-boundary suggestions after prefix hits', c.suggestFilms('part'), [1]);
check('person prefix suggestions', c.suggestPeople('al pac'), [0]);
check('one character suggests nothing', c.suggestPeople('a'), []);
check('suggestions are not filtered by playability',
      c.suggestPeople('joe').includes(2), true);
check('limit respected', c.suggestPeople('', 3).length, 0);

// --- version guard ---
let threw = '';
try { new Corpus({ ...FIXTURE, v: 99 }); } catch (e) { threw = e.message; }
check('unsupported corpus version throws', threw.includes('version 99'), true);

// --- the real asset: invariants only ---
const real = new Corpus(JSON.parse(readFileSync('./docs/graph.json', 'utf8')));
check('real corpus: arrays aligned',
      [real.films.length === real.ids.length, real.films.length === real.cast.length],
      [true, true]);
check('real corpus: every film has at least one credit',
      real.cast.every((x) => x.length > 0), true);
check('real corpus: every person connects two or more films',
      real.credits.every((f) => f.length >= 2), true);
check('real corpus: TMDB lookup covers every film', real.byTmdb.size, real.films.length);
check('real corpus: a known-absent name resolves to null',
      real.resolvePerson('Zzzqx Nonexistentov', null), null);

// Worst case for the client: a guess that hits nothing has to fuzzy-scan the whole
// pool. Keep it comfortably inside a keystroke budget.
const t0 = Date.now();
for (let i = 0; i < 50; i++) real.resolvePerson(`Qwerty Nonesuch ${i}`, null);
const perMiss = (Date.now() - t0) / 50;
check(`real corpus: worst-case resolve under 20 ms (measured ${perMiss.toFixed(1)} ms)`,
      perMiss < 20, true);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
