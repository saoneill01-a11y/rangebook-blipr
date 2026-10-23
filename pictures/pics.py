import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pcb"))
from parts import *
import design as D

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

def draw_pcb(ax, x0, y0, S, modules=True, labels=True, fade=False):
    X = lambda bx: x0 + bx * S
    Y = lambda by: y0 + by * S
    board(ax, X(0), Y(0), D.BOARD_W * S, D.BOARD_H * S, "#1f6b3c", r=1.0, z=1)
    for hx, hy in D.HOLES:
        ax.add_patch(Circle((X(hx), Y(hy)), D.HOLE_D / 2 * S, fc="white", ec="#888", zorder=1.2))
    pads = {}
    for (ref, nm, x, y, sh, w, h, dr, ro) in D.pads_world():
        pads[ref + "-" + nm] = (X(x), Y(y))
        if ref in ("U4", "U5") and modules:
            continue
        ax.add_patch(Circle((X(x), Y(y)), 0.75 * S, fc="#d9b24a", ec="#7a5c10", lw=0.4, zorder=1.4))
    if labels:
        for ref, p in D.P.items():
            if ref[0] in "RCDU" and ref not in ("U4", "U5"):
                label(ax, X(p["x"]), Y(p["y"]), ref, size=4.6, color="#e8f2e8", z=1.6)
    pins = {}
    if modules:
        pins["T"] = teensy(ax, X(8.27), Y(66.0), s=S, hi=("VIN", "GND", "34", "35", "14", "15"), names=False)
        u4 = D.P["U4"]
        pins["E"] = esp32c3(ax, X(u4["x"] - 9.0), Y(u4["y"] - 19.1), s=S, hi=("5V", "GND", "3V3", "3", "6", "7", "10", "20", "21"), names=False)
    return pads, pins, X, Y

# ------------------------------------------------------------------ 1. overview
def overview():
    fig, ax = canvas(330, 228, "How everything connects",
                     "Every wire that leaves the main board. Teensy and ESP32 plug into sockets on the board (the PCB is drawn; on perfboard the same wires land on the same points).")
    S = 1.35
    x0, y0 = 152, 44
    pads, pins, X, Y = draw_pcb(ax, x0, y0, S)
    label(ax, X(35), Y(93.5), "MAIN BOARD  (top view; front edge, the radar side, at the bottom)", size=8, bold=True, color="#1f6b3c")
    # --- power: battery holder straight to J1 (its own button is the power switch)
    sh = shield(ax, 6, 168, s=0.95)
    label(ax, 53, 202, "18650 BATTERY HOLDER", size=8, bold=True)
    wire(ax, sh["5V2"], pads["J1-1"], "5V", via=[(104, 182), (140, 160), (140, Y(60.46))], text="5V \u2192 J1 +5V", tpos=0.45)
    wire(ax, sh["GND3"], pads["J1-2"], "GND", via=[(106, 186), (146, 172), (146, Y(61))], text="GND \u2192 J1 GND", tpos=0.4)
    wire(ax, sh["BAT+"], pads["J1-3"], "BAT", via=[(88, 150), (134, 150), (134, Y(65.54) - 6)], text="cell + tab \u2192 10k \u2192 J1 BAT", tpos=0.3)
    note(ax, 8, 160, "No separate switch: the holder's own button\n(pressed through the hole in the case side)\nturns BLIPR on and off. Set the holder's\nmode switch to 'power on' (stays on).", size=7.4)
    # --- OLED
    op = oled(ax, 20, 90, s=1.05)
    label(ax, 34, 82, "OLED (sits in the lid)", size=8, bold=True)
    for nm, kind, k in (("GND", "GND", 1), ("VCC", "3V3", 2), ("SCL", "SCL", 3), ("SDA", "SDA", 4)):
        a = op[nm]; b = pads["J3-%d" % k]
        wire(ax, a, b, kind, via=[(a[0], a[1] + 4 + k * 1.2), (70 + k * 2.2, a[1] + 4 + k * 1.2), (100 + k * 2.2, 74 - k * 0.8), (b[0] - 6, b[1] + 10 - k)], lw=2.0)
    note(ax, 52, 112, "OLED pin order differs between makers:\ngo by the labels printed on yours.", size=7.2)
    # --- sensors
    label(ax, 52, 63, "SENSOR KIT (optional): both boards in the pod on the lid", size=7.6, bold=True)
    for i, (nm, col, w) in enumerate((("SHT45\ntemp + humidity", "#2457a5", 26), ("DFRobot 10-DoF\ncompass, level\n+ pressure", "#1a1a1a", 34))):
        x = 8 + i * 36
        board(ax, x, 42, w, 16, col, r=1, z=2)
        label(ax, x + w / 2, 50, nm, size=6.4, color="white", bold=True)
    wire(ax, (34, 50), (44, 50), "#555", lw=2.4)
    label(ax, 47, 38.5, "SHT45's 2nd socket \u2192 the DFRobot's Gravity cable", size=6.4, color="#555")
    wire(ax, (21, 42), pads["J4-1"], "SDA", via=[(21, 34), (110, 34), (140, pads["J4-1"][1])], lw=3.0, text="QT cable \u2192 J4 SENSORS", tpos=0.3)
    # --- ammo jack
    ax.add_patch(Circle((20, 15), 4.6, fc="#222", ec="#000", zorder=3))
    ax.add_patch(Circle((20, 15), 1.7, fc="#777", zorder=3.1))
    label(ax, 20, 6.5, "3.5 mm jack (ammo probe)", size=7, color="#333")
    jt = [(26, 18.5), (26, 15), (26, 11.5)]
    for k, (nm, kind) in enumerate((("tip", "DATA"), ("ring", "3V3"), ("sleeve", "GND"))):
        b = pads["J5-%d" % (k + 1)]
        wire(ax, jt[k], b, kind, via=[(70, jt[k][1]), (120 + k * 3, 22 - k), (b[0], b[1] - 10 + k)], lw=2.0, text=nm, tpos=0.12)
    # --- radar
    rp = radar(ax, X(30) - 12.5, 6, s=1.0, top=True)
    label(ax, X(30) + 16, 18, "RADAR K-LC5\n(front pocket)", size=7.5, bold=True, ha="left")
    for k, kind in ((1, "Q"), (2, "3V3A"), (3, "I"), (4, "GND")):
        wire(ax, rp[k], pads["J2-%d" % k], kind, lw=2.2)
    note(ax, X(46), 38, "Radar pins: 1 Q, 2 VCC, 3 I, 4 GND.\nPin 1 to J2 pin 1 \u2026 pin 4 to pin 4.\nPin 5 (VCO): no wire.\nTwist I with a GND wire, Q with the other.", size=7.2)
    # --- legend + notes
    legend(ax, 262, 160, [("5V", "+5 V"), ("BAT", "battery + (gauge)"), ("GND", "ground"), ("3V3", "3.3 V"), ("I", "radar I"), ("Q", "radar Q / SDA"),
                          ("SCL", "SCL / probe data")], size=7.6)
    note(ax, 258, 120, "Pins with a red ring are the\nones this project uses.\n\nTeensy: USB toward the right\nwall of the case.\nESP32: chip side up, USB\ntoward the back, antenna at\nthe board's front edge.", size=7.4)
    save(fig, OUT + "/01_overview.png")

