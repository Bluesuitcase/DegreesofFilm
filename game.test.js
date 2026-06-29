import { Game, scoreForRung } from './docs/game.js';

let pass = 0, fail = 0;
function check(label, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  ok ? pass++ : fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${ok ? '' : `  (got ${JSON.stringify(got)}, want ${JSON.stringify(want)})`}`);
}

// --- scoring curve (the fiddly part) ---
const curve = [1,2,3,4,5,6,7,8,9,10,11,12].map(scoreForRung);
check('score curve rungs 1-12', curve, [1,2,3,4,5,7,9,11,13,15,16,17]);

// --- a scripted playthrough on a tiny 5-rung puzzle ---
const puzzle = { rungs: [
  { role:'Film',     answers:['Alpha'] },
  { role:'Cast',     answers:['Bravo'] },
  { role:'Director', answers:['Charlie'] },
  { role:'DP',       answers:['Delta'] },
  { role:'Editor',   answers:['Echo'] },
]};

// solve rung1 (+1), solve rung2 (+2) => score 3, depth 2
let g = new Game(puzzle);
g.guess('Alpha'); g.guess('Bravo');
check('solve two: score', g.score, 3);
check('solve two: depth', g.depth, 2);

// skip rung3 (-1) => score 2, skipsUsed 1, depth 3
g.skip();
check('after skip: score', g.score, 2);
check('after skip: depth', g.depth, 3);
check('after skip: skipsLeft', g.skipsLeft, 4);

// three wrong on rung4 => strikeout, status over, depth stays 3
g.guess('x'); g.guess('y');
check('two wrong still playing', g.status, 'playing');
const r = g.guess('z');
check('third wrong is strikeout', r.result, 'strikeout');
check('strikeout ends run', g.status, 'over');
check('depth frozen at strikeout', g.depth, 3);

// --- skip cap: exhaust 5 skips then 6th ends the run ---
let h = new Game(puzzle);
for (let i = 0; i < 5; i++) h.skip();     // uses all 5 (puzzle only has 5 rungs though)
// rebuild on a longer puzzle to test the cap cleanly
const long = { rungs: Array.from({length:8}, (_,i)=>({role:'r',answers:['z'+i]})) };
let k = new Game(long);
for (let i = 0; i < 5; i++) k.skip();
check('5 skips used, still playing', k.status, 'playing');
check('skipsLeft is 0', k.skipsLeft, 0);
const out = k.skip();
check('6th skip ends run', out.result, 'out_of_skips');
check('status over after 6th skip', k.status, 'over');

// --- winning: solve every rung ---
let w = new Game(puzzle);
['Alpha','Bravo','Charlie','Delta','Echo'].forEach(a => w.guess(a));
check('solve all -> won', w.status, 'won');
check('win depth == total', w.depth, w.total);
check('win score 1+2+3+4+5', w.score, 15);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
