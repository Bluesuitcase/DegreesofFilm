// Daily puzzle selection from the manifest. Pure logic, no DOM — node-testable.

// Today's date as YYYY-MM-DD in the player's local time (the rollover boundary).
export function todayISO(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

// Pick the manifest entry for `dateISO`: an exact date match if present, else the
// most recent entry on or before that date, else the earliest entry. Returns
// null only for an empty/missing manifest. (So a day with no puzzle of its own
// still shows the latest available one rather than erroring.)
export function pickPuzzle(manifest, dateISO) {
  if (!Array.isArray(manifest) || manifest.length === 0) return null;
  const sorted = [...manifest].sort((a, b) =>
    a.date < b.date ? -1 : a.date > b.date ? 1 : 0);
  const exact = sorted.find((e) => e.date === dateISO);
  if (exact) return exact;
  let past = null;
  for (const e of sorted) {
    if (e.date <= dateISO) past = e;
    else break;
  }
  return past || sorted[0];
}