# ------------------------------------------------------------------ 2. power and battery gauge
def power():
    fig, ax = canvas(250, 150, "Power: battery holder and the battery gauge",
                     "Three wires from the 18650 holder to J1. The holder's own button is the on/off switch; there is no separate switch.")
    sh = shield(ax, 6, 82, s=1.0)
    label(ax, 56, 117, "18650 BATTERY HOLDER (top view)", size=8, bold=True)
    board(ax, 190, 40, 50, 40, "#1f6b3c", r=1.2, z=2)
    label(ax, 215, 84, "MAIN BOARD", size=8, bold=True, color="#1f6b3c")
    J = {}
    for i, nm in enumerate(("BAT", "GND", "+5V")):
        J[nm] = pin(ax, 196, 70 - i * 6, None, hi=True, r=1.0)
        label(ax, 199.5, 70 - i * 6, "J1 %s" % nm, size=7.5, ha="left", color="white", bold=True)
    label(ax, 215, 46, "(perfboard: +5V bus,\nGND bus, R19's free end)", size=6.4, color="#d8ecd8")
    wire(ax, sh["5V2"], J["+5V"], "5V", via=[(112, 92), (150, 76)], text="holder 5V \u2192 J1 +5V", tpos=0.55)
    wire(ax, sh["GND3"], J["GND"], "GND", via=[(140, 104), (180, 98), (180, 64)], text="holder GND \u2192 J1 GND", tpos=0.45)
    a = sh["BAT+"]
    rx = a[0] - 5
    wire(ax, a, (rx, 78), "BAT", via=[(rx, a[1])], lw=2.6, straight=True)
    resistor(ax, (rx, 78), (rx, 60), 10000, "R25", val="10k, its leg soldered\non the tab itself", s=1.4)
    wire(ax, (rx, 60), J["BAT"], "BAT", via=[(rx, 52), (170, 52), (170, 70)], text="\u2192 J1 BAT", tpos=0.55)
    note(ax, 6, 70, "The cell's + tab: solder a 10k resistor (R25)\nstraight onto the metal tab at the + end of the\nholder, with the cell OUT, and cover it with\nheat-shrink. The wire to J1 starts at its other\nend, so a nicked wire can't short the cell.\n\nThe gauge wire is always connected; it draws\nabout 18 \u00b5A, a few months to empty a cell.\nTake the cell out for long storage.", size=7.3)
    note(ax, 6, 22, "Check with a meter before connecting anything:\npress the holder's button on, about 5 V at J1 +5V;\npress it off, 0 V. BAT reads the cell (3.0 to 4.2 V).", size=7.4)
    save(fig, OUT + "/02_power.png")

