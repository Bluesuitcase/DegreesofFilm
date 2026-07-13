"""Tests for image prep. Box/colour math is pure; the crop/sample tests use
Pillow, so run this under the venv:

    .venv/Scripts/python curation/images.test.py      (Windows)
    .venv/bin/python      curation/images.test.py      (macOS/Linux)
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import images  # noqa: E402

passed = failed = 0


def check(label, got, want):
    global passed, failed
    ok = got == want
    passed, failed = passed + (1 if ok else 0), failed + (0 if ok else 1)
    print(f"{'PASS' if ok else 'FAIL'}  {label}"
          + ("" if ok else f"\n        got:  {got!r}\n        want: {want!r}"))


def ok(label, cond):
    check(label, bool(cond), True)


def area(b):
    return (b[2] - b[0]) * (b[3] - b[1])


# --- expand_boxes (pure) ---
BOX = (100, 100, 300, 250)          # 200x150, centred at (200, 175)
boxes = images.expand_boxes(800, 600, BOX)
check("factor 1.0 keeps the tight box", boxes[0], (100, 100, 300, 250))
check("None -> full frame", boxes[2], (0, 0, 800, 600))
ok("tiers widen (areas strictly increase)", area(boxes[0]) < area(boxes[1]) < area(boxes[2]))

# clamping: a box hugging the top-left corner must stay in-bounds when expanded
corner = images.expand_boxes(800, 600, (0, 0, 100, 100), factors=(3.0,))[0]
ok("expanded box stays within image", corner[0] >= 0 and corner[1] >= 0
   and corner[2] <= 800 and corner[3] <= 600)
ok("expanded box keeps requested size", (corner[2] - corner[0]) == 300)

# --- best_window (pure): find the highest-energy window over a grid ---
# 4 cols x 3 rows, energy concentrated in the bottom-right 2x2 block.
GRID = [0, 0, 0, 0,
        0, 0, 5, 5,
        0, 0, 5, 5]
check("best_window finds the hot 2x2 block", images.best_window(GRID, 4, 3, 2, 2), (2, 1))
check("best_window ties break top-left (flat grid)",
      images.best_window([1] * 12, 4, 3, 2, 2), (0, 0))
check("best_window clamps an oversize window to the whole grid",
      images.best_window(GRID, 4, 3, 99, 99), (0, 0))

# --- box_around (pure): centre + clamp ---
check("box_around centres on the point",
      images.box_around(0.5, 0.5, 0.4), {"x": 0.3, "y": 0.3, "w": 0.4, "h": 0.4})
check("box_around clamps into the top-left corner",
      images.box_around(0.0, 0.0, 0.4), {"x": 0.0, "y": 0.0, "w": 0.4, "h": 0.4})
check("box_around clamps into the bottom-right corner",
      images.box_around(1.0, 1.0, 0.4), {"x": 0.6, "y": 0.6, "w": 0.4, "h": 0.4})

# --- deweight_bands (pure): a top-band hot row loses to a middle row ---
# 3 cols x 5 rows; top row hot (10s), a middle row warm (4s), rest 0.
BANDGRID = [10, 10, 10,   0, 0, 0,   4, 4, 4,   0, 0, 0,   0, 0, 0]
dw = images.deweight_bands(BANDGRID, 3, 5, top=0.2, bottom=0.2, factor=0.1)
check("deweight scales the top band by factor", dw[0:3], [1.0, 1.0, 1.0])
check("deweight leaves the middle untouched", dw[6:9], [4, 4, 4])
check("deweighted top row (1.0 each) now loses to the middle row (4 each)",
      images.best_window(dw, 3, 5, 3, 1), (0, 2))

# --- clamp_accent (pure) ---
HEX = re.compile(r"^#[0-9a-f]{6}$")


def to_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


ok("returns #rrggbb", bool(HEX.match(images.clamp_accent((200, 50, 50)))))
red = to_rgb(images.clamp_accent((200, 50, 50)))
ok("saturated red stays red-dominant", red[0] > red[1] and red[0] > red[2])
grey = to_rgb(images.clamp_accent((128, 128, 128)))
ok("grey gets saturation (channels no longer all equal)",
   not (grey[0] == grey[1] == grey[2]))
dark = to_rgb(images.clamp_accent((8, 8, 30), min_val=0.45))
ok("too-dark colour is lifted to the brightness floor", max(dark) >= int(0.45 * 255))

# --- crop_tiers + sample_accent (Pillow) ---
from PIL import Image  # noqa: E402

gradient = Image.new("RGB", (800, 600))
gradient.putdata([(x % 256, y % 256, 128)
                  for y in range(600) for x in range(800)])
tiers = images.crop_tiers(gradient, BOX, out_width=500)
check("three tiers produced", len(tiers), 3)
ok("every tier scaled to out_width", all(t.width == 500 for t in tiers))

# --- auto_crop_box (Pillow): centre on the busiest region ---
canvas = Image.new("RGB", (200, 120), (30, 30, 30))     # flat, low-energy
for y in range(60, 120):                                # high-contrast checker, bottom-right quadrant
    for x in range(100, 200):
        canvas.putpixel((x, y), (255, 255, 255) if (x + y) % 2 else (0, 0, 0))
ab = images.auto_crop_box(canvas, scale=0.5)
ok("auto box is normalized in-bounds",
   0 <= ab["x"] <= 1 and 0 <= ab["y"] <= 1 and 0 < ab["w"] <= 1 and 0 < ab["h"] <= 1)
ok("auto box keeps the frame aspect (w == h in normalized coords)", abs(ab["w"] - ab["h"]) < 0.02)
_cx, _cy = ab["x"] + ab["w"] / 2, ab["y"] + ab["h"] / 2
ok("auto box centres on the busy quadrant (bottom-right)", _cx > 0.5 and _cy > 0.5)
ok("auto box carries the face flag (edge path -> False)", ab["face"] is False)

# --- box_iou: the auto-crop acceptance metric (frontier 1a) ---
B = {"x": 0.1, "y": 0.1, "w": 0.4, "h": 0.4}
ok("iou: identical boxes = 1.0", images.box_iou(B, dict(B)) == 1.0)
ok("iou: disjoint boxes = 0.0", images.box_iou(B, {"x": 0.6, "y": 0.6, "w": 0.3, "h": 0.3}) == 0.0)
_half = images.box_iou(B, {"x": 0.3, "y": 0.1, "w": 0.4, "h": 0.4})   # half-overlap in x
ok("iou: half-shifted box = 1/3", abs(_half - round(1 / 3, 4)) < 1e-9)
ok("iou: degenerate zero-area box = 0.0", images.box_iou(B, {"x": 0.1, "y": 0.1, "w": 0, "h": 0}) == 0.0)

# --- detect_faces: a flat image has no faces (also exercises the no-cv2 fallback) ---
ok("no faces in a flat image", images.detect_faces(Image.new("RGB", (120, 80), (40, 40, 40))) == [])

reddish = Image.new("RGB", (40, 40), (200, 40, 40))
acc = to_rgb(images.sample_accent(reddish))
ok("accent of a red still is reddish", acc[0] > acc[1] and acc[0] > acc[2])
ok("accent is valid hex", bool(HEX.match(images.sample_accent(reddish))))

# --- to_background / derive_background ---
ok("saturation: red > grey", images.saturation((200, 30, 30)) > images.saturation((128, 128, 128)))
bgcol = to_rgb(images.to_background((200, 40, 40)))
ok("background is valid hex", bool(HEX.match(images.to_background((200, 40, 40)))))
ok("background is dark", max(bgcol) < 40)
ok("background keeps the hue (red-dominant)", bgcol[0] >= bgcol[1] and bgcol[0] >= bgcol[2])

twotone = Image.new("RGB", (40, 40))
twotone.putdata([(180, 30, 30) if (x + y) % 2 else (20, 30, 90)
                 for y in range(40) for x in range(40)])
theme = images.derive_background(twotone)
ok("derive_background returns bg + bg2 hexes",
   bool(HEX.match(theme["bg"])) and bool(HEX.match(theme["bg2"])))
ok("both derived backgrounds are dark",
   max(to_rgb(theme["bg"])) < 50 and max(to_rgb(theme["bg2"])) < 85)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
