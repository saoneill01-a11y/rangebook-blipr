"""Every scene of the BLIPR assembly video: narration, side notes and visuals."""
import os as _os
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".."))
BUILD = _os.environ.get("BLIPR_VIDEO_BUILD", _os.path.join(REPO, "tools", "video", "build"))
TTS = _os.environ.get("BLIPR_VIDEO_TTS", _os.path.join(BUILD, "tts"))
from engine import Scene
from draw import *
import cairo
from vis import image_view, board_view, seq_view, items_view, split, switch, drawing, card
import diagrams as DG
import parts as PT
from board import Board, D

B = Board()
PIC = REPO + "/pictures/out/"
CASE = REPO + "/case/out/"
PCB = REPO + "/pcb/out/"
FULL = (35, 45, 158)          # whole board in view
FULLS = (35, 45, 132)         # whole board, in a split view

R_BY_VALUE = [("10 Ω", ["R1", "R18"]), ("100 Ω", ["R22"]), ("330 Ω", ["R10", "R17"]), ("470 Ω", ["R6", "R9", "R13", "R16"]),
              ("1 kΩ", ["R23", "R24"]), ("4.7 kΩ", ["R4", "R7", "R11", "R14", "R21"]),
              ("10 kΩ", ["R2", "R3", "R5", "R8", "R12", "R15"]), ("100 kΩ", ["R19", "R20"])]
ALL_R = [r for _, rs in R_BY_VALUE for r in rs]
CER = [("1 µF (105)", ["C1", "C2", "C14", "C17", "C21", "C24", "C28", "C30"]), ("100 nF (104)", ["C5", "C8", "C9", "C11", "C26"]),
       ("10 nF (103)", ["C12", "C15", "C19", "C22"]), ("1 nF (102)", ["C18", "C25"])]
ALL_CER = [r for _, rs in CER for r in rs]
ELEC = ["C3", "C4", "C7", "C10", "C27", "C29", "L1", "L2"]   # electrolytics, then the inductors (board v1.2)
HDRS = ["J1", "J2", "J3", "J4"]

DONE_R = [(0, -100, ALL_R + ["D1"], 0)]
DONE_C = DONE_R + [(0, -100, ALL_CER, 0)]
DONE_SOCK = [(0, -100, "U1"), (0, -100, "U2")]
DONE_U3 = DONE_C + [(0, -100, ["U3"], 0)]
DONE_E = DONE_U3 + [(0, -100, ELEC, 0)]
DONE_H = DONE_E + [(0, -100, HDRS, 0)]
DONE_FH = [(0, -100, "U4"), (0, -100, "U5")]

SC = []


def add(*a, **k):
    s = Scene(*a, **k)
    SC.append(s)
    return s


def wsize(*a):
    return None


# ================================================================== 1. WELCOME
add("intro_title", "intro", "Range Book BLIPR", [
    "This is BLIPR, a radar chronograph you build yourself.",
    "In this video we'll build it together, one small step at a time.",
], visual=drawing(lambda ctx, c, x, y, w, h: DG.title(ctx, c, x, y, w, h, hero=REPO + "/docs/img/blipr_front.jpg")), full=True, tail=0.8)

add("intro_what", "intro", "What BLIPR does", [
    "BLIPR sits on the bench beside your rifle, a little behind the muzzle.",
    "When you fire, its radar watches the bullet leave, and works out how fast it's going.",
    "The speed shows up on its little screen, and on your phone in Range Book, over Bluetooth.",
    "Nothing goes downrange. There's nothing to shoot through.",
], visual=drawing(lambda ctx, c, x, y, w, h: DG.bench(ctx, c, x, y, w, h, shot_line=1)), full=True)

add("intro_inside", "intro", "How it works inside", [
    "Inside, five parts pass the signal along.",
    "The radar sees the bullet. A small amplifier makes that signal about five hundred times stronger.",
    "A Teensy computer measures the speed, and a tiny ESP32 board runs the screen and Bluetooth.",
], visual=drawing(DG.signal), full=True)

EXP_LABELS = [
    (0, "Sensor pod roof", (559, 74), "r"), (0, "Sensor pod", (540, 194), "r"), (0, "Lid with screen window", (560, 420), "r"),
    (1, "Screen (OLED)", (871, 425), "l"), (1, "Teensy 4.1", (860, 540), "l"), (1, "Main circuit board", (760, 620), "l"),
    (2, "Battery holder + 18650 cell", (560, 540), "r"), (2, "Radar module", (433, 672), "r"), (2, "Front window cover", (325, 742), "r"),
    (3, "Base", (900, 760), "l"),
]


def exp_overlays():
    out = []
    for li, s, (u, v), side in EXP_LABELS:
        out.append({"at": li + 1, "kind": "fn", "fn": (lambda s_, u_, v_, side_: lambda ctx, c, P, k, tt: _leader(ctx, P, s_, u_, v_, side_, k))(s, u, v, side)})
    return out


def _leader(ctx, P, s, u, v, side, k):
    x, y = P(u, v)
    lx = x - 170 if side == "r" else x + 170
    setc(ctx, INK, k); ctx.set_line_width(2.5); ctx.move_to(x, y); ctx.line_to(lx, y - 20); ctx.stroke()
    DG.dot(ctx, x, y, 6, INK)
    tag(ctx, s, lx, y - 20, 24, PAPER, INK, k, "r" if side == "r" else "l")


add("intro_parts", "intro", "All the major parts", [
    "Here are all the major parts, pulled apart so you can see them.",
    "On top, the sensor pod, the lid, and the screen that sits under the lid's window.",
    "Inside, the Teensy rides on the main circuit board.",
    "On the left is the battery holder. At the front, the radar sits behind a thin printed window.",
    "Everything goes into this printed base.",
], visual=seq_view("explode", [(0, 0.5, 0, 71, 3.5)], overlays=exp_overlays()), full=True, holds={4: 1.0})

add("intro_plan", "intro", "The plan", [
    "We'll work in this order.",
    "First the circuit board, with a power check after each stage.",
    "Then the wiring, the firmware, and the case.",
    "Last, the first power-up, and your first shot.",
    "Take your time. Pause the video whenever you need to. Nothing here is a race.",
], visual=drawing(lambda ctx, c, x, y, w, h: _plan(ctx, c, x, y, w, h)), full=True)

PLAN = [("1", "Circuit board", "solder parts, lowest first"), ("2", "Power checks", "multimeter at each stage"),
        ("3", "Wiring", "battery, radar, screen"), ("4", "Firmware", "load both boards"),
        ("5", "The case", "inserts, radar, lid"), ("6", "Sensor pod", "optional"), ("7", "First test", "power-up and first shot")]


def _plan(ctx, c, x, y, w, h):
    n = len(PLAN)
    gw = (w - 40 - (n - 1) * 16) / n
    for i, (num, a, b) in enumerate(PLAN):
        li = 1 if i < 2 else (2 if i < 6 else 3)
        k = ramp(c.t, c.at(li) + (i - {1: 0, 2: 2, 3: 6}[li]) * 0.4, 0.5)
        if k <= 0:
            continue
        bx = x + 20 + i * (gw + 16)
        ctx.push_group()
        card(ctx, bx, y + 200, gw, 330)
        col = list(CHAPTER_COL.values())[4 + (i if i < 7 else 0) % 8]
        setc(ctx, col); ctx.arc(bx + gw / 2, y + 290, 46, 0, 6.29); ctx.fill()
        text(ctx, num, bx + gw / 2, y + 306, 46, PAPER, True, "c")
        text(ctx, a, bx + gw / 2, y + 400, 30, INK, True, "c")
        para(ctx, b, bx + gw / 2, y + 446, gw - 30, 24, INK2, anchor="c")
        ctx.pop_group_to_source(); ctx.paint_with_alpha(k)
        if i < n - 1:
            arrow(ctx, bx + gw + 1, y + 365, bx + gw + 15, y + 365, INK2, 3, 10, k)


# ================================================================== 2. WHAT YOU NEED
add("kit_modules", "kit", "Parts: the big pieces", [
    "Let's lay out everything you need. Start with the big pieces.",
    "The main circuit board, version one point two. The RFbeam K-LC5 radar. Order the dash zero zero C version, which runs on three point three volts.",
    "A Teensy 4.1 with pins, and an ESP32-C3 SuperMini. Buy a pack of those: a spare is worth having.",
    "A 0.96 inch SSD1306 I2C OLED screen with four pins, the 18650 battery holder, a button-top 18650 cell, and a microSD card. A name-brand thirty-two gigabyte A1 card works well.",
], visual=items_view([
    (PT.pcb_bare, {}, "pcb_bare", "Main board v1.2", "PCBWay, through-hole"),
    (PT.radar, {"side": "front"}, "radar", "Radar K-LC5-RFB-00C", "3.3 V version"),
    (PT.teensy, {}, "teensy", "Teensy 4.1", "with pins"),
    (PT.esp32, {}, "esp32", "ESP32-C3 SuperMini", "buy a pack: spares"),
    (PT.oled, {}, "oled", "0.96\" OLED", "SSD1306, I2C, 4 pads"),
    (PT.battery_holder, {"with_cell": False}, "battery_holder", "18650 battery holder", "5 V out, own button"),
    (PT.cell, {}, "cell", "18650 cell", "name brand, button top"),
    (PT.sd_card, {}, "sd_card", "microSD card", "32 GB A1, in the Teensy"),
], cols=4, line_map=[1, 1, 2, 2, 3, 3, 3, 3]), full=True)

add("kit_small", "kit", "Parts: the small pieces", [
    "Next, the small parts. Everything solders into its own labelled holes.",
    "Resistors and ceramic capacitors from assortment kits, and four small electrolytic capacitors.",
    "Two MCP6022-E/P amplifier chips with two eight-pin sockets, an MCP1700-3302E regulator, the three point three volt version, and a 1N5817 diode.",
    "Female headers: two strips of twenty-four for the Teensy, two of eight for the ESP32, a one-by-five for the radar, and a one-by-four for J4.",
], visual=items_view([
    (PT.resistor, {"value": "4.7k"}, "resistor", "Resistors, 1/4 W", "24 on the board, +1 (R25) at the battery"),
    (PT.ceramic, {"code": "104"}, "ceramic", "Ceramic capacitors", "19: 1 µF, 100 nF, 10 nF, 1 nF"),
    (PT.electrolytic_side, {}, "electrolytic_side", "Electrolytic capacitors", "3 × 10 µF, 1 × 100 µF (6.3 mm wide)"),
    (PT.opamp_chip, {}, "esp32", "MCP6022-E/P × 2", "plus 2 DIP-8 sockets"),
    (PT.to92, {}, "to92", "MCP1700-3302E", "3.3 V version, TO-92"),
    (PT.diode, {}, "diode", "1N5817 diode", "stripe = cathode"),
    (PT.header_male, {"n": 4}, "esp32", "Male headers", "optional, for J1"),
    (PT.header_female, {"n": 8}, "teensy", "Female headers", "2×24, 2×8, 1×5, 1×4"),
], cols=4, line_map=[1, 1, 1, 2, 2, 2, 3, 3]), full=True)

