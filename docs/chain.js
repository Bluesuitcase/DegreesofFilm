// Graph-mode chain engine (degrees-of-separation, campaign phase G2). Pure logic,
// no DOM, imports only the matcher — the same purity contract as game.js, so Node
// tests and any future server replay run this exact file.
//
// A challenge is { start:{id,title,year}, goal:{...}, par, films:{id:[title,year]},
// people:{id:name}, edges:[[filmId,personId],...] } — a decoy-padded subgraph.
// Play alternates: from the current film name a PERSON credited in it, then a FILM
// that person is also in, and so on. Naming a person who is ALSO credited in the
// goal film closes the chain (a win). "Degrees" = successful person steps; the brag
// is degrees vs par. 3 wrong guesses on any single step ends the run (the dig's
// rhythm). back() abandons the current person (no refunds) when you hit a dead end.
import { matchGuess } from './match.js';

export const CHAIN_MAX_ATTEMPTS = 3;

export class Chain {
  constructor(ch) {
    this.startFilm = ch.start;
    this.goal = ch.goal;
    this.par = ch.par;
    this.filmLabels = new Map(Object.entries(ch.films).map(([k, v]) => [Number(k), v]));
    this.personNames = new Map(Object.entries(ch.people).map(([k, v]) => [Number(k), v]));
    this.filmPeople = new Map();
    this.personFilms = new Map();
    for (const [f, p] of ch.edges) {
      if (!this.filmPeople.has(f)) this.filmPeople.set(f, []);
      this.filmPeople.get(f).push(p);
      if (!this.personFilms.has(p)) this.personFilms.set(p, []);
      this.personFilms.get(p).push(f);
    }
    this.position = ch.start.id;       // current film id
    this.currentPerson = null;
    this.expecting = 'person';         // 'person' | 'film'
    this.chain = [];                   // [{type, id, label}] in play order
    this.usedFilms = new Set([ch.start.id, ch.goal.id]);
    this.usedPeople = new Set();
    this.degrees = 0;                  // successful person steps (the score vs par)
    this.attempts = 0;                 // wrong guesses on the current step
    this.status = 'playing';           // 'playing' | 'won' | 'over'
  }

  // Valid next entities from here: [{id, label}] — person candidates credited in the
  // current film (unused), or film candidates featuring the current person (unvisited,
  // except the goal, which is never enterable — chains CLOSE on a person).
  candidates() {
    if (this.expecting === 'person') {
      return (this.filmPeople.get(this.position) || [])
        .filter((p) => !this.usedPeople.has(p))
        .map((p) => ({ id: p, label: this.personNames.get(p) }));
    }
    return (this.personFilms.get(this.currentPerson) || [])
      .filter((f) => !this.usedFilms.has(f))
      .map((f) => ({ id: f, label: this.filmLabels.get(f)[0] }));
  }

  // One guess at the current step. The text is matched against every candidate's
  // label with the shipped matcher (typo tolerance + surname rule apply).
  guess(text) {
    if (this.status !== 'playing') return { result: 'ignored' };
    const hit = this.candidates().find((c) => c.label && matchGuess(text, [c.label]));
    if (!hit) {
      this.attempts += 1;
      if (this.attempts >= CHAIN_MAX_ATTEMPTS) {
        this.status = 'over';
        return { result: 'over' };
      }
      return { result: 'wrong', attemptsLeft: CHAIN_MAX_ATTEMPTS - this.attempts };
    }
    this.attempts = 0;
    if (this.expecting === 'person') {
      this.currentPerson = hit.id;
      this.usedPeople.add(hit.id);
      this.degrees += 1;
      this.chain.push({ type: 'person', id: hit.id, label: hit.label });
      // the chain closes when this person is also credited in the goal film
      if ((this.filmPeople.get(this.goal.id) || []).includes(hit.id)) {
        this.status = 'won';
        return { result: 'won', degrees: this.degrees, par: this.par };
      }
      this.expecting = 'film';
      return { result: 'correct', step: 'person', label: hit.label };
    }
    this.position = hit.id;
    this.usedFilms.add(hit.id);
    this.chain.push({ type: 'film', id: hit.id, label: hit.label });
    this.expecting = 'person';
    return { result: 'correct', step: 'film', label: hit.label };
  }

  // Abandon the current person (dead end): return to the film you were at, keep the
  // degree spent and keep the person blocked — no refunds, exactly like a golf stroke.
  back() {
    if (this.status !== 'playing' || this.expecting !== 'film') return false;
    this.chain.pop();
    this.currentPerson = null;
    this.expecting = 'person';
    this.attempts = 0;
    return true;
  }
}
