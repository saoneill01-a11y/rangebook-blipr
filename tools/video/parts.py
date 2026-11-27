"""Flat illustrations of every BLIPR part and tool, drawn with cairo.
Each function draws centred on (0, 0) in millimetre-ish units; SIZE gives its (w, h) box for scaling."""
import math, cairo
from draw import setc, rrect, hexc, text, font, PAPER, INK, WIRE, BAD

BODY_BEIGE = hexc("#E9D5A8")
LEAD = hexc("#A9AFB8")
GOLD = hexc("#D8A93B")
PCB_GREEN = hexc("#1F6B3A")
PCB_BLUE = hexc("#1E4FA3")
BLACK = hexc("#202226")
DARK = hexc("#2D3036")
SILVER = hexc("#C9CED6")
BRASS = hexc("#C9A23F")

BANDS = {"black": "#111111", "brown": "#7A3E12", "red": "#D02525", "orange": "#F07A16", "yellow": "#F2CC1B",
         "green": "#2B9A3A", "blue": "#2457C9", "violet": "#7D3BC1", "grey": "#8A8A8A", "white": "#F2F2F2", "gold": "#C9A227"}
RCODE = {  # 4-band codes used in BLIPR
    "10": ["brown", "black", "black", "gold"], "100": ["brown", "black", "brown", "gold"],
    "330": ["orange", "orange", "brown", "gold"], "470": ["yellow", "violet", "brown", "gold"],
    "1k": ["brown", "black", "red", "gold"], "4.7k": ["yellow", "violet", "red", "gold"],
    "10k": ["brown", "black", "orange", "gold"], "100k": ["brown", "black", "yellow", "gold"],
}

SIZE = {}


def _stroke(ctx, col, lw):
    setc(ctx, col); ctx.set_line_width(lw); ctx.stroke()


def resistor(ctx, value="10k", lead=4.0, body=(6.3, 2.5)):
    bw, bh = body
    setc(ctx, LEAD); ctx.set_line_width(0.55); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(-bw / 2 - lead, 0); ctx.line_to(bw / 2 + lead, 0); ctx.stroke()
    setc(ctx, BODY_BEIGE); rrect(ctx, -bw / 2, -bh / 2, bw, bh, bh / 2.2); ctx.fill_preserve()
    setc(ctx, hexc("#8C7A55")); ctx.set_line_width(0.15); ctx.stroke()
    xs = [-bw * 0.30, -bw * 0.15, 0.0, bw * 0.30]
    for x, b in zip(xs, RCODE.get(value, ["black"] * 4)):
        setc(ctx, hexc(BANDS[b])); ctx.rectangle(x - 0.33, -bh / 2 + 0.05, 0.66, bh - 0.1); ctx.fill()
SIZE["resistor"] = (14.3, 3)


def ceramic(ctx, code="104", lead=4.0, top=False):
    if top:
        setc(ctx, hexc("#E7B43C")); rrect(ctx, -1.6, -1.3, 3.2, 2.6, 0.9); ctx.fill()
        return
    setc(ctx, LEAD); ctx.set_line_width(0.5)
    ctx.move_to(-1.25, 1.5); ctx.line_to(-1.25, 1.5 + lead); ctx.move_to(1.25, 1.5); ctx.line_to(1.25, 1.5 + lead); ctx.stroke()
    setc(ctx, hexc("#E7B43C")); ctx.save(); ctx.scale(1, 0.85); ctx.arc(0, -0.2, 2.6, 0, 2 * math.pi); ctx.restore(); ctx.fill()
    font(ctx, 1.5, True); setc(ctx, hexc("#5B3E00")); e = ctx.text_extents(code); ctx.move_to(-e.x_advance / 2, 0.4); ctx.show_text(code)
SIZE["ceramic"] = (6, 9.5)


def electrolytic_side(ctx, label="100µF", h=11, d=6.3):
    setc(ctx, LEAD); ctx.set_line_width(0.5)
    ctx.move_to(-1.25, h / 2); ctx.line_to(-1.25, h / 2 + 5.0); ctx.move_to(1.25, h / 2); ctx.line_to(1.25, h / 2 + 3.5); ctx.stroke()
    setc(ctx, hexc("#24324F")); rrect(ctx, -d / 2, -h / 2, d, h, 0.8); ctx.fill()
    setc(ctx, hexc("#9AA7BF")); ctx.rectangle(d / 2 - 1.6, -h / 2, 1.6, h); ctx.fill()
    for k in range(3):
        y = -h / 2 + 2 + k * 3
        setc(ctx, hexc("#24324F")); ctx.rectangle(d / 2 - 1.1, y, 0.6, 0.25); ctx.fill()
    setc(ctx, SILVER); ctx.rectangle(-d / 2, -h / 2, d, 0.7); ctx.fill()
