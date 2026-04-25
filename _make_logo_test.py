"""Generate a test logo with soccer-ball-like black pads on the orange dot."""
import math
from PIL import Image, ImageDraw

SRC = r"c:/Users/Marcel/source/repos/BettingwithAI/bettingwithai-logo.png"
DST = r"c:/Users/Marcel/source/repos/BettingwithAI/bettingwithai-logo-balltest.png"

im = Image.open(SRC).convert("RGBA")
W, H = im.size
print("size:", W, H)

# Locate the orange dot by scanning for orange pixels.
px = im.load()
xs, ys = [], []
for y in range(H):
    for x in range(W):
        r, g, b, a = px[x, y]
        # Orange-ish: high red, mid-low green, low blue.
        if r > 200 and 60 < g < 160 and b < 80:
            xs.append(x)
            ys.append(y)

if not xs:
    raise SystemExit("No orange pixels found")

x0, x1 = min(xs), max(xs)
y0, y1 = min(ys), max(ys)
cx = (x0 + x1) / 2.0
cy = (y0 + y1) / 2.0
radius = ((x1 - x0) + (y1 - y0)) / 4.0
print("dot bbox:", x0, y0, x1, y1, "center:", cx, cy, "r:", radius)

# Draw black "pads" (pentagons) on top of the orange circle to evoke a soccer ball.
overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay)

BLACK = (10, 10, 10, 255)


def pentagon(center, size, rotation_deg=0):
    cxp, cyp = center
    pts = []
    for i in range(5):
        ang = math.radians(rotation_deg - 90 + i * 72)
        pts.append((cxp + size * math.cos(ang), cyp + size * math.sin(ang)))
    return pts


# Center pentagon
center_size = radius * 0.22
draw.polygon(pentagon((cx, cy), center_size, 0), fill=BLACK)

# Five surrounding pentagons placed around the center one.
ring_radius = radius * 0.60
ring_size = radius * 0.16
for i in range(5):
    ang = math.radians(-90 + i * 72)
    pcx = cx + ring_radius * math.cos(ang)
    pcy = cy + ring_radius * math.sin(ang)
    # Rotate each so a flat edge faces the center pentagon.
    draw.polygon(pentagon((pcx, pcy), ring_size, 0), fill=BLACK)

# Clip overlay to the circle by intersecting alpha channels.
mask = Image.new("L", im.size, 0)
mdraw = ImageDraw.Draw(mask)
mdraw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=255)

r_, g_, b_, a_ = overlay.split()
new_alpha = Image.eval(Image.merge("L", (a_,)), lambda v: v)
# Keep overlay alpha only where mask is on.
import PIL.ImageChops as ImageChops
combined_alpha = ImageChops.multiply(a_, mask)
overlay = Image.merge("RGBA", (r_, g_, b_, combined_alpha))

out = Image.alpha_composite(im, overlay)
out.save(DST)
print("saved:", DST)
