"""Draw the chronograph schematic with matplotlib (no schematic library needed)."""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LW = 1.4
INK = "#111"
NET = "#1f4e9e"
fig, ax = plt.subplots(figsize=(19.5, 12.5), dpi=120)
ax.set_xlim(0, 194); ax.set_ylim(0, 125); ax.set_aspect("equal"); ax.axis("off")


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


# ======================= title
text((2, 122), "Range Book BLIPR — schematic v0.5 (one amplifier channel shown in full; Q channel is identical)", size=13, ha="left", w="bold")
text((2, 118.5), "All grounds connect together. Op-amps U1, U2 = MCP6022 (pin 8 = +3V3OP, pin 4 = GND). Gain per stage = 1 + 10k/470 ≈ 22, two stages about 480 at the peak.", size=9.5, ha="left")

# ======================= POWER (top band)
box(1, 72, 192, 115, "1. Power")
box(4, 92, 20, 108)
text((12, 100), "BT1\n18650 shield", size=8.5)
wire((20, 104), (26, 104)); text((21, 105.4), "5V", size=7.5, ha="left")
wire((20, 96), (22, 96), (22, 90)); text((21, 97.4), "GND", size=7.5, ha="left"); gnd((22, 90))
wire((26, 104), (28, 104)); ax.plot([28, 32], [104, 105.8], color=INK, lw=LW); dot((28, 104)); dot((32.5, 104))
wire((32.5, 104), (38, 104)); text((30, 107.8), "SW1A", size=8.5)
dot((38, 104)); wire((38, 104), (38, 110)); netlabel((38, 110), "+5V", side="right")
text((46, 110.5), "→ Teensy VIN;  → D1 (1N5817) → ESP32-C3 5V  (table 4)", size=7.5, ha="left", c="#444")
resistor((38, 104), (50, 104), "R18", "10Ω")
wire((50, 104), (70, 104))
dot((54, 104)); cap((54, 104), (54, 92), "C4", "10µF", pol=True, lab_side=1); gnd((54, 92))
dot((63, 104)); cap((63, 104), (63, 92), "C1", "1µF", lab_side=1); gnd((63, 92))
box(70, 97, 82, 107)
text((76, 104.5), "U3", size=8.5, w="bold"); text((76, 100.5), "MCP1700\n3.3 V", size=7.5)
text((69.5, 105.5), "IN", size=6.5, ha="right", c="#666")
wire((76, 97), (76, 93)); gnd((76, 93)); text((77, 95.5), "GND", size=6.5, ha="left", c="#666")
wire((82, 104), (106, 104)); text((82.5, 105.5), "OUT", size=6.5, ha="left", c="#666")
dot((88, 104)); cap((88, 104), (88, 92), "C2", "1µF", lab_side=1); gnd((88, 92))
dot((97, 104)); cap((97, 104), (97, 92), "C3", "100µF", pol=True, lab_side=1); gnd((97, 92))
dot((106, 104)); wire((106, 104), (106, 110)); netlabel((106, 110), "+3V3A", side="right")
# radar: pins listed in physical order, one wire per pin
RX0, RX1 = 120, 136
box(RX0, 80, RX1, 100)
text((128, 98), "RADAR", size=8.5, w="bold"); text((128, 95.6), "K-LC5-RFB-00C", size=6.8)
pins_y = {1: 92.5, 2: 90.0, 3: 87.5, 4: 85.0, 5: 82.5}
names = {1: "1  Q out", 2: "2  VCC", 3: "3  I out", 4: "4  GND", 5: "5  VCO: open"}
for k, yy in pins_y.items():
    text((128, yy), names[k], size=7)
