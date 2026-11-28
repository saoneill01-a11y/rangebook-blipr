"""Schematic of the Range Book BLIPR main board v1.2, drawn with matplotlib.
The parts and connections follow pcb/design.py (the board's netlist). Run: python3 pcb/schematic.py
Writes pcb/out/schematic_v1.2.png and .pdf."""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LW = 1.4
INK = "#111"
NET = "#1f4e9e"
fig, ax = plt.subplots(figsize=(21.5, 15.0), dpi=120)
ax.set_xlim(0, 212); ax.set_ylim(0, 150); ax.set_aspect("equal"); ax.axis("off")


def wire(*pts, c=INK):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=c, lw=LW, solid_capstyle="round")


def dot(p):
    ax.plot(*p, "o", color=INK, ms=4.5)


def text(p, s, size=9, ha="center", va="center", c=INK, w="normal"):
    ax.text(p[0], p[1], s, fontsize=size, ha=ha, va=va, color=c, fontweight=w)


def netlabel(p, name, side="right"):
    """Flag-shaped net label touching point p."""
    x, y = p
    w = 1.6 + 1.05 * len(name)
    if side == "right":
        pts = [(x, y), (x + 1.5, y + 1.3), (x + w, y + 1.3), (x + w, y - 1.3), (x + 1.5, y - 1.3), (x, y)]
        tx = x + 1.5 + (w - 1.5) / 2
    else:
        pts = [(x, y), (x - 1.5, y + 1.3), (x - w, y + 1.3), (x - w, y - 1.3), (x - 1.5, y - 1.3), (x, y)]
        tx = x - 1.5 - (w - 1.5) / 2
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=NET, lw=1.1)
    text((tx, y), name, size=8, c=NET, w="bold")


def gnd(p):
    x, y = p
    wire((x, y), (x, y - 1.5))
    for i, hw in enumerate((1.6, 1.0, 0.4)):
        wire((x - hw, y - 1.5 - 0.6 * i), (x + hw, y - 1.5 - 0.6 * i))


def resistor(p1, p2, ref, val, lab_side=1):
    (x1, y1), (x2, y2) = p1, p2
    L = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    nx, ny = -uy, ux
    body = 4.0
    a = (L - body) / 2
    s = (x1 + ux * a, y1 + uy * a)
    e = (x1 + ux * (a + body), y1 + uy * (a + body))
    wire(p1, s); wire(e, p2)
    pts = [s]
    n = 6
    for i in range(n):
        t = a + body * (i + 0.5) / n
        off = 0.8 * (1 if i % 2 == 0 else -1)
        pts.append((x1 + ux * t + nx * off, y1 + uy * t + ny * off))
    pts.append(e)
    wire(*pts)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    if abs(ux) > 0.5:   # horizontal
        text((mx, my + 2.4 * lab_side), f"{ref} {val}", size=8)
    else:
        text((mx + 1.8 * lab_side, my), f"{ref}\n{val}", size=8, ha="left" if lab_side > 0 else "right")


def cap(p1, p2, ref, val, pol=False, lab_side=1):
    (x1, y1), (x2, y2) = p1, p2
    L = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    nx, ny = -uy, ux
    g = 0.7
    a = (L - g) / 2
    s = (x1 + ux * a, y1 + uy * a)
    e = (x1 + ux * (a + g), y1 + uy * (a + g))
    wire(p1, s); wire(e, p2)
    hw = 1.6
    wire((s[0] + nx * hw, s[1] + ny * hw), (s[0] - nx * hw, s[1] - ny * hw))
    if pol:
        # curved-ish negative plate drawn as thick line, plus sign on the positive side (p1 side)
        ax.plot([e[0] + nx * hw, e[0] - nx * hw], [e[1] + ny * hw, e[1] - ny * hw], color=INK, lw=LW * 2.2)
        text((s[0] - ux * 1.2 + nx * 1.9, s[1] - uy * 1.2 + ny * 1.9), "+", size=9, w="bold")
    else:
        wire((e[0] + nx * hw, e[1] + ny * hw), (e[0] - nx * hw, e[1] - ny * hw))
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    if abs(ux) > 0.5:
        text((mx, my + 2.8 * lab_side), f"{ref} {val}", size=8)
    else:
        text((mx + 2.3 * lab_side, my), f"{ref}\n{val}", size=8, ha="left" if lab_side > 0 else "right")


