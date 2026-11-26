# Wiring picture: 5 V noise filter for the ESP32 (Nov 25, 2026). Run: python pictures/esp_filter.py
# The ESP32's Bluetooth bursts come through BLIPR's 5 V (jumper test, Nov 25), so the ESP32 gets its own filter,
# like the battery holder's: L2 in its 5 V feed, C29/C30 right at its pins. No change to the board's copper.
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle

fig, ax = plt.subplots(figsize=(11.5, 7.2), dpi=100)
ax.set_xlim(0, 1150); ax.set_ylim(0, 720); ax.invert_yaxis(); ax.axis("off")

ax.text(575, 45, "5 V noise filter: board's ESP32 socket to the ESP32", ha="center", fontsize=18, weight="bold")
ax.text(575, 85, "The ESP32's 5 V pin no longer goes into the socket: its power comes through L2 instead. GND, 20 and 21 stay as they are.",
        ha="center", fontsize=11)

# circuit board with the socket holes
ax.add_patch(Rectangle((30, 150), 230, 380, fc="#2e7d32", ec="#1b5e20", lw=2))
ax.text(145, 135, "circuit board", ha="center", color="#1b5e20", fontsize=13, weight="bold")
ax.text(145, 505, "ESP32 socket", ha="center", color="white", fontsize=12, weight="bold")
for y, lab in ((250, "5V hole\n(from D1)"), (340, "GND")):
    ax.add_patch(Circle((240, y), 13, fc="#ffd54f", ec="#333", lw=1.5))
    ax.text(215, y, lab, ha="right", va="center", color="white", fontsize=11, weight="bold")
ax.text(145, 430, "20, 21 and the other\npins: unchanged", ha="center", va="center", color="white", fontsize=10)

# ESP32 module
ax.add_patch(FancyBboxPatch((830, 170), 260, 330, boxstyle="round,pad=4", fc="#222", ec="#111", lw=2))
ax.text(960, 205, "ESP32-C3 SuperMini", ha="center", color="white", fontsize=12, weight="bold")
ax.text(960, 230, "(chip side up)", ha="center", color="#bbb", fontsize=10)
for y, lab in ((250, "5V pin"), (340, "GND pin")):
    ax.add_patch(Circle((850, y), 13, fc="#ffd54f", ec="#c62828", lw=2.5))
    ax.text(875, y, lab, va="center", color="white", fontsize=11, weight="bold")
ax.text(960, 420, "its 5V header pin is clipped\noff under the module, so it\nno longer reaches the socket",
        ha="center", va="center", color="#ffcc80", fontsize=10)

# 5 V path through the inductor
ax.plot([253, 420], [250, 250], color="#d32f2f", lw=5, solid_capstyle="round")
ax.add_patch(FancyBboxPatch((420, 225), 120, 50, boxstyle="round,pad=3", fc="#6d4c41", ec="#333", lw=2))
ax.text(480, 250, "L2", ha="center", va="center", color="white", fontsize=14, weight="bold")
ax.text(480, 195, "inductor 22 µH, 1 A+\n(same as L1; either way round)", ha="center", fontsize=10.5)
ax.plot([540, 837], [250, 250], color="#d32f2f", lw=5, solid_capstyle="round")
# ground (through the socket, as now)
ax.plot([253, 837], [340, 340], color="#222", lw=5, solid_capstyle="round")
ax.text(545, 362, "GND: through the socket as now", ha="center", fontsize=10, color="#444")

# capacitors on the ESP32 side
for x, (fc, top, lab) in ((610, ("#1565c0", "C29", "470 µF\n10 V or more")), (770, ("#f9a825", "C30", "1 µF\nceramic"))):
    ax.plot([x, x], [250, 340], color="#888", lw=3)
    if top == "C29":
        ax.add_patch(Rectangle((x - 22, 272), 44, 38, fc=fc, ec="#333"))
        ax.add_patch(Rectangle((x - 22, 310), 44, 12, fc="#ddd", ec="#333"))
        ax.text(x + 32, 285, "+", color="#d32f2f", fontsize=16, weight="bold")
        ax.text(x + 30, 318, "stripe (−)\nto GND", fontsize=9, va="center")
    else:
        ax.add_patch(Rectangle((x - 17, 280), 34, 32, fc=fc, ec="#333"))
    ax.plot([x, x], [345, 470], color="#aaa", lw=1, ls=":")
    ax.text(x, 480, top + "\n" + lab, ha="center", va="top", fontsize=10.5)

# how-to box
steps = ("How:  1. Clip the ESP32's 5V header pin flush under the module (a pin can be soldered back on later).\n"
         "2. Solder a short male header pin to one L2 leg and push it into the socket's 5V hole; solder the other\n"
         "    leg to the 5V pin's stub on top of the module.   3. Solder C29 and C30 across the module's 5V and GND\n"
         "    pins, as close as you can (C29 lying flat, stripe to GND).   4. Beep the 5V pin to D1's square pad: it\n"
         "    should still beep (through L2), and 5V to GND must not.   Check first that\n    it all fits in the case (I can check the case model).")
ax.add_patch(FancyBboxPatch((40, 578), 1070, 128, boxstyle="round,pad=6", fc="#fff8e1", ec="#e6c34a"))
ax.text(55, 642, steps, va="center", fontsize=10.2, family="DejaVu Sans")

out = os.path.join(os.path.dirname(__file__), "out", "esp_filter.png")
fig.savefig(out, bbox_inches="tight", facecolor="white")
print(out)