SIZE["electrolytic_side"] = (7, 17)


def electrolytic_top(ctx, d=6.3, minus_dir=0.0):
    """Top view: can with the stripe (−) toward angle minus_dir (radians, 0 = +x)."""
    r = d / 2
    setc(ctx, hexc("#24324F")); ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.fill()
    setc(ctx, hexc("#9AA7BF")); ctx.move_to(0, 0); ctx.arc(0, 0, r, minus_dir - 0.5, minus_dir + 0.5); ctx.close_path(); ctx.fill()
    setc(ctx, hexc("#B9C0CC")); ctx.arc(0, 0, r * 0.72, 0, 2 * math.pi); ctx.fill()


def inductor(ctx, d=8.0, h=9.0):
    """Radial drum-core power inductor, side view: two legs down, copper winding on a dark core."""
    setc(ctx, LEAD); ctx.set_line_width(0.5)
    ctx.move_to(-1.8, h / 2); ctx.line_to(-1.8, h / 2 + 4.5); ctx.move_to(1.8, h / 2); ctx.line_to(1.8, h / 2 + 4.5); ctx.stroke()
    setc(ctx, DARK); rrect(ctx, -d / 2, -h / 2, d, 1.6, 0.4); ctx.fill(); rrect(ctx, -d / 2, h / 2 - 1.6, d, 1.6, 0.4); ctx.fill()
    setc(ctx, hexc("#B8642A")); ctx.rectangle(-d / 2 + 0.6, -h / 2 + 1.6, d - 1.2, h - 3.2); ctx.fill()
    setc(ctx, hexc("#8A4518")); ctx.set_line_width(0.25)
    for k in range(9):
        yy = -h / 2 + 2.0 + k * (h - 4.0) / 8
        ctx.move_to(-d / 2 + 0.6, yy); ctx.line_to(d / 2 - 0.6, yy + 0.3); ctx.stroke()
SIZE["inductor"] = (9, 14)


def diode(ctx, lead=4.0, body=(5.2, 2.7)):
    bw, bh = body
    setc(ctx, LEAD); ctx.set_line_width(0.6); ctx.move_to(-bw / 2 - lead, 0); ctx.line_to(bw / 2 + lead, 0); ctx.stroke()
    setc(ctx, BLACK); rrect(ctx, -bw / 2, -bh / 2, bw, bh, 0.5); ctx.fill()
    setc(ctx, SILVER); ctx.rectangle(bw / 2 - 1.3, -bh / 2, 0.8, bh); ctx.fill()
SIZE["diode"] = (13.2, 3)


def dip_socket(ctx, w=7.6, h=10.2):
    setc(ctx, BLACK); rrect(ctx, -w / 2, -h / 2, w, h, 0.4); ctx.fill()
    setc(ctx, hexc("#3B3F46")); ctx.rectangle(-w / 2 + 1.7, -h / 2 + 1.0, w - 3.4, h - 2.0); ctx.fill()
    for i in range(4):
        for sx in (-1, 1):
            setc(ctx, GOLD); ctx.arc(sx * 3.81, -3.81 + i * 2.54, 0.42, 0, 2 * math.pi); ctx.fill()
    setc(ctx, hexc("#3B3F46")); ctx.arc(0, -h / 2, 0.8, 0, math.pi); ctx.fill()


def opamp_chip(ctx, w=6.4, h=9.6, label="MCP6022"):
    for i in range(4):
        for sx in (-1, 1):
            setc(ctx, SILVER); ctx.rectangle(sx * 3.81 - 0.45, -3.81 + i * 2.54 - 0.3, 0.9, 0.6); ctx.fill()
    setc(ctx, DARK); rrect(ctx, -w / 2 + 0.4, -h / 2, w - 0.8, h, 0.3); ctx.fill()
    setc(ctx, hexc("#16181C")); ctx.arc(0, -h / 2, 0.75, 0, math.pi); ctx.fill()
    setc(ctx, hexc("#9AA0AA")); ctx.arc(-1.6, -h / 2 + 1.4, 0.35, 0, 2 * math.pi); ctx.fill()
    ctx.save(); ctx.rotate(math.pi / 2); font(ctx, 1.1, True); setc(ctx, hexc("#C8CCD3"))
    e = ctx.text_extents(label); ctx.move_to(-e.x_advance / 2, 0.4); ctx.show_text(label); ctx.restore()


