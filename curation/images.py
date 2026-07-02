"""Image preparation (Pillow) for a puzzle still: reveal-tier crops + page accent.

Two jobs on the curator-supplied source frame:
  - crop_tiers(): from the tight crop box the curator picked, produce the 3 reveal
    tiers (most-zoomed first) by expanding the box outward toward the full frame.
    We author 3 tiers per the schema even though the v1 client shows only tier 1
    (DESIGN §4) — they're ready for a future reveal mechanic.
  - sample_accent(): a `theme.accent` colour sampled from the still, clamped to a
    saturation/brightness floor so it stays legible against the fixed ink base.

The box and colour MATH is pure (expand_boxes / clamp_accent) and unit-tests
without Pillow; only the pixel work needs Pillow.
"""
import colorsys
import os
import sys

# Reveal tiers, most-zoomed first: tight box, a wider crop, then the full frame.
DEFAULT_FACTORS = (1.0, 1.8, None)


def expand_boxes(img_w, img_h, box, factors=DEFAULT_FACTORS):
    """Concentric crop boxes around `box`'s centre, scaled by each factor and
    clamped inside the image. `None` means the full frame. Pure.

    Tiers share the *box's* aspect (the full-frame tier uses the image aspect),
    so for a smooth zoom-out the crop UI should constrain the box to the frame
    aspect. Only tier 1 is shown in v1; tiers 2-3 await the reveal mechanic.
    """
    left, top, right, bottom = box
    cx, cy = (left + right) / 2, (top + bottom) / 2
    bw, bh = right - left, bottom - top
    out = []
    for f in factors:
        if f is None:
            out.append((0, 0, img_w, img_h))
            continue
        nw, nh = min(bw * f, img_w), min(bh * f, img_h)
        l = max(0, min(cx - nw / 2, img_w - nw))
        t = max(0, min(cy - nh / 2, img_h - nh))
        out.append((round(l), round(t), round(l + nw), round(t + nh)))
    return out


def best_window(energy, cols, rows, win_cols, win_rows):
    """Top-left (col, row) of the win_cols x win_rows window with the greatest
    total 'energy' over a row-major cols x rows grid. Ties break toward the
    top-left. Pure — uses a summed-area table, so it's O(cols*rows)."""
    win_cols = max(1, min(win_cols, cols))
    win_rows = max(1, min(win_rows, rows))
    sat = [[0] * (cols + 1) for _ in range(rows + 1)]      # (rows+1)x(cols+1)
    for r in range(rows):
        base = r * cols
        for c in range(cols):
            sat[r + 1][c + 1] = (energy[base + c]
                                 + sat[r][c + 1] + sat[r + 1][c] - sat[r][c])
    best_c = best_r = 0
    best_sum = None
    for r in range(rows - win_rows + 1):
        for c in range(cols - win_cols + 1):
            s = (sat[r + win_rows][c + win_cols] - sat[r][c + win_cols]
                 - sat[r + win_rows][c] + sat[r][c])
            if best_sum is None or s > best_sum:
                best_sum, best_c, best_r = s, c, r
    return best_c, best_r


def clamp_accent(rgb, *, min_sat=0.45, min_val=0.45, max_val=0.92):
    """Hex accent from an (r,g,b), with saturation and brightness pushed into a
    legible range against the dark ink base. Pure (stdlib colorsys)."""
    r, g, b = (c / 255 for c in rgb)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    s = max(s, min_sat)
    v = min(max(v, min_val), max_val)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def _hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, round(c))) for c in rgb))


def saturation(rgb):
    return colorsys.rgb_to_hsv(*(c / 255 for c in rgb))[1]


def to_background(rgb, *, value=0.12, max_sat=0.55):
    """A deep but visibly film-hued tone for the page background: keep the hue,
    push saturation so the colour reads, and hold brightness low enough that bone
    text stays legible. Pure."""
    h, s, _ = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    s = min(max(s, 0.42), max_sat)
    r, g, b = colorsys.hsv_to_rgb(h, s, value)
    return _hex((r * 255, g * 255, b * 255))


