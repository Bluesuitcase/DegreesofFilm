import { Game, scoreForRung, MAX_HELPS } from './docs/game.js';

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

// --- I Need Help lifeline ---
const helpPuzzle = { rungs: [
  { role:'Film', answers:['Alpha'], decoys:['Beta','Gamma','Delta'] },
  { role:'Cast', answers:['Bravo'], decoys:['Echo','Foxtrot','Golf'] },
  { role:'Cast', answers:['Charlie'] },                 // no decoys
]};

let H = new Game(helpPuzzle);
check('useHelp returns answer + decoys', H.useHelp(), ['Alpha','Beta','Gamma','Delta']);
check('useHelp spends a help', H.helpsLeft, MAX_HELPS - 1);
check('cannot help the same rung twice', H.useHelp(), null);
H.guess('Alpha');                                       // solve via the choice
check('helped rung scores 0', H.score, 0);
check('helped rung still advances depth', H.depth, 1);
check('help flag resets on the next rung', H.helped, false);
H.guess('Bravo');                                       // no help here
check('next (unhelped) rung scores normally', H.score, 2);

// a wrong pick under help still burns an attempt and can strike out
let H2 = new Game(helpPuzzle);
H2.useHelp();
H2.guess('Beta'); H2.guess('Gamma');
check('two wrong picks still playing', H2.status, 'playing');
check('wrong picks burned attempts', H2.attemptsLeft, 1);
check('third wrong pick strikes out', H2.guess('Delta').result, 'strikeout');

// a rung with no decoys can't be helped
let H3 = new Game(helpPuzzle);
H3.guess('Alpha'); H3.guess('Bravo');                   // advance to the no-decoy rung
check('no decoys -> no help', H3.useHelp(), null);

// help is capped at MAX_HELPS per game
let H4 = new Game({ rungs: Array.from({length:5}, (_,i)=>({role:'r',answers:['z'+i],decoys:['a','b','c']})) });
for (let i = 0; i < MAX_HELPS; i++) { H4.useHelp(); H4.guess('z'+i); }
check('all helps used', H4.helpsLeft, 0);
check('help denied past the cap', H4.useHelp(), null);

// --- Poser mode: flat +1 per correct (no curve, no help cap) ---
let P = new Game(puzzle, { mode: 'poser' });
P.guess('Alpha'); P.guess('Bravo'); P.guess('Charlie'); P.guess('Delta');
check('poser scores flat +1 per rung', P.score, 4);
check('poser depth tracks normally', P.depth, 4);
check('poser mode flag set', P.mode, 'poser');
check('default mode is cinephile', new Game(puzzle).mode, 'cinephile');

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
