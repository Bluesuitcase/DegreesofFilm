// Chain-engine tests (node chain.test.js) — graph-mode phase G2 gate suite.
// Includes the gate's forged-chain shapes: wrong credit, skipped hop, out-of-graph.
import { Chain, CHAIN_MAX_ATTEMPTS } from './docs/chain.js';

let pass = 0, fail = 0;
function check(label, got, want) {
  const g = JSON.stringify(got), w = JSON.stringify(want);
  const ok = g === w;
  ok ? pass++ : fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${ok ? '' : `  (got ${g}, want ${w})`}`);
}

// Synthetic challenge: Heat -> Pacino -> Godfather II -> De Niro closes into Goal
// (Casino). Decoys: person 300 (only in Heat, a dead end), film 40 (only via 300).
const CH = () => new Chain({
  start: { id: 1, title: 'Heat', year: 1995 },
  goal: { id: 3, title: 'Casino', year: 1995 },
  par: 2,
  films: { 1: ['Heat', 1995], 2: ['The Godfather Part II', 1974], 3: ['Casino', 1995], 4: ['Dead End Movie', 2001] },
  people: { 100: 'Al Pacino', 200: 'Robert De Niro', 300: 'Val Kilmer', 400: 'Joe Pesci' },
  edges: [[1, 100], [1, 200], [1, 300], [2, 100], [2, 200], [3, 200], [3, 400], [4, 300]],
});

// --- the legit chain wins at par ---
let c = CH();
check('opening candidates are the start film people', c.candidates().map((x) => x.label),
      ['Al Pacino', 'Robert De Niro', 'Val Kilmer']);
check('person step accepted', c.guess('Al Pacino').result, 'correct');
check('film step accepted (matcher handles the article)', c.guess('godfather part ii').result, 'correct');
// Matcher contract carried over: single-token surname works, two-token does NOT
// ("De Niro" fails against 'Robert De Niro' exactly as it would in the dig) —
// the G0 default-on autocomplete is what makes this a non-issue in play.
check('two-token surname does not match (documented matcher rule)', c.guess('De Niro').result, 'wrong');
check('single-token surname closes the chain', c.guess('niro').result, 'won');
check('won at 2 degrees = par', [c.degrees, c.par], [2, 2]);
check('post-win guesses are ignored', c.guess('anything').result, 'ignored');

// --- direct connection wins at 1 degree ---
c = CH();
check('person also in goal closes immediately', c.guess('Robert De Niro').result, 'won');
check('direct close = 1 degree (under par)', c.degrees, 1);

// --- forged chain 1: wrong credit (person not in the current film) ---
c = CH();
c.guess('Al Pacino'); c.guess('Godfather Part II');
check('forge: person NOT credited in current film rejected', c.guess('Joe Pesci').result, 'wrong');

// --- forged chain 2: skipped hop (film the current person is not in) ---
c = CH();
c.guess('Al Pacino');
check('forge: film without the current person rejected', c.guess('Casino').result, 'wrong');
check('forge: goal film is never enterable as a step', c.guess('Casino').result, 'wrong');

// --- forged chain 3: out-of-graph name ---
c = CH();
check('forge: out-of-graph person rejected', c.guess('Tom Hanks').result, 'wrong');
check('attempts burn toward strike-out', c.guess('Meryl Streep').result, 'wrong');
check('third wrong = over', c.guess('Nicolas Cage').result, 'over');
check('status over, chain frozen', [c.status, c.degrees], ['over', 0]);

// --- no revisits: films and people are single-use ---
c = CH();
c.guess('Al Pacino'); c.guess('The Godfather Part II');
check('used person not offered again', c.candidates().map((x) => x.label), ['Robert De Niro']);
check('revisiting the start film rejected', c.guess('Heat').result, 'wrong');

// --- dead end + back(): degree spent, person stays blocked ---
c = CH();
c.guess('Val Kilmer');
check('dead-end film list excludes goal/used', c.candidates().map((x) => x.label), ['Dead End Movie']);
check('back() from a person returns to the film', c.back(), true);
check('back() does not refund the degree', c.degrees, 1);
check('dead-end person stays blocked after back()', c.candidates().map((x) => x.label),
      ['Al Pacino', 'Robert De Niro']);
check('back() only legal when expecting a film', c.back(), false);
let done = CH(); done.guess('Robert De Niro');
check('back() ignored after the game ends', done.back(), false);

// --- attempts reset on success ---
c = CH();
c.guess('nobody'); c.guess('nobody2');
check('two wrong then correct still plays', c.guess('Al Pacino').result, 'correct');
check('attempts reset after a correct step', c.guess('zzz').result === 'wrong' && c.status === 'playing', true);

check('exported attempt cap matches the dig rhythm', CHAIN_MAX_ATTEMPTS, 3);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