def opamp(c, name, pins):
    """Triangle pointing right, centred at c, + input on TOP. pins = (minus_pin, plus_pin, out_pin)."""
    x, y = c
    w, h = 9.0, 9.0
    xs = [x - w / 2, x + w / 2, x - w / 2, x - w / 2]
    ys = [y + h / 2, y, y - h / 2, y + h / 2]
    ax.plot(xs, ys, color=INK, lw=LW)
    p = (x - w / 2, y + 2.2); m = (x - w / 2, y - 2.2); o = (x + w / 2, y)
    text((m[0] + 1.2, m[1]), "−", size=11)
    text((p[0] + 1.2, p[1]), "+", size=10)
    text((x - 0.6, y + 6.5), name, size=8.5, w="bold")
    text((m[0] - 0.5, m[1] - 0.9), str(pins[0]), size=7, ha="right", c="#666")
    text((p[0] - 0.5, p[1] + 0.9), str(pins[1]), size=7, ha="right", c="#666")
    text((o[0] + 0.4, o[1] + 0.9), str(pins[2]), size=7, ha="left", c="#666")
    return m, p, o


def box(x0, y0, x1, y1, title=None, dashed=False):
    ax.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], color=INK, lw=1.0, ls="--" if dashed else "-")
    if title:
        text((x0 + 0.8, y1 - 1.8), title, size=9.5, ha="left", w="bold")


def inductor(p1, p2, ref, val):
    """Horizontal inductor: four humps."""
    (x1, y), (x2, _) = p1, p2
    body = 6.0
    a = x1 + (x2 - x1 - body) / 2
    wire(p1, (a, y)); wire((a + body, y), p2)
    import numpy as np
    for i in range(4):
        cx = a + body / 8 * (2 * i + 1)
        t = np.linspace(math.pi, 0, 20)
        ax.plot(cx + body / 8 * np.cos(t), y + body / 8 * np.sin(t) * 1.3, color=INK, lw=LW)
    text(((x1 + x2) / 2, y + 2.8), f"{ref} {val}", size=8)


def diode(p1, p2, ref, val):
    """Horizontal diode, anode p1 -> cathode p2 (bar = stripe)."""
    (x1, y), (x2, _) = p1, p2
    m = (x1 + x2) / 2
    wire(p1, (m - 1.4, y)); wire((m + 1.4, y), p2)
    ax.fill([m - 1.4, m - 1.4, m + 1.4], [y + 1.4, y - 1.4, y], color=INK)
    wire((m + 1.4, y + 1.5), (m + 1.4, y - 1.5))
    text((m, y + 2.8), f"{ref} {val}", size=8)


# ======================= title
text((2, 147), "Range Book BLIPR — main board v1.2 schematic (one amplifier channel shown in full; Q channel is identical)", size=13, ha="left", w="bold")
text((2, 143.3), "All grounds connect together. Op-amps U1, U2 = MCP6022 (pin 8 = +3V3OP, pin 4 = GND). Gain per stage = 1 + 10k/470 ≈ 22, "
     "two stages about 480 at the peak. Parts and connections follow pcb/design.py.", size=9.5, ha="left")

