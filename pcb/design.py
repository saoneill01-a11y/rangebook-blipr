"""Range Book BLIPR main board v1.2 (v1.1 plus the two 5 V filters; v1.1 is frozen in v1.1/): footprints, placement and netlist (through-hole, 70 x 90 mm, 2 layers).

Coordinates in mm, board origin at the FRONT-LEFT corner (front = the radar side), x to the right, y toward the back.
The board drops into the printed base in place of the 70 x 90 perfboard: same size, same four M3 holes 3 mm in.
"""
import math

BOARD_W, BOARD_H = 70.0, 90.0
HOLES = [(3.0, 3.0), (67.0, 3.0), (3.0, 87.0), (67.0, 87.0)]
HOLE_D = 3.2
ANTENNA_KEEPOUT = (7.5, 0.0, 26.5, 7.5)   # (x0, y0, x1, y1): the ESP32-C3 antenna end, kept free of pour; no traces between its pin rows
HOLE_KEEPOUT = 3.6          # radius kept free of copper/parts around each hole (screw head on top, 7 mm post below)

# ------------------------------------------------------------------ footprints
# pad: (name, dx, dy, shape, w, h, drill)   shape: "circle" | "rect" | "oval"
def axial(pitch, drill=0.8, pad=1.6, body=(6.3, 2.5), band=False):
    p = pitch / 2
    # diodes: pad 2 (cathode, the stripe end) is the square one
    return {"pads": [("1", -p, 0, "circle", pad, pad, drill), ("2", p, 0, "rect" if band else "circle", pad, pad, drill)],
            "body": ("rect", body[0], body[1]), "band": band, "pitch": pitch}

def ceramic(pitch=5.08):
    p = pitch / 2
    return {"pads": [("1", -p, 0, "circle", 1.6, 1.6, 0.8), ("2", p, 0, "circle", 1.6, 1.6, 0.8)], "body": ("rect", 2.7, 2.6)}

def elec(dia=6.3, pitch=2.5):
    p = pitch / 2
    return {"pads": [("1", -p, 0, "rect", 1.6, 1.6, 0.8), ("2", p, 0, "circle", 1.6, 1.6, 0.8)], "body": ("circle", dia), "plus": True}

def radial(dia, pitch, drill=1.0, pad=1.8):
    """Radial part standing up (inductor drum, electrolytic): two leads `pitch` apart, round body `dia`."""
    p = pitch / 2
    return {"pads": [("1", -p, 0, "circle", pad, pad, drill), ("2", p, 0, "circle", pad, pad, drill)], "body": ("circle", dia)}

def inductor(dia=8.4):
    """22 uH drum inductor, two lead spacings: holes 1 and 2 are 5.0 mm apart (e.g. Wurth 744772220), holes 1 and 3
    are 3.2 mm apart (the small 6.7 mm drums Sean has, leads 3.8 mm outside to outside). 2 and 3 are joined."""
    return {"pads": [("1", -2.5, 0, "circle", 1.6, 1.6, 1.0), ("2", 2.5, 0, "circle", 1.5, 1.5, 1.0),
                     ("3", 0.7, 0, "circle", 1.5, 1.5, 1.0)], "body": ("circle", dia)}

def hairpin(pitch=2.54):
    """Resistor standing on end (one lead bent back down): body over pad 1."""
    return {"pads": [("1", 0, 0, "circle", 1.6, 1.6, 0.8), ("2", pitch, 0, "circle", 1.6, 1.6, 0.8)],
            "body": ("rect", 2.6, 2.6), "hairpin": True}

def to92():
    return {"pads": [("1", -2.54, 0, "rect", 1.4, 1.4, 0.8), ("2", 0, 0, "circle", 1.4, 1.4, 0.8), ("3", 2.54, 0, "circle", 1.4, 1.4, 0.8)],
            "body": ("to92",)}

