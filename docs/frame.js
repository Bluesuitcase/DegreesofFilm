// Which still to show, given how deep the run is. Pure logic, no DOM — so the
// Node tests can drive it directly (see frame.test.js).
//
// The still tracks the *last credit you answered*:
//   - on the film rung (index 0) it's the tight crop (images[0]) so naming the
//     film is a challenge;
//   - once you pass a credit rung, it swaps to that person's image + caption
//     (character still for cast, headshot for crew);
//   - any rung without its own image holds the full uncropped frame (the widest
//     tier, images[last]) — which is also what the film rung reveals, so the
//     old post-film-rung reveal falls straight out of this rule.

export function pickCreditFrame(index, rungs, frames) {
  const list = frames || [];
  const tightCrop = list.length ? list[0] : null;
  const fullFrame = list.length ? list[list.length - 1] : null;

  if (index <= 0) return { src: tightCrop, caption: '' };

  // The last rung we actually answered (clamped for the won/over end states,
  // where index can sit at rungs.length).
  const last = (rungs || [])[Math.min(index, (rungs || []).length) - 1];
  if (last && last.image) return { src: last.image, caption: last.caption || '' };
  return { src: fullFrame, caption: '' };
}
