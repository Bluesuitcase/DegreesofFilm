// Degrees of Film — /match Worker (v3 Phase 1, server-side matching).
//
// POST /match  { puzzleId, rungIndex, guess }
//   -> { correct: true, canonical: "..." }   canonical ONLY when correct
//   -> { correct: false }                    NEVER canonical, NEVER answers
//
// Imports docs/match.js UNCHANGED (the campaign's key asset): server and client
// can never disagree on matching semantics. Answers live only in KV, keyed
// `answers:<puzzleId>`, value { rungs: [{ answers: [...] }, ...] } (plaintext) —
// pushed from the private curation tool (curation/push_answers.py), never from
// the public repo.
//
// Bindings (wrangler.toml): ANSWERS (KV), RATE_LIMITER (rate-limit binding,
// optional — the worker degrades to unlimited if absent so `wrangler dev`
// and tests run without it).
import { matchGuess } from '../docs/match.js';

// GitHub Pages is a different origin, so CORS is pinned to it (not '*').
export const ALLOWED_ORIGIN = 'https://bluesuitcase.github.io';

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': ALLOWED_ORIGIN,
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400',
};

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...CORS_HEADERS },
  });
}

// Per-isolate answers cache: KV reads are cheap but metered (100k/day free);
// a short TTL also bounds staleness after an edit-existing-puzzle republish.
const CACHE_TTL_MS = 5 * 60 * 1000;
const cache = new Map();   // puzzleId -> { at, value }

async function loadAnswers(env, puzzleId) {
  const hit = cache.get(puzzleId);
  if (hit && Date.now() - hit.at < CACHE_TTL_MS) return hit.value;
  const value = await env.ANSWERS.get(`answers:${puzzleId}`, 'json');
  cache.set(puzzleId, { at: Date.now(), value });
  return value;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS_HEADERS });
    if (url.pathname !== '/match')    return json({ error: 'not found' }, 404);
    if (request.method !== 'POST')    return json({ error: 'method not allowed' }, 405);

    // Rate limit per IP: legit play needs ~36 calls/game; 60/min is generous
    // for humans and hostile to scripts. Binding config in wrangler.toml.
    if (env.RATE_LIMITER) {
      const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
      const { success } = await env.RATE_LIMITER.limit({ key: ip });
      if (!success) return json({ error: 'rate limited' }, 429);
    }

    let body;
    try { body = await request.json(); } catch { return json({ error: 'bad json' }, 400); }
    const { puzzleId, rungIndex, guess } = body || {};
    if (!Number.isInteger(puzzleId) || !Number.isInteger(rungIndex) || rungIndex < 0
        || typeof guess !== 'string') {
      return json({ error: 'bad request' }, 400);
    }

    const data = await loadAnswers(env, puzzleId);
    if (!data || !Array.isArray(data.rungs)) return json({ error: 'unknown puzzle' }, 404);
    const rung = data.rungs[rungIndex];
    if (!rung || !Array.isArray(rung.answers) || rung.answers.length === 0) {
      return json({ error: 'bad rung' }, 400);
    }

    // The verdict — and on a wrong guess, NOTHING else leaves the server.
    if (matchGuess(guess, rung.answers)) {
      return json({ correct: true, canonical: rung.answers[0] });
    }
    return json({ correct: false });
  },
};