# ======================= POWER
Y = 128
box(1, 74, 210, 140, "1. Power")
box(4, 118, 21, 136)
text((12.5, 127), "BT1\nbattery holder\n18650 + 5 V boost\n(its button is\nthe on/off)", size=7.5)
wire((21, Y), (27, Y)); text((22, Y + 1.4), "5V", size=7, ha="left"); dot((27, Y)); text((27, Y - 2.2), "J1-1", size=6.5, c="#666")
wire((21, 122), (23, 122), (23, 120)); text((22, 123.4), "GND", size=7, ha="left"); gnd((23, 120))
inductor((27, Y), (40, Y), "L1", "22µH")
wire((40, Y), (58, Y))
dot((44, Y)); cap((44, Y), (44, 116), "C27", "470µF", pol=True); gnd((44, 116))
dot((52, Y)); cap((52, Y), (52, 116), "C28", "1µF"); gnd((52, 116))
dot((58, Y)); wire((58, Y), (58, 134)); netlabel((58, 134), "+5V", side="right")
text((67, 134.5), "→ Teensy VIN;  → D1 → L2 → ESP32-C3 5V (below)", size=7.5, ha="left", c="#444")
resistor((58, Y), (70, Y), "R18", "10Ω")
wire((70, Y), (90, Y))
dot((74, Y)); cap((74, Y), (74, 116), "C4", "10µF", pol=True); gnd((74, 116))
dot((83, Y)); cap((83, Y), (83, 116), "C1", "1µF"); gnd((83, 116))
box(90, 121, 102, 131)
text((96, 128.5), "U3", size=8.5, w="bold"); text((96, 124.5), "MCP1700\n3.3 V", size=7.5)
text((89.5, 129.5), "IN", size=6.5, ha="right", c="#666")
wire((96, 121), (96, 117)); gnd((96, 117)); text((97, 119.5), "GND", size=6.5, ha="left", c="#666")
wire((102, Y), (126, Y)); text((102.5, 129.5), "OUT", size=6.5, ha="left", c="#666")
dot((108, Y)); cap((108, Y), (108, 116), "C2", "1µF"); gnd((108, 116))
dot((117, Y)); cap((117, Y), (117, 116), "C3", "100µF", pol=True); gnd((117, 116))
dot((126, Y)); wire((126, Y), (126, 134)); netlabel((126, 134), "+3V3A", side="right")
RX0, RX1 = 140, 156
box(RX0, 104, RX1, 124)
text((148, 122), "RADAR (J2)", size=8.5, w="bold"); text((148, 119.6), "K-LC5-RFB-00C", size=6.8)
names = {1: "1  Q out", 2: "2  VCC", 3: "3  I out", 4: "4  GND", 5: "5  VCO: open"}
for k, yy in {1: 116.5, 2: 114.0, 3: 111.5, 4: 109.0, 5: 106.5}.items():
    text((148, yy), names[k], size=7)
wire((126, Y), (134, Y), (134, 114), (RX0, 114)); dot((134, 114))
cap((134, 114), (134, 106), "C5", "100nF", lab_side=-1); gnd((134, 106))
wire((RX1, 116.5), (159, 116.5)); netlabel((159, 116.5), "Q-IN", side="right")
wire((RX1, 111.5), (159, 111.5)); netlabel((159, 111.5), "I-IN", side="right")
wire((RX1, 109.0), (172, 109.0), (172, 105)); gnd((172, 105))
text((159, 106.5), "not connected", size=6.8, ha="left", c="#666")
wire((134, Y), (170, Y))
resistor((170, Y), (179, Y), "R1", "10Ω")
wire((179, Y), (182, Y)); dot((182, Y)); wire((182, Y), (182, 134)); netlabel((182, 134), "+3V3OP", side="right")
cap((182, Y), (182, 119), "C7", "10µF", pol=True, lab_side=-1); gnd((182, 119))
wire((182, Y), (190, Y), (190, 125))
resistor((190, 125), (190, 116), "R2", "10k", lab_side=-1)
dot((190, 116))
resistor((190, 116), (190, 107), "R3", "10k", lab_side=-1); gnd((190, 107))
wire((190, 116), (201, 116)); dot((194, 116)); dot((201, 116))
cap((194, 116), (194, 108), "C10", "10µF", pol=True); gnd((194, 108))
cap((201, 116), (201, 108), "C11", "100nF"); gnd((201, 108))
wire((201, 116), (201, 120)); netlabel((201, 120), "VREF", side="left")
# battery gauge
wire((12, 118), (12, 116.5)); resistor((12, 116.5), (12, 108), "R25", "10k", lab_side=-1)
text((14, 113.5), "on the cell's + tab", size=6.3, ha="left", c="#666")
wire((12, 108), (12, 102), (21, 102)); dot((21, 102)); text((21, 100), "J1-3", size=6.5, c="#666")
resistor((21, 102), (33, 102), "R19", "100k")
dot((33, 102)); resistor((33, 102), (33, 94.5), "R20", "100k", lab_side=-1); gnd((33, 94.5))
dot((40, 102)); cap((40, 102), (40, 94.5), "C26", "100nF"); gnd((40, 94.5))
wire((33, 102), (48, 102)); netlabel((48, 102), "BATT_SENSE → ESP32 GPIO3", side="right")
# ESP32 supply filter
YE = 86
netlabel((30, YE), "+5V", side="left")
diode((30, YE), (42, YE), "D1", "1N5817")
inductor((42, YE), (54, YE), "L2", "22µH")
wire((54, YE), (74, YE))
dot((58, YE)); cap((58, YE), (58, 78), "C29", "470µF", pol=True, lab_side=-1); gnd((58, 78))
dot((66, YE)); cap((66, YE), (66, 78), "C30", "1µF"); gnd((66, 78))
text((75, YE), "ESP32-C3 5V pin", size=8.5, ha="left", w="bold")
text((100, 99), "Radar pin 5 (VCO) is left unconnected (RFbeam allows it open).  I-IN and Q-IN are the amplifier inputs (sections 2 and 3).",
     size=7.5, c="#444", ha="left")