add("kit_filters", "kit", "Parts: the two 5 V filters", [
    "Six more small parts make two noise filters, and on this board they solder straight on, like everything else.",
    "Two twenty-two microhenry inductors, rated one amp or more: the round drum type, up to eight point four millimetres across.",
    "Two four hundred and seventy microfarad electrolytic capacitors, ten volts or more, eight millimetres across. And two more one microfarad ceramics.",
    "Without them, the battery holder's converter and the ESP32's radio both whisper into the radar through the five volt supply.",
    "Building on an older version one point one board? Those filters go in the wires instead. The build guide's section, If you have a v1.1 board, shows how.",
], visual=items_view([
    (PT.inductor, {}, "inductor", "Inductor 22 µH × 2", "L1, L2 · 1 A or more"),
    (PT.electrolytic_side, {"d": 8, "h": 12}, "electrolytic_side", "470 µF × 2", "C27, C29 · 8 mm across"),
    (PT.ceramic, {"code": "105"}, "ceramic", "1 µF ceramic × 2", "C28, C30"),
    (PT.pcb_bare, {}, "pcb_bare", "All on board v1.2", "v1.1: see the build guide"),
], cols=4, line_map=[1, 2, 2, 4]), full=True)

add("kit_hardware", "kit", "Parts: case hardware", [
    "For the case: the printed parts, eight M3 heat-set inserts, and one quarter-twenty insert for a tripod, nine millimetres long or shorter.",
    "Screws: four M3 by eight for the lid, four M3 by six for the board, and four M3 by six self-tapping screws for the battery holder.",
    "Four tiny M2 by four screws hold the screen. And about fifteen centimetres of one millimetre foam tape holds the radar snug.",
    "Plus hookup wire in several colours, and some heat-shrink tube.",
], visual=items_view([
    (PT.insert, {}, "insert", "M3 heat-set inserts × 8", "+2 more for the sensor pod"),
    (PT.insert, {"d": 7.5, "L": 9}, "insert", "1/4-20 insert × 1", "9 mm long or shorter"),
    (PT.screw, {"L": 8}, "screw", "M3 screws", "4 × 8 mm, 4 × 6 mm"),
    (PT.screw, {"L": 6}, "screw", "M3 × 6 self-tapping × 4", "battery holder"),
    (PT.screw, {"L": 4, "d": 2}, "screw", "M2 × 4 × 4", "screen"),
    (PT.foam_tape, {}, "foam_tape", "Foam tape 1 × 5 mm", "about 150 mm"),
    (PT.wire_set, {}, "wire_set", "26 AWG stranded wire", "several colours"),
    (PT.heatshrink, {}, "heatshrink", "Heat-shrink tube", "small sizes"),
], cols=4, line_map=[0, 0, 1, 1, 2, 2, 3, 3]), full=True)

add("kit_tools", "kit", "Tools", [
    "Now the tools. A temperature-controlled soldering iron with a fine chisel tip, set around three hundred and thirty degrees.",
    "Thin rosin-core solder, and a flux pen.",
    "A multimeter with DC volts and a continuity beep. You'll use it at every checkpoint.",
    "Flush cutters, wire strippers, tweezers, a hobby knife, and digital calipers.",
    "A small screwdriver for your screws, and isopropyl alcohol with an old toothbrush to clean off flux.",
], visual=items_view([
    (PT.iron, {}, "iron", "Soldering iron", "about 330 °C"),
    (PT.solder, {}, "solder", "Solder 0.6–0.8 mm", "rosin core"),
    (PT.flux_pen, {}, "flux_pen", "Flux pen", ""),
    (PT.multimeter, {}, "multimeter", "Multimeter", "DC volts + beep"),
    (PT.cutters, {}, "cutters", "Flush cutters", ""),
    (PT.strippers, {}, "strippers", "Wire strippers", "26 AWG"),
    (PT.tweezers, {}, "tweezers", "Tweezers", ""),
    (PT.knife, {}, "knife", "Hobby knife", ""),
    (PT.calipers, {}, "calipers", "Digital calipers", ""),
    (PT.screwdriver, {}, "screwdriver", "Small screwdriver", "to suit your screws"),
    (PT.insert_tip, {}, "insert_tip", "Insert tip (or iron)", "for heat-set inserts"),
    (PT.ipa, {}, "ipa", "Isopropyl + toothbrush", "flux cleanup"),
], cols=6, line_map=[0, 1, 1, 2, 3, 3, 3, 3, 3, 4, 4, 4]), full=True)

add("kit_sensors", "kit", "Optional: sensor kit", [
    "The sensor pod is optional. BLIPR works the same without it.",
    "If you want it: an Adafruit SHT45 for temperature and humidity, and a DFRobot ten-degree-of-freedom board for compass, level and air pressure.",
    "Two STEMMA QT to male-pins cables, two more M3 inserts with two M3 by eight screws for the pod, and brass screws for the boards. Brass, not steel, because steel upsets the compass.",
], visual=items_view([
    (PT.stemma_board, {"label": "SHT45"}, "stemma_board", "Adafruit SHT45", "temp + humidity"),
    (PT.dfrobot, {}, "dfrobot", "DFRobot SEN0696", "compass, level, pressure"),
    (PT.qt_cable, {}, "qt_cable", "STEMMA QT to pins × 2", "Adafruit 4209, 150 mm"),
    (PT.screw, {"L": 6, "d": 2.5}, "screw", "Brass M2.5×6 × 8, M3×6 × 2", "+ 2 M3 inserts, 2 M3×8"),
], cols=4, line_map=[1, 1, 2, 2]), full=True)

# ================================================================== 3. SAFETY
add("safety", "safety", "Safety first", [
    "Four safety points before we start.",
    "The battery. Use a name-brand cell. Never short it, never solder to the cell itself, and keep it out of the holder until a checkpoint asks for it.",
    "The radar is sensitive to static. Touch something grounded first, hold it by the edges, and never solder to its pins.",
    "Soldering. The iron is hot enough to burn instantly. Work in fresh air, and wash your hands after handling solder.",
    "And the radar transmits whenever it has power. It's very low power, but don't stare into the antenna, and switch it off when you're done.",
], visual=drawing(lambda ctx, c, x, y, w, h: DG.safety(ctx, c, x + 20, y + 20, w - 40, h - 40, cards=[
    (1, "18650 battery", "Name-brand cell only. Never short it or solder to it. Out of the holder until a checkpoint asks for it."),
    (2, "Static", "Touch grounded metal before you handle the radar. Hold it by the edges. Never solder to its pins."),
    (3, "Hot iron", "Around 330 °C. Fresh air, a stand for the iron, and wash your hands after soldering."),
    (4, "Radio transmitter", "The radar transmits whenever it has power. Don't put your eye to it. Switch BLIPR off when you're done."),
]), PAPER), full=True)

# ================================================================== 4. GET READY
add("prep_sort", "prep", "Sort and check the parts", [
    "Start by sorting the parts.",
    "Resistors look alike, so match the colour bands to this chart, and check each one with your meter before it goes in.",
    "Ceramic capacitors carry a three-digit code. One oh four is a hundred nanofarads. One oh five is one microfarad.",
    "Bag them by value and write the value on each bag.",
], visual=image_view(PIC + "10_part_id.png", cams=[(0, (0, 0, 1673, 1070)), (1, (0, 60, 1000, 760)), (2, (1040, 170, 540, 360)), (3, (0, 0, 1673, 1070))],
                     overlays=[{"at": 2, "kind": "box", "xywh": (1085, 215, 450, 275), "until": 3}]),
    notes=[(1, "Measure every resistor before it goes in"), (2, "102 = 1 nF · 103 = 10 nF"), (2, "104 = 100 nF · 105 = 1 µF")],
    pause=5, do="Pause and sort your parts")

add("prep_teensy", "prep", "Cut the Teensy's VIN–VUSB trace", [
    "One job on the Teensy before it goes anywhere near the board.",
    "Turn it over. Near the USB connector are two pads, VIN and VUSB, joined by a thin trace.",
    "Cut that trace with a hobby knife. A few light strokes, not one hard one.",
    "Then check with the beep test. No beep between VIN and VUSB means it's cut.",
    "This keeps the battery and your computer's USB from fighting. From now on, the Teensy only runs when BLIPR is switched on, even when you program it.",
    "If you'd like to try the Firmware tab's bench tests on USB first, do them before you cut.",
], visual=drawing(DG.teensy_cut),
    notes=[(1, "Pads are on the underside, by the USB end"), (2, "Light strokes; don't nick nearby traces"), (3, "*No beep between VIN and VUSB = done"),
           (4, "To program it later, turn BLIPR on"), (5, "Bench tests on USB alone? Do them before the cut")], pause=6, do="Pause and cut the trace")

# ================================================================== 5. CIRCUIT BOARD
add("board_tour", "board", "Meet the board", [
    "This is the main board, seen from the top. The front edge, at the bottom here, faces the radar.",
    "Every part has its own outline and label printed on the board.",
    "The amplifier sits in the middle: two rows of parts and two chip sockets.",
    "The Teensy plugs in along the back. The ESP32 plugs into the front-left corner.",
    "We'll solder the lowest parts first, so the board sits flat on the bench while you work.",
], visual=board_view(B, [(0, FULL), (2, (42, 43, 70)), (3, FULL)],
                     overlays=[{"at": 0, "kind": "tag", "xy": (35, 5), "text": "FRONT EDGE · radar side", "anchor": "c", "until": 1},
                               {"at": 3, "kind": "box", "xywh": (6.5, 66, 63, 18), "until": 4},
                               {"at": 3, "kind": "box", "xywh": (7, 0.5, 20, 23), "delay": 1.5, "until": 4}]),
    notes=[(0, "Front edge = radar side"), (4, "*Order: resistors, diode, ceramics, sockets, regulator, electrolytics, inductors, headers")])

add("board_howto", "board", "How to solder a through-hole part", [
    "If you're new to soldering, here's the whole technique.",
    "Bend the leads, push the part through from the top, and spread the leads a little underneath so it stays put.",
    "Touch the iron to the pad and the lead together for a second, then feed in solder until it flows around the lead.",
    "A good joint is shiny and shaped like a little volcano. Then trim the lead flush with the cutters.",
], visual=drawing(lambda ctx, c, x, y, w, h: _howto(ctx, c, x, y, w, h)),
    notes=[(2, "Heat pad + lead together, 1–2 s"), (2, "Feed solder into the joint, not the iron"), (3, "*Shiny volcano = good joint"), (3, "Trim leads flush")])


