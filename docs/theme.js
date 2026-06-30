// Accent theming helpers. Pure colour math, no DOM — node-testable.
// app.js applies these to CSS variables; the ink base + bone text stay fixed,
// only the accent (and the text that sits *on* the accent) shift per puzzle.

// '#rgb' or '#rrggbb' -> [r,g,b] (0..255), or null if unparseable.
export function parseHex(hex) {
  if (typeof hex !== 'string') return null;
  let h = hex.trim().replace(/^#/, '');
  if (h.length === 3) h = h.split('').map((c) => c + c).join('');
  if (!/^[0-9a-fA-F]{6}$/.test(h)) return null;
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
}

// WCAG relative luminance (0..1).
export function luminance(rgb) {
  const [R, G, B] = rgb.map((c) => {
    c /= 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * R + 0.7152 * G + 0.0722 * B;
}

function contrast(l1, l2) {
  const a = Math.max(l1, l2), b = Math.min(l1, l2);
  return (a + 0.05) / (b + 0.05);
}

// Readable text colour to place ON an accent background: whichever of the dark
// ink / bone text has the higher contrast against the accent. Falls back to dark
// ink for an unparseable accent.
export function onAccentText(hex, { dark = '#1a1206', light = '#ece7dd' } = {}) {
  const rgb = parseHex(hex);
  if (!rgb) return dark;
  const la = luminance(rgb);
  return contrast(la, luminance(parseHex(dark))) >= contrast(la, luminance(parseHex(light)))
    ? dark : light;
}
