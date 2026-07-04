import { matchGuess } from './docs/match.js';
import { cases } from './match.cases.js';

// The case table lives in match.cases.js (shared with worker.test.js so the
// server parity check can never drift from this contract). Add cases THERE.

let pass = 0, fail = 0;
for (const [guess, answers, expected, label] of cases) {
  const got = matchGuess(guess, answers);
  const ok = got === expected;
  ok ? pass++ : fail++;
  const mark = ok ? "PASS" : "FAIL";
  const want = expected ? "match " : "reject";
  console.log(`${mark}  want ${want}  ${JSON.stringify(guess).padEnd(26)} ${label}${ok ? "" : `  <-- got ${got}`}`);
}
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