def _howto(ctx, c, x, y, w, h):
    gw = (w - 60) / 3
    for i in range(3):
        bx = x + 20 + i * (gw + 10)
        k = ramp(c.t, c.at(i + 1), 0.5)
        if k <= 0:
            continue
        ctx.push_group()
        setc(ctx, hexc("#F3F5F8")); rrect(ctx, bx, y + 30, gw, h - 60, 16); ctx.fill()
        cx, cy = bx + gw / 2, y + h / 2 + 40
        # board cross-section
        setc(ctx, hexc("#1F5E3A")); ctx.rectangle(bx + 40, cy - 30, gw - 80, 30); ctx.fill()
        setc(ctx, hexc("#C8B27A")); ctx.rectangle(cx - 30, cy, 60, 8); ctx.fill(); ctx.rectangle(cx - 30, cy - 38, 60, 8); ctx.fill()
        setc(ctx, PT.LEAD); ctx.set_line_width(6)
        ctx.move_to(cx, cy - 160); ctx.line_to(cx, cy + (90 if i < 2 else 14)); ctx.stroke()
        ctx.save(); ctx.translate(cx, cy - 190); ctx.scale(9, 9); ctx.rotate(1.5708); PT.resistor(ctx, "10k", lead=0.5); ctx.restore()
        if i == 0:
            arrow(ctx, cx + 80, cy - 220, cx + 30, cy - 120, FOCUS, 5, 18)
            text(ctx, "1  Push through", cx, y + 90, 28, INK, True, "c")
        if i == 1:
            P = lambda: None
            ctx.save(); ctx.translate(cx + 90, cy + 70); ctx.rotate(-2.4); ctx.scale(8, 8); PT.iron(ctx); ctx.restore()
            setc(ctx, hexc("#B9BEC6")); ctx.set_line_width(5); ctx.move_to(cx - 120, cy + 120); ctx.line_to(cx - 12, cy + 30); ctx.stroke()
            text(ctx, "2  Heat both, add solder", cx, y + 90, 28, INK, True, "c")
        if i == 2:
            setc(ctx, hexc("#C9CED6")); ctx.move_to(cx - 32, cy + 8); ctx.curve_to(cx - 20, cy + 10, cx - 6, cy + 26, cx - 4, cy + 40)
            ctx.line_to(cx + 4, cy + 40); ctx.curve_to(cx + 6, cy + 26, cx + 20, cy + 10, cx + 32, cy + 8); ctx.close_path(); ctx.fill()
            text(ctx, "3  Shiny cone, trim", cx, y + 90, 28, INK, True, "c")
            check(ctx, cx + 90, cy + 50, 54)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(k)


def r_group_scene(sid, title_s, groups, lines, cam, notes, extra_over=None, step=None):
    place = list(DONE_R[:0])
    return add(sid, "board", title_s, lines,
               visual=board_view(B, cam, place=groups, overlays=extra_over or []), notes=notes, pause=6, do="Pause and solder these")


add("board_r1", "board", "Resistors, part 1: the amplifier", [
    "First, the resistors in the amplifier rows. The values are printed beside every outline.",
    "Four point seven k: R4, R7, R11 and R14. Yellow, violet, red.",
    "Four seventy ohm: R6, R9, R13 and R16. Yellow, violet, brown.",
    "Ten k: R2, R3, R5, R8, R12 and R15. Brown, black, orange.",
    "And three thirty ohm: R10 and R17. Orange, orange, brown. Resistors can go in either way round.",
], visual=board_view(B, [(0, (42, 43, 72)), (3, (40, 38, 84)), (4, (42, 43, 72))],
                     place=[(1, 0.6, ["R4", "R7", "R11", "R14"], 0.35), (2, 0.6, ["R6", "R9", "R13", "R16"], 0.35),
                            (3, 0.6, ["R2", "R3", "R5", "R8", "R12", "R15"], 0.3), (4, 0.6, ["R10", "R17"], 0.35)]),
    notes=[(1, "4.7 kΩ: R4 R7 R11 R14"), (2, "470 Ω: R6 R9 R13 R16"), (3, "10 kΩ: R2 R3 R5 R8 R12 R15"), (4, "330 Ω: R10 R17"),
           (4, "Resistors have no direction")], pause=6, do="Pause and solder these resistors")

add("board_r2", "board", "Resistors, part 2: power and the left side", [
    "Now the rest of the resistors.",
    "Ten ohm: R1 and R18, in the power area at the front. Brown, black, black.",
    "One hundred k: R19 and R20, for the battery gauge. Brown, black, yellow.",
    "One k: R23 and R24, at the front-left corner. Brown, black, red. These two stand on end: bend one leg back down beside the body, and stand the resistor over the hole inside its drawn square.",
    "R21, four point seven k, and R22, one hundred ohm, were for an ammo probe BLIPR no longer uses. Fit them anyway. They do no harm.",
], visual=board_view(B, [(0, FULL), (1, (48, 12, 60)), (2, (15, 38, 50)), (3, (21, 31, 34)), (4, (15, 42, 50))],
                     place=DONE_R[:0] + [(0, -100, ["R4", "R7", "R11", "R14", "R6", "R9", "R13", "R16", "R2", "R3", "R5", "R8", "R12", "R15", "R10", "R17"], 0),
                                         (1, 0.8, ["R1", "R18"], 0.4), (2, 0.8, ["R19", "R20"], 0.4), (3, 0.8, ["R23", "R24"], 0.4), (4, 1.0, ["R21", "R22"], 0.4)]),
    notes=[(1, "10 Ω: R1 R18"), (2, "100 kΩ: R19 R20"), (3, "1 kΩ: R23 R24, standing on end"), (4, "4.7 kΩ: R21 · 100 Ω: R22")],
    pause=6, do="Pause and solder these resistors")

add("board_d1", "board", "The diode, D1", [
    "Next, the diode, D1. Unlike a resistor, it only works one way round.",
    "Its body has a silver stripe at one end. That stripe goes to the right, on the square pad.",
    "The outline on the board shows the stripe too. Match them up, then solder it.",
], visual=split(board_view(B, [(0, (17, 25, 34))], place=[(0, -100, ALL_R, 0), (1, 0.8, ["D1"], 0)],
                           overlays=[{"at": 1, "kind": "ring", "xy": (21.88, 24.8), "r": 34}, {"at": 1, "kind": "tag", "xy": (2, 29.5), "text": "stripe → square pad", "delay": 0.6}]),
                drawing(lambda ctx, c, x, y, w, h: (DG.P(ctx, PT.diode, x + w / 2, y + h / 2 - 40, 26),
                                                    text(ctx, "stripe = cathode", x + w / 2 + 50, y + h / 2 + 60, 26, INK, True, "c"),
                                                    arrow(ctx, x + w / 2 + 80, y + h / 2 + 30, x + w / 2 + 56, y + h / 2 - 20, FOCUS, 5, 18))), weights=[1.5, 1]),
    notes=[(1, "!Stripe to the RIGHT, on the square pad")], pause=5, do="Pause and solder D1")

add("board_cer", "board", "Ceramic capacitors", [
    "Now the small ceramic capacitors. These have no direction.",
    "One microfarad, code one oh five: C1, C2, C14, C17, C21 and C24, plus C28 and C30 up by the filters.",
    "One hundred nanofarad, code one oh four: C5, C8, C9, C11 and C26.",
    "Ten nanofarad, code one oh three: C12, C15, C19 and C22.",
    "And one nanofarad, code one oh two: C18 and C25.",
], visual=board_view(B, [(0, FULL)],
                     place=[(0, -100, ALL_R + ["D1"], 0)] + [(i + 1, 0.8, refs, 0.3) for i, (_, refs) in enumerate(CER)]),
    notes=[(1, "1 µF (105): C1 C2 C14 C17 C21 C24 C28 C30"), (2, "100 nF (104): C5 C8 C9 C11 C26"), (3, "10 nF (103): C12 C15 C19 C22"),
           (4, "1 nF (102): C18 C25")], pause=6, do="Pause and solder the ceramics")

add("board_sockets", "board", "The two chip sockets", [
    "Next, the two eight-pin sockets for the amplifier chips. Solder the sockets now. The chips go in later.",
    "Each socket has a notch at one end. Line it up with the notch drawn on the board. On this board both notches point to the right.",
    "Solder two opposite corner pins first, check the socket sits flat, then do the rest.",
], visual=board_view(B, [(0, (46, 43, 60)), (1, (46, 43, 40))], place=[(0, -100, ALL_R + ["D1"] + ALL_CER, 0)],
                     sockets=[(0, 1.0, "U1"), (0, 1.4, "U2")],
                     overlays=[{"at": 1, "kind": "ring", "xy": (41.0, 43), "r": 26}, {"at": 1, "kind": "ring", "xy": (61.0, 43), "r": 26, "delay": 0.3},
                               {"at": 1, "kind": "tag", "xy": (36, 50.5), "text": "notch matches the drawing", "anchor": "c", "delay": 0.6}]),
    notes=[(0, "Sockets only; chips go in after the power test"), (1, "!Notch matches the board drawing"), (1, "Both notches point RIGHT"), (2, "Two corners first, check flat, then the rest")],
    pause=5, do="Pause and solder the sockets")

add("board_u3", "board", "The regulator, U3", [
    "Now U3, the little three-legged regulator. It makes clean three point three volts for the radar.",
    "Its flat, printed face goes toward the board's front edge.",
    "Its legs are closer together than the holes, so spread the two outer legs a little before you push it in.",
    "If it goes in backwards, it gets five volts the wrong way, so double-check before you solder.",
], visual=switch([(0, board_view(B, [(0, (45, 12, 46))], place=[(0, -100, ALL_R + ["D1"] + ALL_CER, 0), (1, 0.5, ["U3"], 0)], sockets=DONE_SOCK,
                                       overlays=[{"at": 1, "kind": "ring", "xy": (42, 11.5), "r": 46}, {"at": 1, "kind": "arrow", "from": (42, 4.5), "to": (42, 8.2), "delay": 0.5}])),
                  (3, drawing(lambda ctx, c, x, y, w, h: DG.compare(ctx, c, x, y, w, h, DG.u3_panel(True), DG.u3_panel(False), line=3)))]),
    notes=[(1, "*Flat face → front edge"), (1, "Legs: GND · IN · OUT, left to right"), (2, "Spread the outer legs slightly")], pause=5, do="Pause and solder U3")

add("board_elec", "board", "Electrolytic capacitors", [
    "The six electrolytic capacitors are polarised. They only go in one way.",
    "The long leg is plus, and it goes in the square pad. The stripe on the can marks the minus side.",
    "Ten microfarad: C4, C7 and C10. One hundred microfarad: C3.",
    "Then the two big ones for the filters, four hundred and seventy microfarads: C27 and C29, in the top-left corner beside J1. Same rule: plus leg in the square pad.",
    "Check every one before you solder. A capacitor in backwards can swell or pop.",
], visual=switch([(0, drawing(lambda ctx, c, x, y, w, h: DG.compare(ctx, c, x, y, w, h, DG.elec_panel(True), DG.elec_panel(False), line=0, line2=1))),
                  (2, board_view(B, [(2, (48, 11, 50)), (3, (16, 57, 34))],
                                 place=[(0, -100, ALL_R + ["D1"] + ALL_CER + ["U3"], 0), (2, 0.6, ["C4", "C7", "C10"], 0.4), (2, 2.4, ["C3"], 0),
                                        (3, 1.2, ["C27", "C29"], 0.5)],
                                 sockets=DONE_SOCK)),
                  (4, drawing(lambda ctx, c, x, y, w, h: DG.compare(ctx, c, x, y, w, h, DG.elec_panel(True), DG.elec_panel(False), line=0, line2=0)))]),
    notes=[(1, "*Long leg (+) → square pad"), (1, "Stripe = minus"), (2, "10 µF: C4 C7 C10 · 100 µF: C3"), (3, "470 µF: C27 C29, top left")],
    pause=5, do="Pause and solder the electrolytics")

