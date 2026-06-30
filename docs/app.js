// DOM glue for Degrees of Film. All rules live in game.js; this just renders.
import { Game, MAX_ATTEMPTS } from './game.js';
import { pickPuzzle, pickById, todayISO } from './daily.js';
import { onAccentText } from './theme.js';
import { loadStats, saveStats, recordResult } from './stats.js';

const $ = (id) => document.getElementById(id);
let game, puzzleId = 1, puzzleDate = null, currentChoices = null;
let manifest = [], isArchive = false;

async function init() {
  const params = new URLSearchParams(location.search);
  if (params.has('modes')) return renderModes();
  if (!params.has('play') && !params.has('id') && !params.has('archive')) return renderHome();

  try {
    // Date-key the manifest fetch so a cached copy can't freeze the daily rotation.
    manifest = await (await fetch('puzzles/manifest.json?d=' + todayISO())).json();
  } catch (e) {
    $('prompt').textContent = 'Could not load — are you running a local server?';
    return;
  }

  if (params.has('archive')) return renderArchiveView();

  const wantId = params.has('id') ? Number(params.get('id')) : null;
  const entry = wantId != null ? pickById(manifest, wantId) : pickPuzzle(manifest, todayISO());
  if (!entry) { $('prompt').textContent = 'No such puzzle.'; return; }
  isArchive = wantId != null;

  let puzzle;
  try {
    puzzle = await (await fetch('puzzles/' + entry.file)).json();
  } catch (e) {
    $('prompt').textContent = 'Could not load the puzzle.';
    return;
  }
  puzzleId = puzzle.id ?? entry.id ?? 1;
  puzzleDate = puzzle.date || entry.date || todayISO();
  game = new Game(puzzle);
  applyTheme(puzzle.theme);

  const img = $('frame-img');
  img.src = 'puzzles/' + puzzle.images[0];
  img.onerror = () => { img.style.display = 'none'; };

  buildRail(puzzle.rungs.length);
  wire();
  render();
}

// Short, iconic one-liners — kept brief, and from films that aren't in the
// puzzle set (no spoilers). Rotates by day.
const QUOTES = [
  ['“Round up the usual suspects.”', 'Casablanca'],
  ['“I’ll be back.”', 'The Terminator'],
  ['“You talkin’ to me?”', 'Taxi Driver'],
  ['“Why so serious?”', 'The Dark Knight'],
  ['“There is no spoon.”', 'The Matrix'],
  ['“To infinity and beyond!”', 'Toy Story'],
];

function enterLobby() {
  document.body.classList.add('lobby');     // hides the game-only header stats
  $('play').classList.add('hidden');
  $('end').classList.add('hidden');
  $('rail').style.display = 'none';
  ['home', 'modes', 'archive'].forEach((s) => $(s).classList.add('hidden'));
}

function renderHome() {
  enterLobby();
  const day = Math.floor(Date.parse(todayISO() + 'T00:00:00Z') / 86400000);
  const [q, film] = QUOTES[((day % QUOTES.length) + QUOTES.length) % QUOTES.length];
  $('quote').innerHTML = `${q}<cite>— ${film}</cite>`;
  $('home').classList.remove('hidden');
}

function renderModes() {
  enterLobby();
  $('modes').classList.remove('hidden');
}

function renderArchiveView() {
  enterLobby();
  $('archive').classList.remove('hidden');
  buildArchive();
}

function buildArchive() {
  const list = $('archive-list');
  list.innerHTML = '';
  const today = document.createElement('a');
  today.className = 'arc';
  today.href = '?play';
  today.innerHTML = `<span class="arc-d">Today</span><span class="arc-n">daily →</span>`;
  list.appendChild(today);
  // most recent first; date + number + accent swatch, never the film title (no spoilers)
  [...manifest].sort((a, b) => (a.date < b.date ? 1 : -1)).forEach((e) => {
    const a = document.createElement('a');
    a.className = 'arc';
    a.href = '?id=' + e.id;
    const sw = e.accent ? `<span class="arc-sw" style="background:${e.accent}"></span>` : '';
    a.innerHTML = `${sw}<span class="arc-d">${fmtDate(e.date)}</span><span class="arc-n">#${e.id}</span>`;
    list.appendChild(a);
  });
}

