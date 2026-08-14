// DOM glue for Degrees. All rules live in chain.js, all graph knowledge in
// corpus.js, and the end-card's route math in solve.js — this file only fetches,
// renders and wires buttons.
//
// Routes: ?  home · ?play today's daily · ?id=N replay a past daily ·
//         ?archive the index · ?history your scorecard
//
// The corpus (~188 KB gz) is fetched only when you actually play; home and archive
// render from challenges.json alone, which carries each day's two film titles.
//
// Persistence (all localStorage, all daily-only — replays touch nothing):
//   dof-run-v1   today's FINISHED result, so revisiting ?play shows the end card
//                (with the countdown) instead of silently restarting the puzzle.
//   dof-live-v1  the in-progress run, saved after every move, so a reload never
//                wipes a chain. Serialized portably (chain.js toJSON) and discarded
//                on any mismatch rather than restored wrong.
import { Corpus } from './corpus.js';
import { Chain, CHAIN_MAX_ATTEMPTS } from './chain.js';
import { pickPuzzle, pickById, todayISO } from './daily.js';
import { loadStats, saveStats, recordResult, relativeLabel, streakState } from './stats.js';
import { shortestChain, countGeodesics } from './solve.js';

const $ = (id) => document.getElementById(id);
const SITE = 'https://bluesuitcase.github.io/DegreesofFilm/';
const RUN_KEY = 'dof-run-v1';
const LIVE_KEY = 'dof-live-v1';

let corpus = null;
let game = null;
let entry = null;
let daily = [];
let isReplay = false;
let sel = -1;            // highlighted suggestion
let trail = [];          // this run's glyph story: 🔗 hop · 🟥 burn · ↩ back
let ticker = null;       // countdown interval

// --- boot / routing -------------------------------------------------------

boot();

async function boot() {
  const params = new URLSearchParams(location.search);
  try {
    if (params.has('archive')) return await renderArchive();
    if (params.has('history')) return renderHistory();
    if (params.has('play') || params.has('id')) return await startGame(params);
    return await renderHome();
  } catch (err) {
    show('home');
    $('today-card').innerHTML =
      `<p class="feedback bad show">Couldn't load today's connection. ${escapeHtml(err.message)}</p>`;
  }
}

function show(id) {
  ['home', 'play', 'end', 'archive', 'history'].forEach((s) => $(s).classList.add('hidden'));
  $(id).classList.remove('hidden');
}

// Date-keyed so a stale CDN copy can't outlive the day it was cached for.
async function loadDailies() {
  const res = await fetch(`challenges.json?d=${todayISO()}`);
  if (!res.ok) throw new Error(`challenges.json ${res.status}`);
  const doc = await res.json();
  return doc.daily || [];
}

async function loadCorpus() {
  if (corpus) return corpus;
  const res = await fetch('graph.json');
  if (!res.ok) throw new Error(`graph.json ${res.status}`);
  corpus = new Corpus(await res.json());
  return corpus;
}

// --- home -----------------------------------------------------------------

async function renderHome() {
  show('home');
  daily = await loadDailies();
  const today = pickPuzzle(daily, todayISO());
  if (!today) {
    $('today-card').innerHTML = '<p class="arc-sub">No connections published yet.</p>';
    return;
  }
  const stats = loadStats(todayISO());
  const done = stats.history[today.date];
  const risk = streakState(stats, todayISO()) === 'at-risk'
    ? ` · 🔥 ${stats.currentStreak}-day streak on the line` : '';
  $('today-card').innerHTML = `
    <p class="today-eyebrow">${today.date === todayISO() ? 'Today' : 'Latest'} · #${today.id}</p>
    <p class="today-pair">
      <span class="cpill film">${escapeHtml(filmLabel(today.from))}</span>
      <span class="carrow">→</span>
      <span class="cpill film goal">${escapeHtml(filmLabel(today.to))}</span>
    </p>
    <p class="today-par">par ${today.par}${done ? ` · you scored ${resultLabel(done)}` : risk}</p>`;
}