def to92(ctx, legs=True, label="1700"):
    if legs:
        setc(ctx, LEAD); ctx.set_line_width(0.45)
        for x in (-1.27, 0, 1.27):
            ctx.move_to(x, 2.2); ctx.line_to(x * (2 if legs == "spread" else 1), 7.0)
        ctx.stroke()
    setc(ctx, BLACK); ctx.move_to(-2.3, 2.2); ctx.line_to(-2.3, -2.2); ctx.line_to(2.3, -2.2); ctx.line_to(2.3, 2.2); ctx.close_path(); ctx.fill()
    font(ctx, 1.1, True); setc(ctx, hexc("#C8CCD3")); e = ctx.text_extents(label); ctx.move_to(-e.x_advance / 2, 0.4); ctx.show_text(label)
SIZE["to92"] = (5, 10)


def to92_top(ctx):
    """Top view: flat face toward -y (front)."""
    setc(ctx, BLACK); ctx.move_to(-2.4, -0.9)
    ctx.arc_negative(0, -0.9, 2.4, math.pi, 0) if False else None
    ctx.new_path(); ctx.move_to(-2.4, -1.1); ctx.line_to(2.4, -1.1)
    ctx.arc(0, -1.1, 2.4, 0, math.pi); ctx.close_path(); ctx.fill()


def header_male(ctx, n=4, pitch=2.54):
    w = n * pitch
    setc(ctx, BLACK); ctx.rectangle(-w / 2, -1.27, w, 2.54); ctx.fill()
    for i in range(n):
        setc(ctx, GOLD); x = -w / 2 + pitch / 2 + i * pitch; ctx.rectangle(x - 0.32, -0.32, 0.64, 0.64); ctx.fill()


def header_female(ctx, n=8, pitch=2.54, along="x"):
    w = n * pitch
    ctx.save()
    if along == "y":
        ctx.rotate(math.pi / 2)
    setc(ctx, BLACK); ctx.rectangle(-w / 2, -1.27, w, 2.54); ctx.fill()
    for i in range(n):
        setc(ctx, hexc("#55585E")); x = -w / 2 + pitch / 2 + i * pitch; ctx.rectangle(x - 0.5, -0.5, 1.0, 1.0); ctx.fill()
    ctx.restore()


def teensy(ctx, under=False):
    """Teensy 4.1 top view, 61 x 18 mm, USB end at +x."""
    L, Wd = 61.0, 18.0
    setc(ctx, hexc("#1C6E3D")); rrect(ctx, -L / 2, -Wd / 2, L, Wd, 0.8); ctx.fill()
    for i in range(24):
        for sy in (-1, 1):
            x = L / 2 - 1.27 - i * 2.54
            setc(ctx, GOLD); ctx.arc(x, sy * 7.62, 0.75, 0, 2 * math.pi); ctx.fill()
            setc(ctx, BLACK); ctx.arc(x, sy * 7.62, 0.4, 0, 2 * math.pi); ctx.fill()
    if under:
        setc(ctx, GOLD); ctx.rectangle(L / 2 - 9.0, -2.0, 1.4, 1.4); ctx.fill(); ctx.rectangle(L / 2 - 9.0, 0.6, 1.4, 1.4); ctx.fill()
        setc(ctx, hexc("#E7C66A")); ctx.set_line_width(0.4); ctx.move_to(L / 2 - 8.3, -0.6); ctx.line_to(L / 2 - 8.3, 0.6); ctx.stroke()
        font(ctx, 1.2, True); setc(ctx, PAPER); ctx.move_to(L / 2 - 13.3, -0.9); ctx.show_text("VIN"); ctx.move_to(L / 2 - 14.0, 2.0); ctx.show_text("VUSB")
        return
    setc(ctx, SILVER); ctx.rectangle(L / 2 - 4.0, -3.8, 5.2, 7.6); ctx.fill()           # micro USB
    setc(ctx, hexc("#888E98")); ctx.rectangle(-L / 2 - 1.0, -5.5, 12, 11); ctx.fill()     # SD slot
    setc(ctx, hexc("#16181C")); ctx.rectangle(-4, -4, 9, 9); ctx.fill()                    # i.MX RT1062
    font(ctx, 1.4, True); setc(ctx, hexc("#C8CCD3")); ctx.move_to(-2.6, 0.5); ctx.show_text("i.MX")
    setc(ctx, PAPER); ctx.rectangle(14.0, -1.6, 3.4, 2.6); ctx.fill()                     # program button
    setc(ctx, hexc("#FF8A00")); ctx.arc(22.5, 4.2, 0.7, 0, 2 * math.pi); ctx.fill()         # orange LED
    font(ctx, 2.2, True); setc(ctx, PAPER); ctx.move_to(-14, -3.4); ctx.show_text("TEENSY 4.1")
SIZE["teensy"] = (64, 19)