add("board_inductors", "board", "The inductors, L1 and L2", [
    "Next, the two inductors, L1 and L2, beside the big capacitors. They're the heart of the two noise filters.",
    "They have no direction: either way round is fine.",
    "Each one has three holes in a row. The two outer holes are five millimetres apart. The left and middle holes are three point two millimetres apart, for the smaller drums.",
    "Use whichever pair fits your inductor's legs. The third hole stays empty. Push it down flat, and solder.",
], visual=board_view(B, [(0, (16, 57, 34)), (2, (12, 57, 26)), (3, (16, 57, 34))],
                     place=[(0, -100, ALL_R + ["D1"] + ALL_CER + ["U3", "C3", "C4", "C7", "C10", "C27", "C29"], 0), (3, 1.0, ["L1", "L2"], 0.5)],
                     sockets=DONE_SOCK,
                     overlays=[{"at": 2, "kind": "ring", "xy": (7.9, 61.6), "r": 26, "until": 3}, {"at": 2, "kind": "ring", "xy": (12.9, 61.6), "r": 26, "until": 3},
                               {"at": 2, "kind": "tag", "xy": (10.4, 58.8), "text": "outer pair: 5 mm", "anchor": "c", "until": 3},
                               {"at": 2, "kind": "ring", "xy": (7.9, 52.5), "r": 26, "delay": 1.2, "until": 3}, {"at": 2, "kind": "ring", "xy": (11.1, 52.5), "r": 26, "delay": 1.2, "until": 3},
                               {"at": 2, "kind": "tag", "xy": (10.4, 49.9), "text": "left + middle: 3.2 mm", "anchor": "c", "delay": 1.2, "until": 3}]),
    notes=[(0, "L1, L2: 22 µH, 1 A or more"), (1, "Either way round"), (2, "Three holes: 5 mm or 3.2 mm apart"), (3, "*Use the pair that fits; push down flat")],
    pause=5, do="Pause and solder L1 and L2")

add("board_headers", "board", "Headers J1 to J4", [
    "Next, the connectors along the left side and the front.",
    "J1 is power, J2 the radar, J3 the screen, and J4 the sensor kit. J5 stays empty.",
    "For J1, J2 and J3, you can solder the wires straight into the holes later. We'll do that. It's the simplest, and nothing can wiggle loose.",
    "For J4, solder a one-by-four female header, so the sensor cable can plug in.",
], visual=board_view(B, [(0, (22, 42, 92)), (1, FULL), (3, (12, 38, 46))], place=[(0, -100, ALL_R + ["D1"] + ALL_CER + ["U3"] + ELEC, 0), (3, 0.8, ["J4"], 0)], sockets=DONE_SOCK,
                     overlays=[{"at": 1, "kind": "box", "xywh": (2.5, 58.5, 4, 9)}, {"at": 1, "kind": "box", "xywh": (26, 2.5, 13, 5), "delay": 0.4},
                               {"at": 1, "kind": "box", "xywh": (1, 39.5, 4, 11), "delay": 0.8}, {"at": 1, "kind": "box", "xywh": (1, 27.5, 4, 11), "delay": 1.2},
                               {"at": 3, "kind": "tag", "xy": (6, 27.2), "text": "J4: 1×4 female header"}]),
    notes=[(1, "J1 power · J2 radar · J3 screen · J4 sensors"), (1, "J5 is not used"), (2, "J1–J3: wires go straight into the holes (later)"),
           (3, "J4: solder a 1×4 female header")], pause=5, do="Pause and fit the J4 header")

add("board_fheaders", "board", "Sockets for the Teensy and ESP32", [
    "Now the long female headers that the Teensy and ESP32 plug into.",
    "Here's the trick. Plug the headers onto the module's pins first, set the whole thing on the board, and solder from underneath. The rows come out perfectly straight.",
    "The Teensy goes along the back, with its USB end at the board's right edge.",
    "Solder all forty-eight pins, then lift the Teensy back out for now.",
], visual=board_view(B, [(0, FULL), (2, (38, 72, 90))], place=[(0, -100, ALL_R + ["D1"] + ALL_CER + ["U3"] + ELEC + ["J4"], 0)], sockets=DONE_SOCK,
                     fheaders=[(1, 1.0, "U5")], modules=[(1, 1.0, "U5")],
                     overlays=[{"at": 2, "kind": "tag", "xy": (66, 86), "text": "USB → right edge", "anchor": "r"}]),
    notes=[(1, "Headers on the module, then solder"), (2, "*Teensy USB at the right edge"), (3, "Lift the Teensy out again for now")],
    pause=6, do="Pause and solder the Teensy headers")

add("board_esp", "board", "The ESP32 socket: check the direction", [
    "The ESP32 socket is the one place it's easy to go wrong, so slow down here.",
    "The ESP32 sits chip side up, with its USB socket toward the back, and its antenna at the board's front edge.",
    "Its pin names are printed underneath, so from above they read the other way round. Don't match them by eye. Its pins must stick out of that underside.",
    "Seen from above, its five volt pin is the one nearest the USB on the right-hand edge. To be sure, power the ESP32 from USB on its own, and find the pin that reads five volts to G with your meter.",
    "Plug the ESP32 into its headers, seat it on the board without power, and do the beep test: its five volt pin to D1's square pad, and its G pin to J1 pin two.",
    "Both must beep. If either doesn't, stop, and check the direction before you solder. When it's soldered, lift the ESP32 back out for now.",
], visual=switch([(0, board_view(B, [(0, (17, 14, 44))], place=[(0, -100, ALL_R + ["D1"] + ALL_CER + ["U3"] + ELEC + ["J4"], 0)], sockets=DONE_SOCK,
                                   fheaders=[(1, 0.8, "U4"), (0, -100, "U5")], modules=[(1, 0.8, "U4")])),
                  (2, drawing(lambda ctx, c, x, y, w, h: DG.esp_orient(ctx, c, x, y, w, h)))]),
    notes=[(1, "*Chip side UP, USB to the BACK"), (2, "!Names are printed underneath: read mirrored"), (3, "5V = right row, nearest the USB"), (3, "*Confirm: on USB, 5V pin reads 5 V to G"),
           (4, "Beep: 5V pin → D1 square pad"), (4, "Beep: G pin → J1 pin 2"), (5, "Then lift the ESP32 out again")], pause=6, do="Pause: beep test, then solder")

add("board_trim", "board", "Trim, clean and inspect", [
    "Three finishing jobs.",
    "The tripod post sits under this area. Trim the solder tails of R19 to R22, C26, J3 and J4 to two millimetres or less.",
    "Scrub the amplifier area with isopropyl alcohol and the toothbrush, to remove the sticky flux.",
    "Then look at every joint with good light. Hunt for solder bridges between neighbouring pins, especially around the sockets.",
], visual=board_view(B, [(0, FULL), (1, (12, 40, 50)), (2, (44, 43, 70)), (3, (46, 43, 44))],
                     place=[(0, -100, ALL_R + ["D1"] + ALL_CER + ["U3"] + ELEC + ["J4"], 0)], sockets=DONE_SOCK, fheaders=DONE_FH,
                     overlays=[{"at": 1, "kind": "box", "xywh": (0.5, 30, 20, 18), "until": 2}]),
    notes=[(1, "!Tails of R19–R22, C26, J3, J4: 2 mm max"), (2, "Clean flux with isopropyl"), (3, "Look for bridges between pins")],
    pause=5, do="Pause: trim, clean and inspect")

# ================================================================== 6. POWER + CHECKS
add("power_holder", "power", "Wire the battery holder", [
    "Time for power. The battery holder has its own button, and that button is BLIPR's on and off switch.",
    "Before you solder anything, put the cell in, turn the holder on, and meter its pads. The red probe on the five volt pad must read plus five, not minus five.",
    "Nothing on the board protects against those two swapped. Then take the cell out.",
    "With no cell in the holder, solder a red wire to its five volt pad and a black wire to its ground pad. They go straight to J1 plus five volts and J1 ground. The holder's noise filter is already on the board, right beside J1.",
    "Now the battery gauge. Tin the holder's plus end tab, and quickly solder one leg of a ten k resistor, R25, straight onto it. Cover it with heat-shrink.",
    "Solder a wire to R25's other leg. Brown in our pictures. It goes to J1 BAT. With the resistor right at the tab, a nicked wire can't short the cell.",
    "Set the holder's mode switch to power on. About ten centimetres of wire reaches from the holder to the board.",
], visual=drawing(lambda ctx, c, x, y, w, h: DG.holder_wiring(ctx, c, x, y, w, h, steps=(3, 4, 5, 6))),
    notes=[(1, "!First: meter its pads, +5 V not −5 V"), (2, "Then cell out while soldering"), (3, "Red: 5V pad → J1 +5V"), (3, "Black: GND pad → J1 GND"),
           (4, "R25 (10 kΩ) soldered on the + tab, heat-shrink"), (5, "R25 → J1 BAT"), (6, "Mode switch: power on")],
    pause=6, do="Pause and wire the holder")

add("power_check1", "power", "Checkpoint 1: power rails", [
    "Checkpoint one. The chips and modules are still out.",
    "Put the cell in the holder, plus end to plus, and press the button to turn it on.",
    "Set your meter to DC volts, and put the black probe on ground, J1 pin two.",
    "At J1 plus five volts, expect four point nine to five point two volts.",
    "At U3's output leg, the right-hand leg, expect three point two five to three point three five.",
    "If it reads about five volts, or zero, turn it off now. U3 is in backwards, or it's the wrong version.",
    "At the plus leg of C10, expect about one point six five volts. That's the reference the amplifier works around.",
    "And at the ESP32 socket hole marked three, expect the cell voltage divided by two point one, about one point four to two volts. That's the battery gauge.",
    "All good? Turn it off and take the cell out.",
], visual=split(board_view(B, [(0, FULLS), (2, (24, 40, 92)), (3, (24, 36, 92)), (4, (40, 14, 60)), (6, (34, 16, 60)), (7, (20, 18, 60)), (8, FULLS)],
                           place=[(0, -100, ALL_R + ["D1"] + ALL_CER + ["U3"] + ELEC + ["J4"], 0)], sockets=DONE_SOCK, fheaders=DONE_FH,
                           extra=lambda ctx, c, b: _meter(ctx, c, b)),
                drawing(lambda ctx, c, x, y, w, h: DG.readings(ctx, c, x + 10, y + 10, w - 20, h - 20, [
                    (3, "J1 +5V", "4.9–5.2 V"), (4, "U3 output leg", "3.25–3.35 V"), (6, "C10 + leg (VREF)", "1.60–1.70 V"),
                    (7, "ESP32 hole “3” (gauge)", "cell ÷ 2.1: 1.4–2.0 V")]), PAPER), weights=[1.35, 1]),
    full=True, pause=6, do="Pause and measure")

PROBE_STEPS = [(2, None, "0.00"), (3, ("J1", "1"), "5.04"), (4, ("U3", "3"), "3.30"), (6, ("C10", "1"), "1.65"), (7, ("U4", "A4"), "1.95")]


