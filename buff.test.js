// Movie Buff autocomplete tests (node buff.test.js). House style: PASS/FAIL
// lines, non-zero exit on any failure.
import { indexKeys, suggest } from './docs/buff.js';

let fails = 0;
function check(label, got, expected) {
  const g = JSON.stringify(got), e = JSON.stringify(expected);
  const ok = g === e;
  console.log((ok ? 'PASS  ' : 'FAIL  ') + label + (ok ? '' : `  got=${g} expected=${e}`));
  if (!ok) fails++;
}

const ENTRIES = [
  ['The Godfather', 1972],
  ['The Godfather Part II', 1974],
  ['Goodfellas', 1990],
  ['The Good, the Bad and the Ugly', 1966],
  ['No Country for Old Men', 2007],
  ['Amélie', 2001],
  ['City of God', 2002],
  ['A Good Day to Die Hard', 2013],
];
const KEYS = indexKeys(ENTRIES);

check('keys use matcher normalize (article dropped)', KEYS[0], 'godfather');
check('keys strip diacritics', KEYS[5], 'amelie');

check('prefix match, popularity order', suggest(ENTRIES, KEYS, 'godf'),
      [['The Godfather', 1972], ['The Godfather Part II', 1974]]);
check('leading article in the QUERY is dropped too', suggest(ENTRIES, KEYS, 'The Godf'),
      [['The Godfather', 1972], ['The Godfather Part II', 1974]]);
check('prefix matches (incl. dropped-article titles) in index order', suggest(ENTRIES, KEYS, 'good'),
      [['Goodfellas', 1990], ['The Good, the Bad and the Ugly', 1966], ['A Good Day to Die Hard', 2013]]);
check('word-boundary contains ranks after prefix', suggest(ENTRIES, KEYS, 'god'),
      [['The Godfather', 1972], ['The Godfather Part II', 1974], ['City of God', 2002]]);
check('diacritic-insensitive query', suggest(ENTRIES, KEYS, 'amel'), [['Amélie', 2001]]);
check('single char suggests nothing', suggest(ENTRIES, KEYS, 'g'), []);
check('empty query suggests nothing', suggest(ENTRIES, KEYS, ''), []);
check('no match -> empty', suggest(ENTRIES, KEYS, 'zzzz'), []);
check('limit respected', suggest(ENTRIES, KEYS, 'good', 1).length, 1);

console.log(`\n${11 - fails} passed, ${fails} failed`);
process.exit(fails ? 1 : 0);