def esp32(ctx, labels=False):
    """ESP32-C3 SuperMini, chip side up, USB end at -y (top of picture), antenna at +y."""
    Wd, L = 18.0, 22.5
    setc(ctx, hexc("#17191D")); rrect(ctx, -Wd / 2, -L / 2, Wd, L, 0.8); ctx.fill()
    setc(ctx, SILVER); rrect(ctx, -4.5, -L / 2 - 1.2, 9, 7.2, 1.2); ctx.fill()              # USB-C
    setc(ctx, PAPER); ctx.rectangle(-7.0, -3.6, 2.6, 2.0); ctx.fill(); ctx.rectangle(4.4, -3.6, 2.6, 2.0); ctx.fill()
    setc(ctx, hexc("#2B2E34")); ctx.rectangle(-3.4, -1.0, 6.8, 6.8); ctx.fill()
    font(ctx, 2.0, True); setc(ctx, hexc("#C8CCD3")); ctx.move_to(-1.6, 3.2); ctx.show_text("C3")
    setc(ctx, hexc("#D9DCE1")); ctx.rectangle(-3.2, L / 2 - 3.0, 6.4, 1.8); ctx.fill()     # antenna
    for i in range(8):
        y = -L / 2 + 2.4 + i * 2.54
        for sx in (-1, 1):
            setc(ctx, GOLD); ctx.arc(sx * 7.62, y, 0.75, 0, 2 * math.pi); ctx.fill()
            setc(ctx, BLACK); ctx.arc(sx * 7.62, y, 0.38, 0, 2 * math.pi); ctx.fill()
    if labels:
        font(ctx, 1.25, True)
        for i, nm in enumerate(["5V", "GND", "3V3", "4", "3", "2", "1", "0"]):
            setc(ctx, hexc("#FFE680")); e = ctx.text_extents(nm); ctx.move_to(7.62 - 1.2 - e.x_advance, -L / 2 + 2.4 + i * 2.54 + 0.45); ctx.show_text(nm)
        for i, nm in enumerate(["5", "6", "7", "8", "9", "10", "20", "21"]):
            setc(ctx, hexc("#FFE680")); ctx.move_to(-7.62 + 1.2, -L / 2 + 2.4 + i * 2.54 + 0.45); ctx.show_text(nm)
SIZE["esp32"] = (19, 25)


def oled(ctx, reading="2,712", unit="fps"):
    setc(ctx, hexc("#1E4FA3")); rrect(ctx, -13.5, -14, 27, 28, 1.2); ctx.fill()
    for i in range(4):
        setc(ctx, GOLD); ctx.arc(-3.81 + i * 2.54, -12.2, 0.7, 0, 2 * math.pi); ctx.fill()
    font(ctx, 1.05, True); setc(ctx, PAPER)
    for i, nm in enumerate(["GND", "VCC", "SCL", "SDA"]):
        e = ctx.text_extents(nm); ctx.move_to(-3.81 + i * 2.54 - e.x_advance / 2, -10.3); ctx.show_text(nm)
    setc(ctx, hexc("#0B0C0E")); ctx.rectangle(-12.5, -8.0, 25, 15.5); ctx.fill()
    if reading:
        font(ctx, 5.0, True); setc(ctx, PAPER); e = ctx.text_extents(reading); ctx.move_to(-e.x_advance / 2, 0.4); ctx.show_text(reading)
        font(ctx, 2.2, True); e = ctx.text_extents(unit); ctx.move_to(-e.x_advance / 2, 4.4); ctx.show_text(unit)
SIZE["oled"] = (28, 29)


def radar(ctx, side="front", pins_label=True):
    """RFbeam K-LC5, 25 x 25 mm. front = antenna patches, back = 5 pins along the top edge."""
    setc(ctx, hexc("#E9E5D8") if side == "front" else hexc("#1F6B3A")); rrect(ctx, -12.5, -12.5, 25, 25, 0.8); ctx.fill()
    if side == "front":
        for col, x0 in ((hexc("#C98F2C"), -9.5), (hexc("#C98F2C"), 1.5)):
            for i in range(2):
                for j in range(4):
                    setc(ctx, col); ctx.rectangle(x0 + i * 4.2, -10.0 + j * 5.0, 3.2, 3.6); ctx.fill()
        font(ctx, 1.6, True); setc(ctx, hexc("#555")); ctx.move_to(-5.5, 11.6); ctx.show_text("TX        RX")
    else:
        setc(ctx, SILVER); rrect(ctx, -9, -5, 18, 14, 0.6); ctx.fill()
        font(ctx, 1.8, True); setc(ctx, hexc("#444")); ctx.move_to(-4.3, 3); ctx.show_text("K-LC5")
        for i in range(5):
            x = -5.08 + i * 2.54
            setc(ctx, GOLD); ctx.rectangle(x - 0.4, -10.8, 0.8, 0.8); ctx.fill()
            if pins_label:
                font(ctx, 1.4, True); setc(ctx, PAPER); e = ctx.text_extents(str(i + 1)); ctx.move_to(x - e.x_advance / 2, -7.6); ctx.show_text(str(i + 1))