# pin 2 VCC on the left, with C5
wire((106, 104), (114, 104), (114, 90), (RX0, 90)); dot((114, 90))
cap((114, 90), (114, 82), "C5", "100nF", lab_side=-1); gnd((114, 82))
# right side stubs
wire((RX1, 92.5), (139, 92.5)); netlabel((139, 92.5), "Q-IN", side="right")
wire((RX1, 87.5), (139, 87.5)); netlabel((139, 87.5), "I-IN", side="right")
wire((RX1, 85.0), (152, 85.0), (152, 81)); gnd((152, 81))
text((139, 82.5), "not connected", size=6.8, ha="left", c="#666")
text((60, 77.5), "Radar pin 5 (VCO) is left unconnected (RFbeam allows it open).  I-IN and Q-IN are the amplifier inputs (sections 2 and 3).", size=7.5, c="#444", ha="left")
# battery sense through the second pole of SW1 (DPDT)
wire((12, 92), (12, 90.5)); resistor((12, 90.5), (12, 84), "R25", "10k", lab_side=-1); wire((12, 84), (12, 82), (15, 82))
text((24.5, 90.0), "BATT+ (cell + tab);\nR25 right at the tab", size=6.3, ha="left", c="#666")
dot((15, 82)); ax.plot([15, 19], [82, 83.8], color=INK, lw=LW); dot((19.5, 82))
text((17, 85.8), "SW1B", size=8)
resistor((19.5, 82), (31, 82), "R19", "100k")
dot((31, 82)); resistor((31, 82), (31, 74.5), "R20", "100k", lab_side=-1); gnd((31, 74.5))
dot((38, 82)); cap((38, 82), (38, 74.5), "C26", "100nF", lab_side=1); gnd((38, 74.5))
wire((31, 82), (46, 82)); netlabel((46, 82), "BATT_SENSE → ESP32 GPIO3", side="right")
text((50, 86), "SW1 is DPDT: both halves switch together", size=7, ha="left", c="#444")
# op-amp supply filter + VREF
wire((106, 104), (150, 104))
resistor((150, 104), (159, 104), "R1", "10Ω")
wire((159, 104), (162, 104)); dot((162, 104)); wire((162, 104), (162, 110)); netlabel((162, 110), "+3V3OP", side="right")
cap((162, 104), (162, 95), "C7", "10µF", pol=True, lab_side=-1); gnd((162, 95))
wire((162, 104), (172, 104), (172, 101))
resistor((172, 101), (172, 92), "R2", "10k", lab_side=-1)
dot((172, 92))
resistor((172, 92), (172, 83), "R3", "10k", lab_side=-1); gnd((172, 83))
wire((172, 92), (185, 92)); dot((176, 92)); dot((185, 92))
cap((176, 92), (176, 84), "C10", "10µF", pol=True, lab_side=1); gnd((176, 84))
cap((185, 92), (185, 84), "C11", "100nF", lab_side=1); gnd((185, 84))
wire((185, 92), (185, 96)); netlabel((185, 96), "VREF", side="left")

# ======================= AMPLIFIER channel I
box(1, 24, 192, 70, "2. Amplifier — I channel (I-IN from radar pin 3 → Teensy A0)")
def stage(xin, label_in, cin, rb, rf, cf, rg, cg, name, pins):
    """One non-inverting AC-coupled stage. Returns output node."""
    yp = 58.0                               # + input line height
    cap((xin, yp), (xin + 8, yp), cin[0], cin[1])
    nb = (xin + 8, yp); dot(nb)
    resistor(nb, (nb[0], 46), rb[0], rb[1], lab_side=-1); netlabel((nb[0], 46), "VREF", side="right")
    m, p, o = opamp((nb[0] + 24, yp - 2.2), name, pins)
    wire(nb, p)
    xm = m[0] - 3
    fy = 46.0
    wire(m, (xm, m[1])); dot((xm, m[1]))
    wire((xm, m[1]), (xm, fy))
    resistor((xm, fy), (o[0] + 3, fy), rf[0], rf[1], lab_side=-1)
    wire((o[0] + 3, fy), (o[0] + 3, o[1])); dot((o[0] + 3, fy)); dot((xm, fy))
    if cf:
        wire((xm, fy), (xm, fy - 6)); cap((xm, fy - 6), (o[0] + 3, fy - 6), cf[0], cf[1], lab_side=-1)
        wire((o[0] + 3, fy - 6), (o[0] + 3, fy))
    wire(o, (o[0] + 3, o[1])); dot((o[0] + 3, o[1]))
    # gain leg
    xg = xm - 7
    wire((xm, m[1]), (xg, m[1]), (xg, 50))
    resistor((xg, 50), (xg, 41), rg[0], rg[1], lab_side=1)
    cap((xg, 41), (xg, 33), cg[0], cg[1], lab_side=1); gnd((xg, 33))
    return (o[0] + 3, o[1])