# ------------------------------------------------------------------ 3. radar
def radar_pic():
    fig, ax = canvas(220, 132, "Radar: the 4-wire connection",
                     "The K-LC5 seen from the back (its antenna side faces downrange, through the front cover). Pin 1 is marked on the module.")
    rp = radar(ax, 62, 34, s=2.1, top=True)
    names = {1: ("Q out", "Q"), 2: ("VCC 3.3 V", "3V3A"), 3: ("I out", "I"), 4: ("GND", "GND"), 5: ("VCO: no wire", "VCO")}
    for k in range(1, 6):
        label(ax, 6, 60 - (k - 1) * 6.5, "pin %d  %s" % (k, names[k][0]), size=8, ha="left", bold=True, color=WIRE[names[k][1]] if names[k][1] not in ("GND", "VCO") else ("#222" if k == 4 else "#888"))
    board(ax, 150, 8, 64, 66, "#1f6b3c", r=1.2, z=2)
    label(ax, 182, 78, "MAIN BOARD", size=8, bold=True, color="#1f6b3c")
    J = {}
    for k, nm in enumerate(("Q", "VCC", "I", "GND")):
        J[k + 1] = pin(ax, 189 + k * 5.6, 24, None, hi=True, r=1.0)
        label(ax, 189 + k * 5.6, 19.5, nm, size=6.3, color="white", bold=True)
    label(ax, 197, 12.5, "J2 RADAR (PCB)", size=7.6, color="white", bold=True)
    ax.text(153, 66, "perfboard:\nQ \u2192 Q-IN (C19)\nVCC \u2192 +3V3A bus\nI \u2192 I-IN (C12)\nGND \u2192 GND by\n   the amplifier", fontsize=7.0, color="#e8f4e8", va="top", ha="left", zorder=20)
    for k in range(1, 5):
        a, b = rp[k], J[k]
        yy = 86 + k * 3.0
        wire(ax, a, b, names[k][1], via=[(a[0], yy), (176 + k * 1.5, yy), (b[0], 60 - k * 1.2)], lw=2.6)
    note(ax, 6, 25, "Pin 5 (VCO) gets no wire at all: RFbeam's datasheet allows it\nto be left open, and a long wire on it would pick up noise.\nPCB: C5 (VCC to GND) sits next to J2. Join both GND wires\nat the GND pin. Perfboard: solder C5 across radar pins 2\nand 4, right at the radar's header.\nWires 8 to 10 cm; twist I with one GND, Q with the other.", size=7.3)
    save(fig, OUT + "/03_radar.png")

# ------------------------------------------------------------------ 4. Teensy
def teensy_pic():
    fig, ax = canvas(240, 128, "Teensy 4.1: the 7 pins it uses",
                     "Top view, USB to the right (toward the right wall). Red rings = used. Board v1.1 / firmware 0.2.2: pins 0 and 1 are not used.")
    S = 2.6
    x0 = 50
    tp = teensy(ax, x0, 40, s=S, hi=("VIN", "GND", "34", "35", "14", "15"), names=True, fs=7.2)
    rear = [("rear:0", "GND \u2192 ground", "GND")]
    for k, (key, txt, kind) in enumerate(rear):
        a = tp[key]; yy = 91 + k * 5.2
        wire(ax, a, (a[0] - 30 - k * 4, yy), kind, via=[(a[0], yy - 2)], lw=2.4)
        label(ax, a[0] - 31 - k * 4, yy, txt, size=7.8, ha="right", bold=True)
    front = [("front:0", "VIN \u2190 +5 V", "5V"), ("front:1", "GND \u2192 ground", "GND"), ("front:11", "pin 15 (A1) \u2190 Q amplifier (R17, C25)", "Q"), ("front:12", "pin 14 (A0) \u2190 I amplifier (R10, C18)", "I")]
    for k, (key, txt, kind) in enumerate(front):
        a = tp[key]; yy = 26 - k * 5.0
        wire(ax, a, (a[0] - 14 - (0 if k < 2 else 8), yy), kind, via=[(a[0], yy + 2)], lw=2.4)
        label(ax, a[0] - 15 - (0 if k < 2 else 8), yy, txt, size=7.8, ha="right", bold=True)
    ser = [("front:21", "pin 35 (TX8) \u2192 R23 1k \u2192 ESP32 GPIO20 (RX)", "TX"), ("front:22", "pin 34 (RX8) \u2190 R24 1k \u2190 ESP32 GPIO21 (TX)", "RX")]
    for k, (key, txt, kind) in enumerate(ser):
        a = tp[key]; yy = 26 - k * 5.0
        wire(ax, a, (a[0] + 8 + k * 4, yy), kind, via=[(a[0], yy + 2)], lw=2.4)
        label(ax, a[0] + 9 + k * 4, yy, txt, size=7.8, ha="left", bold=True)
    note(ax, 6, 70, "Before first use, on the underside:\ncut the thin trace between the two\npads marked VIN and VUSB (sharp\nknife, 3 or 4 strokes; check with a\nmeter that they no longer connect).\nThen the computer's USB and the\nbattery can't feed each other.", size=7.2)
    save(fig, OUT + "/04_teensy.png")

# ------------------------------------------------------------------ 5. ESP32-C3
def esp_pic():
    fig, ax = canvas(230, 130, "ESP32-C3 SuperMini: the 9 pins it uses",
                     "Chip side up (USB socket and buttons on top), the way it sits on the board, USB-C at the top.")
    S = 3.2
    ep = esp32c3(ax, 92, 22, s=S, hi=("5V", "GND", "3V3", "3", "6", "7", "10", "20", "21"), names=True, fs=8.5)
    right = [("5V", "5V \u2190 +5 V through D1\n(stripe toward the ESP32)", "5V"), ("GND", "GND \u2192 ground", "GND"), ("3V3", "3V3 \u2192 OLED VCC, sensors, probe", "3V3"),
             ("3", "GPIO3 \u2190 battery gauge\n(R19, R20, C26)", "SENSE")]
    left = [("6", "GPIO6 \u2194 SDA (OLED, sensors)", "SDA"), ("7", "GPIO7 \u2192 SCL (OLED, sensors)", "SCL"), ("10", "GPIO10 \u2194 ammo probe data\n(R21 4.7k to 3V3)", "DATA"),
            ("20", "GPIO20 (RX) \u2190 R23 \u2190 Teensy pin 35", "TX"), ("21", "GPIO21 (TX) \u2192 R24 \u2192 Teensy pin 34", "RX")]
    for nm, txt, kind in left:
        a = ep[nm]; b = (72, a[1])
        wire(ax, a, b, kind, lw=2.4); label(ax, 71, a[1], txt, size=7.6, ha="right", bold=True)
    for nm, txt, kind in right:
        a = ep[nm]; b = (165, a[1])
        wire(ax, a, b, kind, lw=2.4); label(ax, 166, a[1], txt, size=7.6, ha="left", bold=True)
    note(ax, 6, 18, "The pin names are printed on the UNDERSIDE, so from this side they read the other way round: here 5V is the\nright-hand pin nearest the USB. On the board it goes at the front-left corner, chip side up, USB toward the back.\nBefore powering up, beep the module's 5V pin to D1's square pad. Leave GPIO8 and GPIO9 free (LED, BOOT button).", size=7.0)
    save(fig, OUT + "/05_esp32.png")