function filmLabel(pair) { return `${pair[0]} (${pair[1]})`; }

function resultLabel(r) {
  return r.won ? `${r.degrees} degrees (${relativeLabel(r.degrees, r.par)})` : 'a broken chain';
}

// --- persistence ----------------------------------------------------------

function readJSON(key) {
  try { return JSON.parse(localStorage.getItem(key) || 'null'); } catch { return null; }
}
function writeJSON(key, obj) {
  try { localStorage.setItem(key, JSON.stringify(obj)); } catch { /* ignore */ }
}

// The finished record IS the end card's input — renderEndCard runs from it alone,
// so a restored visit and a just-finished run render identically.
function loadRun() {
  const r = readJSON(RUN_KEY);
  return r && entry && r.date === entry.date && r.id === entry.id ? r : null;
}

function saveLive() {
  if (isReplay || !game) return;
  writeJSON(LIVE_KEY, { date: entry.date, id: entry.id, state: game.toJSON(), trail });
}
function loadLive() {
  const r = readJSON(LIVE_KEY);
  return r && r.date === entry.date && r.id === entry.id ? r : null;
}
function clearLive() {
  try { localStorage.removeItem(LIVE_KEY); } catch { /* ignore */ }
}

// --- the game -------------------------------------------------------------

async function startGame(params) {
  show('play');
  $('prompt').textContent = 'Loading the film graph…';
  daily = await loadDailies();
  const id = Number(params.get('id'));
  entry = id ? pickById(daily, id) : pickPuzzle(daily, todayISO());
  if (!entry) throw new Error('no such connection');
  isReplay = Boolean(id) && entry.date !== todayISO();
  await loadCorpus();

  // Already finished today? Land on the result, not a silent restart.
  if (!isReplay) {
    const done = loadRun();
    if (done) return renderEndCard(done, { restored: true });
  }

  game = null;
  trail = [];
  if (!isReplay) {
    const live = loadLive();
    if (live) {
      const restored = Chain.fromJSON(corpus, entry, live.state);
      if (restored && restored.status === 'playing') {
        game = restored;
        trail = Array.isArray(live.trail) ? live.trail : [];
      } else {
        clearLive();
      }
    }
  }
  if (!game) game = new Chain(corpus, entry);

  $('scoreboard').hidden = false;
  $('mode-badge').textContent = isReplay ? `Replay · #${entry.id} · ${entry.date}` : '';
  $('guess-btn').onclick = submit;
  $('back-btn').onclick = stepBack;
  $('guess').addEventListener('input', renderSuggest);
  $('guess').addEventListener('keydown', onKey);
  render();
  $('guess').focus();
}

function render() {
  $('degrees').textContent = game.degrees;
  $('par').textContent = game.par;

  const row = $('chain');
  row.innerHTML = '';
  row.appendChild(pill(game.startLabel, 'film'));
  game.chain.forEach((step) => {
    row.appendChild(arrow());
    row.appendChild(pill(step.label, step.type === 'film' ? 'film' : 'person'));
  });
  if (game.status === 'playing') {
    row.appendChild(arrow());
    row.appendChild(pill('?', 'current'));
  }
  row.appendChild(arrow());
  row.appendChild(pill(game.goalLabel, 'film goal'));

  $('prompt').innerHTML = game.expecting === 'person'
    ? `Who worked on <b>${escapeHtml(game.currentFilmLabel)}</b>?`
    : `Which other film did <b>${escapeHtml(lastLabel())}</b> work on?`;
  $('guess').placeholder = game.expecting === 'person' ? 'Name someone…' : 'Name a film…';
  $('back-btn').disabled = game.expecting !== 'film';

  const dots = $('attempts');
  dots.innerHTML = '';
  for (let i = 0; i < CHAIN_MAX_ATTEMPTS; i++) {
    const d = document.createElement('span');
    d.className = `dot${i < game.attempts ? ' spent' : ''}`;
    dots.appendChild(d);
  }
  hideSuggest();
  if (game.status !== 'playing') renderEnd();
}

