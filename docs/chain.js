// Degrees — the chain engine. Pure logic, no DOM; imports only the corpus (which
// imports only the matcher), so Node tests and any future server replay run this
// exact file.
//
// A challenge is {id, start, goal, par} where start/goal are TMDB film ids into the
// shared corpus. Play alternates: from the current film name a PERSON credited in
// it, then a FILM they are also in, and so on. Naming a person who is ALSO credited
// in the goal film closes the chain. "Degrees" = person steps taken; the brag is
// degrees against par (golf).
//
// Verdicts are deliberately finer than right/wrong, because the corpus knows the
// difference between a name that doesn't exist and one that does but doesn't help:
//
//   correct     the hop is legal, chain advanced
//   won         that person is credited in the goal — chain closed
//   wrong       a real person/film of the right kind that is NOT a legal hop  [burns]
//   unknown     nothing by that name, or a film typed where a person belongs   [free]
//   over        the third burn on one step ends the run
//   ignored     the run is already finished
//
// Only `wrong` burns an attempt. Typos and category slips are not strategy errors,
// and punishing them just makes the game feel like a spelling test.
export const CHAIN_MAX_ATTEMPTS = 3;

export class Chain {
  constructor(corpus, challenge) {
    const start = corpus.filmIndex(challenge.start);
    const goal = corpus.filmIndex(challenge.goal);
    if (start < 0 || goal < 0) {
      throw new Error(`challenge ${challenge.id}: film not in this corpus ` +
                      `(start ${challenge.start}, goal ${challenge.goal})`);
    }
    this.corpus = corpus;
    this.id = challenge.id;
    this.start = start;
    this.goal = goal;
    this.par = challenge.par;
    this.position = start;             // current film index
    this.currentPerson = null;         // person index once one is named
    this.expecting = 'person';         // 'person' | 'film'
    this.chain = [];                   // [{type, index, label}] in play order
    this.usedFilms = new Set([start, goal]);
    this.usedPeople = new Set();
    this.degrees = 0;
    this.attempts = 0;                 // burns on the current step
    this.status = 'playing';           // 'playing' | 'won' | 'over'
  }

  // The legal hops from here. Curator/test surface — never render this, it is the
  // answer. Player-facing autocomplete comes from Corpus.suggest*, which is global.
  legalMoves() {
    if (this.status !== 'playing') return new Set();
    if (this.expecting === 'person') {
      return new Set(this.corpus.castOf(this.position).filter((p) => !this.usedPeople.has(p)));
    }
    return new Set(this.corpus.filmsOf(this.currentPerson).filter((f) => !this.usedFilms.has(f)));
  }

  get startLabel() { return this.corpus.filmLabel(this.start); }
  get goalLabel() { return this.corpus.filmLabel(this.goal); }

  // Where the next hop departs from: the last film reached (or the start).
  get currentFilmLabel() { return this.corpus.filmLabel(this.position); }

  guess(text) {
    if (this.status !== 'playing') return { result: 'ignored' };
    return this.expecting === 'person' ? this.guessPerson(text) : this.guessFilm(text);
  }

  guessPerson(text) {
    const legal = this.legalMoves();
    const hit = this.corpus.resolvePerson(text, legal);
    if (hit && hit.scope === 'here') return this.takePerson(hit.index);

    // Not a legal hop. Say why — the corpus knows.
    if (hit) {
      const used = this.usedPeople.has(hit.index);
      return this.burn({
        reason: used ? 'used' : 'notCredited',
        label: this.corpus.personName(hit.index),
        film: this.currentFilmLabel,
      });
    }
    const asFilm = this.corpus.resolveFilm(text, null);
    if (asFilm) {
      return { result: 'unknown', reason: 'wrongType', expected: 'person',
               label: this.corpus.filmLabel(asFilm.index) };
    }
    return { result: 'unknown', reason: 'unrecognized' };
  }

