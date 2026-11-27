# Picture: what BLIPR's screen does from power-up to a shot (ESP32 firmware 0.2.16-0.2.20).
# Run: python pictures/screen_sequence.py  ->  pictures/out/screen_sequence.png
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
BLUE = "#7cc4ff"

fig, ax = plt.subplots(figsize=(15, 7.4), dpi=110)
ax.set_xlim(0, 1500); ax.set_ylim(0, 740); ax.invert_yaxis(); ax.axis("off")
ax.text(750, 40, "What BLIPR's screen does", ha="center", fontsize=21, weight="bold")
ax.text(750, 78, "ESP32 firmware 0.2.20. The screen is dark while BLIPR listens: a lit screen adds noise the radar can hear.",
        ha="center", fontsize=12, color="#333")

def screen(x, y, w=230, h=118):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=6", fc="#111", ec="#444", lw=2))
    return x, y, w, h

def txt(x, y, s, size=12, color=BLUE, **kw):
    ax.text(x, y, s, color=color, fontsize=size, family="DejaVu Sans Mono", weight="bold", **kw)

steps = []
# 1. level (crop of the real level preview, right half: "LEVEL")
x0, y = 30, 130
lv = Image.open(os.path.join(OUT, "oled_level_preview.png"))
W, H = lv.size
crop = lv.crop((W // 2 + 12, 10, W - 12, H - 36))
sx, sy, sw, sh = screen(x0, y)
ax.imshow(crop, extent=(sx, sx + sw, sy + sh, sy), zorder=3)
steps.append((x0, "1  Level", "Switch on: a bubble level,\nup to a minute. Shim BLIPR\nuntil it says LEVEL, hold 3 s.\n(Skipped if the level is\ndisabled in Range Book.)"))

# 2. weather
x1 = x0 + 295
sx, sy, sw, sh = screen(x1, y)
txt(sx + 10, sy + 34, "71.6F", 20)
txt(sx + 10, sy + 62, "Humidity 38%", 11)
txt(sx + 10, sy + 82, "Pressure 29.92 in", 11)
txt(sx + 10, sy + 104, "Hdg 271", 11)
steps.append((x1, "2  Weather, 10 s", "Temperature, humidity,\npressure and heading,\nonce. (Sensor kit only.)"))

# 3. READY
x2 = x1 + 295
sx, sy, sw, sh = screen(x2, y)
txt(sx + sw / 2, sy + sh / 2 + 10, "READY", 30, ha="center")
steps.append((x2, "3  READY, 2 s", "BLIPR arms itself."))

# 4. dark
x3 = x2 + 295
sx, sy, sw, sh = screen(x3, y)
ax.text(sx + sw / 2, sy + sh / 2 + 6, "(dark)", color="#555", fontsize=13, ha="center", style="italic")
steps.append((x3, "4  Dark: listening", "Armed and quiet. Shoot."))

# 5. shot (crop of the Classic look)
x4 = x3 + 295
lk = Image.open(os.path.join(OUT, "oled_looks.png"))
crop = lk.crop((10, 42, 416, 242))
sx, sy, sw, sh = screen(x4, y)
ax.imshow(crop, extent=(sx, sx + sw, sy + sh, sy), zorder=3)
steps.append((x4, "5  Shot, 3 s", "Speed and string (n, avg,\nSD, ES) for 'Show each\nshot for' (default 3 s).\nNot listening while lit.\nThen dark again."))

for x, head, body in steps:
    ax.text(x + 115, 285, head, ha="center", fontsize=13.5, weight="bold")
    ax.text(x + 115, 310, body, ha="center", va="top", fontsize=10.5, color="#222", linespacing=1.35)
for a, b in zip(steps[:-1], steps[1:]):
    ax.add_patch(FancyArrowPatch((a[0] + 240, 190), (b[0] - 10, 190), arrowstyle="-|>", mutation_scale=22, color="#555", lw=2))

# loop back from shot to dark
ax.add_patch(FancyArrowPatch((x4 + 60, 400), (x3 + 115, 340), connectionstyle="arc3,rad=-0.5",
                             arrowstyle="-|>", mutation_scale=20, color="#1565c0", lw=2))
ax.text((x3 + x4) / 2 + 115, 490, "next shot", ha="center", fontsize=10.5, color="#1565c0")

box = ("After each shot BLIPR checks it hasn't been knocked: tilted more than 1 degree, or turned more than 5 degrees from where\n"
       "it was levelled. If so, the level comes back once the shot has been shown, then READY and dark again.\n"
       "Range Book's chronograph settings:  'Re-level and update the heading' shows the level now  ·  'Disable the level' (for shooting\n"
       "at an angle) skips the level at power-up and after shots  ·  'Show each shot for' sets step 5 (0 = until the next shot).")
ax.add_patch(FancyBboxPatch((40, 560), 1420, 140, boxstyle="round,pad=8", fc="#fff8e1", ec="#e6c34a"))
ax.text(60, 630, box, va="center", fontsize=11.5, linespacing=1.55)

out = os.path.join(OUT, "screen_sequence.png")
fig.savefig(out, bbox_inches="tight", facecolor="white")
print(out)