function lastLabel() {
  const last = game.chain[game.chain.length - 1];
  return last ? last.label : game.startLabel;
}

function pill(label, cls) {
  const el = document.createElement('span');
  el.className = `cpill ${cls}`;
  el.textContent = label;
  return el;
}

function arrow() {
  const el = document.createElement('span');
  el.className = 'carrow';
  el.textContent = '→';
  return el;
}

function stepBack() {
  if (game.back()) {
    trail.push('↩');
    flash('Stepped back.', 'muted');
    saveLive();
    render();
  }
}

function submit() {
  if (!game || game.status !== 'playing') return;
  const text = $('guess').value.trim();
  if (!text) return;
  const verdict = game.guess(text);
  $('guess').value = '';
  if (verdict.result === 'wrong' || verdict.result === 'over') trail.push('🟥');
  if (verdict.result === 'won' || (verdict.result === 'correct' && verdict.step === 'person')) {
    trail.push('🔗');
  }
  if (game.status === 'playing') saveLive();
  speak(verdict);
  render();
  $('guess').focus();
}

// Turn an engine verdict into a sentence. The engine already worked out WHY a
// guess failed; this only picks the words.
function speak(v) {
  const person = game.expecting === 'person';
  switch (v.result) {
    case 'correct':
      return flash(`${v.label} ✓`, 'good');
    case 'won':
      return flash(`${v.label} closes it.`, 'good');
    case 'wrong':
    case 'over':
      if (v.reason === 'used') {
        return flash(`You've already used ${v.label}.`, 'bad');
      }
      return flash(v.film
        ? `${v.label} isn't credited on ${v.film}.`
        : `${v.person} didn't work on ${v.label}.`, 'bad');
    case 'unknown':
      if (v.reason === 'goalFilm') {
        return flash(`That's the target — close the chain by naming someone who worked on it.`,
                     'muted');
      }
      if (v.reason === 'wrongType') {
        return flash(v.expected === 'person'
          ? `${v.label} is a film — name a person from it instead.`
          : `${v.label} is a person — name one of their films.`, 'muted');
      }
      return flash(person
        ? 'Nobody in the pool by that name — check the spelling?'
        : 'No film in the pool by that title.', 'muted');
    default:
      return null;
  }
}

function flash(msg, kind) {
  const el = $('feedback');
  el.textContent = msg;
  el.className = `feedback show ${kind}`;
}

// --- suggestions (global: the whole pool, never just the legal hops) -------

function renderSuggest() {
  const box = $('suggest');
  if (!game || game.status !== 'playing') return hideSuggest();
  const q = $('guess').value;
  const person = game.expecting === 'person';
  const hits = person ? corpus.suggestPeople(q) : corpus.suggestFilms(q);
  if (!hits.length) return hideSuggest();
  box.innerHTML = '';
  hits.forEach((i, n) => {
    const el = document.createElement('div');
    el.className = `choice${n === sel ? ' sel' : ''}`;
    el.innerHTML = person
      ? escapeHtml(corpus.personName(i))
      : `${escapeHtml(corpus.filmTitle(i))}<span class="yr">${corpus.filmYear(i)}</span>`;
    el.onclick = () => {
      $('guess').value = person ? corpus.personName(i) : corpus.filmTitle(i);
      hideSuggest();
      submit();
    };
    box.appendChild(el);
  });
  box.hidden = false;
}

function hideSuggest() {
  $('suggest').hidden = true;
  sel = -1;
}