SIZE["radar"] = (26, 26)


def battery_holder(ctx, with_cell=True, mode_on=True):
    """18650 holder board ~ 98 x 30 mm: holder, USB-C at left, button at top-left, mode switch, 5V/GND pads at right."""
    setc(ctx, hexc("#2457A8")); rrect(ctx, -49, -15, 98, 30, 1.5); ctx.fill()
    setc(ctx, hexc("#16181C")); rrect(ctx, -38, -11.5, 72, 23, 2); ctx.fill()
    if with_cell:
        setc(ctx, hexc("#3B8D45")); rrect(ctx, -34, -9, 64, 18, 8.5); ctx.fill()
        font(ctx, 3.2, True); setc(ctx, PAPER); ctx.move_to(-9, 1.2); ctx.show_text("18650")
        setc(ctx, SILVER); ctx.rectangle(30, -3, 2.5, 6); ctx.fill()
    setc(ctx, SILVER); ctx.rectangle(-51, -4.5, 6, 9); ctx.fill()                   # USB-C
    setc(ctx, PAPER); ctx.rectangle(-46.5, -14, 5, 3.5); ctx.fill()                 # button
    setc(ctx, hexc("#111")); ctx.rectangle(-44, 9.5, 5, 3); ctx.fill()              # mode switch
    setc(ctx, PAPER); ctx.rectangle(-44 + (2.8 if mode_on else 0.2), 10, 2, 2); ctx.fill()
    for i, nm in enumerate(["GND", "5V"]):
        setc(ctx, GOLD); ctx.arc(42, -6 + i * 4, 1.0, 0, 2 * math.pi); ctx.fill()
SIZE["battery_holder"] = (104, 31)


def cell(ctx):
    setc(ctx, hexc("#3B8D45")); rrect(ctx, -32.5, -9, 65, 18, 3); ctx.fill()
    setc(ctx, SILVER); ctx.rectangle(32.5, -3.5, 2, 7); ctx.fill()
    font(ctx, 4.5, True); setc(ctx, PAPER); ctx.move_to(-11, 1.6); ctx.show_text("18650")
    font(ctx, 4.5, True); ctx.move_to(25, 1.6); ctx.show_text("+")
SIZE["cell"] = (68, 19)


def insert(ctx, d=4.6, L=5.7, label=None):
    setc(ctx, BRASS); ctx.rectangle(-d / 2, -L / 2, d, L); ctx.fill()
    setc(ctx, hexc("#8E6E1E")); ctx.set_line_width(0.25)
    for k in range(6):
        y = -L / 2 + 0.5 + k * (L - 1) / 5
        ctx.move_to(-d / 2, y); ctx.line_to(d / 2, y + 0.6)
    ctx.stroke()
SIZE["insert"] = (5, 6)


def screw(ctx, L=8.0, d=3.0):
    setc(ctx, hexc("#7D838C")); ctx.rectangle(-d / 2, 0, d, L); ctx.fill()
    setc(ctx, hexc("#5E636B")); ctx.set_line_width(0.22)
    for k in range(int(L / 0.5)):
        ctx.move_to(-d / 2, 0.3 + k * 0.5); ctx.line_to(d / 2, 0.55 + k * 0.5)
    ctx.stroke()
    setc(ctx, hexc("#9AA0A8")); rrect(ctx, -d * 0.95, -d * 0.6, d * 1.9, d * 0.65, 0.6); ctx.fill()
SIZE["screw"] = (6, 10)


def foam_tape(ctx):
    setc(ctx, hexc("#F2F2F2")); ctx.arc(0, 0, 8, 0, 2 * math.pi); ctx.fill()
    setc(ctx, hexc("#C8CDD4")); ctx.set_line_width(0.4); ctx.arc(0, 0, 8, 0, 2 * math.pi); ctx.stroke()
    setc(ctx, hexc("#E05353")); ctx.arc(0, 0, 4, 0, 2 * math.pi); ctx.fill()
    setc(ctx, BG_SOFT); ctx.arc(0, 0, 3.2, 0, 2 * math.pi); ctx.fill()
BG_SOFT = hexc("#FFFFFF")
SIZE["foam_tape"] = (17, 17)