# ------------------------------------------------------------------ 6. amplifier, I channel, picture-style
def amp_pic(ch="I"):
    if ch == "I":
        R = dict(Cin="C12", Rb="R4", Rf1="R5", Rg1="R6", Cg1="C14", Cc="C15", Rb2="R7", Rf2="R8", Rg2="R9", Cg2="C17", Ro="R10", Co="C18", U="U1", C8="C8")
        src, dst, kind = "I from radar pin 3", "to Teensy pin 14 (A0)", "I"
    else:
        R = dict(Cin="C19", Rb="R11", Rf1="R12", Rg1="R13", Cg1="C21", Cc="C22", Rb2="R14", Rf2="R15", Rg2="R16", Cg2="C24", Ro="R17", Co="C25", U="U2", C8="C9")
        src, dst, kind = "Q from radar pin 1", "to Teensy pin 15 (A1)", "Q"
    fig, ax = canvas(282, 150, "Amplifier, %s channel: where every part goes" % ch,
                     "Parts drawn as they look (colour bands, capacitor codes). A black dot joins wires; lines that cross without a dot don't touch. VREF is the 1.65 V point from the power picture.")
    S = 2.6
    up = dip8(ax, 130, 78, s=S, name="%s  MCP6022" % R["U"])
    P = up
    # buses
    GY, TOP = 14, 124
    ax.plot([20, 258], [GY, GY], color=WIRE["GND"], lw=4, solid_capstyle="round", zorder=5); label(ax, 19, GY, "GND", size=8, ha="right", bold=True)
    ax.plot([100, 258], [TOP, TOP], color=WIRE["3V3OP"], lw=4, solid_capstyle="round", zorder=5); label(ax, 99, TOP, "+3V3OP", size=8, ha="right", bold=True, color="#b07800")
    def vref(x, y):
        wire(ax, (x, y), (x, y - 5), "VREF", lw=2.2, straight=True)
        label(ax, x, y - 7.5, "VREF", size=6.8, box=True, ec=WIRE["VREF"], bold=True, color="#0e7c88")
    dot = lambda x, y: ax.add_patch(Circle((x, y), 1.1, fc="#333", zorder=12))
    # power pins
    wire(ax, P[8], (P[8][0] + 6, TOP), "3V3OP", via=[(P[8][0] + 6, P[8][1])], lw=2.4, straight=True)
    wire(ax, P[4], (P[4][0] - 8, GY), "GND", via=[(P[4][0] - 8, P[4][1])], lw=2.4, straight=True)
    ceramic(ax, (258, TOP), (258, GY), "104", R["C8"], "100nF")
    label(ax, 270, 40, "close to\nthe socket's\npin 8", size=6.2, color="#555")
    # stage 1 (left)
    label(ax, 6, P[3][1] + 10, src, size=7.8, ha="left", bold=True, color=WIRE[kind])
    wire(ax, (8, P[3][1]), (24, P[3][1]), kind, lw=2.6, straight=True)
    ceramic(ax, (24, P[3][1]), (40, P[3][1]), "103", R["Cin"], "10nF")
    n1 = (48, P[3][1]); dot(*n1)
    wire(ax, (40, P[3][1]), n1, kind, lw=2.2, straight=True); wire(ax, n1, P[3], kind, lw=2.2, straight=True)
    resistor(ax, n1, (48, 40), 4700, R["Rb"]); vref(48, 40)
    n2 = (72, P[2][1]); dot(*n2)
    wire(ax, P[2], n2, "#555", lw=2.2, straight=True)
    fb_l, fb_r = (72, 104), (100, 104)
    wire(ax, n2, fb_l, "#555", lw=2.0, straight=True)
    resistor(ax, fb_l, fb_r, 10000, R["Rf1"])
    out1 = (106, 104); dot(*out1)
    wire(ax, fb_r, out1, "#555", lw=2.0, straight=True); wire(ax, out1, P[1], "#555", via=[(106, P[1][1])], lw=2.0, straight=True)
    resistor(ax, (72, P[2][1] - 4), (72, 50), 470, R["Rg1"]); wire(ax, n2, (72, P[2][1] - 4), "#555", lw=2.0, straight=True)
    ceramic(ax, (72, 46), (72, GY), "105", R["Cg1"], "1uF"); wire(ax, (72, 50), (72, 46), "#555", lw=2.0, straight=True)
    label(ax, 90, 58, "stage 1:\ngain about 22", size=7.0, color="#555")
    # stage 2 (right)
    wire(ax, out1, (212, 118), "#555", via=[(106, 118)], lw=2.0, straight=True)
    ceramic(ax, (212, 118), (212, 100), "103", R["Cc"], "10nF")
    n3 = (212, P[5][1]); dot(*n3)
    wire(ax, (212, 100), n3, "#555", lw=2.0, straight=True); wire(ax, n3, P[5], "#555", lw=2.0, straight=True)
    n3b = (198, P[5][1]); dot(*n3b)
    resistor(ax, n3b, (198, 40), 4700, R["Rb2"]); vref(198, 40)
    n4 = (160, P[6][1]); dot(*n4)
    wire(ax, P[6], n4, "#555", lw=2.0, straight=True)
    f2l, f2r = (160, 98), (186, 98)
    wire(ax, n4, f2l, "#555", lw=2.0, straight=True)
    resistor(ax, f2l, f2r, 10000, R["Rf2"])
    n5 = (186, P[7][1]); dot(*n5)
    wire(ax, f2r, n5, "#555", lw=2.0, straight=True); wire(ax, n5, P[7], "#555", lw=2.0, straight=True)
    resistor(ax, (172, P[6][1] - 3), (172, 50), 470, R["Rg2"]); wire(ax, n4, (172, P[6][1] - 3), "#555", via=[(166, P[6][1] - 1)], lw=2.0, straight=True)
    ceramic(ax, (172, 46), (172, GY), "105", R["Cg2"], "1uF"); wire(ax, (172, 50), (172, 46), "#555", lw=2.0, straight=True)
    label(ax, 228, 60, "stage 2:\ngain about 22", size=7.0, color="#555")
    # output filter
    wire(ax, n5, (222, P[7][1]), "#555", lw=2.0, straight=True)
    resistor(ax, (222, P[7][1]), (238, P[7][1]), 330, R["Ro"])
    n6 = (244, P[7][1]); dot(*n6)
    wire(ax, (238, P[7][1]), n6, kind, lw=2.2, straight=True)
    ceramic(ax, (244, P[7][1] - 4), (244, GY), "102", R["Co"], "1nF"); wire(ax, n6, (244, P[7][1] - 4), kind, lw=2.0, straight=True)
    wire(ax, n6, (252, P[7][1] + 14), kind, via=[(244, P[7][1] + 14)], lw=2.6, straight=True)
    label(ax, 254, P[7][1] + 18, dst, size=7.6, ha="right", bold=True, color=WIRE[kind])
    other = "Q channel: same layout with C19, R11, R12, R13, C21, C22, R14, R15, R16, C24, R17, C25 on U2." if ch == "I" else "I channel: same layout with C12, R4, R5, R6, C14, C15, R7, R8, R9, C17, R10, C18 on U1."
    label(ax, 6, 6, other, size=7.4, ha="left", color="#444")
    save(fig, OUT + "/06_amplifier_%s.png" % ch)