function onKey(e) {
  const box = $('suggest');
  const options = box.hidden ? [] : [...box.children];
  if (e.key === 'ArrowDown' && options.length) {
    e.preventDefault();
    sel = (sel + 1) % options.length;
  } else if (e.key === 'ArrowUp' && options.length) {
    e.preventDefault();
    sel = (sel - 1 + options.length) % options.length;
  } else if (e.key === 'Enter') {
    e.preventDefault();
    if (sel >= 0 && options[sel]) return options[sel].click();
    return submit();
  } else if (e.key === 'Escape') {
    return hideSuggest();
  } else {
    return;
  }
  options.forEach((el, i) => el.classList.toggle('sel', i === sel));
}

// --- end of a live run ----------------------------------------------------

function renderEnd() {
  const record = {
    date: entry.date, id: entry.id,
    won: game.status === 'won',
    degrees: game.degrees, par: game.par,
    start: game.startLabel, goal: game.goalLabel,
    steps: game.chain.map((s) => ({ t: s.type, label: s.label })),
    trail: [...trail],
  };
  if (!isReplay) {
    saveStats(recordResult(loadStats(), record));
    writeJSON(RUN_KEY, record);
    clearLive();
  }
  renderEndCard(record, { replay: isReplay });
}

// --- the ritual end card ----------------------------------------------------
// One screen, five jobs: your chain, the reveal, how you stack up, when the next
// one lands, and the share. Renders from a plain record so a just-finished run
// and a restored visit look identical.

function renderEndCard(rec, opts = {}) {
  const stats = loadStats(todayISO());
  const rel = relativeLabel(rec.degrees, rec.par);
  const line = rec.won
    ? (rec.degrees < rec.par ? `Under par. You found a link the shortest path missed.`
      : rec.degrees === rec.par ? `Par. That's the tightest chain there is.`
      : `${rel} over par — the shortest route was ${rec.par} degrees.`)
    : `Three wrong links on one step ended the run.`;

  if (ticker) { clearInterval(ticker); ticker = null; }

  $('end').innerHTML = `
    <p class="eyebrow">${escapeHtml(rec.start)} → ${escapeHtml(rec.goal)}</p>
    <div class="hero">
      <span class="herodepth">${rec.won ? rec.degrees : '—'}</span>
      <label>${rec.won ? 'degrees' : 'chain broken'}</label>
    </div>
    <p class="endline">${line}</p>
    <div class="endchain" id="end-mine"></div>
    <div class="revealbox" id="end-reveal"></div>
    <div class="hist" id="end-hist"></div>
    <p class="streakline" id="end-streak"></p>
    <p class="countdown" id="end-count"></p>
    <div class="row endrow">
      <button class="btn-primary" id="share-btn">Share</button>
      <a class="btn-ghost" href="?archive">Archive</a>
      <a class="btn-ghost" href="?history">Scorecard</a>
    </div>
    <pre class="share" id="share-text"></pre>
    <p class="feedback muted" id="share-note">&nbsp;</p>`;

  renderMyChain(rec);
  renderReveal(rec);
  renderHistogram(rec, opts.replay ? null : stats);
  renderStreak(stats, opts.replay);
  renderCountdown(opts.replay);
  const text = shareText(rec, stats);
  $('share-text').textContent = text;
  $('share-btn').onclick = () => share(text);

  $('play').classList.add('hidden');
  $('end').classList.remove('hidden');
}

// The chain you actually built — the run's content, kept on screen to admire,
// screenshot, or compare. On a loss it ends at the open step.
function renderMyChain(rec) {
  const row = $('end-mine');
  row.appendChild(pill(rec.start, 'film'));
  for (const s of rec.steps) {
    row.appendChild(arrow());
    row.appendChild(pill(s.label, s.t === 'film' ? 'film' : 'person'));
  }
  if (!rec.won) { row.appendChild(arrow()); row.appendChild(pill('?', 'current')); }
  row.appendChild(arrow());
  row.appendChild(pill(rec.goal, 'film goal'));
}