def _meter(ctx, c, b):
    cur = None
    for li, pin, rd in PROBE_STEPS:
        if c.t >= c.at(li):
            cur = (li, pin, rd)
    if c.t >= c.at(8) or cur is None:
        return
    li, pin, rd = cur
    k = ramp(c.t, c.at(li), 0.5)
    x, y, w, h = b.vp
    red = b.pad_xy(*pin) if pin else (None, None)
    blk = b.pad_xy("J1", "2")
    if not (x < blk[0] < x + w and y < blk[1] < y + h):
        blk = (None, None)
    DG.probes(ctx, red, blk, (x + w - 120, y + 170), rd, k, 4.4)


add("power_opamps", "power", "Checkpoint 2: the amplifier chips", [
    "Now the two amplifier chips. Each has a notch or a dot at one end, marking pin one.",
    "Line the notch up with the socket's notch, so each chip's dot sits beside the square pad, and press it in gently. Check no pins folded under.",
    "Put the cell back in and turn it on. Measure on each chip, with the black probe on ground.",
    "Pin eight, three point three volts. Pins three and five, about one point six five. And the outputs, pins one and seven, also about one point six five.",
    "After a minute, touch each chip. They should not be warm. A warm chip is in backwards: turn off and take it out.",
    "All good? Turn off, and take the cell out again.",
], visual=switch([(0, drawing(lambda ctx, c, x, y, w, h: DG.opamp_volts(ctx, c, x, y, w, h, line0=0))),
                  (1, board_view(B, [(1, (46, 43, 44))], place=[(0, -100, ALL_R + ["D1"] + ALL_CER + ["U3"] + ELEC + ["J4"], 0)], sockets=DONE_SOCK, fheaders=DONE_FH,
                                 chips=[(1, 0.6, "U1"), (1, 1.4, "U2")],
                                 overlays=[{"at": 1, "kind": "ring", "xy": (41.0, 43), "r": 24, "delay": 0.8}, {"at": 1, "kind": "ring", "xy": (61.0, 43), "r": 24, "delay": 1.6}])),
                  (2, drawing(lambda ctx, c, x, y, w, h: DG.opamp_volts(ctx, c, x, y, w, h, line0=2)))]),
    notes=[(1, "*Notch to notch: dot by the square pad"), (3, "Pin 8: 3.25–3.35 V"), (3, "Pins 3, 5: 1.60–1.70 V"), (3, "Pins 1, 7: 1.60–1.70 V"), (4, "!Warm chip = backwards. Off at once.")],
    pause=6, do="Pause and check both chips")

# ================================================================== 7. WIRING
add("wire_overview", "wiring", "Every wire that leaves the board", [
    "Here's every wire that leaves the main board. The colours match all our pictures.",
    "Red is five volts, black is ground, orange is three point three volts, brown is the battery gauge.",
    "Green is the radar's I signal, blue its Q signal, and the screen's SDA. Yellow is the screen's SCL.",
    "You've done the battery. Next, the radar, then the screen.",
], visual=switch([(0, image_view(PIC + "01_overview.png", cams=[(0, (0, 120, 2208, 1300))], overlays=[{"at": 0, "kind": "fn", "fn": lambda ctx, c, P, k, tt: _hide_jack(ctx, P)}])),
                  (1, drawing(lambda ctx, c, x, y, w, h: _wire_legend(ctx, c, x, y, w, h))),
                  (3, image_view(PIC + "01_overview.png", cams=[(0, (0, 120, 2208, 1300))], overlays=[{"at": 0, "kind": "fn", "fn": lambda ctx, c, P, k, tt: _hide_jack(ctx, P)}]))]),
    notes=[(1, "Red +5 V · black GND"), (1, "Orange 3.3 V · brown gauge"), (2, "Green radar I · blue radar Q / SDA"), (2, "Yellow SCL")])


def _wire_legend(ctx, c, x, y, w, h):
    rows = [(1, WIRE["5V"], "+5 V", "red"), (1, WIRE["GND"], "Ground", "black"), (1, WIRE["3V3"], "3.3 V", "orange"),
            (1, WIRE["BAT"], "Battery gauge", "brown"), (2, WIRE["I"], "Radar I", "green"), (2, WIRE["Q"], "Radar Q, and screen SDA", "blue"),
            (2, WIRE["SCL"], "Screen SCL", "yellow")]
    for i, (li, col, lab, nm) in enumerate(rows):
        k = ramp(c.t, c.at(li) + (i if li == 1 else i - 4) * 0.5, 0.4)
        if k <= 0:
            continue
        yy = y + 120 + i * 92
        setc(ctx, col, k); ctx.set_line_width(22); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.new_path()
        ctx.move_to(x + 120, yy - 12); ctx.line_to(x + 330, yy - 12); ctx.stroke()
        text(ctx, nm, x + 370, yy, 36, INK2, True, alpha=k)
        text(ctx, lab, x + 560, yy, 40, INK, True, alpha=k)


def _hide_jack(ctx, P):
    x0, y0 = P(0, 1250); x1, y1 = P(330, 1525)
    setc(ctx, PAPER); ctx.rectangle(x0, y0, x1 - x0, y1 - y0); ctx.fill()


add("wire_radar", "wiring", "The radar pigtail", [
    "The radar plugs onto a short pigtail. Take a one-by-five female header and find pin one on the radar. It's marked on the module. Mark the same end of the header, and put a paint mark by pin one on the module too.",
    "Solder five wires, about eight to ten centimetres long, to the back of the header. Pin one is Q. Blue.",
    "Pin two is VCC, three point three volts. Orange.",
    "Pin three is I. Green.",
    "Pin four is ground. Use two black wires on this pin.",
    "Pin five gets no wire at all.",
    "Twist the I wire with one ground wire, and the Q wire with the other. That keeps out noise.",
    "On the board, solder the wires straight into J2, with no plug there: Q, VCC, I, and both grounds together into the GND hole.",
], visual=drawing(lambda ctx, c, x, y, w, h: DG.pigtail(ctx, c, x, y, w, h, line0=0)),
    notes=[(0, "Mark pin 1 on the radar AND the header"), (1, "1 → Q (blue)"), (2, "2 → VCC 3.3 V (orange)"), (3, "3 → I (green)"), (4, "4 → GND (two black)"),
           (5, "!5 → nothing"), (6, "Twist I with a GND, Q with the other"), (7, "Solder into J2: no plug there"), (7, "Both grounds share J2's GND hole")],
    pause=6, do="Pause and make the pigtail")

add("wire_radar_check", "wiring", "Before the radar goes on", [
    "Before the radar ever gets power, check the pigtail with the beep test.",
    "Header pin two must beep to U3's output leg. Header pin four must beep to ground. That proves the wires, but not which way round the plug goes on.",
    "Then, touch something grounded, and plug the header onto the radar's pins, pin one to pin one, with the two marks together.",
    "This is the one plug that can destroy the radar. Its power and ground pins mirror each other, so a plug turned round swaps them, and no beep test can tell. Always check that the two pin one marks meet.",
], visual=switch([(0, image_view(PIC + "03_radar.png", cams=[(0, (0, 100, 1472, 783))])), (1, drawing(DG.pigtail_check))]),
    notes=[(1, "Pin 2 → U3 output: beep"), (1, "Pin 4 → GND: beep"), (2, "*Pin 1 to pin 1: marks together"),
           (3, "!Plug turned round = power and ground swapped"), (3, "No beep test catches it: check the marks")], pause=5, do="Pause and beep-test the pigtail")

add("wire_oled", "wiring", "The screen", [
    "Now the screen. It's wired directly: four wires soldered to the screen's pads, and straight into J3. No header, and no plug-on jumpers.",
    "Screen ground to J3 ground, and screen VCC to J3 VCC.",
    "Screen SCL to J3 SCL, and screen SDA to J3 SDA.",
    "Screens don't all put their pins in the same order, so always go by the labels printed on yours.",
    "Make these wires about fifteen centimetres long, because the screen lives in the lid. If your screen came with header pins already fitted, unsolder or clip them off first. Under the lid there's no room for a header with Dupont plugs on it.",
], visual=drawing(lambda ctx, c, x, y, w, h: DG.oled_wiring(ctx, c, x, y, w, h, line0=0)),
    notes=[(1, "GND → J3 GND (black)"), (1, "VCC → J3 VCC (orange)"), (2, "SCL → J3 SCL (yellow)"), (2, "SDA → J3 SDA (blue)"),
           (3, "!Go by YOUR screen's labels"), (4, "Wires ~15 cm, soldered at both ends"), (4, "!No header, no Dupont plugs")], pause=6, do="Pause and wire the screen")

add("wire_check3", "wiring", "Checkpoint 3: everything powered", [
    "Checkpoint three. Plug the Teensy and the ESP32 into their sockets, and the radar onto its pigtail.",
    "Put the microSD card in the Teensy's slot.",
    "Put your meter on U3's output leg first, and be ready to cut power. Then insert the cell and turn it on. The Teensy's orange light should blink, and the ESP32's light should come on.",
    "With the radar on, the three point three volt supply should still read three point two five to three point three five, and U3 should be no more than warm.",
    "If it doesn't, or U3 gets hot, cut power at once. Pull the cell if the button is slow. The radar plug is on backwards.",
    "Passing all three checkpoints means the hardware is ready for its firmware.",
], visual=split(board_view(B, [(0, FULLS)], place=[(0, -100, ALL_R + ["D1"] + ALL_CER + ["U3"] + ELEC + ["J4"], 0)], sockets=DONE_SOCK, fheaders=DONE_FH,
                           chips=[(0, -100, "U1"), (0, -100, "U2")], modules=[(0, 0.6, "U5"), (0, 1.4, "U4")],
                           overlays=[{"at": 2, "kind": "fn", "fn": lambda ctx, c, P, k, tt: _blink(ctx, P, tt)}]),
                drawing(lambda ctx, c, x, y, w, h: DG.readings(ctx, c, x + 10, y + 10, w - 20, h - 20, [
                    (2, "Teensy orange light", "blinking"), (2, "ESP32 light", "on"), (3, "U3 output, radar on", "3.25–3.35 V"),
                    (3, "U3 by touch", "warm at most")]), PAPER), weights=[1.35, 1]),
    full=True, pause=5, do="Pause and run checkpoint 3")


def _blink(ctx, P, tt):
    if int(tt * 2) % 2 == 0:
        x, y = P(68.0 + 1.27 - 30.5 + 22.5, 75.0 - 4.2)
        setc(ctx, hexc("#FF8A00", 0.5)); ctx.arc(x, y, 18, 0, 6.29); ctx.fill()
        setc(ctx, hexc("#FF8A00")); ctx.arc(x, y, 8, 0, 6.29); ctx.fill()