# ------------------------------------------------------------------ 7. op-amp pin map
def opamp_pins():
    fig, ax = canvas(270, 112, "Op-amp sockets: what lands on each pin",
                     "Both MCP6022s seen from above, notch at the top. U1 is the I channel, U2 the Q channel.")
    rows = {1: ("OUT A", "R5, C15", "R12, C22"), 2: ("\u2212IN A", "R5, R6", "R12, R13"),
            3: ("+IN A", "C12, R4", "C19, R11"), 4: ("GND", "GND, C8", "GND, C9"),
            5: ("+IN B", "C15, R7", "C22, R14"), 6: ("\u2212IN B", "R8, R9", "R15, R16"),
            7: ("OUT B", "R8, R10", "R15, R17"), 8: ("+3V3OP", "+3V3OP, C8", "+3V3OP, C9")}
    for col, (cx, nm, idx) in enumerate(((70, "U1  (I channel)", 1), (200, "U2  (Q channel)", 2))):
        pins = dip8(ax, cx, 58, s=3.0, name="MCP6022")
        label(ax, cx, 84, nm, size=9.5, bold=True)
        for k in range(1, 9):
            x, y = pins[k]
            if k <= 4:
                ax.text(x - 2, y, "%s  %d" % (rows[k][idx], k), fontsize=7.6, ha="right", va="center", color="#222", zorder=10)
                ax.text(x - 2, y - 3.0, rows[k][0], fontsize=6.0, ha="right", va="center", color="#777", zorder=10)
            else:
                ax.text(x + 2, y, "%d  %s" % (k, rows[k][idx]), fontsize=7.6, ha="left", va="center", color="#222", zorder=10)
                ax.text(x + 2, y - 3.0, rows[k][0], fontsize=6.0, ha="left", va="center", color="#777", zorder=10)
    note(ax, 6, 26, "Solder the 8-pin SOCKETS to the board, not the chips. Line the socket's notch up with the notch drawn on the board,\nthen press the chips in last, after the power test, with their notch (or dot) at the same end.", size=7.4)
    save(fig, OUT + "/07_opamp_pins.png")