// The payoff: one shortest route, revealed only now that the run is over. On a
// loss this is the answer the old screen withheld; on a win it's the comparison.
function renderReveal(rec) {
  const box = $('end-reveal');
  const a = corpus.filmIndex(entry.start);
  const b = corpus.filmIndex(entry.goal);
  const route = shortestChain(corpus, a, b);
  if (!route || !route.length) return;
  const par = (route.length + 1) / 2;
  const ways = countGeodesics(corpus, a, b, par);
  const mine = rec.steps.map((s) => s.label);
  const same = rec.won &&
    route.length === rec.steps.length &&
    route.every((s, i) => labelOf(s) === mine[i]);

  const head = document.createElement('p');
  head.className = 'reveal-label';
  head.textContent = rec.won
    ? (same ? 'The textbook route — and you played it:' : `A shortest route (par ${par}):`)
    : `The link you were hunting (par ${par}):`;
  box.appendChild(head);

  if (!same) {
    const row = document.createElement('div');
    row.className = 'endchain revealchain';
    row.appendChild(pill(rec.start, 'film dim'));
    for (const s of route) {
      row.appendChild(arrow());
      row.appendChild(pill(labelOf(s), 'reveal'));
    }
    row.appendChild(arrow());
    row.appendChild(pill(rec.goal, 'film dim'));
    box.appendChild(row);
  }

  const count = document.createElement('p');
  count.className = 'reveal-count';
  count.textContent = ways >= 1000
    ? `There were 1,000+ distinct ways to do it in ${par}.`
    : `There ${ways === 1 ? 'was exactly 1 way' : `were ${ways} distinct ways`} to do it in ${par}.`;
  box.appendChild(count);
}

function labelOf(step) {
  return step.type === 'film' ? corpus.filmLabel(step.index) : corpus.personName(step.index);
}

// Your golf distribution, today's bucket lit — the daily self-comparison hit.
// Data has been recorded since day one; this is its first render.
function renderHistogram(rec, stats) {
  if (!stats) return;
  const hist = stats.histogram || {};
  const keys = Object.keys(hist);
  if (!keys.length) return;
  const val = (k) => k === 'x' ? Infinity : k === 'E' ? 0 : Number(k.replace('−', '-'));
  keys.sort((p, q) => val(p) - val(q));
  const max = Math.max(...keys.map((k) => hist[k]));
  const today = rec.won ? relativeLabel(rec.degrees, rec.par) : 'x';
  const box = $('end-hist');
  box.innerHTML = '<p class="histlabel">Your scores</p>';
  for (const k of keys) {
    const row = document.createElement('div');
    row.className = 'hrow';
    const label = document.createElement('span');
    label.className = 'hd';
    label.textContent = k;
    const bar = document.createElement('span');
    bar.className = `hb${k === today ? ' cur' : ''}`;
    bar.style.width = `${Math.max(9, Math.round((hist[k] / max) * 100))}%`;
    bar.textContent = hist[k];
    row.appendChild(label);
    row.appendChild(bar);
    box.appendChild(row);
  }
}

function renderStreak(stats, replay) {
  if (replay || stats.currentStreak < 1) return;
  $('end-streak').textContent =
    `🔥 ${stats.currentStreak}-day streak${stats.currentStreak === stats.maxStreak &&
      stats.maxStreak > 1 ? ' — your best' : ''}`;
}

