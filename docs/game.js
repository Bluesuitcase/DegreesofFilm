// Core game rules + scoring for Degrees of Film.
// Pure logic, no DOM. Imports the matcher so app.js stays thin.
import { matchGuess } from './match.js';

export const MAX_ATTEMPTS = 3;
export const MAX_SKIPS = 5;
export const MAX_HELPS = 3;

// Rung N is worth N points, plus a deep-dig bonus that starts at rung 6,
// climbs +1 per rung, and caps at +5 from rung 10 onward.
export function scoreForRung(n) {
  const bonus = Math.min(Math.max(n - 5, 0), 5);
  return n + bonus;
}

export class Game {
  constructor(puzzle) {
    this.rungs = puzzle.rungs;
    this.index = 0;            // 0-based rung currently being attempted
    this.attempts = 0;         // wrong attempts on the current rung
    this.skipsUsed = 0;
    this.helpsUsed = 0;
    this.helped = false;       // current rung converted to multiple choice?
    this.score = 0;
    this.status = 'playing';   // 'playing' | 'over' | 'won'
  }

  get currentRung()  { return this.rungs[this.index]; }
  get depth()        { return this.index; }              // rungs passed (the hero stat)
  get total()        { return this.rungs.length; }
  get attemptsLeft() { return MAX_ATTEMPTS - this.attempts; }
  get skipsLeft()    { return MAX_SKIPS - this.skipsUsed; }
  get helpsLeft()    { return MAX_HELPS - this.helpsUsed; }

  guess(text) {
    if (this.status !== 'playing') return { result: 'noop' };
    if (matchGuess(text, this.currentRung.answers)) {
      this.score += this.helped ? 0 : scoreForRung(this.index + 1);
      this._advance();
      return { result: this.status === 'won' ? 'won' : 'correct' };
    }
    this.attempts++;
    if (this.attempts >= MAX_ATTEMPTS) {
      this.status = 'over';
      return { result: 'strikeout' };
    }
    return { result: 'wrong', attemptsLeft: this.attemptsLeft };
  }

  skip() {
    if (this.status !== 'playing') return { result: 'noop' };
    if (this.skipsUsed >= MAX_SKIPS) {   // a skip beyond the 5th ends the run
      this.status = 'over';
      return { result: 'out_of_skips' };
    }
    this.skipsUsed++;
    this.score -= 1;
    this._advance();
    return { result: this.status === 'won' ? 'won' : 'skipped' };
  }

  // Convert the current rung to multiple choice (value capped at 0). Returns the
  // choices (correct answer + decoys) to show, or null if help isn't available
  // (none left, already used on this rung, no decoys, or not playing). A wrong
  // pick still burns an attempt — solving it via the matcher does the scoring.
  useHelp() {
    if (this.status !== 'playing' || this.helped) return null;
    if (this.helpsUsed >= MAX_HELPS) return null;
    const decoys = this.currentRung.decoys;
    if (!decoys || decoys.length === 0) return null;
    this.helpsUsed++;
    this.helped = true;
    return [this.currentRung.answers[0], ...decoys];
  }

  _advance() {
    this.index++;
    this.attempts = 0;
    this.helped = false;
    if (this.index >= this.rungs.length) this.status = 'won';
  }
}
