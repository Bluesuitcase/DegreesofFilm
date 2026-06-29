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


def clamp_accent(rgb, *, min_sat=0.45, min_val=0.45, max_val=0.92):
    """Hex accent from an (r,g,b), with saturation and brightness pushed into a
    legible range against the dark ink base. Pure (stdlib colorsys)."""
    r, g, b = (c / 255 for c in rgb)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    s = max(s, min_sat)
    v = min(max(v, min_val), max_val)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


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


def sample_accent(image, **clamp_opts):
    """Average the still down to a swatch and clamp it to a usable accent."""
    small = image.resize((64, 64))
    pixels = list(small.getdata())
    n = len(pixels)
    avg = tuple(sum(p[i] for p in pixels) // n for i in range(3))
    return clamp_accent(avg, **clamp_opts)


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