netlabel((14, 58), "I-IN", side="left")
out1 = stage(14, "", ("C12", "10nF"), ("R4", "4.7k"), ("R5", "10k"), None, ("R6", "470Ω"), ("C14", "1µF"), "U1A", (2, 3, 1))
wire(out1, (out1[0] + 6, out1[1]), (out1[0] + 6, 58), (out1[0] + 8, 58))
out2 = stage(out1[0] + 8, "", ("C15", "10nF"), ("R7", "4.7k"), ("R8", "10k"), None, ("R9", "470Ω"), ("C17", "1µF"), "U1B", (6, 5, 7))
x3 = out2[0]
resistor((x3, out2[1]), (x3 + 12, out2[1]), "R10", "330Ω")
dot((x3 + 12, out2[1]))
cap((x3 + 12, out2[1]), (x3 + 12, 42), "C18", "1nF", lab_side=1); gnd((x3 + 12, 42))
wire((x3 + 12, out2[1]), (x3 + 20, out2[1]))
text((x3 + 21, out2[1]), "Teensy A0\n(pin 14)", size=8.5, ha="left", w="bold")
wire((150, 46), (186, 46)); netlabel((150, 46), "+3V3OP", side="left")
dot((160, 46)); cap((160, 46), (160, 37), "C8", "100nF", lab_side=1); gnd((160, 37))
dot((176, 46)); cap((176, 46), (176, 37), "C9", "100nF", lab_side=1); gnd((176, 37))
text((168, 50.5), "Op-amp supply: U1 and U2 pin 8 = +3V3OP, pin 4 = GND.\nC8 across U1 pins 8–4, C9 across U2 pins 8–4.", size=7.5, c="#444")
text((128, 64.5), "Gain ≈ 22 per stage (1 + R5/R6), about 480 total at the peak.\nHigh-pass ≈ 3.4 kHz (C12, R4).  The top end is set by the op-amp\n(10 MHz): about 3 dB down near 245 kHz = 5,000 fps.\nADC filter ≈ 480 kHz (R10, C18).  Each output idles at 1.65 V.", size=8, ha="left", c="#333")

# ======================= Q channel + connections table
box(1, 1, 84, 22, "3. Q channel — same circuit, different parts")
rows = [("Function", "I channel", "Q channel"), ("Input", "RADAR pin 3", "RADAR pin 1"), ("Op-amp", "U1A, U1B", "U2A, U2B"),
        ("Stage 1", "C12 R4 R5 R6 C14", "C19 R11 R12 R13 C21"), ("Stage 2", "C15 R7 R8 R9 C17", "C22 R14 R15 R16 C24"),
        ("Output filter", "R10 C18", "R17 C25"), ("Teensy pin", "A0 (pin 14)", "A1 (pin 15)")]
for i, r in enumerate(rows):
    y = 17.8 - i * 2.4
    for j, (cx, s) in enumerate(zip((3, 22, 52), r)):
        text((cx, y), s, size=8, ha="left", w="bold" if i == 0 else "normal")

box(86, 1, 192, 22, "4. Module connections")
conn = [("+5V", "Teensy VIN; D1 1N5817 (stripe to ESP32) → ESP32 5V; R18 → U3"), ("GND", "Teensy GND, ESP32 GND, OLED GND, all grounds"),
        ("Teensy pin 35 (TX8)", "R23 1k → ESP32-C3 GPIO20 (RX)"), ("Teensy pin 34 (RX8)", "R24 1k ← ESP32-C3 GPIO21 (TX)"),
        ("ESP32 3V3 pin", "OLED VCC"), ("ESP32 GPIO6 / GPIO7", "OLED SDA / SCL"),
        ("ESP32 GPIO3", "BATT_SENSE (cell ÷ 2.1, max 2.0 V)"), ("Teensy board", "cut the VIN–VUSB pads on the underside")]
for i, (a, b) in enumerate(conn):
    y = 17.9 - i * 2.1
    text((88, y), a, size=8, ha="left", w="bold"); text((112, y), b, size=8, ha="left")

plt.savefig(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "out", "schematic_v0.5.png"), bbox_inches="tight")
print("saved")