def header(n, pitch=2.54, drill=1.0, pad=1.7):
    x0 = -(n - 1) * pitch / 2
    return {"pads": [(str(i + 1), x0 + i * pitch, 0, "rect" if i == 0 else "circle", pad, pad, drill) for i in range(n)],
            "body": ("rect", n * pitch, 2.54)}

def dip8():
    pads = []
    for i in range(4):                       # pins 1-4 down the left, 5-8 up the right (top view, notch at top)
        pads.append((str(i + 1), -3.81, 3.81 - i * 2.54, "rect" if i == 0 else "oval", 1.6, 1.6, 0.8))
    for i in range(4):
        pads.append((str(5 + i), 3.81, -3.81 + i * 2.54, "oval", 1.6, 1.6, 0.8))
    return {"pads": pads, "body": ("dip", 5.3, 10.0)}

def double_row(n, rowsep, names_a, names_b, pitch=2.54, drill=1.0, pad=1.7):
    """Two 1xN socket rows (a module on headers). Row A at dy=-rowsep/2, row B at +rowsep/2; index 0 at dx=0, growing by -pitch."""
    pads = []
    for i in range(n):
        pads.append(("A%d" % i, -i * pitch, -rowsep / 2, "rect" if i == 0 else "circle", pad, pad, drill))
        pads.append(("B%d" % i, -i * pitch, rowsep / 2, "rect" if i == 0 else "circle", pad, pad, drill))
    return {"pads": pads, "body": ("module", n, rowsep, pitch), "names": (names_a, names_b)}

# Teensy 4.1, USB end at the RIGHT edge of the board (case hole), top side up.
# index 0 = the pin column next to the USB end. Rear row (+y) = GND,0,1..12,3.3V,24..32; front row = VIN,GND,3.3V,23..13,GND,41..33
T_REAR = ["GND", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "3.3V", "24", "25", "26", "27", "28", "29", "30", "31", "32"]
T_FRONT = ["VIN", "GND", "3.3V", "23", "22", "21", "20", "19", "18", "17", "16", "15", "14", "13", "GND", "41", "40", "39", "38", "37", "36", "35", "34", "33"]
# ESP32-C3 SuperMini, plugged in chip side up, USB end toward the back. index 0 = the pin pair next to the USB end.
# Seen from the chip side with USB at the top, 5V/GND/3V3/4/3/2/1/0 run down the RIGHT edge (v1.0 had this mirrored:
# the names printed on the module's underside read the other way round from above).
E_LEFT = ["5", "6", "7", "8", "9", "10", "20", "21"]
E_RIGHT = ["5V", "GND", "3V3", "4", "3", "2", "1", "0"]

def teensy():
    fp = double_row(24, 15.24, T_FRONT, T_REAR)
    return fp

def esp():
    # rotate later: rows run along y. Built as rows along x with index 0 at dx=0.
    # row A ends up on the right (x larger) after the 90 degree turn, row B on the left
    return double_row(8, 15.24, E_RIGHT, E_LEFT)

# ------------------------------------------------------------------ parts
# ref: (footprint, x, y, rotation_deg, value, description)
R = lambda pitch=10.16: axial(pitch)
P = {}
def part(ref, fp, x, y, rot, value, desc=""):
    P[ref] = {"fp": fp, "x": x, "y": y, "rot": rot, "value": value, "desc": desc}

# modules
TX0 = 68.0                    # Teensy pin column 0 (next to USB); its USB plug ends about 1 mm past the board edge
part("U5", teensy(), TX0, 75.0, 0, "Teensy 4.1", "on 2 x 24-pin female headers")
part("U4", esp(), 17.0, 20.4, 90, "ESP32-C3 SuperMini", "on 2 x 8-pin female headers, chip side up, USB toward the back, antenna at the front edge")