// The appointment mechanic: a live countdown to the next daily. Renders only when
// tomorrow's entry actually exists in challenges.json — a countdown to nothing
// would be a broken promise.
function renderCountdown(replay) {
  const el = $('end-count');
  if (replay) return;
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  if (!daily.some((e) => e.date === todayISO(tomorrow))) return;
  const midnight = new Date();
  midnight.setHours(24, 0, 0, 0);
  const tick = () => {
    const left = midnight - Date.now();
    if (left <= 0) { clearInterval(ticker); ticker = null; return location.reload(); }
    const h = Math.floor(left / 3600000);
    const m = Math.floor((left % 3600000) / 60000);
    const s = Math.floor((left % 60000) / 1000);
    el.textContent = `Next connection in ${String(h).padStart(2, '0')}:` +
                     `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };
  tick();
  ticker = setInterval(tick, 1000);
}

// --- share ------------------------------------------------------------------
// Line 1 is a FROZEN grammar (DESIGN.md "Share grammar") — accountless leagues
// parse it; never reformat. Line 3 is the route silhouette: the run's shape with
// honesty markers, never its names. Spoiler-safe by construction.

function shareText(rec, stats) {
  const rel = relativeLabel(rec.degrees, rec.par);
  const line1 = rec.won
    ? `Degrees of Film #${rec.id} — ${rec.degrees}° (par ${rec.par}, ${rel})`
    : `Degrees of Film #${rec.id} — X (par ${rec.par})`;
  const glyphs = rec.trail.length > 14
    ? `🔗×${rec.trail.filter((g) => g === '🔗').length} 🟥×${rec.trail.filter((g) => g === '🟥').length}`
    : rec.trail.join('');
  const streak = !isReplay && rec.won && stats.currentStreak >= 2
    ? ` · streak ${stats.currentStreak}` : '';
  const line3 = rec.won ? `${glyphs}${streak}` : `💔 ${glyphs}`;
  return [
    line1,
    `${rec.start} → ${rec.goal}`,
    line3,
    SITE,
  ].join('\n');
}

async function share(text) {
  try {
    if (navigator.share) return await navigator.share({ text });
    await navigator.clipboard.writeText(text);
    $('share-note').textContent = 'Copied to clipboard.';
  } catch {
    $('share-note').textContent = 'Copy failed — select the text above instead.';
  }
}

// --- archive + scorecard --------------------------------------------------

async function renderArchive() {
  show('archive');
  daily = await loadDailies();
  const today = todayISO();
  const history = loadStats(today).history;
  const past = daily.filter((e) => e.date <= today).reverse();
  $('archive-list').innerHTML = past.length ? past.map((e) => `
    <a class="arc-row" href="?id=${e.id}">
      <span class="arc-date">${e.date}</span>
      <span class="arc-pair">${escapeHtml(e.from[0])} → ${escapeHtml(e.to[0])}</span>
      <span class="arc-par">par ${e.par}${history[e.date] ? ` · ${resultLabel(history[e.date])}` : ''}</span>
    </a>`).join('') : '<p class="arc-sub">Nothing in the archive yet.</p>';
}

function renderHistory() {
  show('history');
  const today = todayISO();
  const s = loadStats(today);
  const risk = streakState(s, today) === 'at-risk';
  const rows = Object.entries(s.history).sort((a, b) => (a[0] < b[0] ? 1 : -1));
  $('history-summary').innerHTML = `
    <div class="statgrid">
      <div><b>${s.played}</b><span>played</span></div>
      <div><b>${s.wins}</b><span>connected</span></div>
      <div><b>${s.currentStreak}</b><span>streak${risk ? ' ⚠' : ''}</span></div>
      <div><b>${s.maxStreak}</b><span>best streak</span></div>
      <div><b>${s.best === null ? '—' : relativeLabel(s.best, 0)}</b><span>best score</span></div>
    </div>
    ${risk ? `<p class="arc-sub riskline">Your ${s.currentStreak}-day streak ends at midnight — <a href="?play">play today's connection</a>.</p>` : ''}`;
  $('history-list').innerHTML = rows.length ? rows.map(([date, r]) => `
    <a class="arc-row" href="?id=${r.id}">
      <span class="arc-date">${date}</span>
      <span class="arc-pair">${r.won ? `${r.degrees} degrees` : 'chain broken'}</span>
      <span class="arc-par">par ${r.par}${r.won ? ` · ${relativeLabel(r.degrees, r.par)}` : ''}</span>
    </a>`).join('')
    : '<p class="arc-sub">No dailies played on this device yet.</p>';
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