  guessFilm(text) {
    const legal = this.legalMoves();
    const hit = this.corpus.resolveFilm(text, legal);
    if (hit && hit.scope === 'here') return this.takeFilm(hit.index);

    if (hit) {
      if (hit.index === this.goal) {
        // Naming the goal is a rules slip, not a wrong answer: you close the chain
        // on a PERSON credited in it, you never step into it.
        return { result: 'unknown', reason: 'goalFilm', label: this.goalLabel };
      }
      const used = this.usedFilms.has(hit.index);
      return this.burn({
        reason: used ? 'used' : 'notCredited',
        label: this.corpus.filmLabel(hit.index),
        person: this.corpus.personName(this.currentPerson),
      });
    }
    const asPerson = this.corpus.resolvePerson(text, null);
    if (asPerson) {
      return { result: 'unknown', reason: 'wrongType', expected: 'film',
               label: this.corpus.personName(asPerson.index) };
    }
    return { result: 'unknown', reason: 'unrecognized' };
  }

  takePerson(index) {
    this.attempts = 0;
    this.currentPerson = index;
    this.usedPeople.add(index);
    this.degrees += 1;
    const label = this.corpus.personName(index);
    this.chain.push({ type: 'person', index, label });
    if (this.corpus.isCredited(this.goal, index)) {
      this.status = 'won';
      return { result: 'won', label, degrees: this.degrees, par: this.par };
    }
    this.expecting = 'film';
    return { result: 'correct', step: 'person', label };
  }

  takeFilm(index) {
    this.attempts = 0;
    this.position = index;
    this.usedFilms.add(index);
    this.expecting = 'person';
    const label = this.corpus.filmLabel(index);
    this.chain.push({ type: 'film', index, label });
    return { result: 'correct', step: 'film', label };
  }

  burn(detail) {
    this.attempts += 1;
    if (this.attempts >= CHAIN_MAX_ATTEMPTS) {
      this.status = 'over';
      return { result: 'over', ...detail };
    }
    return { result: 'wrong', attemptsLeft: CHAIN_MAX_ATTEMPTS - this.attempts, ...detail };
  }

  // Abandon the current person (dead end): back to the film you came from. The
  // degree is spent and the person stays blocked — no refunds, like a golf stroke.
  back() {
    if (this.status !== 'playing' || this.expecting !== 'film') return false;
    this.chain.pop();
    this.currentPerson = null;
    this.expecting = 'person';
    this.attempts = 0;
    return true;
  }

  // Mid-run persistence. Serialized PORTABLY — films by TMDB id, people by exact
  // name — never by corpus index: indices shift on every graph.json rebuild, and a
  // save restored across one would silently corrupt the chain. The used sets ride
  // along explicitly because back() removes a pill but keeps the person blocked,
  // so the chain alone under-states them.
  toJSON() {
    return {
      id: this.id,
      status: this.status,
      expecting: this.expecting,
      degrees: this.degrees,
      attempts: this.attempts,
      chain: this.chain.map((s) => s.type === 'film'
        ? { t: 'f', id: this.corpus.ids[s.index] }
        : { t: 'p', n: this.corpus.personName(s.index) }),
      usedF: [...this.usedFilms].map((f) => this.corpus.ids[f]),
      usedP: [...this.usedPeople].map((p) => this.corpus.personName(p)),
    };
  }

  // Rebuild a run from toJSON output, or null when the save doesn't fit — wrong
  // challenge, or any name/id no longer resolving (a corpus rebuild happened).
  // Discard-on-mismatch beats a corrupted chain.
  static fromJSON(corpus, challenge, data) {
    if (!data || data.id !== challenge.id) return null;
    const personIx = (name) => {
      const i = corpus.people.indexOf(name);
      return i >= 0 ? i : null;
    };
    const c = new Chain(corpus, challenge);
    c.status = data.status;
    c.expecting = data.expecting;
    c.degrees = data.degrees;
    c.attempts = data.attempts;
    for (const s of data.chain || []) {
      if (s.t === 'f') {
        const i = corpus.filmIndex(s.id);
        if (i < 0) return null;
        c.chain.push({ type: 'film', index: i, label: corpus.filmLabel(i) });
        c.position = i;
      } else {
        const i = personIx(s.n);
        if (i === null) return null;
        c.chain.push({ type: 'person', index: i, label: corpus.personName(i) });
        c.currentPerson = i;
      }
    }
    const last = c.chain[c.chain.length - 1];
    if (!last || last.type === 'film') c.currentPerson = null;
    for (const id of data.usedF || []) {
      const i = corpus.filmIndex(id);
      if (i < 0) return null;
      c.usedFilms.add(i);
    }
    for (const n of data.usedP || []) {
      const i = personIx(n);
      if (i === null) return null;
      c.usedPeople.add(i);
    }
    return c;
  }
}