def stemma_board(ctx, label="SHT45", col="#1A1C20"):
    setc(ctx, hexc(col)); rrect(ctx, -12.7, -8.9, 25.4, 17.8, 1.0); ctx.fill()
    for sx in (-1, 1):
        for sy in (-1, 1):
            setc(ctx, GOLD); ctx.arc(sx * 10.16, sy * 6.35, 1.3, 0, 2 * math.pi); ctx.fill()
            setc(ctx, BG_SOFT); ctx.arc(sx * 10.16, sy * 6.35, 0.8, 0, 2 * math.pi); ctx.fill()
    for sx in (-1, 1):
        setc(ctx, hexc("#F1F1F1")); ctx.rectangle(sx * 8.5 - 2.4, -3, 4.8, 6); ctx.fill()
    font(ctx, 2.4, True); setc(ctx, PAPER); e = ctx.text_extents(label); ctx.move_to(-e.x_advance / 2, 0.9); ctx.show_text(label)
SIZE["stemma_board"] = (26, 18)


def dfrobot(ctx):
    setc(ctx, hexc("#1A1C20")); rrect(ctx, -15, -11, 30, 22, 1.2); ctx.fill()
    for sx in (-1, 1):
        setc(ctx, GOLD); ctx.arc(sx * 12, -8, 1.5, 0, 2 * math.pi); ctx.fill()
        setc(ctx, BG_SOFT); ctx.arc(sx * 12, -8, 0.9, 0, 2 * math.pi); ctx.fill()
    setc(ctx, hexc("#F1F1F1")); ctx.rectangle(-4, 7, 8, 4); ctx.fill()
    setc(ctx, hexc("#2D3036")); ctx.rectangle(-3, -4, 6, 6); ctx.fill()
    font(ctx, 2.0, True); setc(ctx, PAPER); ctx.move_to(-8.5, 5.5); ctx.show_text("10-DoF IMU")
SIZE["dfrobot"] = (31, 23)


def qt_cable(ctx, L=40):
    cols = [WIRE["GND"], WIRE["5V"], WIRE["SDA"], WIRE["SCL"]]
    for i, c in enumerate(cols):
        setc(ctx, c); ctx.set_line_width(0.9)
        y = -1.5 + i * 1.0
        ctx.move_to(-L / 2 + 4, y); ctx.curve_to(-5, y - 6, 5, y + 6, L / 2 - 4, y); ctx.stroke()
    setc(ctx, hexc("#F1F1F1")); rrect(ctx, -L / 2, -2.5, 5, 5, 0.6); ctx.fill()
    for i, c in enumerate(cols):
        setc(ctx, LEAD); ctx.set_line_width(0.4); y = -1.5 + i * 1.0; ctx.move_to(L / 2 - 4, y); ctx.line_to(L / 2, y); ctx.stroke()
SIZE["qt_cable"] = (42, 12)


def sd_card(ctx):
    setc(ctx, hexc("#2C2F36")); ctx.move_to(-5.5, -7.5); ctx.line_to(3.5, -7.5); ctx.line_to(5.5, -5.5); ctx.line_to(5.5, 7.5); ctx.line_to(-5.5, 7.5); ctx.close_path(); ctx.fill()
    for i in range(8):
        setc(ctx, GOLD); ctx.rectangle(-4.6 + i * 1.15, -6.8, 0.7, 2.2); ctx.fill()
    font(ctx, 2.2, True); setc(ctx, PAPER); ctx.move_to(-3.2, 3); ctx.show_text("32GB")
SIZE["sd_card"] = (12, 16)


def wire_set(ctx):
    cols = [WIRE["5V"], WIRE["GND"], WIRE["3V3"], WIRE["I"], WIRE["Q"], WIRE["SCL"], WIRE["BAT"]]
    for i, c in enumerate(cols):
        setc(ctx, c); ctx.set_line_width(1.1)
        y = -6 + i * 2
        ctx.move_to(-14, y); ctx.curve_to(-4, y - 5, 4, y + 5, 14, y); ctx.stroke()
SIZE["wire_set"] = (30, 16)


def pcb_bare(ctx):
    setc(ctx, hexc("#1F5E3A")); rrect(ctx, -35, -45, 70, 90, 1); ctx.fill()
    setc(ctx, PAPER)
    for hx, hy in ((-32, -42), (32, -42), (-32, 42), (32, 42)):
        ctx.arc(hx, hy, 1.6, 0, 2 * math.pi); ctx.fill()
    setc(ctx, hexc("#D9D9D9"))
    for i in range(24):
        for y in (-37.5, -22.3):
            ctx.arc(-29 + i * 2.54, y, 0.7, 0, 2 * math.pi); ctx.fill()
    font(ctx, 3.0, True); setc(ctx, hexc("#FFE680")); ctx.move_to(-16, 10); ctx.show_text("RB BLIPR v1.2")
SIZE["pcb_bare"] = (72, 92)


