// The end-card's graph intelligence: shortest-route reveal and route counting.
// Pure logic, no DOM — takes a loaded Corpus, imports nothing, so Node tests run
// this exact file. Only ever called AFTER a run ends: this module computes the
// answer, and nothing here may leak into the play surface.
//
// Units, pinned once: "degrees" counts PERSON hops (the game's brag number). A
// chain of d degrees passes through d-1 intermediate films, so film-layer BFS
// distance k means k+1 degrees when a closer is found in that film's cast.

// One shortest chain from `start` to `goal` (film indices), as steps in play
// order: [{type:'person',index}, {type:'film',index}, …, {type:'person',index}]
// — the same shape as Chain#chain, ending on the person who closes it. Returns
// null when no chain exists within maxDegrees. The corpus adjacency is in
// popularity order, so the first route found reads famous, not obscure.
export function shortestChain(corpus, start, goal, maxDegrees = 6) {
  if (start === goal) return [];
  const closer = (film) => corpus.castOf(film).find((p) => corpus.isCredited(goal, p));

  // Degree 1: someone in the start film is credited in the goal.
  const direct = closer(start);
  if (direct !== undefined) return [{ type: 'person', index: direct }];

  // BFS over films (never stepping into the goal — chains close ON it, not IN it),
  // remembering how each film was reached for reconstruction.
  const via = new Map([[start, null]]);       // film -> {from: film, person} | null
  let frontier = [start];
  for (let depth = 1; depth < maxDegrees && frontier.length; depth++) {
    const next = [];
    for (const film of frontier) {
      for (const person of corpus.castOf(film)) {
        for (const f of corpus.filmsOf(person)) {
          if (via.has(f) || f === goal) continue;
          via.set(f, { from: film, person });
          const end = closer(f);
          if (end !== undefined) {
            const steps = [{ type: 'person', index: end }];
            for (let at = f; via.get(at); ) {
              const hop = via.get(at);
              steps.unshift({ type: 'person', index: hop.person }, { type: 'film', index: at });
              at = hop.from;
            }
            return steps;
          }
          next.push(f);
        }
      }
    }
    frontier = next;
  }
  return null;
}

// Degrees on a shortest chain, or null. The reveal's own par check — never trust
// a stored par against a corpus it wasn't built from.
export function degreesBetween(corpus, start, goal, maxDegrees = 6) {
  const steps = shortestChain(corpus, start, goal, maxDegrees);
  if (steps === null) return null;
  return steps.length === 0 ? 0 : (steps.length + 1) / 2;
}

// The route's deep-cut factor, 0–99: how obscure were the people you hopped
// through, relative to the whole pool? Fame proxy = pool credit count (the only
// signal the shipped graph carries; the pool prunes single-credit people, so the
// floor is 2). Score per person = geometric blend of a midpoint-rank percentile
// (population-honest, but the bottom-heavy pile compresses it) and a log-scale
// position (spreads the obscure end, but flatters mid-fame) — each corrects the
// other's failure mode. Calibrated on the real corpus 2026-08-14: hub people 0,
// fame-10 ≈ 20, fame-4 ≈ 49, the floor ≈ 88. Returns null for an empty route.
export function obscurity(corpus, people) {
  if (!people || !people.length) return null;
  const fame = corpus.people.map((_, i) => corpus.filmsOf(i).length);
  const sorted = [...fame].sort((a, b) => a - b);
  const vmax = sorted[sorted.length - 1];
  const logDen = vmax > 2 ? Math.log(vmax - 1) : 1;
  const below = (v) => {   // index of first element >= v
    let lo = 0, hi = sorted.length;
    while (lo < hi) { const m = (lo + hi) >> 1; sorted[m] < v ? lo = m + 1 : hi = m; }
    return lo;
  };
  const above = (v) => {   // index of first element > v
    let lo = 0, hi = sorted.length;
    while (lo < hi) { const m = (lo + hi) >> 1; sorted[m] <= v ? lo = m + 1 : hi = m; }
    return lo;
  };
  let sum = 0;
  for (const p of people) {
    const v = fame[p];
    const pct = (below(v) + 0.5 * (above(v) - below(v))) / sorted.length;
    const logPos = vmax > 2 ? 1 - Math.log(v - 1) / logDen : 1;
    sum += Math.sqrt(Math.max(0, (1 - pct) * logPos));
  }
  return Math.round((sum / people.length) * 99);
}

// How many DISTINCT shortest chains exist at exactly `par` degrees — full
// (person, film, person, …) sequences, not just closing people. Path-DP over the
// layered BFS DAG: count paths into each film at its minimal depth, then multiply
// out the closers. Capped because "38,412 ways" reads no better than "1,000+".
export function countGeodesics(corpus, start, goal, par, cap = 1000) {
  if (par < 1) return 0;
  const closersIn = (film) =>
    corpus.castOf(film).filter((p) => corpus.isCredited(goal, p)).length;

  // Films at minimal film-distance par-1 from start, with geodesic path counts.
  let layer = new Map([[start, 1]]);          // film -> paths reaching it
  const seen = new Set([start, goal]);        // goal is never an intermediate step
  for (let depth = 1; depth <= par - 1; depth++) {
    const next = new Map();
    for (const [film, paths] of layer) {
      for (const person of corpus.castOf(film)) {
        for (const f of corpus.filmsOf(person)) {
          if (seen.has(f)) continue;          // reached earlier = not geodesic here
          if (layer.has(f)) continue;         // same-layer edge, not forward
          next.set(f, (next.get(f) || 0) + paths);
        }
      }
    }
    for (const f of next.keys()) seen.add(f);
    layer = next;
    if (!layer.size) return 0;
  }

  let total = 0;
  for (const [film, paths] of layer) {
    total += paths * closersIn(film);
    if (total >= cap) return cap;
  }
  return total;
}