text((100, 93), "5 V filters (new on v1.2): L1, C27, C28 keep the holder's boost converter (~494 kHz) out of the shared 5 V;\n"
     "L2, C29, C30 keep the ESP32's Bluetooth bursts out of it. On a v1.1 board the same parts are wired by hand (build guide).\n"
     "D1 stops the ESP32's own USB port from back-feeding the rest of BLIPR. There is no separate power switch.",
     size=7.5, c="#444", ha="left", va="top")

# ======================= AMPLIFIER channel I
box(1, 26, 210, 72, "2. Amplifier — I channel (I-IN from radar pin 3 → Teensy A0)")
def stage(xin, cin, rb, rf, rg, cg, name, pins):
    yp = 60.0
    cap((xin, yp), (xin + 8, yp), cin[0], cin[1])
    nb = (xin + 8, yp); dot(nb)
    resistor(nb, (nb[0], 48), rb[0], rb[1], lab_side=-1); netlabel((nb[0], 48), "VREF", side="right")
    m, p, o = opamp((nb[0] + 24, yp - 2.2), name, pins)
    wire(nb, p)
    xm = m[0] - 3
    fy = 48.0
    wire(m, (xm, m[1])); dot((xm, m[1]))
    wire((xm, m[1]), (xm, fy))
    resistor((xm, fy), (o[0] + 3, fy), rf[0], rf[1], lab_side=-1)
    wire((o[0] + 3, fy), (o[0] + 3, o[1])); dot((o[0] + 3, fy)); dot((xm, fy))
    wire(o, (o[0] + 3, o[1])); dot((o[0] + 3, o[1]))
    xg = xm - 7
    wire((xm, m[1]), (xg, m[1]), (xg, 52))
    resistor((xg, 52), (xg, 43), rg[0], rg[1], lab_side=1)
    cap((xg, 43), (xg, 35), cg[0], cg[1]); gnd((xg, 35))
    return (o[0] + 3, o[1])

