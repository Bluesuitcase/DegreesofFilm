// /match Worker tests (node worker.test.js). Exercises server/worker.js's real
// fetch handler in-process with a stub KV env — no network, no account.
//
// The heart is the parity block: the ENTIRE match.cases.js table (the matcher
// contract) replayed through the endpoint. GATE 1 check 3 runs this same table
// against the LIVE endpoint after deploy; 25/25 here proves the handler wiring,
// 25/25 there proves the deployment.
import worker, { ALLOWED_ORIGIN } from './server/worker.js';
import { cases } from './match.cases.js';

let pass = 0, fail = 0;
function check(label, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  ok ? pass++ : fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${ok ? '' : `  (got ${JSON.stringify(got)}, want ${JSON.stringify(want)})`}`);
}

// Stub env: one puzzle per contract case (rung 0 holds that case's answer list),
// plus puzzle 900 with two rungs for rung-index tests.
const store = new Map();
cases.forEach(([, answers], i) => {
  store.set(`answers:${100 + i}`, { rungs: [{ answers }] });
});
store.set('answers:900', { rungs: [{ answers: ['Alpha'] }, { answers: ['Bravo', 'Beta'] }] });

const env = {
  ANSWERS: { get: async (key, type) => (type === 'json' ? store.get(key) ?? null : null) },
};

function post(body, { method = 'POST', path = '/match' } = {}) {
  return worker.fetch(new Request(`https://dof-match.example.workers.dev${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: method === 'POST' ? JSON.stringify(body) : undefined,
  }), env);
}

// --- parity: the full matcher contract through the endpoint ---
let parityOk = 0;
for (let i = 0; i < cases.length; i++) {
  const [guess, , expected, label] = cases[i];
  const res = await post({ puzzleId: 100 + i, rungIndex: 0, guess });
  const body = await res.json();
  if (body.correct === expected) parityOk++;
  else console.log(`FAIL  parity: ${label}  (got ${JSON.stringify(body)}, want correct=${expected})`);
}
check(`parity with match.cases.js (${cases.length} cases)`, parityOk, cases.length);

// --- response contract: no answer material ever leaks ---
let res = await post({ puzzleId: 900, rungIndex: 1, guess: 'zzz definitely wrong' });
check('wrong guess body is EXACTLY {correct:false}', await res.json(), { correct: false });
check('wrong guess status 200', res.status, 200);

res = await post({ puzzleId: 900, rungIndex: 1, guess: 'Bravo' });
check('correct guess carries canonical (answers[0])', await res.json(), { correct: true, canonical: 'Bravo' });

res = await post({ puzzleId: 900, rungIndex: 1, guess: 'Beta' });
check('alternate answer form matches, canonical still answers[0]',
      await res.json(), { correct: true, canonical: 'Bravo' });

// --- routing + validation ---
res = await post({ puzzleId: 999, rungIndex: 0, guess: 'x' });
check('unknown puzzle -> 404', res.status, 404);
res = await post({ puzzleId: 900, rungIndex: 5, guess: 'x' });
check('rung index out of range -> 400', res.status, 400);
res = await post({ puzzleId: '900', rungIndex: 0, guess: 'x' });
check('non-integer puzzleId -> 400', res.status, 400);
res = await post({ puzzleId: 900, rungIndex: 0, guess: 42 });
check('non-string guess -> 400', res.status, 400);
res = await worker.fetch(new Request('https://x.dev/match', { method: 'POST', body: 'not json' }), env);
check('malformed json -> 400', res.status, 400);
res = await post(null, { method: 'GET' });
check('GET -> 405', res.status, 405);
res = await post({ puzzleId: 900, rungIndex: 0, guess: 'x' }, { path: '/other' });
check('unknown path -> 404', res.status, 404);

// --- CORS pinned to the Pages origin (not *) ---
res = await post({ puzzleId: 900, rungIndex: 0, guess: 'Alpha' });
check('CORS origin pinned', res.headers.get('Access-Control-Allow-Origin'), ALLOWED_ORIGIN);
res = await post(null, { method: 'OPTIONS' });
check('preflight 204', res.status, 204);
check('preflight allows POST', res.headers.get('Access-Control-Allow-Methods'), 'POST, OPTIONS');

// --- rate limiting: denial -> 429; absent binding -> unlimited (already proven above) ---
const limitedEnv = { ...env, RATE_LIMITER: { limit: async () => ({ success: false }) } };
res = await worker.fetch(new Request('https://x.dev/match', {
  method: 'POST', body: JSON.stringify({ puzzleId: 900, rungIndex: 0, guess: 'Alpha' }),
}), limitedEnv);
check('rate-limit denial -> 429', res.status, 429);
const openEnv = { ...env, RATE_LIMITER: { limit: async () => ({ success: true }) } };
res = await worker.fetch(new Request('https://x.dev/match', {
  method: 'POST', body: JSON.stringify({ puzzleId: 900, rungIndex: 0, guess: 'Alpha' }),
}), openEnv);
check('rate-limit pass -> verdict flows', (await res.json()).correct, true);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