# ================================================================== 8. FIRMWARE
add("fw_install", "firmware", "Install Arduino IDE 2", [
    "Now the firmware. You do this part once, on your computer.",
    "Install Arduino IDE 2. In Preferences, add the two board manager addresses from the build guide: one for Teensy, one for the ESP32.",
    "In the Boards Manager, install Teensy by Paul Stoffregen, and esp32 by Espressif, version three point three.",
    "In the Library Manager, install Adafruit SSD1306, and say yes to its extra libraries. Then the sensor libraries in the firmware read-me, even if you skip the sensor kit. The two DFRobot ones may have to come from GitHub as a ZIP.",
], visual=drawing(lambda ctx, c, x, y, w, h: DG.ide(ctx, c, x, y, w, h, [
    (1, "Board manager URL 1", "pjrc.com/teensy/…index.json"), (1, "Board manager URL 2", "espressif…esp32_index.json"),
    (2, "Boards Manager", "Teensy  ·  esp32 3.3.x"), (3, "Library Manager", "Adafruit SSD1306 + all"),
    (3, "Also", "SHT4x · BMP3XX · LSM6DS · LIS3MDL · Unified Sensor"), (3, "And", "OneWire · DallasTemperature · DFRobot IMU + RTU")], title_s="Arduino IDE 2  ·  one-time setup",
    intro="Arduino IDE 2\nfree, from arduino.cc")),
    notes=[(1, "Two board URLs: Teensy and ESP32"), (2, "esp32 by Espressif: version 3.3.x"), (3, "Full list: firmware/README.md"), (3, "DFRobot IMU + RTU: GitHub ZIP if needed")])

add("fw_teensy", "firmware", "Load the Teensy", [
    "Load the Teensy first. Turn BLIPR on with the holder's button, then plug a USB data cable into the Teensy.",
    "Open BliprTeensy dot I N O. In the Tools menu choose Teensy 4.1, USB type Serial plus MTP Disk, and CPU speed six hundred megahertz.",
    "Click Upload. The first time, the Teensy Loader may ask you to press the little white button on the Teensy.",
    "Open the Serial Monitor. If it's blank, press the Teensy's button once. Type stat. Overruns should be zero, and SD should say ok. Paused is normal while it's plugged into a computer.",
    "Then type set f s equals five hundred thousand, and then reboot. That sets the sample rate to five hundred kilohertz, and it's saved. It moves the battery holder's whistle down to about a hundred feet per second, out of the way.",
], visual=switch([(0, drawing(lambda ctx, c, x, y, w, h: DG.ide(ctx, c, x, y, w, h, [
    (1, "Sketch", "BliprTeensy.ino"), (1, "Board", "Teensy 4.1"), (1, "USB Type", "Serial + MTP Disk (Experimental)"),
    (1, "CPU Speed", "600 MHz"), (2, "Upload", "press the Teensy's button if asked")],
    intro="1. Press the holder's button: BLIPR on\n2. USB data cable into the Teensy"))),
    (3, drawing(lambda ctx, c, x, y, w, h: DG.serial(ctx, c, x, y, w, h, [
        (3, "Range Book BLIPR, Teensy firmware 0.2.8", None), (3, "Sample rate 600000 Hz (asked for 600000). SD card found.", None),
        (3, "> stat", hexc("#7FD1FF")), (3, "armed 1 (paused: USB drive mode), shots 0,", hexc("#9BE39B")),
        (3, "sample rate 600000 Hz, ... overruns 0, SD ok, fw 0.2.8", hexc("#9BE39B")),
        (4, "> set fs=500000", hexc("#7FD1FF")), (4, "vmin=600,vmax=3500,...,fs=500000,...", hexc("#9BE39B")),
        (4, "New sample rate takes effect after 'reboot'.", None), (4, "> reboot", hexc("#7FD1FF"))])))]),
    notes=[(0, "!BLIPR must be ON to program the Teensy"), (1, "USB Type: Serial + MTP Disk"), (2, "First time: press the Teensy's button"),
           (3, "*stat → overruns 0"), (4, "set fs=500000, then reboot")], pause=5, do="Pause and load the Teensy")

add("fw_esp", "firmware", "Load the ESP32", [
    "Now the ESP32. Plug a USB-C data cable into it. Open BliprBLE dot I N O in a second IDE window, so each board keeps its own Serial Monitor.",
    "Choose the Nologo ESP32C3 Super Mini board, with USB CDC On Boot enabled, and its port.",
    "Click Upload. If it can't connect, hold the BOOT button, tap RESET, let go of BOOT, and upload again.",
    "When it's done, tap RESET. The Serial Monitor shows the ESP32 firmware version, ready.",
    "You only need the cable this once. After this, Range Book updates the ESP32 over Bluetooth in about thirty seconds. If the computer ever can't see it while it's in BLIPR, take it out of its socket to flash it.",
], visual=switch([(0, drawing(lambda ctx, c, x, y, w, h: DG.ide(ctx, c, x, y, w, h, [
    (0, "Sketch", "BliprBLE.ino  (second window)"), (1, "Board", "Nologo ESP32C3 Super Mini"), (1, "USB CDC On Boot", "Enabled"),
    (2, "Can't connect?", "hold BOOT, tap RESET, release")], intro="USB-C data cable into the ESP32"))),
    (3, drawing(lambda ctx, c, x, y, w, h: DG.serial(ctx, c, x, y, w, h, [(3, "BLIPR ESP32-C3 firmware 0.2.20 ready.", hexc("#9BE39B")),
                                                                              (3, "Sensors found: ...", None)])))]),
    notes=[(1, "USB CDC On Boot: Enabled"), (2, "No connection? BOOT + tap RESET"), (4, "Later updates: Range Book, over Bluetooth")],
    pause=5, do="Pause and load the ESP32")

add("fw_phone", "firmware", "Talk to it from Range Book", [
    "Now let's see the two boards working together.",
    "Open Range Book through its https address, in Chrome on Android, or in the Bluefy app on an iPhone.",
    "Go to Tools, BLIPR Chronograph, and tap Connect chronograph. Pick RB BLIPR. You need Range Book two point four four or later.",
    "Tap Test shot. A test shot of twenty-seven hundred feet per second appears on your phone, and on BLIPR's screen.",
    "If that works, the radar board, the Bluetooth board and the app are all talking. Turn BLIPR off. Time for the case.",
], visual=drawing(lambda ctx, c, x, y, w, h: _phone_and_screen(ctx, c, x, y, w, h)),
    notes=[(1, "Chrome on Android · Bluefy on iPhone"), (2, "Tools › BLIPR Chronograph › Connect"), (3, "*Test shot → 2,700 fps")],
    pause=4, do="Pause and try a test shot")

def _phone_and_screen(ctx, c, x, y, w, h):
    k = c.k(3)
    DG.phone(ctx, c, x - 220 * k, y, w, h, [(0, DG.scr_connect), (3, DG.scr_shot)])
    if k > 0:
        DG.P(ctx, PT.oled, x + w / 2 + 240, y + h / 2, 13, alpha=k, reading="2,700")
        text(ctx, "BLIPR's screen", x + w / 2 + 240, y + h / 2 + 230, 26, INK2, True, "c", alpha=k)


# ================================================================== 9. CASE
add("case_print", "case", "Print the case", [
    "The case is printed in ASA. ASA warps, so use an enclosure or a draft shield, a brim on the base, and a bed around a hundred degrees.",
    "The base prints floor down: point two millimetre layers, six walls, four top and bottom layers, twenty-five percent gyroid infill.",
    "The lid prints top face down, with the same settings.",
    "The front cover prints flat, smooth face down, at point one five layers and one hundred percent infill. Use natural, white or grey filament, never black. The radar has to see through it.",
    "The sensor pod prints upright, and its roof flat face down, in a light colour.",
], visual=drawing(lambda ctx, c, x, y, w, h: DG.print_table(ctx, c, x + 10, y + 10, w - 20, h - 20, [
    (0, "all parts", "ASA filament", "enclosure or draft shield · brim on the base · bed about 100 °C"),
    (1, "base", "floor down", "0.2 mm layers · 6 walls · 4 top/bottom · 25% gyroid · brim"),
    (2, "lid_sensors (or lid_oled)", "top face down", "same as the base"),
    (3, "front_cover", "flat, smooth face down", "0.15 mm · 100% infill · natural, white or grey, NOT black"),
    (4, "sensor_pod", "upright", "same as the base; no supports"), (4, "sensor_pod_roof", "flat face down", "light-coloured filament")]), PAPER),
    full=True)

add("case_inserts", "case", "Heat-set inserts", [
    "Next, the heat-set inserts. These give the plastic strong metal threads.",
    "Eight M3 inserts: four in the corner columns, and four in the board posts. Every hole is four point one millimetres wide and seven and a half deep.",
    "Rest the insert on the hole, then press it in with the hot iron, slowly and straight.",
    "Stop when it's a hair below the top. A tilted insert, or one sticking up, won't line up with its screw.",
    "Let each one cool before you move on. The big quarter-twenty insert goes into the hole under the floor, for a tripod.",
], visual=switch([(0, seq_view("baseonly", [(0, 0, 0, 0, 0)], overlays=[
    {"at": 1, "kind": "ring", "xy": (225, 435), "r": 22, "delay": 0.0}, {"at": 1, "kind": "ring", "xy": (564, 665), "r": 22, "delay": 0.2}, {"at": 1, "kind": "ring", "xy": (706, 236), "r": 22, "delay": 0.5}, {"at": 1, "kind": "ring", "xy": (1044, 466), "r": 22, "delay": 0.8}, {"at": 1, "kind": "tag", "xy": (60, 120), "text": "corner columns", "delay": 0.2}])),
    (2, drawing(lambda ctx, c, x, y, w, h: DG.compare(ctx, c, x, y, w, h, DG.insert_section(True), DG.insert_section(False), line=2, line2=3))),
    (4, image_view(CASE + "preview_base_bottom.png", overlays=[{"at": 4, "kind": "ring", "xy": (310, 307), "r": 40, "delay": 0.5},
                                                              {"at": 4, "kind": "tag", "xy": (262, 300), "text": "1/4-20 tripod insert", "delay": 0.8, "anchor": "r"}]))]),
    notes=[(1, "8 × M3: corners + board posts"), (1, "Holes 4.1 mm wide, 7.5 mm deep"), (3, "*Straight, a hair below the top"), (4, "Let each cool"),
           (4, "1/4-20 under the floor (tripod)")], pause=6, do="Pause and set the inserts")

add("case_holder", "case", "Mount the battery holder", [
    "The battery holder goes in the bay on the left.",
    "Check its mode switch is on power on. Then screw it to its four pads with M3 by six self-tapping screws.",
    "Drive them gently. They cut their own thread in the plastic.",
    "Its USB-C charging port and its button line up with the two openings in the side wall. You'll press the button through that slot to turn BLIPR on and off.",
], visual=switch([(0, seq_view("build", [(0, 0.3, 0, 29, 1.4)], overlays=[{"at": 0, "kind": "tag", "xy": (511, 360), "text": "battery holder", "delay": 1.6, "anchor": "c"}])),
                  (3, image_view(CASE + "preview_base_holder.png", cams=[(3, (660, 100, 660, 400))],
                                 overlays=[{"at": 3, "kind": "ring", "xy": (856, 228), "r": 40}, {"at": 3, "kind": "ring", "xy": (1066, 350), "r": 44, "delay": 0.8},
                                           {"at": 3, "kind": "tag", "xy": (856, 300), "text": "USB-C charging", "anchor": "c", "delay": 0.4},
                                           {"at": 3, "kind": "tag", "xy": (1066, 430), "text": "button slot 14 × 10 mm", "anchor": "c", "delay": 1.2}]))]),
    notes=[(1, "Mode switch: power on"), (1, "4 × M3×6 self-tapping"), (2, "Gently: they cut their own thread"), (3, "USB-C + button line up with the side wall")],
    pause=5, do="Pause and mount the holder")

