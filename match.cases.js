// The matcher contract, as data: every case is [guess, answers, expected, label].
// Shared by match.test.js (local contract), worker.test.js (server parity — GATE 1
// check 3 replays this exact table against the /match endpoint), and any future
// live-endpoint gate script. Add cases HERE, never fork the table.

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

export const cases = [
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
