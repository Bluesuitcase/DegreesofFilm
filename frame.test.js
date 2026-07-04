import { pickCreditFrame } from './docs/frame.js';

let pass = 0, fail = 0;
function check(label, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  ok ? pass++ : fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${ok ? '' : `  (got ${JSON.stringify(got)}, want ${JSON.stringify(want)})`}`);
}

// A puzzle with three reveal tiers and a mix of rungs: cast with a character
// still, a crew rung with a headshot, and one rung with no image.
const frames = ['images/004-1.jpg', 'images/004-2.jpg', 'images/004-3.jpg'];
const rungs = [
  { role: 'Film' },                                                   // rung 1
  { role: 'Cast', image: 'images/004-r2.jpg', caption: 'Bale as Bruce Wayne' }, // rung 2
  { role: 'Director', image: 'images/004-r3.jpg', caption: 'Christopher Nolan' }, // rung 3
  { role: 'Cast' },                                                   // rung 4, no image
];

// index 0: still on the film rung -> tight crop, no caption.
check('film rung -> tight crop', pickCreditFrame(0, rungs, frames),
  { src: 'images/004-1.jpg', caption: '' });

// Reveal mechanic: each wrong guess on the film rung widens the crop one tier.
check('film rung, 0 misses -> tightest crop', pickCreditFrame(0, rungs, frames, 0),
  { src: 'images/004-1.jpg', caption: '' });
check('film rung, 1 miss -> wider tier', pickCreditFrame(0, rungs, frames, 1),
  { src: 'images/004-2.jpg', caption: '' });
check('film rung, 2 misses -> full frame', pickCreditFrame(0, rungs, frames, 2),
  { src: 'images/004-3.jpg', caption: '' });
check('film rung reveal clamps at the widest tier', pickCreditFrame(0, rungs, frames, 9),
  { src: 'images/004-3.jpg', caption: '' });
check('reveal ignores negative tiers', pickCreditFrame(0, rungs, frames, -1),
  { src: 'images/004-1.jpg', caption: '' });

// index 1: passed the film rung (rungs[0] has no image) -> full frame reveal.
check('after film rung -> full frame', pickCreditFrame(1, rungs, frames),
  { src: 'images/004-3.jpg', caption: '' });

// index 2: passed the first cast rung -> its headshot + "Name as Character" caption.
check('after cast rung -> headshot + character caption', pickCreditFrame(2, rungs, frames),
  { src: 'images/004-r2.jpg', caption: 'Bale as Bruce Wayne' });

// index 3: passed the director -> headshot + name-only caption.
check('after crew rung -> headshot', pickCreditFrame(3, rungs, frames),
  { src: 'images/004-r3.jpg', caption: 'Christopher Nolan' });

// index 4 (won / past the last rung): last rung has no image -> hold full frame.
check('imageless last rung -> full frame', pickCreditFrame(4, rungs, frames),
  { src: 'images/004-3.jpg', caption: '' });

// Overshoot (defensive): clamp to the last rung.
check('overshoot clamps to last rung', pickCreditFrame(99, rungs, frames),
  { src: 'images/004-3.jpg', caption: '' });

// Single-tier puzzle (like 001): tight crop and full frame are the same file.
const one = ['images/001.jpg'];
check('single tier, film rung', pickCreditFrame(0, rungs, one),
  { src: 'images/001.jpg', caption: '' });
check('single tier, after film rung', pickCreditFrame(1, rungs, one),
  { src: 'images/001.jpg', caption: '' });
check('single tier reveal stays on the one image', pickCreditFrame(0, rungs, one, 2),
  { src: 'images/001.jpg', caption: '' });

// No frames at all: film rung has nothing, but a credit image still shows.
check('no frames, film rung -> null', pickCreditFrame(0, rungs, []),
  { src: null, caption: '' });
check('no frames, credit rung still shows its image', pickCreditFrame(2, rungs, []),
  { src: 'images/004-r2.jpg', caption: 'Bale as Bruce Wayne' });

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