add("case_radar", "case", "Fit the radar", [
    "Now the radar. Put a strip of the one millimetre foam tape down each of its two sides.",
    "And another strip across its back.",
    "Then a twenty millimetre strip on its top edge. A rib under the lid presses down on it.",
    "Press the radar into its pocket from above, antenna face forward, flat against the window frame, pins pointing back. It sits on a small ledge.",
    "No glue. That way it can be turned ninety degrees later, if testing shows it's better that way.",
], visual=switch([(0, drawing(lambda ctx, c, x, y, w, h: DG.radar_tape(ctx, c, x, y, w, h, line0=0))),
                  (3, seq_view("build", [(3, 0.2, 30, 59, 1.4)], overlays=[{"at": 3, "kind": "tag", "xy": (180, 470), "text": "radar, antenna face forward", "delay": 1.6, "anchor": "c"},
                                                                       {"at": 3, "kind": "arrow", "from": (260, 490), "to": (455, 595), "delay": 1.8}]))]),
    notes=[(0, "Foam 1 × 5 mm on both sides"), (1, "…and across the back"), (2, "20 mm strip on the top edge"), (3, "*Antenna face flat against the window"),
           (4, "No glue")], pause=5, do="Pause and fit the radar")

add("case_align", "case", "Radar alignment matters", [
    "This is the one alignment that really matters inside the case.",
    "The radar's face must sit flat against the window frame, square to the front of the case. Then the beam points straight out the front.",
    "If it's tipped in its pocket, the beam points off to the side, and the bullet can slip past the edge of it.",
    "The foam holds it square. If it won't sit flat, look for a wire or a blob of solder behind it.",
], visual=drawing(lambda ctx, c, x, y, w, h: DG.compare(ctx, c, x, y, w, h, DG.radar_align(True), DG.radar_align(False), line=0, line2=2)),
    notes=[(1, "*Flat against the frame, square to the front"), (2, "!Tipped = beam off to the side"), (3, "Won't sit flat? Check behind it")])

add("case_board", "case", "Mount the main board", [
    "Lower the main board onto its four posts, with the Teensy's USB facing the opening in the right-hand wall.",
    "Screw it down with four M3 by six screws. The back-right screw sits close to the Teensy's header, so use a pan head no wider than five and a half millimetres there.",
    "Plug the radar pigtail onto the radar, pin one to pin one, with the two marks together, and run the wires down along the pocket, away from the ESP32.",
], visual=seq_view("build", [(0, 0.2, 60, 89, 1.4)], overlays=[
    {"at": 0, "kind": "tag", "xy": (840, 420), "text": "Teensy USB → right-wall hole", "delay": 1.6}, {"at": 0, "kind": "arrow", "from": (950, 440), "to": (968, 555), "delay": 1.9},
    {"at": 2, "kind": "ring", "xy": (479, 600), "r": 40}]),
    notes=[(0, "Teensy USB → right-wall opening"), (1, "4 × M3×6"), (1, "!Back-right: pan head ≤ 5.5 mm"), (2, "Radar: pin 1 to pin 1, wires away from the ESP32")],
    pause=5, do="Pause and mount the board")

add("case_cover", "case", "The front cover", [
    "Now the thin front cover. It's the window the radar looks through.",
    "Slide it down into the slot behind the front wall, recessed side toward the radar, and the wider edge of its frame at the top.",
    "The lid will hold it down.",
], visual=switch([(0, image_view(CASE + "preview_cover.png")),
                  (1, seq_view("build", [(1, 0.2, 90, 119, 1.4)], overlays=[{"at": 1, "kind": "tag", "xy": (250, 790), "text": "front cover", "delay": 1.6, "anchor": "c"},
                                                                   {"at": 1, "kind": "arrow", "from": (300, 770), "to": (430, 680), "delay": 1.8}]))]),
    notes=[(1, "Recessed side toward the radar"), (1, "Wider frame edge at the top")], pause=4, do="Pause and fit the cover")

add("case_screen", "case", "Screen into the lid", [
    "The screen goes into the pocket under the lid's window, its four wires already soldered on, pointing toward the board.",
    "Screw it to the four corner pads with the tiny M2 by four screws. Snug only. The holes are plastic.",
    "Under the lid you can also see the rib that presses on the radar's foam.",
], visual=image_view(CASE + "preview_lid_sensors_under.png", overlays=[{"at": 1, "kind": "box", "xywh": (298, 340, 112, 72)},
                                                                     {"at": 1, "kind": "tag", "xy": (355, 440), "text": "screen pocket, 4 pads", "anchor": "c", "delay": 0.4},
                                                                     {"at": 2, "kind": "ring", "xy": (459, 217), "r": 34},
                                                                     {"at": 2, "kind": "tag", "xy": (459, 172), "text": "radar hold-down rib", "anchor": "c", "delay": 0.4}]),
    notes=[(1, "4 × M2×4, snug only"), (2, "The rib presses the radar's top foam")], pause=4, do="Pause and fit the screen")

add("case_lid", "case", "Close the lid", [
    "Before you close it, tuck the screen wires in so nothing gets pinched.",
    "Put the lid on and screw it down with four M3 by eight screws into the corner inserts.",
    "The lid holds the front cover in place, and its rib presses gently on the radar.",
], visual=seq_view("build", [(0, 0.3, 120, 149, 1.4)], overlays=[{"at": 1, "kind": "tag", "xy": (635, 160), "text": "4 × M3×8 into the corners", "delay": 1.0, "anchor": "c"},
                                                                  {"at": 1, "kind": "ring", "xy": (225, 425), "r": 22, "delay": 0.2}, {"at": 1, "kind": "ring", "xy": (564, 655), "r": 22, "delay": 0.4},
                                                                  {"at": 1, "kind": "ring", "xy": (706, 226), "r": 22, "delay": 0.6}, {"at": 1, "kind": "ring", "xy": (1044, 456), "r": 22, "delay": 0.8}]),
    notes=[(0, "Don't pinch the screen wires"), (1, "4 × M3×8")], pause=4, do="Pause and close the lid")

# ================================================================== 10. SENSOR POD
add("pod_intro", "sensors", "The sensor pod (optional)", [
    "If you're adding the sensor kit, here's the pod. Skip ahead if you're not. For the kit, print the lid called lid sensors, not lid O L E D. Only it has the pod's insert risers and cable slot.",
    "It sits on the lid, in the front corner on the far side from the gun. The screen is in the back corner, nearest you.",
    "The temperature sensor has to be outside the case to read the real air, and the compass stays with it, well away from the battery.",
], visual=seq_view("build", [(0, 0.2, 150, 179, 1.4), (1, 1.6, 180, 209, 1.4)], overlays=[{"at": 1, "kind": "tag", "xy": (462, 280), "text": "sensor pod", "delay": 1.6, "anchor": "c"}]),
    notes=[(0, "*Print lid_sensors, not lid_oled"), (1, "Pod: front corner, far side"), (1, "Screen: back corner, nearest you")])

add("pod_wire", "sensors", "Wire the sensors", [
    "One cable chain feeds both sensors. The hundred-and-fifty millimetre cable plugs its pins into J4, black to ground, red to three point three volts, blue to SDA, yellow to SCL. It runs up through the lid's slot to the SHT45.",
    "The DFRobot board has its own Gravity cable. Join it to the SHT45's other socket with the second to-pins cable, or splice a cut STEMMA QT cable to its wires.",
    "Match the DFRobot's pin labels: red to plus, black to minus, yellow to C, blue to D. Set its switch to I2C, and A0 and A1 to zero.",
], visual=drawing(lambda ctx, c, x, y, w, h: DG.qt_chain(ctx, c, x, y, w, h, line0=0)),
    notes=[(0, "J4 → SHT45 → DFRobot, one chain"), (0, "!J4: black GND · red 3V3 · blue SDA · yellow SCL"), (1, "DFRobot: its own Gravity cable"), (2, "*DFRobot: switch to I2C, A0/A1 = 0")], pause=5, do="Pause and wire the sensors")

add("pod_mount", "sensors", "Mount the pod", [
    "Press an M3 insert into each of the pod's two holes in the lid, from the top.",
    "Thread the cable up through the slot, and screw the pod down with two M3 by eight screws, before the IMU board goes in.",
    "The SHT45 goes on the posts at the far-side end, with four brass M2.5 screws. The DFRobot goes at the gun-side end, with two brass M3 screws, its plug end facing you.",
    "Drive each screw slowly, just until snug. Then plug in the cables and screw the roof on with four more brass screws.",
], visual=image_view(CASE + "pod_layout_10dof.png", cams=[(0, (0, 0, 1100, 860)), (2, (100, 80, 1000, 760))],
                     overlays=[{"at": 2, "kind": "box", "xywh": (705, 245, 275, 390)}, {"at": 2, "kind": "tag", "xy": (842, 660), "text": "SHT45: 4 × brass M2.5", "anchor": "c", "delay": 0.4},
                               {"at": 2, "kind": "box", "xywh": (195, 90, 410, 560), "delay": 3.5}, {"at": 2, "kind": "tag", "xy": (400, 680), "text": "DFRobot: 2 × brass M3", "anchor": "c", "delay": 3.9}]),
    notes=[(0, "2 inserts in the lid's pod holes"), (1, "Pod down first: 2 × M3×8"), (2, "SHT45: 4 × brass M2.5×6"), (2, "DFRobot: 2 × brass M3×6"),
           (3, "!Brass only near the compass"), (3, "Roof: 4 × brass M2.5×6")], pause=6, do="Pause and build the pod")

# ================================================================== 11. FIRST TEST
add("test_boot", "test", "Power it up", [
    "Everything's together. Press the battery holder's button through the side slot.",
    "BLIPR plays its start-up: a bullet flies across the screen, writes BLIPR, and the screen blinks.",
    "With the sensor kit fitted, a bubble level comes next, for up to a minute.",
], visual=drawing(lambda ctx, c, x, y, w, h: DG.oled_play(ctx, c, x, y, w, h, REPO + "/pictures/out/oled_boot_animation.gif", 1, "BLIPR's start-up animation")),
    notes=[(0, "On/off: the holder's button"), (2, "Sensor kit: bubble level, up to 1 minute")])

add("test_level", "test", "Level it on the bench", [
    "Shim the case until the bubble sits in the middle circle, and the screen says LEVEL. That's within half a degree.",
    "Hold it there for three seconds.",
    "The top of the screen is the front, downrange. The text tells you which way to move: lift the nose, lower the nose, lift left or right.",
], visual=image_view(PIC + "oled_level_preview.png", cams=[(0, (0, 0, 1074, 300)), (2, (0, 0, 540, 300))]),
    notes=[(0, "LEVEL = within 0.5°"), (1, "Hold 3 s"), (2, "Top of screen = downrange")])