# connectors (pin 1 = square pad)
part("J1", header(3), 4.5, 63.0, 90, "POWER", "1 +5V from switch, 2 GND, 3 battery+ from switch")
part("J2", header(4), 32.0, 5.0, 0, "RADAR", "1 Q, 2 VCC, 3 I, 4 GND (K-LC5 pin order; radar pin 5, VCO, is left unconnected)")
part("J3", header(4), 3.0, 45.0, 90, "OLED", "1 GND, 2 VCC, 3 SCL, 4 SDA")
part("J4", header(4), 3.0, 33.0, 90, "SENSORS", "1 GND, 2 3V3, 3 SDA, 4 SCL (STEMMA QT: black, red, blue, yellow)")
part("J5", header(3), 3.0, 55.0, 90, "AMMO", "1 tip (data), 2 ring (3V3 via R22), 3 sleeve (GND)")

# power + reference (front strip, y 0..20)
part("C5", ceramic(), 31.0, 9.5, 0, "100nF", "radar VCC decoupling")
part("C11", ceramic(), 27.6, 15.0, 90, "100nF", "VREF")
part("C10", elec(5.0, 2.0), 32.3, 15.0, 90, "10uF", "VREF, 10 V or more")
part("R3", R(), 37.0, 14.0, 90, "10k", "VREF divider")
part("R18", R(), 44.0, 5.0, 0, "10", "5 V filter to the radar regulator")
part("C4", elec(5.0, 2.0), 53.5, 5.0, 0, "10uF", "10 V or more")
part("C1", ceramic(), 60.0, 5.0, 0, "1uF")
part("U3", to92(), 42.0, 11.5, 0, "MCP1700-3302E", "3.3 V regulator, flat face toward the front")
part("C2", ceramic(), 49.0, 11.5, 0, "1uF")
part("C3", elec(6.3, 2.5), 56.5, 11.5, 0, "100uF", "10 V or more")
part("R1", R(), 62.0, 13.0, 90, "10", "op-amp supply filter")
part("C7", elec(5.0, 2.0), 66.5, 14.0, 90, "10uF", "10 V or more")
part("R2", R(), 44.5, 17.5, 0, "10k", "VREF divider")

# amplifier: I channel band (y 22..32), Q channel band (y 47..57), op-amps between
def band(y, refs, x0=24.5, dx=3.25):
    for i, (ref, kind, val) in enumerate(refs):
        fp = R() if kind == "R" else ceramic()
        part(ref, fp, x0 + i * dx, y, 90, val)

band(29.0, [("C12", "C", "10nF"), ("R4", "R", "4.7k"), ("R6", "R", "470"), ("C14", "C", "1uF"), ("R5", "R", "10k"),
            ("C15", "C", "10nF"), ("R7", "R", "4.7k"), ("R9", "R", "470"), ("C17", "C", "1uF"), ("R8", "R", "10k"),
            ("R10", "R", "330"), ("C18", "C", "1nF")])
band(57.0, [("C19", "C", "10nF"), ("R11", "R", "4.7k"), ("R13", "R", "470"), ("C21", "C", "1uF"), ("R12", "R", "10k"),
            ("C22", "C", "10nF"), ("R14", "R", "4.7k"), ("R16", "R", "470"), ("C24", "C", "1uF"), ("R15", "R", "10k"),
            ("R17", "R", "330"), ("C25", "C", "1nF")])
part("U1", dip8(), 36.0, 43.0, 270, "MCP6022", "I channel, in a DIP-8 socket")
part("U2", dip8(), 56.0, 43.0, 270, "MCP6022", "Q channel, in a DIP-8 socket")
part("C8", ceramic(), 43.14, 36.5, 0, "100nF", "U1 supply, right beside pin 8")
part("C9", ceramic(), 63.14, 36.5, 0, "100nF", "U2 supply, right beside pin 8")