netlabel((14, 60), "I-IN", side="left")
out1 = stage(14, ("C12", "10nF"), ("R4", "4.7k"), ("R5", "10k"), ("R6", "470Ω"), ("C14", "1µF"), "U1A", (2, 3, 1))
wire(out1, (out1[0] + 6, out1[1]), (out1[0] + 6, 60), (out1[0] + 8, 60))
out2 = stage(out1[0] + 8, ("C15", "10nF"), ("R7", "4.7k"), ("R8", "10k"), ("R9", "470Ω"), ("C17", "1µF"), "U1B", (6, 5, 7))
x3 = out2[0]
resistor((x3, out2[1]), (x3 + 12, out2[1]), "R10", "330Ω")
dot((x3 + 12, out2[1]))
cap((x3 + 12, out2[1]), (x3 + 12, 44), "C18", "1nF"); gnd((x3 + 12, 44))
wire((x3 + 12, out2[1]), (x3 + 20, out2[1]))
text((x3 + 21, out2[1]), "Teensy A0\n(pin 14)", size=8.5, ha="left", w="bold")
wire((160, 46), (196, 46)); netlabel((160, 46), "+3V3OP", side="left")
dot((170, 46)); cap((170, 46), (170, 37), "C8", "100nF"); gnd((170, 37))
dot((186, 46)); cap((186, 46), (186, 37), "C9", "100nF"); gnd((186, 37))
text((178, 51), "Op-amp supply: U1 and U2 pin 8 = +3V3OP, pin 4 = GND.\nC8 across U1 pins 8–4, C9 across U2 pins 8–4.", size=7.5, c="#444")
text((136, 66.5), "Gain ≈ 22 per stage (1 + R5/R6), about 480 total at the peak.\nHigh-pass ≈ 3.4 kHz (C12, R4).  The top end is set by the op-amp\n"
     "(10 MHz): about 3 dB down near 245 kHz = 5,000 fps.\nADC filter ≈ 480 kHz (R10, C18).  Each output idles at 1.65 V.", size=8, ha="left", c="#333", va="top")

# ======================= Q channel + connections
box(1, 1, 84, 24, "3. Q channel — same circuit, different parts")
rows = [("Function", "I channel", "Q channel"), ("Input", "RADAR pin 3", "RADAR pin 1"), ("Op-amp", "U1A, U1B", "U2A, U2B"),
        ("Stage 1", "C12 R4 R5 R6 C14", "C19 R11 R12 R13 C21"), ("Stage 2", "C15 R7 R8 R9 C17", "C22 R14 R15 R16 C24"),
        ("Output filter", "R10 C18", "R17 C25"), ("Teensy pin", "A0 (pin 14)", "A1 (pin 15)")]
for i, r in enumerate(rows):
    y = 19.5 - i * 2.5
    for cx, s in zip((3, 22, 52), r):
        text((cx, y), s, size=8, ha="left", w="bold" if i == 0 else "normal")

box(86, 1, 210, 24, "4. Module and header connections")
conn = [("+5V", "Teensy VIN; D1 → L2 → ESP32-C3 5V; R18 → U3"),
        ("Teensy pin 35 (TX8)", "R23 1k (stands on end) → ESP32-C3 GPIO20 (RX)"),
        ("Teensy pin 34 (RX8)", "R24 1k (stands on end) ← ESP32-C3 GPIO21 (TX)"),
        ("J1 power", "1 +5V from the holder (before L1), 2 GND, 3 cell + through R25"),
        ("J2 radar", "1 Q, 2 VCC (+3V3A), 3 I, 4 GND"),
        ("J3 screen", "1 GND, 2 VCC (ESP32 3V3), 3 SCL (GPIO7), 4 SDA (GPIO6)"),
        ("J4 sensor kit", "1 GND, 2 3V3, 3 SDA (GPIO6), 4 SCL (GPIO7)  (STEMMA QT: black, red, blue, yellow)"),
        ("J5 ammo jack", "optional: tip → GPIO10 with R21 4.7k to 3V3; ring ← R22 100Ω ← 3V3; sleeve GND"),
        ("Teensy board", "cut the VIN–VUSB pads on the underside")]
for i, (a, b) in enumerate(conn):
    y = 19.6 - i * 2.1
    text((88, y), a, size=8, ha="left", w="bold"); text((114, y), b, size=8, ha="left")

import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
for ext in ("png", "pdf"):
    plt.savefig(os.path.join(OUT, "schematic_v1.2." + ext), bbox_inches="tight")
print("saved")