# ---------------------------------------------------------------- tools
def iron(ctx):
    setc(ctx, hexc("#3A3F47")); rrect(ctx, -22, -3.2, 26, 6.4, 3); ctx.fill()
    setc(ctx, hexc("#2B2F35")); ctx.rectangle(-26, -1.2, 5, 2.4); ctx.fill()
    setc(ctx, SILVER); ctx.rectangle(4, -1.6, 12, 3.2); ctx.fill()
    setc(ctx, hexc("#8A8F96")); ctx.move_to(16, -1.6); ctx.line_to(24, -0.3); ctx.line_to(24, 0.3); ctx.line_to(16, 1.6); ctx.close_path(); ctx.fill()
    setc(ctx, hexc("#D04A2B")); ctx.rectangle(-10, -3.2, 3, 6.4); ctx.fill()
SIZE["iron"] = (52, 8)


def solder(ctx):
    setc(ctx, hexc("#30343B")); ctx.arc(0, 0, 9, 0, 2 * math.pi); ctx.fill()
    setc(ctx, hexc("#B9BEC6")); ctx.arc(0, 0, 7.5, 0, 2 * math.pi); ctx.fill()
    setc(ctx, hexc("#30343B")); ctx.arc(0, 0, 3, 0, 2 * math.pi); ctx.fill()
    setc(ctx, hexc("#B9BEC6")); ctx.set_line_width(0.8); ctx.move_to(7.5, 0); ctx.curve_to(12, 2, 10, 8, 14, 9); ctx.stroke()
SIZE["solder"] = (30, 20)


def flux_pen(ctx):
    setc(ctx, hexc("#E7E1C4")); rrect(ctx, -14, -2.5, 24, 5, 2); ctx.fill()
    setc(ctx, hexc("#C0392B")); rrect(ctx, 8, -2.8, 6, 5.6, 1.5); ctx.fill()
    setc(ctx, hexc("#555")); ctx.move_to(-14, -1); ctx.line_to(-18, 0); ctx.line_to(-14, 1); ctx.close_path(); ctx.fill()
    font(ctx, 2.2, True); setc(ctx, hexc("#7A5C00")); ctx.move_to(-10, 0.8); ctx.show_text("FLUX")
SIZE["flux_pen"] = (34, 7)


def multimeter(ctx, reading="3.30", probes=True):
    setc(ctx, hexc("#F2C230")); rrect(ctx, -11, -17, 22, 34, 3); ctx.fill()
    setc(ctx, hexc("#2C2F36")); rrect(ctx, -9, -15, 18, 30, 2); ctx.fill()
    setc(ctx, hexc("#B8C7B0")); ctx.rectangle(-7, -13, 14, 7); ctx.fill()
    font(ctx, 4.6, True, mono=True); setc(ctx, hexc("#1B1E22")); e = ctx.text_extents(reading); ctx.move_to(6 - e.x_advance, -7.6); ctx.show_text(reading)
    setc(ctx, hexc("#5A5F68")); ctx.arc(0, 3, 5, 0, 2 * math.pi); ctx.fill()
    setc(ctx, PAPER); ctx.set_line_width(0.8); ctx.move_to(0, 3); ctx.line_to(0, -1.5); ctx.stroke()
    setc(ctx, BAD); ctx.arc(4, 12, 1.2, 0, 2 * math.pi); ctx.fill()
    setc(ctx, hexc("#111")); ctx.arc(-4, 12, 1.2, 0, 2 * math.pi); ctx.fill()
    if probes:
        for x, c, ex in ((4, BAD, 15), (-4, hexc("#111"), -15)):
            setc(ctx, c); ctx.set_line_width(0.9); ctx.move_to(x, 12); ctx.curve_to(x, 22, ex, 18, ex, 26); ctx.stroke()
SIZE["multimeter"] = (34, 46)


def cutters(ctx):
    setc(ctx, hexc("#C0392B"))
    for s in (-1, 1):
        ctx.move_to(-18, s * 1.5); ctx.curve_to(-8, s * 6, -2, s * 4, 0, s * 1.2); ctx.line_to(0, s * 0.2); ctx.curve_to(-4, s * 2, -10, s * 3.5, -18, s * 3.5); ctx.close_path(); ctx.fill()
    setc(ctx, hexc("#6B7079")); ctx.move_to(0, -1.4); ctx.curve_to(5, -3, 8, -1, 10, 0); ctx.curve_to(8, 1, 5, 3, 0, 1.4); ctx.close_path(); ctx.fill()
    setc(ctx, hexc("#9AA0A8")); ctx.arc(0, 0, 1.0, 0, 2 * math.pi); ctx.fill()
SIZE["cutters"] = (30, 12)