# ------------------------------------------------------------------ 8. power + reference
def power_ref():
    fig, ax = canvas(272, 150, "Power and reference parts",
                     "From +5 V to the radar's quiet 3.3 V, the op-amps' supply, and the 1.65 V VREF the amplifier sits on. Lines that cross without a dot don't touch.")
    GY = 14
    ax.plot([8, 262], [GY, GY], color=WIRE["GND"], lw=4, solid_capstyle="round", zorder=5); label(ax, 7, GY, "GND", size=8, ha="right", bold=True)
    dot = lambda x, y: ax.add_patch(Circle((x, y), 1.1, fc="#333", zorder=12))
    W = lambda a, b, k, via=None, lw=2.3: wire(ax, a, b, k, via=via, lw=lw, straight=True)
    Y = 84
    label(ax, 6, Y - 7, "+5 V (from J1,\nthe holder's 5 V)", size=7.8, ha="left", bold=True, color=WIRE["5V"])
    W((8, Y), (16, Y), "5V", lw=2.8); dot(16, Y)
    W((16, Y), (40, 122), "5V", via=[(16, 122)], lw=2.8); label(ax, 42, 122, "\u2192 Teensy VIN", size=7.6, ha="left", bold=True)
    dot(16, 114); W((16, 114), (30, 114), "5V")
    diode(ax, (30, 114), (48, 114))
    W((48, 114), (60, 114), "5V"); label(ax, 62, 114, "\u2192 ESP32 5V pin", size=7.6, ha="left", bold=True)
    resistor(ax, (16, Y), (36, Y), 10, "R18", val="10\u03a9")
    nA = (42, Y); dot(*nA); W((36, Y), nA, "5V")
    W(nA, (50, Y), "5V"); electrolytic(ax, (50, Y), (50, GY), "C4", "10\u00b5F")
    W((50, Y), (68, Y), "5V"); ceramic(ax, (68, Y), (68, GY), "105", "C1", "1\u00b5F")
    u3 = to92(ax, 96, 96, s=1.6)
    label(ax, 86, 96, "U3", size=8.5, bold=True, ha="right")
    W((68, Y), u3["IN"], "5V", via=[(80, Y), (80, 76), (96, 76)])
    W(u3["GND"], (u3["GND"][0], GY), "GND")
    nB = (112, 70); dot(*nB)
    W(u3["OUT"], nB, "3V3A", via=[(u3["OUT"][0], 70)], lw=2.5)
    ceramic(ax, nB, (112, GY), "105", "C2", "1\u00b5F")
    W(nB, (128, 70), "3V3A", lw=2.5); electrolytic(ax, (128, 70), (128, GY), "C3", "100\u00b5F")
    dot(140, 70); W((128, 70), (140, 70), "3V3A", lw=2.5)
    W((140, 70), (146, 108), "3V3A", via=[(140, 108)], lw=2.5)
    label(ax, 148, 108, "+3V3A \u2192 radar VCC (J2 pin 2), with C5 100nF to GND at J2", size=7.4, ha="left", bold=True, color="#c06000")
    resistor(ax, (140, 70), (158, 70), 10, "R1", val="10\u03a9")
    nC = (164, 70); dot(*nC); W((158, 70), nC, "3V3OP", lw=2.5)
    W(nC, (170, 70), "3V3OP", lw=2.5); electrolytic(ax, (170, 70), (170, GY), "C7", "10\u00b5F")
    dot(178, 70); W((170, 70), (178, 70), "3V3OP", lw=2.5)
    W((178, 70), (184, 94), "3V3OP", via=[(178, 94)], lw=2.5)
    label(ax, 186, 94, "+3V3OP \u2192 U1 pin 8, U2 pin 8\n(C8, C9 100nF at the sockets)", size=7.4, ha="left", bold=True, color="#b07800")
    W((178, 70), (196, 70), "3V3OP", lw=2.5)
    resistor(ax, (196, 70), (196, 52), 10000, "R2", val="10k")
    nD = (196, 46); dot(*nD); W((196, 52), nD, "VREF", lw=2.5)
    resistor(ax, (196, 40), (196, 18), 10000, "R3", val="10k"); W(nD, (196, 40), "VREF"); W((196, 18), (196, GY), "GND")
    W(nD, (216, 46), "VREF", lw=2.5); electrolytic(ax, (216, 46), (216, GY), "C10", "10\u00b5F")
    W((216, 46), (236, 46), "VREF", lw=2.5); ceramic(ax, (236, 46), (236, GY), "104", "C11", "100nF")
    W((236, 46), (250, 46), "VREF", lw=2.5)
    label(ax, 244, 58, "VREF (1.65 V)\n\u2192 R4, R7, R11, R14", size=7.4, bold=True, color="#0e7c88")
    save(fig, OUT + "/08_power_reference.png")

