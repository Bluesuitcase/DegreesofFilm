// Chain-engine tests (node chain.test.js) — Degrees played against the shared
// corpus. Carries the old G2 gate's forged-chain shapes (wrong credit, skipped hop,
// out-of-graph name) and pins the new verdict contract: only a real-but-illegal hop
// burns an attempt.
import { Corpus } from './docs/corpus.js';
import { Chain, CHAIN_MAX_ATTEMPTS } from './docs/chain.js';

let pass = 0, fail = 0;
function check(label, got, want) {
  const g = JSON.stringify(got), w = JSON.stringify(want);
  const ok = g === w;
  ok ? pass++ : fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${ok ? '' : `  (got ${g}, want ${w})`}`);
}

// Heat --De Niro--> Casino --Pesci--> Goodfellas is the par-2 line. Nobody in Heat
// is credited in Goodfellas, so par really is 2. Godfather II and Dead End Movie are
// the detours that make dead ends and back() testable. Outer Reach hangs one hop
// further out (Far Guy is 2 from Heat's cast) and the Isle pair is disconnected
// entirely — the near-miss temperature ladder.
const CORPUS = new Corpus({
  v: 1,
  ids: [1, 2, 3, 4, 5, 6, 7],
  films: [['Heat', 1995], ['Casino', 1995], ['Goodfellas', 1990],
          ['The Godfather Part II', 1974], ['Dead End Movie', 2001],
          ['Outer Reach', 2010], ['Isle Story', 2015]],
  people: ['Al Pacino', 'Robert De Niro', 'Joe Pesci', 'Val Kilmer', 'Ray Liotta',
           'Far Guy', 'Isle One', 'Isle Two'],
  cast: ['0,1,2', '1,1', '2,2', '0,1', '3,1', '2,3', '6,1'],
});
const CH = () => new Chain(CORPUS, { id: 1, start: 1, goal: 3, par: 2 });

// --- setup ---
let c = CH();
check('start and goal resolve by TMDB id', [c.startLabel, c.goalLabel],
      ['Heat (1995)', 'Goodfellas (1990)']);
check('opens expecting a person', c.expecting, 'person');

// --- the par line ---
check('person step accepted', c.guess('Robert De Niro').result, 'correct');
check('now expecting a film', c.expecting, 'film');
check('film step accepted', c.guess('Casino').result, 'correct');
check('person credited in the goal closes the chain', c.guess('Joe Pesci').result, 'won');
check('won at 2 degrees = par', [c.degrees, c.par], [2, 2]);
check('post-win guesses ignored', c.guess('anything').result, 'ignored');

// --- a longer route still wins, over par ---
c = CH();
c.guess('Al Pacino'); c.guess('The Godfather Part II'); c.guess('Robert De Niro');
c.guess('Casino');
check('detour route closes too', c.guess('Joe Pesci').result, 'won');
check('three degrees, one over par', [c.degrees, c.par], [3, 2]);

// --- verdict contract: what burns and what does not ---
c = CH();
check('unrecognized name is free', c.guess('Zzz Nobody').result, 'unknown');
check('  ... and burns nothing', c.attempts, 0);
check('a film typed where a person belongs is free',
      c.guess('Casino').reason, 'wrongType');
check('  ... and burns nothing', c.attempts, 0);
const notHere = c.guess('Joe Pesci');
check('a real person not in this film is wrong', notHere.result, 'wrong');
check('  ... with the reason and both labels for the message',
      [notHere.reason, notHere.label, notHere.film],
      ['notCredited', 'Joe Pesci', 'Heat (1995)']);
check('  ... and burns an attempt', c.attempts, 1);
check('attemptsLeft counts down', c.guess('Ray Liotta').attemptsLeft, CHAIN_MAX_ATTEMPTS - 2);
check('third burn ends the run', c.guess('Ray Liotta').result, 'over');
check('run frozen at zero degrees', [c.status, c.degrees], ['over', 0]);

// --- typo tolerance survives, in context ---
c = CH();
check('typo in a legal hop still lands', c.guess('Robert De Nir').result, 'correct');
c = CH();
check('surname alone lands a legal hop', c.guess('kilmer').result, 'correct');

// --- the goal film is never a step ---
c = CH();
c.guess('Robert De Niro');
const g = c.guess('Goodfellas');
check('naming the goal is a rules slip, not a wrong answer',
      [g.result, g.reason], ['unknown', 'goalFilm']);
check('  ... and burns nothing', c.attempts, 0);

// --- no revisiting ---
c = CH();
c.guess('Robert De Niro'); c.guess('Casino');
const again = c.guess('Robert De Niro');
check('a spent person is blocked, with a distinct reason',
      [again.result, again.reason], ['wrong', 'used']);

// --- forged chains (the old G2 gate shapes) ---
c = CH();
c.guess('Al Pacino');
check('forge: film the current person is not in is rejected',
      c.guess('Dead End Movie').result, 'wrong');
c = CH();
check('forge: out-of-corpus person is not a hop', c.guess('Tom Hanks').result, 'unknown');

// --- back() out of a dead end ---
c = CH();
c.guess('Val Kilmer');
check('dead-end person accepted (Heat -> Kilmer)', c.expecting, 'film');
check('back() returns to the film', c.back(), true);
check('  ... expecting a person again', c.expecting, 'person');
check('  ... the degree is spent, no refund', c.degrees, 1);
check('  ... and that person stays blocked', c.guess('Val Kilmer').reason, 'used');
check('back() only from a film step', CH().back(), false);

// --- legalMoves is the answer, and is not what the player sees ---
c = CH();
check('legalMoves lists the start cast', [...c.legalMoves()].sort(), [0, 1, 3]);
check('suggestions are global, not the legal set',
      CORPUS.suggestPeople('joe').includes(2), true);

// --- a challenge pointing outside the corpus fails loudly (stale daily after a rebuild) ---
let threw = '';
try { new Chain(CORPUS, { id: 9, start: 1, goal: 999, par: 2 }); } catch (e) { threw = e.message; }
check('unknown challenge film throws', threw.includes('not in this corpus'), true);

// --- near-miss temperature on burns (measured 2026-08-14: d=1 27% / d=2 60% /
// --- d=3+ 15% over the real corpus — every bucket is signal) ---
c = CH();
let miss = c.guess('Joe Pesci');
check('a warm miss carries d=1 and a witness year, never a name',
      miss.near, { d: 1, year: 1995 });
miss = c.guess('Far Guy');
check('two hops out reads d=2, no witness', miss.near, { d: 2 });
miss = c.guess('Isle One');
check('a disconnected guess reads cold (d=3)', miss.near, { d: 3 });
c = CH();
c.guess('Robert De Niro'); c.guess('Casino');
check('a spent person burns WITHOUT near-miss info (already known-connected)',
      'near' in c.guess('Robert De Niro'), false);
c = CH();
c.guess('Al Pacino');
check('film-step burns get temperature too (person -> guessed film)',
      c.guess('Dead End Movie').near, { d: 1, year: 1995 });

// --- mid-run persistence: toJSON/fromJSON round-trips portably ---
const CHALLENGE = { id: 1, start: 1, goal: 3, par: 2 };
c = CH();
c.guess('Robert De Niro'); c.guess('Casino');
let saved = c.toJSON();
check('save carries films as TMDB ids, people as names',
      saved.chain, [{ t: 'p', n: 'Robert De Niro' }, { t: 'f', id: 2 }]);
let back = Chain.fromJSON(CORPUS, CHALLENGE, saved);
check('restore rebuilds position/expecting/degrees',
      [back.position, back.expecting, back.degrees, back.status],
      [c.position, c.expecting, c.degrees, c.status]);
check('restored run plays on to the win', back.guess('Joe Pesci').result, 'won');

// back() state survives: the popped person stays blocked across a save.
c = CH();
c.guess('Val Kilmer'); c.back();
back = Chain.fromJSON(CORPUS, CHALLENGE, c.toJSON());
check('backed-out person stays blocked after restore',
      back.guess('Val Kilmer').reason, 'used');
check('  ... and the spent degree survives', back.degrees, 1);
check('  ... expecting a person again', back.expecting, 'person');

// Burn count survives so a reload can't refund attempts.
c = CH();
c.guess('Joe Pesci'); // wrong here: burns 1
back = Chain.fromJSON(CORPUS, CHALLENGE, c.toJSON());
check('attempts survive the round-trip', back.attempts, 1);

// Discard-on-mismatch: wrong challenge, or names that no longer resolve.
check('save for another challenge is rejected',
      Chain.fromJSON(CORPUS, { id: 2, start: 1, goal: 3, par: 2 }, c.toJSON()), null);
saved = CH().toJSON();
saved.chain = [{ t: 'p', n: 'Gone From Corpus' }];
check('unresolvable person discards the save', Chain.fromJSON(CORPUS, CHALLENGE, saved), null);
saved = CH().toJSON();
saved.usedF = [999];
check('unresolvable film id discards the save', Chain.fromJSON(CORPUS, CHALLENGE, saved), null);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