add("test_screen", "test", "Dark means listening", [
    "After the level, the weather shows for ten seconds, then READY for two. Then BLIPR arms itself, and the screen goes dark.",
    "Dark means listening. A lit screen makes a little electrical noise the radar can hear, so BLIPR keeps it off while it waits for a shot.",
    "After each shot, the speed and the string show for three seconds, then it goes dark again. Range Book's Show each shot for setting changes that time. Keep it short: BLIPR doesn't listen while the screen is lit.",
    "After every shot, BLIPR also checks it hasn't been knocked. Tilted more than a degree, or turned more than five, and the level comes back once the shot has been shown.",
    "In Range Book's chronograph settings, Re-level and update the heading shows the level any time. Disable the level is for shooting at an angle: then there's no level at all.",
], visual=image_view(PIC + "screen_sequence.png", cams=[(0, (0, 0, 1292, 648)), (3, (0, 420, 1292, 228))]),
    notes=[(0, "Level → weather 10 s → READY 2 s → dark"), (1, "*Dark = listening"), (2, "Each shot: 3 s, then dark"), (2, "Not listening while lit"),
           (3, "Knocked > 1° or turned > 5°: level again"), (4, "Range Book: Re-level · Disable the level")])

add("test_compass", "test", "Calibrate the compass once", [
    "If you fitted the sensor kit, calibrate the compass once.",
    "In Range Book's chronograph settings, choose Compass, then Calibrate compass.",
    "Turn BLIPR slowly through a full circle on the bench. Tip it nose up, nose down, and onto each side along the way. Then tap Finish.",
    "Do this away from vehicles, steel benches and the rifle.",
], visual=drawing(lambda ctx, c, x, y, w, h: _compass(ctx, c, x, y, w, h)),
    notes=[(1, "Settings › Compass › Calibrate"), (2, "Full slow circle, tip all ways, Finish"), (3, "!Away from steel and vehicles")])


def _compass(ctx, c, x, y, w, h):
    cx, cy = x + w / 2, y + h / 2 + 20
    setc(ctx, RULE); ctx.set_line_width(4); ctx.arc(cx, cy, 250, 0, 6.29); ctx.stroke()
    a = (c.t - c.at(2)) * 0.9 if c.t > c.at(2) else 0
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(a)
    setc(ctx, hexc("#8A93A3")); rrect(ctx, -90, -100, 180, 200, 16); ctx.fill()
    setc(ctx, hexc("#C9A23F")); ctx.rectangle(-44, -104, 88, 10); ctx.fill()
    text(ctx, "BLIPR", 0, 10, 28, PAPER, True, "c")
    ctx.restore()
    if c.t > c.at(2):
        DG.wire_path(ctx, [(cx + 250 * __import__('math').cos(t), cy + 250 * __import__('math').sin(t)) for t in [i * 0.1 for i in range(int(min(a, 6.28) / 0.1) + 1)]], FOCUS, 6, 1, False)
    for i, d in enumerate("NESW"):
        import math as m
        text(ctx, d, cx + 300 * m.sin(i * m.pi / 2), cy - 300 * m.cos(i * m.pi / 2) + 12, 32, INK2, True, "c")


add("test_place", "test", "Set it up at the bench", [
    "At the bench, BLIPR sits beside the rifle, behind the muzzle, out of the blast. From your seat it's at about one o'clock.",
    "The front window faces downrange, and the screen corner is nearest you.",
    "For a rifle, a good place to start is about thirty centimetres behind the muzzle, and twelve centimetres to the side, out of the blast. A twenty-two has no real blast: the first twenty-two tests had BLIPR about ten centimetres behind the muzzle and ten to the side.",
    "In Range Book's chronograph settings, enter where it sits, so BLIPR can correct for the angle.",
], visual=drawing(lambda ctx, c, x, y, w, h: DG.bench(ctx, c, x, y, w, h, shot_line=None, phone=False, dims=2)), full=True)

add("test_aim", "test", "Aim it parallel to the bore", [
    "Aim matters here too. Point BLIPR straight downrange, parallel to the barrel.",
    "If it's turned away, the beam can miss the bullet's path. Use the edge of the bench or the rifle as your guide.",
], visual=drawing(lambda ctx, c, x, y, w, h: DG.compare(ctx, c, x, y, w, h,
                                                         lambda ctx_, cx, cy, c_: _mini_bench(ctx_, cx, cy, c_, False),
                                                         lambda ctx_, cx, cy, c_: _mini_bench(ctx_, cx, cy, c_, True), line=0, line2=1)),
    notes=[(0, "*Parallel to the barrel"), (1, "!Turned away = missed shots")])


def _mini_bench(ctx, cx, cy, c, bad):
    import math as m
    setc(ctx, hexc("#30343B")); ctx.rectangle(cx - 100, cy - 160, 14, 330); ctx.fill()
    ctx.save(); ctx.translate(cx + 40, cy + 40); ctx.rotate(m.radians(22) if bad else 0)
    setc(ctx, hexc("#8A93A3")); rrect(ctx, -40, -44, 80, 88, 10); ctx.fill()
    setc(ctx, FOCUS, 0.14); ctx.move_to(-18, -46); ctx.line_to(-110, -300); ctx.line_to(90, -300); ctx.line_to(18, -46); ctx.close_path(); ctx.fill()
    ctx.restore()
    DG.dot(ctx, cx - 93, cy - 230, 7, hexc("#B8860B"))


add("test_settings", "test", "Two things before the first shot", [
    "Two things before the first shot. First, the speed window. BLIPR only reports speeds inside it, so set it a little wider than your load.",
    "Range Book's chronograph settings show BLIPR's window, and a button sets it from your load. Or type it on the Teensy: for twenty-two standard velocity, v min nine fifty and v max twelve hundred.",
    "Second, keep other radar chronographs away. Two twenty-four gigahertz radars side by side interfere with each other. Use one at a time, or set them well apart.",
], visual=drawing(lambda ctx, c, x, y, w, h: DG.serial(ctx, c, x, y, w, h, [
    (1, "> set vmin=950 vmax=1200", hexc("#7FD1FF")), (1, "vmin=950,vmax=1200,...,fs=500000,save=1,arm=1,band=15", hexc("#9BE39B"))])),
    notes=[(0, "Window a little wider than your load"), (1, "Range Book: window from the load"), (1, ".22 SV: 950–1200 fps"),
           (2, "!One radar chronograph at a time")])

add("test_shot", "test", "Your first shot", [
    "Connect Range Book, and fire.",
    "The speed appears on BLIPR's screen and on your phone, shot by shot, with the string's count, average, standard deviation and extreme spread.",
    "If you have another chronograph, compare a string. Range Book's settings can calibrate BLIPR against it.",
    "One last note. Plugging the Teensy into a computer turns on USB drive mode and pauses shots. Unplug it, and it listens again a few seconds later.",
], visual=split(drawing(lambda ctx, c, x, y, w, h: DG.bench(ctx, c, x, y, w, h, shot_line=0, phone=True)),
                drawing(lambda ctx, c, x, y, w, h: DG.oled_play(ctx, c, x, y, w, h, REPO + "/pictures/out/oled_shot_animation.gif", 0, "BLIPR's screen after a shot (shot animation on)")), weights=[1.4, 1]),
    full=True)

# ================================================================== 12. TROUBLESHOOTING
add("trouble1", "trouble", "If something's wrong", [
    "Finally, the common problems, and what to check.",
    "Nothing turns on: the cell is flat or in backwards, or the holder's output is off. Press its button.",
    "It switches itself off after half a minute: set the holder's mode switch to power on.",
    "The computer can't see the Teensy: BLIPR is off. Turn it on first. The Teensy only runs on battery power.",
    "The regulator U3 gets hot: something is shorted on the three point three volt supply, or the radar header is on backwards.",
    "An amplifier output is stuck near zero or three point three volts: a missing or bridged part, or the chip is in backwards.",
], visual=drawing(lambda ctx, c, x, y, w, h: DG.trouble(ctx, c, x + 10, y + 10, w - 20, h - 20, [
    (1, "Nothing turns on", "Cell flat or reversed · holder output off: press its button"),
    (2, "Turns itself off", "Holder's mode switch → power on"),
    (3, "Computer can't see the Teensy", "BLIPR is off. Turn it on: the Teensy only runs on battery"),
    (4, "U3 hot", "Short on the 3.3 V supply, or the radar header reversed. Off at once"),
    (5, "Op-amp output stuck at 0 or 3.3 V", "Missing or bridged part · chip backwards · C14/C17 shorted")]), BG), full=True)

add("trouble2", "trouble", "More fixes", [
    "The radar's I and Q read zero volts: the radar isn't powered, or pin one is the wrong way round.",
    "The screen says NO RADAR: the ESP32 can't hear the Teensy. Check pin thirty-five through R23 to GPIO twenty, pin thirty-four through R24 to GPIO twenty-one, and that the Teensy has power.",
    "The screen says PAUSED: the Teensy is plugged into a computer, or it was disarmed. Unplug it, or send arm.",
    "Still stuck? Measure at the checkpoints again, in order. The first reading that's off points to the problem.",
], visual=drawing(lambda ctx, c, x, y, w, h: DG.trouble(ctx, c, x + 10, y + 10, w - 20, h - 20, [
    (0, "Radar I/Q at 0 V", "Radar not powered (pin 2 at the header) or pin 1 the wrong way"),
    (1, "Screen: NO RADAR", "Teensy 35 → R23 → GPIO20 · Teensy 34 → R24 → GPIO21 · shared GND · Teensy power"),
    (2, "Screen: PAUSED", "Teensy on a computer (USB drive mode), or disarmed. Unplug it, or send arm"),
    (3, "Still stuck", "Repeat the checkpoints in order. The first wrong reading points to the fault")]), BG), full=True)

add("trouble3", "trouble", "Noise, and a few quirks", [
    "BLIPR's radar hears more than bullets. If it reads the same speed again and again, or reports shots nobody fired, look for a steady tone.",
    "On the Teensy, type live. Twice a second it shows the noise and the strongest line, with its speed. Type rec to record a tenth of a second and see what's in it.",
    "Most tones come from switching converters or a lit screen. Check the five volt filter parts are all in, the sample rate is five hundred thousand, and the window stays clear of the tone's speed.",
    "If the holder's button won't turn BLIPR on after a night on the charger, take the cell out, put it back, and press the button.",
    "And if a Bluetooth update stops partway, keep the phone close with its screen on, and try again. Nothing changes until the whole file has arrived.",
], visual=drawing(lambda ctx, c, x, y, w, h: DG.trouble(ctx, c, x + 10, y + 10, w - 20, h - 20, [
    (0, "Same speed every time, or false shots", "A steady tone: type live (strongest line) or rec on the Teensy"),
    (2, "Where tones come from", "Converters, a lit screen: filters fitted · fs=500000 · window clear of the line"),
    (3, "Button won't switch on after charging", "Take the cell out, put it back, press the button"),
    (4, "Bluetooth update stops partway", "Phone close, screen on, try again: nothing changes until it's all arrived")]), BG), full=True)

add("outro", "intro", "You built BLIPR", [
    "That's it. You've built BLIPR.",
    "Keep it in the shade at the range, give the air reading ten minutes to settle, and enjoy your data.",
    "Good shooting.",
], visual=drawing(DG.outro), full=True, tail=2.0)


# step numbers for the 'STEP n OF N' counter: every scene with a pause (a hands-on step)
_n = 0
for s in SC:
    if s.pause > 0:
        _n += 1
        s.step = _n
NSTEPS = _n