# --- Pillow-backed pixel work -------------------------------------------------

def load_image(path):
    from PIL import Image
    return Image.open(path).convert("RGB")


def crop_tiers(image, box, *, factors=DEFAULT_FACTORS, out_width=1000):
    """Return the reveal-tier crops (PIL Images), each scaled to out_width."""
    tiers = []
    for b in expand_boxes(image.width, image.height, box, factors):
        crop = image.crop(b)
        w, h = crop.size
        tiers.append(crop.resize((out_width, max(1, round(h * out_width / w)))))
    return tiers


def auto_crop_box(image, *, scale=0.5, sample_w=160):
    """Suggest a tight tier-1 crop as a normalized box {x, y, w, h} (0..1): a
    `scale`-sized window (same aspect as the frame, so the tiers zoom out smoothly)
    placed over the busiest, most-detailed region of the still. 'Busy' = highest
    edge energy, from a downscaled FIND_EDGES map (best_window does the search).
    A STARTING POINT the curator reviews and approves/re-drags — not final."""
    from PIL import ImageFilter
    sw = max(8, min(sample_w, image.width))
    sh = max(8, round(image.height * sw / image.width))
    edges = image.convert("L").resize((sw, sh)).filter(ImageFilter.FIND_EDGES)
    energy = list(edges.getdata())
    win_c = max(1, round(sw * scale))
    win_r = max(1, round(sh * scale))
    c, r = best_window(energy, sw, sh, win_c, win_r)
    return {"x": round(c / sw, 4), "y": round(r / sh, 4),
            "w": round(win_c / sw, 4), "h": round(win_r / sh, 4)}


def sample_accent(image, **clamp_opts):
    """Average the still down to a swatch and clamp it to a usable accent."""
    small = image.resize((64, 64))
    pixels = list(small.getdata())
    n = len(pixels)
    avg = tuple(sum(p[i] for p in pixels) // n for i in range(3))
    return clamp_accent(avg, **clamp_opts)


def sample_palette(image, colors=8):
    """Dominant colours of the still as [(r,g,b), ...], most frequent first."""
    q = image.convert("RGB").resize((128, 128)).quantize(colors=colors)
    pal = q.getpalette()
    return [tuple(pal[i * 3: i * 3 + 3]) for _, i in sorted(q.getcolors(), reverse=True)]


def derive_background(image):
    """Two deep, film-hued background tones (for a gradient) from the still's
    palette: the most dominant colour darkened, plus a second for depth."""
    palette = sample_palette(image)
    second = palette[1] if len(palette) > 1 else palette[0]
    return {"bg": to_background(palette[0], value=0.14),
            "bg2": to_background(second, value=0.28)}


def save_tiers(tiers, out_dir, stem, *, quality=85):
    os.makedirs(out_dir, exist_ok=True)
    names = []
    for i, im in enumerate(tiers, start=1):
        name = f"{stem}-{i}.jpg"
        im.save(os.path.join(out_dir, name), quality=quality)
        names.append(name)
    return names


def _main(argv):
    import argparse
    ap = argparse.ArgumentParser(description="Crop reveal tiers + sample accent.")
    ap.add_argument("--src", required=True, help="source still")
    ap.add_argument("--box", type=int, nargs=4, metavar=("L", "T", "R", "B"),
                    help="tight crop box (default = full image)")
    ap.add_argument("--out", help="dir to write tier JPGs")
    ap.add_argument("--stem", default="tier")
    args = ap.parse_args(argv)

    img = load_image(args.src)
    box = tuple(args.box) if args.box else (0, 0, img.width, img.height)
    print(f"source {img.width}x{img.height}  accent {sample_accent(img)}")
    tiers = crop_tiers(img, box)
    for i, t in enumerate(tiers, start=1):
        print(f"  tier {i}: {t.width}x{t.height}")
    if args.out:
        print("wrote:", ", ".join(save_tiers(tiers, args.out, args.stem)))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