function fmtDate(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

// Theme the page from the puzzle: accent on highlights (button text auto-
// contrasts), plus deep film-hued background tones (theme.bg/bg2) tinting the
// surfaces and a subtle gradient. Bone text stays fixed for legibility.
function applyTheme(theme) {
  if (!theme) return;
  const s = document.documentElement.style;
  if (theme.accent) {
    s.setProperty('--amber', theme.accent);
    s.setProperty('--amber-deep', theme.accent);
    s.setProperty('--on-accent', onAccentText(theme.accent));
  }
  if (theme.bg) s.setProperty('--ink', theme.bg);
  if (theme.bg2) s.setProperty('--ink2', theme.bg2);
  if (theme.bg) {
    const top = theme.bg2 || theme.bg;
    document.body.style.background = `linear-gradient(180deg, ${top} 0%, ${theme.bg} 55%)`;
    document.body.style.backgroundAttachment = 'fixed';
  }
}

function buildRail(n) {
  const rail = $('rail');
  rail.innerHTML = '';
  for (let i = 0; i < n; i++) {
    const m = document.createElement('div');
    m.className = 'mark';
    rail.appendChild(m);
  }
}

function render() {
  $('depth').textContent = game.depth;
  $('score').textContent = game.score;

  document.querySelectorAll('.mark').forEach((m, i) => {
    m.classList.toggle('done', i < game.index);
    m.classList.toggle('active', i === game.index && game.status === 'playing');
  });

  if (game.status !== 'playing') return showEnd();

  const rung = game.currentRung;
  $('role').textContent = rung.role;
  $('prompt').textContent = rung.prompt || 'Name it.';

  const a = $('attempts');
  a.innerHTML = '';
  for (let i = 0; i < MAX_ATTEMPTS; i++) {
    const d = document.createElement('span');
    d.className = 'dot' + (i < game.attemptsLeft ? '' : ' spent');
    a.appendChild(d);
  }
  $('skip-btn').textContent = `Skip −1  ·  ${game.skipsLeft} left`;
  renderHelp();
  $('guess').focus();
}

function renderHelp() {
  if (!game.helped) currentChoices = null;
  const btn = $('help-btn');
  const rung = game.currentRung;
  const canHelp = game.helpsLeft > 0 && !game.helped && rung.decoys && rung.decoys.length > 0;
  btn.textContent = `I Need Help · ${game.helpsLeft} left`;
  btn.disabled = !canHelp;
  // hide once spent (and not mid-use) to keep the row tidy
  btn.style.display = (game.helpsLeft === 0 && !game.helped) ? 'none' : '';

  const box = $('choices');
  box.innerHTML = '';
  if (game.helped && currentChoices) {
    const note = document.createElement('p');
    note.className = 'choices-note';
    note.textContent = 'Multiple choice — this rung is now worth 0.';
    box.appendChild(note);
    for (const c of currentChoices) {
      const b = document.createElement('button');
      b.className = 'choice';
      b.textContent = c;
      b.onclick = () => { $('guess').value = c; onGuess(); };
      box.appendChild(b);
    }
  }
}

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function flash(msg, kind) {
  const f = $('feedback');
  f.textContent = msg;
  f.className = 'feedback show ' + (kind || '');
}

function onGuess() {
  if (!game || game.status !== 'playing') return;
  const v = $('guess').value.trim();
  if (!v) return;
  const r = game.guess(v);
  $('guess').value = '';
  if (r.result === 'correct') flash('Correct — keep digging.', 'good');
  else if (r.result === 'wrong') flash(`Not it. ${r.attemptsLeft} ${r.attemptsLeft === 1 ? 'try' : 'tries'} left.`, 'bad');
  render();
}

function onSkip() {
  if (!game || game.status !== 'playing') return;
  const r = game.skip();
  if (r.result === 'skipped') flash('Skipped (−1).', 'muted');
  render();
}

function onHelp() {
  if (!game || game.status !== 'playing') return;
  const choices = game.useHelp();
  if (!choices) { flash('No help available here.', 'muted'); return; }
  currentChoices = shuffle(choices);
  flash('Multiple choice — pick the right one (worth 0).', 'muted');
  render();
}

function showEnd() {
  $('play').classList.add('hidden');
  const end = $('end');
  end.classList.remove('hidden');

  const won = game.status === 'won';
  const reached = game.depth;
  const missed = won ? null : game.currentRung;
  const r = roast(reached, game.total, won);

  let stats = loadStats();
  if (!isArchive) {                    // archived replays don't touch the daily streak/stats
    stats = recordResult(stats, { date: todayISO(), depth: reached, won });
    saveStats(stats);
  }

  end.innerHTML = `
    <p class="eyebrow">${won ? 'You reached the bottom' : 'Run over'}</p>
    <div class="hero"><span class="herodepth">${reached}</span><label>degrees deep</label></div>
    ${missed ? `<p class="reveal">${missed.role} was <strong>${missed.answers[0]}</strong></p>` : ''}
    <p class="endline">${game.score} pts · ${game.skipsUsed} skip${game.skipsUsed === 1 ? '' : 's'} · ${reached}/${game.total} rungs</p>
    <p class="roast">${r.text}</p>
    ${r.mode ? `<a class="roast-cta" href="?modes">${r.mode} mode might be more your speed →</a>` : ''}
    ${statsHtml(stats, reached)}
    <pre class="share" id="share">${shareText(reached, game.total, game.score, won)}</pre>
    <div class="endbtns">
      <button id="copy" class="copy">Copy result</button>
      <button id="again" class="again">Play again</button>
    </div>`;
  $('again').onclick = () => location.reload();
  $('copy').onclick = async () => {
    const btn = $('copy');
    try { await navigator.clipboard.writeText($('share').textContent); btn.textContent = 'Copied ✓'; }
    catch { btn.textContent = 'Press Ctrl/Cmd+C'; }
    setTimeout(() => { btn.textContent = 'Copy result'; }, 1600);
  };
}

// Spoiler-free shareable result: a depth bar (dug rungs vs remaining) + score.
function shareText(reached, total, score, won) {
  const bar = '🟫'.repeat(reached) + '⬛'.repeat(Math.max(0, total - reached));
  const line = won ? `Reached the bottom — ${total}/${total} · ${score} pts`
                   : `${reached}/${total} deep · ${score} pts`;
  return `🎬 Degrees of Film #${puzzleId}\n${line}\n${bar}`;
}

// End-of-round roast: savage but tasteful, and it nudges you toward the mode you
// clearly belong in. Tier by how deep you dug; a win earns grudging respect.
const ROASTS = {
  poser: [
    'You named the film and then ran on pure vibes. Poser mode is multiple choice — built for exactly that.',
    'Bold of you to pick Cinephile. Poser mode exists for performances like the one we just watched.',
    'The Academy would like its screener access back. Poser mode is down the hall, to your left.',
    'A valiant nosedive. In Poser mode the choices are made for you — as, frankly, they should be.',
  ],
  buff: [
    'You know the marquee names and then the credits got scary. Movie Buff is probably your ceiling.',
    'Got the leads, fumbled everyone who actually made the film. Textbook Movie Buff energy.',
    'Respectable — in the way that showing up is respectable. Movie Buff mode awaits.',
    'You hit the wall labeled "the crew" at full speed. Movie Buff it is.',
  ],
  almost: [
    'So close to the bottom you could smell the key grip. Almost a Cinephile. Almost.',
    'One bad guess from greatness. The credits will remember this.',
  ],
  cinephile: [
    'Certified Cinephile. You dug to the bottom and salted the earth.',
    'Flawless descent. Everyone else is a poser and, deep down, they know it.',
    'You named the production designer. Touch grass — right after you finish bragging.',
  ],
};

function roastTier(reached, total, won) {
  if (won) return 'cinephile';
  const ratio = reached / total;
  if (ratio >= 0.6) return 'almost';
  if (ratio >= 0.3) return 'buff';
  return 'poser';
}

function roast(reached, total, won) {
  const tier = roastTier(reached, total, won);
  const pool = ROASTS[tier];
  return {
    text: pool[Math.floor(Math.random() * pool.length)],
    mode: tier === 'poser' ? 'Poser' : tier === 'buff' ? 'Movie Buff' : null,
  };
}

function statsHtml(s, reached) {
  const winPct = s.played ? Math.round((100 * s.wins) / s.played) : 0;
  const tiles = `
    <div class="statgrid">
      <div><b>${s.currentStreak}</b><span>streak</span></div>
      <div><b>${s.maxStreak}</b><span>max</span></div>
      <div><b>${s.bestDepth}</b><span>best</span></div>
      <div><b>${s.played}</b><span>played</span></div>
      <div><b>${winPct}%</b><span>won</span></div>
    </div>`;
  const depths = Object.keys(s.histogram).map(Number).sort((a, b) => a - b);
  const max = Math.max(1, ...depths.map((d) => s.histogram[d]));
  const bars = depths.map((d) => {
    const c = s.histogram[d];
    const w = Math.max(8, Math.round((100 * c) / max));
    return `<div class="hrow"><span class="hd">${d}</span><span class="hb${d === reached ? ' cur' : ''}" style="width:${w}%">${c}</span></div>`;
  }).join('');
  return tiles + (bars ? `<div class="hist"><p class="histlabel">depth distribution</p>${bars}</div>` : '');
}

function wire() {
  $('guess-btn').onclick = onGuess;
  $('skip-btn').onclick = onSkip;
  $('help-btn').onclick = onHelp;
  $('guess').addEventListener('keydown', (e) => { if (e.key === 'Enter') onGuess(); });
}

init();
