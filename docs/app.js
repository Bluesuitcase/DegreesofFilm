// DOM glue for Degrees. All rules live in chain.js and all graph knowledge in
// corpus.js — this file only fetches, renders and wires buttons.
//
// Routes: ?  home · ?play today's daily · ?id=N replay a past daily ·
//         ?archive the index · ?history your scorecard
//
// The corpus (~188 KB gz) is fetched only when you actually play; home and archive
// render from challenges.json alone, which carries each day's two film titles.
import { Corpus } from './corpus.js';
import { Chain, CHAIN_MAX_ATTEMPTS } from './chain.js';
import { pickPuzzle, pickById, todayISO } from './daily.js';
import { loadStats, saveStats, recordResult, relativeLabel } from './stats.js';

const $ = (id) => document.getElementById(id);
const SITE = 'https://bluesuitcase.github.io/DegreesofFilm/';

let corpus = null;
let game = null;
let entry = null;
let isReplay = false;
let sel = -1;            // highlighted suggestion

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
  const daily = await loadDailies();
  const today = pickPuzzle(daily, todayISO());
  if (!today) {
    $('today-card').innerHTML = '<p class="arc-sub">No connections published yet.</p>';
    return;
  }
  const done = loadStats().history[today.date];
  $('today-card').innerHTML = `
    <p class="today-eyebrow">${today.date === todayISO() ? 'Today' : 'Latest'} · #${today.id}</p>
    <p class="today-pair">
      <span class="cpill film">${escapeHtml(filmLabel(today.from))}</span>
      <span class="carrow">→</span>
      <span class="cpill film goal">${escapeHtml(filmLabel(today.to))}</span>
    </p>
    <p class="today-par">par ${today.par}${done ? ` · you scored ${resultLabel(done)}` : ''}</p>`;
}

function filmLabel(pair) { return `${pair[0]} (${pair[1]})`; }

function resultLabel(r) {
  return r.won ? `${r.degrees} degrees (${relativeLabel(r.degrees, r.par)})` : 'a broken chain';
}

// --- the game -------------------------------------------------------------

async function startGame(params) {
  show('play');
  $('prompt').textContent = 'Loading the film graph…';
  const daily = await loadDailies();
  const id = Number(params.get('id'));
  entry = id ? pickById(daily, id) : pickPuzzle(daily, todayISO());
  if (!entry) throw new Error('no such connection');
  isReplay = Boolean(id) && entry.date !== todayISO();
  await loadCorpus();
  game = new Chain(corpus, entry);

  $('scoreboard').hidden = false;
  $('mode-badge').textContent = isReplay ? `Replay · #${entry.id} · ${entry.date}` : '';
  $('guess-btn').onclick = submit;
  $('back-btn').onclick = () => { if (game.back()) { flash('Stepped back.', 'muted'); render(); } };
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

function submit() {
  if (!game || game.status !== 'playing') return;
  const text = $('guess').value.trim();
  if (!text) return;
  const verdict = game.guess(text);
  $('guess').value = '';
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

// --- end screen -----------------------------------------------------------

function renderEnd() {
  const won = game.status === 'won';
  const rel = relativeLabel(game.degrees, game.par);
  if (!isReplay) {
    const stats = loadStats();
    saveStats(recordResult(stats, {
      date: entry.date, id: entry.id, degrees: game.degrees, par: game.par, won,
    }));
  }
  const line = won
    ? (game.degrees < game.par ? `Under par. You found a link the shortest path missed.`
      : game.degrees === game.par ? `Par. That's the tightest chain there is.`
      : `${rel} over par — the shortest route was ${game.par} degrees.`)
    : `Three wrong links on one step. The connection stays hidden.`;

  $('end').innerHTML = `
    <p class="eyebrow">${escapeHtml(game.startLabel)} → ${escapeHtml(game.goalLabel)}</p>
    <div class="hero">
      <span class="herodepth">${won ? game.degrees : '—'}</span>
      <label>${won ? 'degrees' : 'chain broken'}</label>
    </div>
    <p class="endline">${line}</p>
    <div class="row endrow">
      <button class="btn-primary" id="share-btn">Share</button>
      <a class="btn-ghost" href="?archive">Archive</a>
      <a class="btn-ghost" href="?history">Scorecard</a>
    </div>
    <p class="feedback muted" id="share-note">&nbsp;</p>`;
  $('play').classList.add('hidden');
  $('end').classList.remove('hidden');
  $('share-btn').onclick = share;
}

// Spoiler-safe by construction: the two films are the prompt everyone sees, and
// the chain itself is never in the text.
function shareText() {
  const won = game.status === 'won';
  return [
    `Degrees of Film #${entry.id}`,
    `${game.startLabel} → ${game.goalLabel}`,
    won ? `${'🔗'.repeat(Math.min(game.degrees, 10))} ${game.degrees} degrees (par ${game.par})`
        : `💔 chain broken (par ${game.par})`,
    SITE,
  ].join('\n');
}

async function share() {
  const text = shareText();
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
  const daily = await loadDailies();
  const today = todayISO();
  const history = loadStats().history;
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
  const s = loadStats();
  const rows = Object.entries(s.history).sort((a, b) => (a[0] < b[0] ? 1 : -1));
  $('history-summary').innerHTML = `
    <div class="statgrid">
      <div><b>${s.played}</b><span>played</span></div>
      <div><b>${s.wins}</b><span>connected</span></div>
      <div><b>${s.currentStreak}</b><span>streak</span></div>
      <div><b>${s.maxStreak}</b><span>best streak</span></div>
      <div><b>${s.best === null ? '—' : relativeLabel(s.best, 0)}</b><span>best score</span></div>
    </div>`;
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