# ESP32 side: battery gauge, diode, sensor pull-ups
part("D1", axial(10.16, 1.0, 1.8, (5.2, 2.7), band=True), 16.8, 24.8, 0, "1N5817", "stripe (cathode) toward the right")
part("R19", R(), 13.9, 29.5, 0, "100k", "battery divider")
part("R20", R(), 13.9, 33.0, 0, "100k", "battery divider")
part("C26", ceramic(), 14.4, 36.5, 0, "100nF", "battery divider")
part("R21", R(), 13.9, 40.0, 0, "4.7k", "ammo probe pull-up")
part("R22", R(), 13.9, 43.5, 0, "100", "ammo jack ring feed")
# 1 k in each serial line: limits the current if the ESP32 is on USB while the Teensy is unpowered
part("R23", hairpin(), 21.3, 29.7, 90, "1k", "serial: Teensy TX8 (pin 35) to ESP32 GPIO20; stands on end")
part("R24", hairpin(), 21.3, 35.7, 90, "1k", "serial: ESP32 GPIO21 to Teensy RX8 (pin 34); stands on end")

# v1.2: the two 5 V noise filters, on the board (v1.1 had them in the wiring)
part("L1", inductor(), 10.4, 61.6, 0, "22uH", "battery holder filter: 1 A or more, up to 8.4 mm across; leads 5 mm apart (holes 1-2) or 3.2 mm (holes 1-3)")
part("C27", elec(8.0, 3.5), 18.8, 61.9, 0, "470uF", "battery holder filter, 10 V or more, 8 mm")
part("C28", ceramic(), 10.4, 46.6, 0, "1uF", "battery holder filter")
part("L2", inductor(), 10.4, 52.5, 0, "22uH", "ESP32 filter: 1 A or more, up to 8.4 mm across; leads 5 mm apart (holes 1-2) or 3.2 mm (holes 1-3)")
part("C29", elec(8.0, 3.5), 18.8, 52.5, 0, "470uF", "ESP32 filter, 10 V or more, 8 mm")
part("C30", ceramic(), 18.9, 46.6, 0, "1uF", "ESP32 filter")

# ------------------------------------------------------------------ nets
NETS = {}
def net(name, *pins):
    NETS.setdefault(name, [])
    for p in pins:
        NETS[name].append(p)

def tpin(label, row):  # Teensy pad name for a label in a row ("F" front / "R" rear)
    lst = T_FRONT if row == "F" else T_REAR
    return "U5-%s%d" % ("A" if row == "F" else "B", lst.index(label))

def epin(label):
    if label in E_LEFT:
        return "U4-B%d" % E_LEFT.index(label)
    return "U4-A%d" % E_RIGHT.index(label)

net("GND", "J1-2", "J2-4", "J3-1", "J4-1", "J5-3", tpin("GND", "F"), "U5-B0", "U5-A14", epin("GND"),
    "C4-2", "C1-2", "U3-1", "C2-2", "C3-2", "C7-2", "R3-2", "C10-2", "C11-2", "C5-2",
    "C14-2", "C17-2", "C18-2", "C21-2", "C24-2", "C25-2", "U1-4", "U2-4", "C8-2", "C9-2", "R20-2", "C26-2", "C27-2", "C28-2", "C29-2", "C30-2")