# ------------------------------------------------------------------ 9. ESP32-side small parts, sensors and ammo jack
def esp_side():
    fig, ax = canvas(250, 150, "Battery gauge, sensor kit and ammo-probe jack",
                     "The small parts around the ESP32-C3, and how the optional sensors plug in. The three-line symbol means: to GND.")
    dot = lambda x, y: ax.add_patch(Circle((x, y), 1.1, fc="#333", zorder=12))
    W = lambda a, b, k, via=None, lw=2.3: wire(ax, a, b, k, via=via, lw=lw, straight=True)
    # battery gauge
    label(ax, 8, 122, "Battery gauge", size=8.5, bold=True, ha="left")
    label(ax, 8, 113, "BAT (J1 pin 3, from the cell's\n+ tab through R25 10k)", size=6.6, ha="left", color=WIRE["BAT"], bold=True)
    W((10, 104), (20, 104), "BAT", lw=2.5)
    resistor(ax, (20, 104), (40, 104), 100000, "R19", val="100k")
    nS = (46, 104); dot(*nS); W((40, 104), nS, "SENSE")
    resistor(ax, (46, 100), (46, 84), 100000, "R20", val="100k"); W(nS, (46, 100), "SENSE"); gnd(ax, 46, 84)
    W(nS, (64, 104), "SENSE"); ceramic(ax, (64, 104), (64, 84), "104", "C26", "100nF"); gnd(ax, 64, 84)
    W((64, 104), (84, 104), "SENSE", lw=2.5); label(ax, 86, 104, "\u2192 ESP32 GPIO3", size=7.6, ha="left", bold=True)
    label(ax, 86, 96, "with R25: cell \u00f7 2.1,\n4.2 V \u2192 2.0 V", size=6.6, ha="left", color="#555")
    # ammo probe parts
    label(ax, 8, 70, "Ammo probe parts", size=8.5, bold=True, ha="left")
    label(ax, 8, 62, "3V3 (ESP32)", size=7.2, ha="left", color="#c06000", bold=True)
    W((10, 58), (24, 58), "3V3", lw=2.5); dot(24, 58)
    resistor(ax, (24, 58), (24, 38), 4700, "R21", val="4.7k")
    nO = (24, 34); dot(*nO); W((24, 38), nO, "DATA")
    W(nO, (10, 34), "DATA", lw=2.5); label(ax, 9, 28, "ESP32 GPIO10", size=6.8, ha="left", bold=True)
    W(nO, (88, 34), "DATA", lw=2.5); label(ax, 90, 34, "J5 TIP", size=7.4, ha="left", bold=True)
    W((24, 58), (44, 58), "3V3")
    resistor(ax, (44, 58), (64, 58), 100, "R22", val="100\u03a9")
    W((64, 58), (88, 58), "3V3", lw=2.5); label(ax, 90, 58, "J5 RING", size=7.4, ha="left", bold=True)
    W((88, 46), (80, 46), "GND", lw=2.5); gnd(ax, 80, 46); label(ax, 90, 46, "J5 SLEEVE", size=7.4, ha="left", bold=True)
    # TRS plug drawing
    px, py = 168, 46
    ax.add_patch(Rectangle((px, py - 3), 22, 6, fc="#bbb", ec="#777", zorder=3))
    ax.add_patch(Rectangle((px + 22, py - 2.2), 6, 4.4, fc="#ccc", ec="#777", zorder=3))
    ax.add_patch(Rectangle((px + 28.4, py - 2.2), 1.2, 4.4, fc="#222", zorder=3))
    ax.add_patch(Rectangle((px + 29.6, py - 2.2), 5, 4.4, fc="#ccc", ec="#777", zorder=3))
    ax.add_patch(Rectangle((px + 34.6, py - 2.2), 1.2, 4.4, fc="#222", zorder=3))
    ax.add_patch(Polygon([(px + 35.8, py - 2.2), (px + 40, py - 2.2), (px + 42, py), (px + 40, py + 2.2), (px + 35.8, py + 2.2)], fc="#ccc", ec="#777", zorder=3))
    label(ax, px + 25, py - 7, "SLEEVE", size=6.6, color="#333"); label(ax, px + 32, py + 6.5, "RING", size=6.6, color="#333"); label(ax, px + 39.5, py - 7, "TIP", size=6.6, color="#333")
    label(ax, px + 11, py + 7.5, "3.5 mm stereo plug", size=7, bold=True)
    ax.plot([px - 10, px], [py, py], color="#111", lw=5, solid_capstyle="round", zorder=2)
    ax.add_patch(Rectangle((px - 26, py - 2.5), 16, 5, fc="#aaa", ec="#666", zorder=3))
    label(ax, px - 18, py - 7, "DS18B20 probe", size=7, bold=True)
    note(ax, 132, 30, "In the plug: yellow (or white) data \u2192 TIP, red \u2192 RING,\nblack (or blue) \u2192 SLEEVE. The panel jack gets the same\nthree from J5. Plug and unplug with the power off.", size=7.0)
    # sensor chain
    label(ax, 130, 124, "Sensor kit: one chain of STEMMA QT cables", size=8.5, bold=True, ha="left")
    board(ax, 130, 95, 18, 12, "#1f6b3c", r=1, z=2); label(ax, 139, 101, "J4\nSENSORS", size=6.2, color="white", bold=True)
    for i, (nm, col, w) in enumerate((("SHT45", "#2457a5", 22), ("DFRobot\n10-DoF", "#1a1a1a", 28))):
        x = 158 + i * 34
        board(ax, x, 94, w, 14, col, r=1, z=2)
        label(ax, x + w / 2, 101, nm, size=7.0, color="white", bold=True)
    for k, kind in enumerate(("GND", "3V3", "SDA", "SCL")):
        wire(ax, (148, 98 + k * 1.7), (158, 98 + k * 1.7), kind, lw=1.6, straight=True)
    for k, kind in enumerate(("GND", "3V3", "SDA", "SCL")):
        wire(ax, (180, 98 + k * 1.7), (192, 98 + k * 1.7), kind, lw=1.4, straight=True)
    label(ax, 153, 90.5, "150 mm, up\nthrough the lid", size=6.2, color="#555"); label(ax, 186, 90.5, "QT to its\nGravity cable", size=6.0, color="#555")
    label(ax, 190, 76.5, "DFRobot pins: + red, \u2212 black,\nC/R yellow (SCL), D/T blue (SDA)", size=6.2, ha="left", color="#333", va="top")
    label(ax, 139, 86, "J4 order: GND, 3V3, SDA, SCL = cable colours black, red, blue, yellow\n(3V3 is drawn orange here, like everywhere in these pictures)", size=6.6, ha="left", color="#333", va="top")
    label(ax, 199, 112, "both in the vented pod on the lid (the DFRobot board at the gun-side end)", size=6.2, color="#555")
    save(fig, OUT + "/09_gauge_sensors_jack.png")

