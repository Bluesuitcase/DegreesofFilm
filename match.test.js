import { matchGuess } from './docs/match.js';

// Answer sets mirror docs/puzzles/001.json
const film      = ["No Country for Old Men", "No es pais para viejos"];
const bell      = ["Tommy Lee Jones"];
const moss      = ["Josh Brolin", "Joshua Brolin"];
const director  = ["Coen brothers", "The Coens", "Joel and Ethan Coen", "Joel Coen", "Ethan Coen"];
const chigurh   = ["Javier Bardem"];
const wells     = ["Woody Harrelson", "Woodrow Harrelson"];
const dp        = ["Roger Deakins", "Roger A. Deakins"];
const composer  = ["Carter Burwell"];
const editor    = ["Roderick Jaynes", "Coen brothers", "The Coens", "Joel and Ethan Coen"];
const pd        = ["Jess Gonchor"];

const cases = [
  ["No Country for Old Men", film, true,  "exact title"],
  ["no country for old men", film, true,  "lowercase title"],
  ["No Country for Old Man", film, true,  "title typo men->man"],
  ["Javier Bardum",      chigurh, true,  "name typo"],
  ["Tommy Lee Jonas",       bell, true,  "name typo"],
  ["No es país para viejos", film, true,  "foreign title WITH accent"],
  ["no es pais para viejos", film, true,  "foreign title no accent"],
  ["Bardem",            chigurh, true,  "surname only"],
  ["Deakins",               dp, true,  "surname only (DP)"],
  ["Brolin",              moss, true,  "surname only"],
  ["Gonchor",               pd, true,  "surname only (PD)"],
  ["Harrelson",          wells, true,  "surname only"],
  ["Coen brothers",   director, true,  "director: coen brothers"],
  ["the coens",       director, true,  "director: the coens"],
  ["Joel and Ethan Coen", director, true, "director: full names"],
  ["Joel & Ethan Coen", director, true, "director: ampersand"],
  ["coen",            director, true,  "director: surname"],
  ["Roderick Jaynes",   editor, true,  "editor: pseudonym"],
  ["Coen brothers",     editor, true,  "editor: the real answer"],
  ["Steven Spielberg", director, false, "wrong director"],
  ["Brad Pitt",        chigurh, false, "wrong actor"],
  ["Roger Moore",           dp, false, "right first name wrong surname"],
  ["Josh Hartnett",       moss, false, "right first name wrong surname"],
  ["",                    film, false, "empty guess"],
  ["xkcd",            composer, false, "nonsense"],
];

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
