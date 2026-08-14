// End-card solver tests (node solve.test.js): the shortest-route reveal and the
// geodesic count that the ritual end card renders after a run. Fixtures are
// synthetic (spoiler discipline: no real daily's chain may appear in a committed
// test), mirroring chain.test.js's corpus so both engines are pinned to the same
// tiny graph.
import { Corpus } from './docs/corpus.js';
import { shortestChain, degreesBetween, countGeodesics } from './docs/solve.js';

let pass = 0, fail = 0;
function check(label, got, want) {
  const g = JSON.stringify(got), w = JSON.stringify(want);
  const ok = g === w;
  ok ? pass++ : fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${ok ? '' : `  (got ${g}, want ${w})`}`);
}

// Same graph as chain.test.js: Heat --De Niro--> Casino --Pesci--> Goodfellas is
// one par-2 line; Heat --Kilmer--> Dead End Movie --Liotta--> Goodfellas is the
// other. Godfather II is a detour that never closes.
const CORPUS = new Corpus({
  v: 1,
  ids: [1, 2, 3, 4, 5],
  films: [['Heat', 1995], ['Casino', 1995], ['Goodfellas', 1990],
          ['The Godfather Part II', 1974], ['Dead End Movie', 2001]],
  people: ['Al Pacino', 'Robert De Niro', 'Joe Pesci', 'Val Kilmer', 'Ray Liotta'],
  cast: ['0,1,2', '1,1', '2,2', '0,1', '3,1'],
});
const HEAT = 0, CASINO = 1, GOODFELLAS = 2, GF2 = 3;

const labels = (steps) => steps.map((s) =>
  s.type === 'film' ? CORPUS.filmTitle(s.index) : CORPUS.personName(s.index));

// --- shortest chain ---
const par2 = shortestChain(CORPUS, HEAT, GOODFELLAS);
check('par-2 route found', labels(par2), ['Robert De Niro', 'Casino', 'Joe Pesci']);
check('route alternates person/film and ends on the closer',
      par2.map((s) => s.type), ['person', 'film', 'person']);

check('degree-1 route is a single person',
      labels(shortestChain(CORPUS, CASINO, GOODFELLAS)), ['Joe Pesci']);
check('start === goal is an empty chain', shortestChain(CORPUS, HEAT, HEAT), []);

// --- degrees ---
check('degreesBetween matches the route', degreesBetween(CORPUS, HEAT, GOODFELLAS), 2);
check('adjacent films are 1 degree', degreesBetween(CORPUS, CASINO, GOODFELLAS), 1);
check('Godfather II reaches Goodfellas in 2 (via De Niro -> Casino -> Pesci)',
      degreesBetween(CORPUS, GF2, GOODFELLAS), 2);

// --- unreachable ---
const ISLAND = new Corpus({
  v: 1,
  ids: [1, 2],
  films: [['Alpha', 2000], ['Beta', 2001]],
  people: ['Solo Star', 'Lone Wolf'],
  cast: ['0', '1'],
});
check('no chain between disconnected films', shortestChain(ISLAND, 0, 1), null);
check('  ... and degreesBetween says null', degreesBetween(ISLAND, 0, 1), null);

// --- geodesic counting ---
check('two distinct par-2 chains Heat -> Goodfellas (Casino line + Dead End line)',
      countGeodesics(CORPUS, HEAT, GOODFELLAS, 2), 2);
check('one par-1 chain Casino -> Goodfellas (Pesci)',
      countGeodesics(CORPUS, CASINO, GOODFELLAS, 1), 1);
check('par below the true distance counts zero',
      countGeodesics(CORPUS, HEAT, GOODFELLAS, 1), 0);
check('par 0 is not a chain', countGeodesics(CORPUS, HEAT, GOODFELLAS, 0), 0);

// Two closers from one film multiply out: build A -[p1|p2]-> B where both p1 and
// p2 are also in the goal — 2 chains at par 1.
const TWIN = new Corpus({
  v: 1,
  ids: [1, 2],
  films: [['From', 2000], ['Goal', 2001]],
  people: ['Both One', 'Both Two'],
  cast: ['0,1', '0,1'],
});
check('multiple closers in one film each count', countGeodesics(TWIN, 0, 1, 1), 2);

// The cap keeps absurd counts readable.
check('cap respected', countGeodesics(CORPUS, HEAT, GOODFELLAS, 2, 1), 1);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