# ------------------------------------------------------------------ 10. telling the parts apart
def part_id():
    fig, ax = canvas(250, 160, "Telling the parts apart",
                     "Resistor colour bands (4-band kits are beige; 1% kits are usually blue with 5 bands), capacitor codes, and which way round the polarised parts go.")
    vals = [(10, "10 \u03a9", "R1, R18"), (100, "100 \u03a9", "R22"), (330, "330 \u03a9", "R10, R17"), (470, "470 \u03a9", "R6, R9, R13, R16"),
            (1000, "1 k\u03a9", "R23, R24"), (4700, "4.7 k\u03a9", "R4, R7, R11, R14, R21"), (10000, "10 k\u03a9", "R2, R3, R5, R8, R12, R15, R25"), (100000, "100 k\u03a9", "R19, R20")]
    label(ax, 10, 128, "Resistors", size=9, bold=True, ha="left")
    label(ax, 52, 128, "4-band", size=7.4, color="#555"); label(ax, 86, 128, "5-band (1%)", size=7.4, color="#555")
    for i, (o, txt, refs) in enumerate(vals):
        y = 121 - i * 9
        label(ax, 10, y, txt, size=8, ha="left", bold=True)
        resistor(ax, (38, y), (66, y), o, s=1.6)
        resistor(ax, (72, y), (100, y), o, s=1.6, five=True)
        label(ax, 104, y, refs, size=6.8, ha="left", color="#555")
    caps = [("102", "1 nF", "C18, C25"), ("103", "10 nF", "C12, C15, C19, C22"),
            ("104", "100 nF", "C5, C8, C9, C11, C26"), ("105", "1 \u00b5F", "C1, C2, C14, C17, C21, C24")]
    label(ax, 160, 128, "Ceramic capacitors (no polarity)", size=9, bold=True, ha="left")
    for i, (code, txt, refs) in enumerate(caps):
        y = 120 - i * 10
        ax.add_patch(Ellipse((166, y), 7, 6, fc="#e3a33a", ec="#9a6a17", lw=0.6, zorder=4))
        label(ax, 166, y, code, size=7, bold=True, color="#3a2400")
        label(ax, 172, y, "%s  (%s)" % (txt, refs), size=7.2, ha="left")
    label(ax, 160, 70, "Board v1.1 uses no 22 pF capacitors.\nThe 1 \u00b5F ones can be bigger blue or\nyellow blobs marked 105.", size=6.8, ha="left", color="#555")
    # polarised parts
    y0 = 36
    label(ax, 10, 48, "Polarised: these go in one way only", size=9, bold=True, ha="left")
    # electrolytic
    ax.add_patch(Rectangle((18, y0 - 6), 9, 13, fc="#2a3f8f", ec="#111", zorder=3))
    ax.add_patch(Rectangle((24, y0 - 6), 3, 13, fc="#d9d9d9", zorder=3.1))
    label(ax, 25.5, y0, "\u2212", size=9, bold=True, color="#333")
    ax.plot([20.5, 20.5], [y0 - 6, y0 - 17], color="#999", lw=1.6); ax.plot([24.5, 24.5], [y0 - 6, y0 - 13], color="#999", lw=1.6)
    label(ax, 20.5, y0 - 20, "+ long", size=6.6); label(ax, 27, y0 - 15, "\u2212 short", size=6.6)
    label(ax, 32, y0 + 2, "Electrolytic (C3, C4, C7, C10):\nstripe = \u2212 leg; long leg = +;\non the PCB, + is the square pad", size=6.8, ha="left")
    # diode
    ax.plot([84, 108], [y0, y0], color="#999", lw=1.6)
    ax.add_patch(Rectangle((90, y0 - 2), 12, 4, fc="#151515", zorder=3)); ax.add_patch(Rectangle((99.5, y0 - 2), 1.5, 4, fc="#ddd", zorder=3.1))
    label(ax, 96, y0 - 6, "1N5817 (D1): stripe end = cathode,\ntoward the ESP32", size=6.8)
    # TO-92
    ax.add_patch(Wedge((134, y0 - 1), 5, 0, 180, fc="#1a1a1a", zorder=3)); ax.add_patch(Rectangle((129, y0 - 3), 10, 2, fc="#1a1a1a", zorder=3))
    label(ax, 134, y0 + 2.4, "MCP1700", size=5.5, color="#bbb")
    for k in range(3):
        ax.plot([131.5 + k * 2.5] * 2, [y0 - 3, y0 - 10], color="#999", lw=1.6)
    label(ax, 134, y0 - 13, "flat face toward the\nboard's front edge", size=6.6)
    label(ax, 134, y0 + 7.5, "U3 (TO-92)", size=7, bold=True)
    # DIP
    ax.add_patch(FancyBboxPatch((158, y0 - 7), 10, 14, boxstyle="round,pad=0,rounding_size=0.6", fc="#1a1a1a", zorder=3))
    ax.add_patch(Wedge((163, y0 + 7), 1.6, 180, 360, fc="white", zorder=3.1))
    ax.add_patch(Circle((160.2, y0 + 4.5), 0.7, fc="#777", zorder=3.2))
    label(ax, 172, y0 + 2, "Op-amps (U1, U2): notch or dot\nmarks pin 1; match the notch\ndrawn on the board", size=6.8, ha="left")
    save(fig, OUT + "/10_part_id.png")

if __name__ == "__main__":
    for f in (overview, power, radar_pic, teensy_pic, esp_pic, lambda: amp_pic("I"), lambda: amp_pic("Q"), opamp_pins, power_ref, esp_side, part_id):
        f()
    print("ok")
