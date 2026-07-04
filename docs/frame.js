// Which still to show, given how deep the run is. Pure logic, no DOM — so the
// Node tests can drive it directly (see frame.test.js).
//
// The still tracks the *last credit you answered*:
//   - on the film rung (index 0) it starts as the tightest crop (images[0]) so
//     naming the film is a challenge, then the REVEAL MECHANIC widens it one image
//     tier per wrong guess (revealTier), up to the full frame — each miss shows
//     more of the shot;
//   - once you pass a credit rung, it swaps to that person's image + caption
//     (their TMDB headshot, cast and crew alike; cast captions read "Name as
//     Character", crew captions are the name alone);
//   - any rung without its own image holds the full uncropped frame (the widest
//     tier, images[last]) — which is also what the film rung reveals, so the
//     old post-film-rung reveal falls straight out of this rule.

export function pickCreditFrame(index, rungs, frames, revealTier = 0) {
  const list = frames || [];
  const fullFrame = list.length ? list[list.length - 1] : null;

  if (index <= 0) {
    if (!list.length) return { src: null, caption: '' };
    // Widen the crop one tier per wrong guess, clamped to the widest authored tier.
    const tier = Math.min(Math.max(revealTier, 0), list.length - 1);
    return { src: list[tier], caption: '' };
  }

  // The last rung we actually answered (clamped for the won/over end states,
  // where index can sit at rungs.length).
  const last = (rungs || [])[Math.min(index, (rungs || []).length) - 1];
  if (last && last.image) return { src: last.image, caption: last.caption || '' };
  return { src: fullFrame, caption: '' };
}