net("5VIN", "J1-1", "L1-1")
net("+5V", "L1-2", "L1-3", "C27-1", "C28-1", tpin("VIN", "F"), "D1-1", "R18-1")
net("ESP5V", "D1-2", "L2-1")
net("ESP5VF", "L2-2", "L2-3", "C29-1", "C30-1", epin("5V"))
net("5VF", "R18-2", "C4-1", "C1-1", "U3-2")
net("+3V3A", "U3-3", "C2-1", "C3-1", "J2-2", "C5-1", "R1-1")
net("+3V3OP", "R1-2", "C7-1", "R2-1", "U1-8", "U2-8", "C8-1", "C9-1")
net("VREF", "R2-2", "R3-1", "C10-1", "C11-1", "R4-2", "R7-2", "R11-2", "R14-2")
# I channel: radar pin 3
net("I_IN", "J2-3", "C12-1")
net("I1P", "C12-2", "R4-1", "U1-3")
net("I1M", "U1-2", "R5-1", "R6-1")
net("I1G", "R6-2", "C14-1")
net("I1O", "U1-1", "R5-2", "C15-1")
net("I2P", "C15-2", "R7-1", "U1-5")
net("I2M", "U1-6", "R8-1", "R9-1")
net("I2G", "R9-2", "C17-1")
net("I2O", "U1-7", "R8-2", "R10-1")
net("ADC_I", "R10-2", "C18-1", tpin("14", "F"))
# Q channel: radar pin 1
net("Q_IN", "J2-1", "C19-1")
net("Q1P", "C19-2", "R11-1", "U2-3")
net("Q1M", "U2-2", "R12-1", "R13-1")
net("Q1G", "R13-2", "C21-1")
net("Q1O", "U2-1", "R12-2", "C22-1")
net("Q2P", "C22-2", "R14-1", "U2-5")
net("Q2M", "U2-6", "R15-1", "R16-1")
net("Q2G", "R16-2", "C24-1")
net("Q2O", "U2-7", "R15-2", "R17-1")
net("ADC_Q", "R17-2", "C25-1", tpin("15", "F"))
# Teensy <-> ESP32 serial
# v1.1: Teensy Serial8 (TX8 = pin 35, RX8 = pin 34, at the front row's left end, right next to the ESP32) instead of Serial1
net("T_TX", tpin("35", "F"), "R23-2")       # Teensy TX8 -> 1k -> ESP RX (GPIO20)
net("E_RX", "R23-1", epin("20"))
net("T_RX", tpin("34", "F"), "R24-2")       # Teensy RX8 <- 1k <- ESP TX (GPIO21)
net("E_TX", "R24-1", epin("21"))
# ESP32 3.3 V for the screen and sensors
net("3V3D", epin("3V3"), "J3-2", "J4-2", "R21-1", "R22-1")
net("SDA", epin("6"), "J3-4", "J4-3")
net("SCL", epin("7"), "J3-3", "J4-4")
net("BSW", "J1-3", "R19-1")
net("BSENSE", "R19-2", "R20-1", "C26-1", epin("3"))
net("ONEWIRE", epin("10"), "R21-2", "J5-1")
net("AMMO_V", "R22-2", "J5-2")

POWER_NETS = {"GND": 0.6, "+5V": 0.6, "5VIN": 0.6, "ESP5V": 0.6, "ESP5VF": 0.6, "5VF": 0.5, "+3V3A": 0.5, "+3V3OP": 0.4, "3V3D": 0.4, "VREF": 0.3}
SIGNAL_W = 0.3
CLEARANCE = 0.25

# ------------------------------------------------------------------ geometry helpers
def rot(dx, dy, deg):
    a = math.radians(deg)
    return dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)

def pads_world():
    """[(ref, padname, x, y, shape, w, h, drill, rot)] for every pad."""
    out = []
    for ref, p in P.items():
        for (nm, dx, dy, sh, w, h, dr) in p["fp"]["pads"]:
            rx, ry = rot(dx, dy, p["rot"])
            out.append((ref, nm, p["x"] + rx, p["y"] + ry, sh, w, h, dr, p["rot"]))
    return out

def pin_net():
    m = {}
    for n, pins in NETS.items():
        for pn in pins:
            if pn in m:
                raise SystemExit("pin in two nets: %s (%s, %s)" % (pn, m[pn], n))
            m[pn] = n
    return m

def check_netlist():
    pw = {(r + "-" + nm) for (r, nm, *_ ) in pads_world()}
    bad = [pn for pins in NETS.values() for pn in pins if pn not in pw]
    if bad:
        raise SystemExit("netlist pins with no pad: %s" % bad)
    pin_net()
    return True

if __name__ == "__main__":
    check_netlist()
    print(len(P), "parts,", len(NETS), "nets,", sum(len(v) for v in NETS.values()), "connections")