def strippers(ctx):
    setc(ctx, hexc("#1E63C7"))
    for s in (-1, 1):
        rrect(ctx, -20, s * 2.2 - 1.5, 15, 3, 1.5); ctx.fill()
    setc(ctx, hexc("#6B7079")); ctx.rectangle(-5, -3.6, 18, 7.2); ctx.fill()
    setc(ctx, hexc("#2C2F36"))
    for i in range(5):
        ctx.arc(-1 + i * 3, 0, 0.5 + i * 0.12, 0, 2 * math.pi); ctx.fill()
SIZE["strippers"] = (34, 9)


def tweezers(ctx):
    setc(ctx, hexc("#A9AFB8"))
    for s in (-1, 1):
        ctx.move_to(-16, 0); ctx.line_to(14, s * 1.6); ctx.line_to(14, s * 0.4); ctx.line_to(-16, 0); ctx.close_path(); ctx.fill()
        ctx.move_to(-16, s * 0.2); ctx.line_to(4, s * 2.6); ctx.line_to(4, s * 1.4); ctx.close_path(); ctx.fill()
SIZE["tweezers"] = (32, 7)


def knife(ctx):
    setc(ctx, hexc("#2B2F35")); rrect(ctx, -18, -2, 22, 4, 2); ctx.fill()
    setc(ctx, hexc("#B9BEC6")); ctx.rectangle(4, -1.4, 3, 2.8); ctx.fill()
    setc(ctx, hexc("#D5D9DF")); ctx.move_to(7, -1.2); ctx.line_to(16, 1.2); ctx.line_to(7, 1.2); ctx.close_path(); ctx.fill()
SIZE["knife"] = (36, 6)


def calipers(ctx):
    setc(ctx, hexc("#B9BEC6")); ctx.rectangle(-22, -1.5, 44, 3); ctx.fill()
    setc(ctx, hexc("#9AA0A8")); ctx.move_to(-22, -1.5); ctx.line_to(-22, 9); ctx.line_to(-19, 9); ctx.line_to(-19, -1.5); ctx.fill()
    setc(ctx, hexc("#2C2F36")); rrect(ctx, -8, -5, 14, 9, 1.2); ctx.fill()
    setc(ctx, hexc("#B8C7B0")); ctx.rectangle(-6, -3.6, 10, 4); ctx.fill()
    font(ctx, 3.0, True, mono=True); setc(ctx, hexc("#1B1E22")); ctx.move_to(-5.6, -0.6); ctx.show_text("7.15")
    setc(ctx, hexc("#9AA0A8")); ctx.move_to(-8, 4); ctx.line_to(-8, 9); ctx.line_to(-11, 9); ctx.line_to(-11, 1.5); ctx.close_path(); ctx.fill()
SIZE["calipers"] = (46, 16)


def ipa(ctx):
    setc(ctx, hexc("#E9F1FB")); rrect(ctx, -6, -10, 12, 20, 2); ctx.fill()
    setc(ctx, hexc("#2F6DB5")); ctx.rectangle(-6, -2, 12, 6); ctx.fill()
    setc(ctx, hexc("#2C2F36")); ctx.rectangle(-2.5, -14, 5, 4); ctx.fill()
    font(ctx, 2.6, True); setc(ctx, PAPER); ctx.move_to(-3.4, 2.0); ctx.show_text("IPA")
    setc(ctx, hexc("#5AA9E6")); rrect(ctx, 9, -10, 3, 20, 1.4); ctx.fill()
    setc(ctx, hexc("#F4F4F4")); ctx.rectangle(8.2, -10, 4.6, 5); ctx.fill()
SIZE["ipa"] = (28, 30)


def insert_tip(ctx):
    iron(ctx)
    setc(ctx, BRASS); ctx.rectangle(22.5, -1.8, 4, 3.6); ctx.fill()
SIZE["insert_tip"] = (56, 8)


def screwdriver(ctx):
    setc(ctx, hexc("#D04A2B")); rrect(ctx, -18, -3, 14, 6, 2.5); ctx.fill()
    setc(ctx, hexc("#B9BEC6")); ctx.rectangle(-4, -0.9, 18, 1.8); ctx.fill()
    ctx.move_to(14, -0.9); ctx.line_to(17, 0); ctx.line_to(14, 0.9); ctx.close_path(); ctx.fill()
SIZE["screwdriver"] = (36, 7)


def heatshrink(ctx):
    for i, c in enumerate(["#1B1B1B", "#D7263D", "#1F6FC0"]):
        setc(ctx, hexc(c)); rrect(ctx, -12, -5 + i * 4, 24, 2.6, 1.2); ctx.fill()
SIZE["heatshrink"] = (26, 12)
