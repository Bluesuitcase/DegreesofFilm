// DOM glue for Degrees of Film. All rules live in game.js; this just renders.
import { Game, MAX_ATTEMPTS } from './game.js';
import { pickPuzzle, todayISO } from './daily.js';
import { onAccentText } from './theme.js';

const $ = (id) => document.getElementById(id);
let game, puzzleId = 1, currentChoices = null;

async function init() {
  let puzzle, entry;
  try {
    const today = todayISO();
    // Date-key the manifest fetch so a cached copy can't freeze the daily rotation.
    const manifest = await (await fetch('puzzles/manifest.json?d=' + today)).json();
    entry = pickPuzzle(manifest, today);
    if (!entry) throw new Error('empty manifest');
    puzzle = await (await fetch('puzzles/' + entry.file)).json();
  } catch (e) {
    $('prompt').textContent = 'Could not load today’s puzzle — are you running a local server?';
    return;
  }
  puzzleId = puzzle.id ?? entry.id ?? 1;
  game = new Game(puzzle);
  applyAccent(puzzle.theme && puzzle.theme.accent);

  const img = $('frame-img');
  img.src = 'puzzles/' + puzzle.images[0];
  img.onerror = () => { img.style.display = 'none'; };

  buildRail(puzzle.rungs.length);
  wire();
  render();
}

// Recolor the page accent from the puzzle's theme.accent. Ink base + bone text
// stay fixed; the guess-button text flips to whatever reads on the accent.
function applyAccent(accent) {
  if (!accent) return;
  const s = document.documentElement.style;
  s.setProperty('--amber', accent);
  s.setProperty('--amber-deep', accent);
  s.setProperty('--on-accent', onAccentText(accent));
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

  end.innerHTML = `
    <p class="eyebrow">${won ? 'You reached the bottom' : 'Run over'}</p>
    <div class="hero"><span class="herodepth">${reached}</span><label>degrees deep</label></div>
    ${missed ? `<p class="reveal">${missed.role} was <strong>${missed.answers[0]}</strong></p>` : ''}
    <p class="endline">${game.score} pts · ${game.skipsUsed} skip${game.skipsUsed === 1 ? '' : 's'} · ${reached}/${game.total} rungs</p>
    <pre class="share">Degrees of Film #${puzzleId}\n${reached}/${game.total} deep · ${game.score} pts</pre>
    <button id="again" class="again">Play again</button>`;
  $('again').onclick = () => location.reload();
}

function wire() {
  $('guess-btn').onclick = onGuess;
  $('skip-btn').onclick = onSkip;
  $('help-btn').onclick = onHelp;
  $('guess').addEventListener('keydown', (e) => { if (e.key === 'Enter') onGuess(); });
}

init();
