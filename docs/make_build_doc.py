"""Builds docs/BLIPR Build Guide.docx (and the case pictures it uses, docs/img/case_*.png).
Covers the circuit board build (v1.2, with the v1.1 steps kept), case v0.12, Teensy firmware 0.2.8 and ESP32 firmware 0.2.20,
with both 5 V filters and the direct-wired screen. docs/make_build_pdf.py turns it into the PDF. Needs: pip install python-docx pillow numpy matplotlib.
Run from the repo root: python docs/make_build_doc.py"""
import sys
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "docs" / "img"
IMG.mkdir(parents=True, exist_ok=True)
OUT = ROOT / "docs" / "BLIPR Build Guide.docx"
CASE = ROOT / "case" / "out"
PICS = ROOT / "pictures" / "out"
PCB = ROOT / "pcb" / "out"
BLUE = RGBColor(0x1F, 0x4E, 0x9A)


# ---------------------------------------------------------------- case pictures (from the current STL files)
def case_pictures():
    sys.path.insert(0, str(ROOT / "case"))
    import render
    base = str(CASE / "base.stl")
    # from above with the front (radar window) at the top, the way Sean checks the case
    render.views([base], str(IMG / "case_base_above.png"),
                 [(75, 180, "Base from above: front (radar window) at the top")], size=(7, 6.2))
    render.views([base], str(IMG / "case_base_under.png"), [(-40, 30, "Underside: tripod insert")], size=(6, 5))
    wall_diagram(base)


def wall_holes(t, x):
    """Openings in a side wall: (y0, y1, z0, z1) boxes found by testing points in the middle of the wall."""
    import numpy as np
    from scipy import ndimage
    (_, ya, za), (_, yb, zb) = t.bounds
    ys, zs = np.arange(ya + 3, yb - 3, 0.25), np.arange(za + 0.3, zb - 0.3, 0.25)
    Y, Z = np.meshgrid(ys, zs)
    hole = ~t.contains(np.c_[np.full(Y.size, x), Y.ravel(), Z.ravel()]).reshape(Z.shape)
    lab, n = ndimage.label(hole)
    out = []
    for i in range(1, n + 1):
        zz, yy = np.where(lab == i)
        out.append((ys[yy.min()] - 0.125, ys[yy.max()] + 0.125, zs[zz.min()] - 0.125, zs[zz.max()] + 0.125))
    return out


def wall_diagram(base):
    """Both side walls drawn flat from outside, with their openings measured from the STL."""
    import trimesh
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, FancyBboxPatch
    t = trimesh.load(base, force="mesh")
    (x0, _, _), (x1, D, H) = t.bounds
    fig, axs = plt.subplots(1, 2, figsize=(12, 3.2))
    # seen from outside the left wall, the front is on your right; outside the right wall, on your left
    walls = (("Left wall (battery side), seen from outside", x0 + 1.2, True,
              ["power-button slot", "battery USB-C"]),
             ("Right wall (Teensy side), seen from outside", x1 - 1.2, False, ["Teensy USB"]))
    for ax, (title, x, flip, names) in zip(axs, walls):
        ax.add_patch(FancyBboxPatch((0, 0), D, H, boxstyle="round,pad=0,rounding_size=4", fc="#9aa6bd", ec="#333"))
        holes = sorted(wall_holes(t, x), key=lambda h: -h[0])          # rear-most first
        for (a, b, c, d), name in zip(holes, names):
            u0, u1 = (D - b, D - a) if flip else (a, b)
            ax.add_patch(Rectangle((u0, c), u1 - u0, d - c, fc="white", ec="#333"))
            ax.text((u0 + u1) / 2, d + 1.5, "%s\n%g x %g mm, %g-%g mm up" % (name, round(b - a, 1), round(d - c, 1), round(c, 1), round(d, 1)),
                    ha="center", va="bottom", fontsize=11)
        lft, rgt = ("REAR", "FRONT (radar)") if flip else ("FRONT (radar)", "REAR")
        ax.text(1, -2, lft, va="top", fontsize=11, weight="bold")
        ax.text(D - 1, -2, rgt, va="top", ha="right", fontsize=11, weight="bold")
        ax.set_xlim(-3, D + 3); ax.set_ylim(-9, H + 14); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(title, fontsize=13)
    plt.tight_layout()
    plt.savefig(IMG / "case_base_walls.png", dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------- document
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
for m in ("left_margin", "right_margin"):
    setattr(sec, m, Inches(0.8))
sec.top_margin = sec.bottom_margin = Inches(0.7)
st = doc.styles["Normal"]
st.font.name, st.font.size = "Arial", Pt(12)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
for lvl, size in ((1, 20), (2, 15)):
    h = doc.styles[f"Heading {lvl}"]
    h.font.name, h.font.size, h.font.color.rgb = "Arial", Pt(size), BLUE


def para(text, bold=False, size=None, color=None, align=None, space=6):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = bold
    if size:
        r.font.size = Pt(size)
    if color:
        r.font.color.rgb = RGBColor(*color)
    if align:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space)
    return p


def rich(*parts, space=6):
    """A paragraph from (text, bold) pieces; a plain string is not bold."""
    p = doc.add_paragraph()
    for part in parts:
        text, bold = (part, False) if isinstance(part, str) else part
        p.add_run(text).bold = bold
    p.paragraph_format.space_after = Pt(space)
    return p


def steps(items, style="List Number"):
    for it in items:
        p = doc.add_paragraph(style=style)
        if isinstance(it, tuple):
            p.add_run(it[0]).bold = True
            p.add_run(it[1])
        else:
            p.add_run(it)
        p.paragraph_format.space_after = Pt(4)


def bullets(items):
    steps(items, "List Bullet")


def restart_numbering():
    """Start the next numbered list at 1 again (python-docx otherwise carries on counting)."""
    global _num_restarts
    numbering = doc.part.numbering_part.numbering_definitions._numbering
    abstract = doc.styles["List Number"].element.pPr.numPr.numId.val
    num_el = [n for n in numbering.findall(qn("w:num")) if n.get(qn("w:numId")) == str(abstract)][0]
    abs_id = num_el.find(qn("w:abstractNumId")).get(qn("w:val"))
    new = numbering.add_num(int(abs_id))
    ov = OxmlElement("w:lvlOverride")
    ov.set(qn("w:ilvl"), "0")
    so = OxmlElement("w:startOverride")
    so.set(qn("w:val"), "1")
    ov.append(so)
    new.append(ov)
    return new.numId


def numbered(items):
    nid = restart_numbering()
    for it in items:
        p = doc.add_paragraph(style="List Number")
        pPr = p._p.get_or_add_pPr()
        numPr = OxmlElement("w:numPr")
        il = OxmlElement("w:ilvl")
        il.set(qn("w:val"), "0")
        ni = OxmlElement("w:numId")
        ni.set(qn("w:val"), str(nid))
        numPr.append(il)
        numPr.append(ni)
        pPr.append(numPr)
        if isinstance(it, tuple):
            p.add_run(it[0]).bold = True
            p.add_run(it[1])
        else:
            p.add_run(it)
        p.paragraph_format.space_after = Pt(4)


def checkbox_list(items):
    for it in items:
        p = doc.add_paragraph()
        p.add_run("☐  ").font.size = Pt(14)
        p.add_run(it)
        p.paragraph_format.space_after = Pt(2)


def shade(cell, hexcol):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), hexcol)
    tcPr.append(sh)


def table(rows, widths, header=True, size=11):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.width = Inches(widths[j])
            c.text = ""
            r = c.paragraphs[0].add_run(str(val))
            r.font.size = Pt(size)
            if header and i == 0:
                r.bold = True
                shade(c, "DCE6F2")
            # short tables stay on one page; no row is ever split across a page break
            if len(rows) <= 10 and i < len(rows) - 1:
                c.paragraphs[0].paragraph_format.keep_with_next = True
        trPr = t.rows[i]._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
        if header and i == 0:
            trPr.append(OxmlElement("w:tblHeader"))
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def picture(path, width=6.9, caption=None):
    doc.add_picture(str(path), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    if caption:
        p = para(caption, size=10, color=(90, 90, 90), align=WD_ALIGN_PARAGRAPH.CENTER, space=10)
        p.runs[0].italic = True


def tip(text):
    p = para("", space=8)
    r = p.add_run("Tip: ")
    r.bold = True
    r.font.color.rgb = BLUE
    p.add_run(text)


def warn(text):
    p = para("", space=8)
    r = p.add_run("Careful: ")
    r.bold = True
    r.font.color.rgb = RGBColor(0xB0, 0x1E, 0x1E)
    p.add_run(text)


def check(rows):
    """A checkpoint table: where to measure, what to expect, what it means if not."""
    table([("Measure at", "Expect", "If not")] + rows, [1.9, 1.6, 3.4], size=10.5)


def build():
    case_pictures()

    # ---------------------------------------------------------------- cover
    para("RANGE BOOK BLIPR", bold=True, size=36, color=(0x1F, 0x4E, 0x9A), align=WD_ALIGN_PARAGRAPH.CENTER, space=0)
    para("Ballistic Launch Inspection Portable Radar", size=13, align=WD_ALIGN_PARAGRAPH.CENTER, space=2)
    para("Build guide: a bench-side radar chronograph for Range Book", bold=True, size=16,
         align=WD_ALIGN_PARAGRAPH.CENTER, space=14)
    picture(IMG / "blipr_front.jpg", 4.6, "The first BLIPR, on a small tripod (case v0.12).")
    para("A 24 GHz Doppler radar chronograph that sits on the bench beside the rifle and sends each shot's muzzle "
         "velocity over Bluetooth to Range Book. Nothing goes downrange. This guide covers everything: parts, "
         "printing the case, loading and bench-testing the firmware, soldering the circuit board, wiring, the "
         "electrical checks, putting it in the case and the first session at the range.",
         align=WD_ALIGN_PARAGRAPH.CENTER)
    para("You'll need Range Book, free: rangebook.org shows how to install it. On iPhone and iPad, get the Range Book "
         "app (Range Book: Shooting Log) from the App Store: apps.apple.com/app/id6837895002.",
         bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    para("Watch the build: the narrated assembly video (about 39 minutes) is on YouTube: youtu.be/nRWELvyEKN8",
         bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    para("Parts → Print → Flash and bench test → Solder → Check → Wire → Case → Range",
         bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    para("Status, Nov 26, 2026: built and tested live on .22 LR. 9 of 10 shots read on the first two strings, "
         "averaging within about 1% of an Athlon chronograph with the same rifle and ammo.",
         size=11, align=WD_ALIGN_PARAGRAPH.CENTER)
    para("Circuit board v1.2 (v1.1 notes kept) · Case v0.12 · Teensy firmware 0.2.8 · ESP32 firmware 0.2.20 · November 2026",
         size=10, color=(90, 90, 90), align=WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_page_break()

    # ---------------------------------------------------------------- how it works
    doc.add_heading("How it works", 1)
    para("The RFbeam K-LC5 radar sends out a 24 GHz signal and gives back two very weak signals, called I and Q, "
         "whose pitch rises with the bullet's speed: about 161 Hz per m/s, so roughly 150 kHz for a 3,000 fps "
         "bullet. A two-stage amplifier boosts each one about 500 times. The Teensy 4.1 samples both 500,000 "
         "times a second, finds the shot, measures its pitch and works out the velocity, and saves a raw "
         "recording of every shot to its SD card. The ESP32-C3 shows the speed on the small screen and sends it to "
         "your phone over Bluetooth.")
    picture(PICS / "01_overview.png", 6.9, "Everything that connects to the main board. Red is +5 V, black ground, "
            "orange 3.3 V, green radar I, blue radar Q.")
    rich(("Power. ", True), "One 18650 cell in a battery holder makes 5 V, and the holder's own button turns BLIPR "
         "on and off (there's no separate switch). 5 V feeds the Teensy, the ESP32 through diode D1, and a separate "
         "low-noise 3.3 V regulator (U3) that powers only the radar and the amplifiers. That keeps digital noise "
         "out of the weakest signals in the build.")
    rich(("Two 5 V filters. ", True), "The radar hears more than bullets. The battery holder's boost converter "
         "whistles at about 494 kHz, and the ESP32's Bluetooth radio draws its current in bursts. Both reached the "
         "radar through the shared 5 V, so each gets a small filter: L1 (22 µH) with C27 and C28 at J1, and L2 (22 µH) "
         "with C29 and C30 in the ESP32's 5 V feed. On circuit board v1.2 both are on the board; on a v1.1 board they "
         "go in the wires, by hand (marked \"If you have a v1.1 board\" below).")
    doc.add_page_break()

    # ---------------------------------------------------------------- 1 parts
    doc.add_heading("1. Check you have everything", 1)
    doc.add_heading("Modules", 2)
    checkbox_list(["RFbeam K-LC5-RFB-00C radar (the 3.3 V version: don't substitute another suffix)",
                   "Teensy 4.1 with pins",
                   "ESP32-C3 SuperMini (buy a pack: a spare is worth having)",
                   "18650 battery holder with 5 V output and its own power button, plus a name-brand 18650 cell",
                   "0.96\" SSD1306 I2C OLED screen, 4-pin (white reads best). Bare pads or pins both work",
                   "microSD card, name brand, A1, FAT32 or exFAT. A 32 GB A1 card worked; an 8 GB card that had been in another "
                   "device wasn't read",
                   "RB BLIPR circuit board v1.2 (from PCBWay; a v1.1 board also works, see the v1.1 notes)",
                   "A micro-USB DATA cable (Teensy) and a USB-C DATA cable (ESP32). Many cables only charge: "
                   "if the computer doesn't see the board, try another cable first"])

    doc.add_heading("Parts for the circuit board", 2)
    para("Every part has its own labelled holes on the board. The board's parts list is pcb/out/RBBLIPR_BOM.csv.",
         space=4)
    table([("Ref", "Part", "Notes"),
           ("U1, U2", "MCP6022-E/P op-amp + 8-pin socket", "Buy spares. Dot (pin 1) beside the square pad"),
           ("U3", "MCP1700-3302E 3.3 V regulator (TO-92)", "Flat face toward the board's front edge"),
           ("D1", "1N5817 Schottky diode", "Often printed \"IN5817\" on the bag: same part. Stripe on the square pad"),
           ("R1, R18", "10 Ω", "Supply filters"),
           ("R2, R3, R5, R8, R12, R15", "10 kΩ", "Reference divider and feedback"),
           ("R4, R7, R11, R14, R21", "4.7 kΩ", "Input bias (R21: ammo-probe jack)"),
           ("R6, R9, R13, R16", "470 Ω", "Gain"),
           ("R10, R17", "330 Ω", "Output filter"),
           ("R19, R20", "100 kΩ", "Battery gauge"),
           ("R22", "100 Ω", "Ammo-probe jack"),
           ("R23, R24", "1 kΩ (brown, black, red)", "Serial link between the Teensy and the ESP32. v1.2: they stand on end"),
           ("R25", "10 kΩ", "Soldered on the battery holder's + tab, not on the board"),
           ("C1, C2, C14, C17, C21, C24", "1 µF ceramic", "Either way round"),
           ("C5, C8, C9, C11, C26", "100 nF ceramic", "Either way round"),
           ("C12, C15, C19, C22", "10 nF ceramic", "Either way round"),
           ("C18, C25", "1 nF ceramic", "Either way round"),
           ("C4, C7, C10", "10 µF electrolytic", "Use 25 V ones (10 V or more works; 25 V cans are smaller than 50 V)"),
           ("C3", "100 µF electrolytic", "16 V or 25 V, no wider than 6.3 mm (a 50 V can is 8 mm and crowds C4)"),
           ("Teensy socket", "2 × 1x24 female header", "The Teensy sits on these 8.5 mm sockets: the case's USB hole "
                                                       "is placed for that height"),
           ("ESP32 socket", "2 × 1x8 female header", ""),
           ("J1, J5", "1x3 header, or wires soldered straight in", "J1 battery, J5 ammo-probe jack (optional, can stay empty)"),
           ("J2", "Wires soldered straight in", "Radar: never a plug here"),
           ("J3", "Wires soldered straight in", "Screen: at the screen end, female jumper wires on its pins, or "
                                                "wires soldered to its pads"),
           ("J4", "Wires soldered straight in", "Sensor kit: snip the pins off the sensor cable and solder its wires in "
                                              "(a header plus plug stands too tall under the lid)"),
           ("L1, L2", "22 µH inductor, 1 A or more", "v1.2: on the board; drum type up to 8.4 mm across, leads 5 mm or 3.2 mm "
                                                     "apart (three holes; e.g. Würth 744772220 or small 6.7 mm drums). v1.1: in the holder's red wire and the ESP32's 5 V"),
           ("C27, C29", "470 µF electrolytic, 10 V or more", "v1.2: on the board; 8 mm across, leads 3.5 mm apart (e.g. Nichicon "
                                                            "UKA1A471MPD1TD). v1.1: across J1, and across the ESP32's 5V and GND"),
           ("C28, C30", "1 µF ceramic", "v1.2: on the board. v1.1: beside C27 and C29")],
          [1.75, 2.35, 2.8], size=10)

    doc.add_heading("Printed parts (ASA recommended)", 2)
    checkbox_list(["base.stl (case v0.12)",
                   "lid_oled.stl (or lid_sensors.stl with the sensor kit, or lid_plain.stl with no screen)",
                   "front_cover.stl, in natural, white or grey filament (never black or any filled filament: the "
                   "radar looks through it)",
                   "With the sensor kit: sensor_pod.stl and sensor_pod_roof.stl (roof in white or light grey)"])
    doc.add_heading("Hardware", 2)
    checkbox_list(["8 × M3 heat-set inserts, about 4.6-5 mm across, up to 7 mm long (4 lid corners, 4 board posts)",
                   "1 × 1/4-20 heat-set insert, 13 mm long or shorter (tripod mount)",
                   "4 × M3 × 8 mm screws (lid), 4 × M3 × 6 mm pan-head screws no wider than 5.5 mm (board)",
                   "4 × M3 × 6 mm self-tapping screws (battery holder), 4 × M2 × 4 mm screws (OLED)",
                   "Hot glue gun and glue (holds the radar in its pocket)",
                   "26-28 AWG stranded wire in at least 4 colours, heat-shrink"])
    doc.add_heading("Sensor kit (optional)", 2)
    checkbox_list(["Adafruit SHT45 temperature and humidity board",
                   "DFRobot Gravity 10-DoF IMU (SEN0696): compass, level and air pressure",
                   "2 × STEMMA QT to male pins cable, 150 mm",
                   "2 × M3 × 8 screws and 2 M3 inserts for the pod; 8 × M2.5 × 6 brass screws; 2 × M3 × 6 brass screws "
                   "(brass or nylon only near the compass, never steel)"])
    doc.add_heading("Tools", 2)
    checkbox_list(["Temperature-controlled soldering iron (about 330 °C), 0.6-0.8 mm rosin-core solder, flux pen",
                   "Multimeter with DC volts and the continuity beep: every checkpoint uses it",
                   "Digital calipers, flush cutters, wire strippers, tweezers",
                   "Hobby knife (for the Teensy's VIN-VUSB trace)",
                   "Heat-set insert tip for the iron (or the plain tip)",
                   "Isopropyl alcohol and an old toothbrush (flux clean-up)",
                   "Paint pen (pin-1 marks on the radar and its plug)"])

    # ---------------------------------------------------------------- 2 safety
    doc.add_heading("2. Safety first", 1)
    bullets([("18650 cell: ", "name-brand only. Never short its ends, never solder to the cell itself, and put it in "
                              "the way the holder is marked. Don't charge it unattended overnight the first time."),
             ("Battery out while soldering: ", "the cell stays out of the holder until a checkpoint asks for it."),
             ("Radar module: ", "static-sensitive. Touch something grounded first, hold it by its edges, and never "
                                "solder to its pins: a plug goes on them instead."),
             ("The radar plug only fits one way that's safe: ", "the radar's power and ground pins mirror each "
              "other, so a plug turned round swaps them and kills the radar. No beep test can catch it. Paint-mark "
              "pin 1 on the radar and on its plug, and always match the marks."),
             ("It's a transmitter: ", "low power, but don't hold your eye right at the antenna, and switch it off "
                                      "when not in use. It's a personal device for use at the range.")])

    # ---------------------------------------------------------------- 3 print
    doc.add_heading("3. Print the case", 1)
    para("The case is 118.8 × 130.8 mm and 38.8 mm tall with the lid, and every part prints without supports. It's also on MakerWorld, with Sean's print "
         "project (BLIPR_Case.3mf, also in case/out) ready to open: makerworld.com/en/models/3697742")
    table([("Part", "Print it", "Settings (ASA)"),
           ("base", "Floor on the bed, open top up", "0.2 mm layers, 6 walls, 4 top/bottom layers, 25% gyroid. "
                                                     "Brim. Bridges are 34 mm or shorter"),
           ("lid_oled / lid_sensors / lid_plain", "Top face on the bed", "Same settings. Print one lid"),
           ("front_cover", "Smooth outside face on the bed", "0.15 mm layers, 100% infill. The window is 0.9 mm thick"),
           ("sensor_pod, sensor_pod_roof", "Pod upright; roof flat side down", "Same as the base")],
          [1.8, 2.1, 3.0], size=10.5)
    tip("ASA warps: use an enclosure or a draft shield and a bed around 100 °C.")
    picture(IMG / "case_base_above.png", 5.4, "Base v0.12 from above, front at the top. The battery bay is on the "
            "right of this view with its four round pads; the main board's four posts and the tripod post are on the left.")
    picture(IMG / "case_base_walls.png", 6.9, "The two side walls from outside. Left: the battery holder's USB-C "
            "charge hole and the 14 × 10 mm power-button slot. Right: the Teensy's USB hole, 24-32 mm up, which "
            "matches the Teensy sitting on its 8.5 mm sockets (a 12 × 5.5 mm plug fits).")
    picture(CASE / "preview_lid.png", 6.4, "Lid v0.12 from above and below: the 13 mm screen window, and the screen pocket with "
            "its four M2 pads underneath. lid_sensors is the same with the sensor pod's two risers and cable slot.")
    rich(("What changed in v0.10 to v0.12: ", True), "the Teensy USB hole moved up to 24-32 mm (it had been too "
         "low for the socketed Teensy), the leftover stubs beside the two left battery pads are gone, and the lid's "
         "screen window is 13 mm tall (1 mm more toward the front, so the screen's top line shows).")
    doc.add_page_break()

    # ---------------------------------------------------------------- 4 firmware
    doc.add_heading("4. Load the firmware and bench-test the boards", 1)
    para("Do this before any soldering, with each board loose on the bench and powered from the computer's USB. "
         "It proves the Teensy measures a shot and the ESP32 sends it to your phone, with no radar, amplifier or "
         "battery involved. It also has to happen before you cut the Teensy's VIN-VUSB trace in section 5.")
    rich(("With Claude Code (optional): ", True), "plug the board in and say so; Claude Code builds the firmware, finds the "
         "board, flashes it and runs the checks below. The build settings and port names are in the project's "
         "CLAUDE.md.")
    rich(("By hand: ", True), "Arduino IDE 2 with the Teensy and esp32 (3.3.x) board packages and the libraries "
         "listed in firmware/README.md. Teensy: board Teensy 4.1, USB Type Serial + MTP Disk. ESP32: board Nologo "
         "ESP32C3 Super Mini, USB CDC On Boot Enabled. Ready-made files are in firmware/prebuilt/.")

    doc.add_heading("a. Teensy", 2)
    numbered([("SD card in. ", "Push the microSD card into the Teensy's slot, gold contacts toward the board. "
                               "It sits flush; there's no click."),
              ("Plug in ", "with the micro-USB data cable and load BliprTeensy. The first time, the Teensy Loader "
                           "may ask you to press the Teensy's white button."),
              ("Check: ", "type stat: 0 overruns and SD ok, firmware 0.2.8."),
              ("Set the sample rate: ", "set fs=500000, then reboot (it's saved). The battery holder's converter whistles at about "
                                        "494 kHz; sampled at 500 kHz it reads near 100 fps, out of the way, instead "
                                        "of near 2,150 fps at the default 600 kHz.")])
    tip("If it says SD missing, unplug, re-seat the card and plug in again (it only looks for the card at start-up). "
        "Still missing: try another card. An 8 GB card that had been in another device wasn't read; a 32 GB A1 "
        "card worked straight away.")

    doc.add_heading("b. Fake-bullet test", 2)
    para("The Teensy plays a fake bullet's tone on pin 2 and measures it like a real shot.")
    numbered([("Unplug, then add two jumpers: ", "pin 2 to pin 14 (A0) and pin 2 to pin 15 (A1), through a "
                                                 "1 kΩ resistor each if you have them. A breadboard makes it easy."),
              ("Plug in and run ", "sim 2800, sim 1100 and sim 3300. Each should come back within a few fps."),
              ("Take the jumpers off ", "before the Teensy ever goes near the amplifier.")])
    table([("Fake bullet", "First build read", "Signal"),
           ("2800 fps", "2800.1 fps", "50 dB"), ("1100 fps", "1100.0 fps", "50 dB"),
           ("3300 fps", "3299.9 fps", "51 dB"), ("2500 fps", "2500.2 fps (and on the phone)", "51 dB")],
          [2.0, 3.0, 1.9], size=10.5)

    doc.add_heading("c. ESP32-C3", 2)
    numbered([("Plug in ", "with a USB-C DATA cable and load BliprBLE. If the computer shows nothing at all while "
                           "the red LED is on, the cable is charge-only: swap it. If the upload won't connect, hold "
                           "BOOT, tap RESET, let go of BOOT."),
              ("Check on your phone: ", "the Range Book app (iPhone, iPad) or nRF Connect should list RB BLIPR and connect to it.")])
    tip("Load the ESP32 over USB now (firmware 0.2.20). On a v1.1 board, once its hand-wired filter is fitted (section 8), the computer sees "
        "it only when it's out of BLIPR's socket, and Range Book updates it over Bluetooth from then on.")

    doc.add_heading("d. The two boards together", 2)
    para("Leave both on their own USB cables and add three wires. Don't join 5 V or VIN between them.", space=4)
    table([("Teensy", "ESP32-C3"), ("pin 35, through 1 kΩ", "GPIO 20"), ("pin 34, through 1 kΩ", "GPIO 21"),
           ("GND", "G")], [3.45, 3.45], size=10.5)
    para("With the fake-bullet jumpers on too, a sim shot on the Teensy appears at the ESP32 and on your phone. "
         "Take every wire off afterwards.")

    # ---------------------------------------------------------------- 5 VIN-VUSB
    doc.add_heading("5. Cut the Teensy's VIN-VUSB trace", 1)
    para("On the Teensy's underside, near the USB socket, two pads marked VIN and VUSB are joined by a thin trace. "
         "Cut it with a hobby knife, a few light strokes, then check with the meter's beep: no beep between VIN and "
         "VUSB. This stops the battery and the computer's USB from fighting.")
    warn("from now on the Teensy only runs when BLIPR is switched on, including when you program it. For a "
         "later upload: switch BLIPR on first, then plug in the USB.")
    doc.add_page_break()

    # ---------------------------------------------------------------- 6 solder the board
    doc.add_heading("6. Solder the circuit board", 1)
    picture(PCB / "pcb_assembly.png", 5.6, "Board v1.2: where each part goes (top view, front edge at the bottom). "
            "The v1.1 drawing is in pcb/v1.1/out/.")
    para("Lowest parts first, so the board sits flat on the bench while you solder:")
    numbered([("Resistors. ", "Measure each with the meter before it goes in (10 Ω, 330 Ω, 470 Ω, 4.7 kΩ and 10 kΩ "
                              "look alike). R23 and R24 are 1 kΩ; on v1.2 they stand on end: bend one lead back down "
                              "beside the body, with the body over the hole inside the drawn square."),
              ("D1 (1N5817). ", "Stripe to the right, on the square pad."),
              ("Ceramic capacitors ", "(either way round), then the two 8-pin sockets with their notch pointing "
                                      "right, as drawn."),
              ("U3 (MCP1700). ", "Flat face toward the board's front edge, legs GND, IN, OUT from left to right. "
                                 "Spread the two outer legs a little to reach the holes."),
              ("Electrolytic capacitors. ", "The + leg (longer) goes in the square pad; the stripe on the can is the "
                                            "minus side. C3 (100 µF) is the small 16 V or 25 V one; C4, C7, C10 are "
                                            "10 µF 25 V. On v1.2 also C27 and C29 (470 µF, 8 mm across)."),
              ("L1 and L2 (v1.2). ", "22 µH, either way round, pushed down flat. Each has three holes in a row: the two "
                                     "outer holes are 5 mm apart, the left and middle 3.2 mm apart for small drums. Use "
                                     "whichever pair fits; the third hole stays empty. On a v1.1 board these and C27-C30 have no "
                                     "holes: they go in the wires (sections 7 and 8)."),
              ("Headers. ", "J1 and J5 as headers or wires. J2 (radar), J3 (screen) and J4 (sensor kit) get wires "
                            "soldered straight in later, no headers: a header plus plug stands too tall under the lid."),
              ("Teensy and ESP32 sockets. ", "Plug each module into its female headers, set it in place and solder "
                                             "the headers with the module in them, so they come out straight. Then "
                                             "lift the modules out again."),
              ("Clean. ", "Scrub the amplifier area with isopropyl alcohol and check every joint with a magnifier "
                          "for bridges, especially round the sockets.")])
    picture(PICS / "10_part_id.png", 6.9, "Telling the parts apart: resistor bands, capacitor codes and which way "
            "the polarised parts go.")
    doc.add_page_break()
    doc.add_heading("The ESP32 goes in chip side up", 2)
    picture(PICS / "05_esp32.png", 6.4)
    para("USB socket toward the back, antenna at the front edge. Its pin names are printed on the underside, so from "
         "above they read the other way round: don't match them by eye. Seen from above, its 5V pin is the one "
         "nearest the USB on the right-hand edge, and it goes in the back hole of the right-hand row, next to D1's "
         "square pad.")
    numbered([("Before it goes in: ", "power it from USB alone and find the pin that reads 5 V to G with the meter. "
                                      "That's the pin for that hole."),
              ("Seated, not powered: ", "beep its 5V pin to D1's square pad, and its G pin to J1 pin 2. Both must "
                                        "beep before you power up.")])
    picture(PICS / "07_opamp_pins.png", 6.4, "The op-amp sockets pin by pin. Each chip's dot goes beside the square pad.")
    doc.add_page_break()

    # ---------------------------------------------------------------- 7 power + checkpoints
    doc.add_heading("7. Battery holder and the power test", 1)
    picture(PICS / "02_power.png", 6.6)
    numbered([("Check the holder first. ", "Cell in, holder on: red probe on its 5 V pad, black on GND must read "
                                           "about +5 V, not -5 V. Nothing on the board protects against those two "
                                           "swapped. Then take the cell out."),
              ("Wire it. ", "Holder 5 V to J1 +5V, holder GND to J1 GND (use its solder pads, not the USB-A socket), "
                            "side by side. On v1.2 the filter (L1, C27, C28) is already on the board. Set the holder's "
                            "mode switch to \"power on\"."),
              ("Battery gauge. ", "With the cell out, tin the holder's + end tab and quickly solder one leg of R25 "
                                  "(10 kΩ) straight onto it. Heat-shrink it, solder a wire (orange) to its other leg "
                                  "and run that to J1 BAT. A nicked wire then can't short the cell. About 10 cm of "
                                  "wire reaches the board."),
              ("Leave out ", "the op-amps, Teensy, ESP32 and radar for now.")])
    doc.add_heading("If you have a v1.1 board: the holder's filter by hand", 2)
    numbered([("L1. ", "Cut the red wire and put L1 (22 µH, 1 A or more, either way round) in the gap."),
              ("C27 and C28. ", "470 µF (stripe to GND) and 1 µF across J1's +5V and GND, on the board side of L1, as "
                                "close to J1 as you can. Heat-shrink every joint.")])
    picture(PICS / "power_filter.png", 6.0, "v1.1 only: L1 in the red wire, C27 and C28 across J1.")
    doc.add_heading("Checkpoint 1: power (meter on DC volts, black probe on GND)", 2)
    para("Cell in, press the holder's button.", space=4)
    check([("J1 +5V", "4.9-5.2 V", "Holder off (press its button) or cell flat"),
           ("U3's OUT leg", "3.25-3.35 V", "Switch off now. 5 V or 0 V: U3 backwards. U3 hot: short on 3.3 V"),
           ("C10's + leg (VREF)", "1.60-1.70 V", "R2/R3 wrong value or not reaching GND"),
           ("Battery sense", "cell voltage ÷ 2.1 (about 1.4-2.0 V)", "Check R25, R19, R20. Write both numbers down: "
                                                                    "they calibrate the battery gauge")])
    para("All good? Switch off and take the cell out.")

    doc.add_heading("Checkpoint 2: amplifier", 2)
    para("Op-amps into their sockets (dot beside the square pad). Radar, Teensy and ESP32 still out. Cell in, on.",
         space=4)
    check([("U1, U2 pin 8", "3.25-3.35 V", "Supply to the socket"),
           ("U1, U2 pins 3 and 5", "1.60-1.70 V", "R4/R7/R11/R14 not reaching VREF"),
           ("U1, U2 pins 1 and 7", "1.60-1.70 V", "Stuck near 0 or 3.3 V: feedback part missing or bridged"),
           ("A0 and A1 (Teensy pins 14, 15)", "1.60-1.70 V", "R10/R17 open or C18/C25 shorted"),
           ("Op-amps by touch after a minute", "Not warm", "Warm: in backwards. Switch off and pull it")])
    doc.add_page_break()

    # ---------------------------------------------------------------- 8 wiring
    doc.add_heading("8. Radar, screen and modules", 1)
    picture(PICS / "03_radar.png", 6.4)
    numbered([("Mark pin 1 ", "on the radar (it's marked on the module and in RFbeam's drawing) with a paint pen, and "
                              "on the matching end of a 1x5 female header."),
              ("Four short wires on the header, ", "just long enough to reach J2 with a little slack: pin 1 Q (blue), "
                                                   "pin 2 +3.3 V (orange), pin 3 I (green), pin 4 GND (black), pin 5 "
                                                   "nothing (VCO stays unconnected). One ground wire is enough, and "
                                                   "they don't need twisting."),
              ("Solder them straight into J2 ", "(Q, VCC, I, GND as printed). Keep the bundle away from the ESP32.")])
    picture(IMG / "blipr_radar_wired.jpg", 5.4, "The radar's plug with four short wires, and the radar held in its "
            "pocket with hot glue at the sides.")
    picture(PICS / "04_teensy.png", 5.6, "The Teensy's pins this build uses. It plugs into its sockets with its USB "
            "toward the right wall.")
    rich(("Screen (OLED). ", True), "VCC to the ESP32's 3V3, GND to GND, SDA to GPIO6, SCL to GPIO7, "
         "through J3. Go by the labels on your screen, since makers order them differently. Four wires about 15 cm "
         "long, soldered straight into J3. If your screen came with pins fitted, plug female jumper wires onto them "
         "(they clear the lid); if it has bare pads, solder the wires to the pads.")
    picture(IMG / "blipr_screen_jumpers.jpg", 4.6, "A screen with pins: female jumper wires plugged on, their other "
            "ends soldered into J3.")
    doc.add_heading("If you have a v1.1 board: the ESP32's 5 V filter by hand", 2)
    para("On v1.2 this filter (L2, C29, C30) is on the board and the ESP32 plugs in with all its pins: skip this part.",
         space=4)
    picture(PICS / "esp_filter.png", 6.0)
    numbered([("Firmware first. ", "Load the ESP32 over USB (section 4) before this step."),
              ("Cut its 5V pin. ", "Module out of BLIPR, cut its 5V pin off under the black plastic with flush cutters, "
                                   "holding the module flat. Don't lever it: the first build's module got an "
                                   "intermittent USB joint here. Nothing on the board is cut."),
              ("L2 (22 µH). ", "From the socket's empty 5V hole (solder a short header pin to L2 and push it in) or from "
                              "D1's leg on the square-pad side, to the pin's stub on top of the module."),
              ("C29 and C30. ", "470 µF (stripe to GND) and 1 µF across the module's 5V stub and its GND pin, close in. "
                                "Lay L2 and C29 flat so the lid clears them."),
              ("Beep test. ", "The 5V stub to D1's square pad beeps (through L2); 5V to GND must not.")])

    picture(IMG / "blipr_inside.jpg", 5.4, "The first build with the lid off: the screen's four wires, "
            "the board with the Teensy and the ESP32, and the 18650 cell in its holder.")
    doc.add_heading("Checkpoint 3: everything powered", 2)
    para("Beep J2's VCC hole to the 3.3 V supply and GND to ground, then check by eye that the two pin-1 marks "
         "meet. Plug in the Teensy, the ESP32 and the radar plug. Put the meter on 3.3 V and keep it there, ready to "
         "pull the cell. Switch on: if it doesn't read 3.3 V within a second, or U3 gets warm, cut power.", space=4)
    check([("Screen", "READY (not NO RADAR)", "ESP32 not hearing the Teensy: R23/R24 and the shared GND"),
           ("+5 V with everything on", "4.8 V or more", "Weak cell or thin battery wires"),
           ("3.3 V with the radar on", "3.25-3.35 V", "Radar plug backwards: switch off at once"),
           ("Radar I and Q at the plug", "about 0.1-0.4 V", "0 V or 3.3 V: a wiring fault"),
           ("A0 and A1", "still 1.60-1.70 V", "Radar wires touching a supply")])
    doc.add_page_break()

    # ---------------------------------------------------------------- 9 case
    doc.add_heading("9. Put it in the case", 1)
    picture(CASE / "assembly_exploded.png", 6.9)
    numbered([("Inserts. ", "M3 inserts into the four corner columns and the four board posts (holes 4.1 mm, 7.5 mm "
                            "deep). The 1/4-20 insert into the hole under the floor (7.15 mm, 9 mm deep). Straight in, "
                            "slightly below flush; let each cool."),
              ("Radar. ", "Press it into its pocket from above, antenna face forward and flat against the window "
                          "frame, pins back. Hold it square and run hot glue down both sides, where the module meets "
                          "the pocket. Keep glue off the antenna face and the pins. Glue holds far better than foam "
                          "tape, and still peels off if the radar has to come out."),
              ("Battery holder. ", "Mode switch on \"power on\", then screw it to the four round pads with M3 × 6 "
                                   "self-tapping screws, button lined up with the rounded slot (toward the back) and USB-C with the square opening (toward the front). Gently: "
                                   "the screws cut their own thread."),
              ("Main board. ", "Onto the four posts with M3 × 6 pan-head screws (no wider than 5.5 mm in the "
                               "back-right corner, next to the Teensy socket). The Teensy's USB lines up with the "
                               "right-wall hole."),
              ("Radar plug ", "on, pin 1 to pin 1. Dress the wires down along the pocket, away from the ESP32."),
              ("Front cover. ", "Slide it down the slot behind the front wall, recessed side toward the radar."),
              ("OLED ", "(its wires already soldered on) into the pocket under the lid's window, wires toward the "
                        "board, four M2 × 4 screws, snug only."),
              ("Lid. ", "Tuck the screen wires in so nothing gets pinched, then four M3 × 8 screws into the corner "
                        "inserts. It also holds the front cover down.")])
    picture(IMG / "case_base_under.png", 2.6, "The tripod insert under the floor, at the balance point.")
    picture(IMG / "blipr_radar_side.jpg", 4.4, "Finished: the radar window on the front face, the screen in the lid's back "
            "corner, the sensor pod in front.")

    # ---------------------------------------------------------------- 10 sensor kit
    doc.add_heading("10. Sensor kit (optional)", 1)
    para("Adds air temperature, humidity, pressure, a compass and a level. The firmware finds each sensor by itself, "
         "so you can add it any time; BLIPR works the same without it.")
    picture(CASE / "pod_layout_10dof.png", 5.0, "The pod from above, roof off: DFRobot 10-DoF at the gun end, SHT45 "
            "at the other.")
    numbered([("Wiring. ", "A 150 mm QT-to-pins cable, pins snipped off and its wires soldered into J4 (black GND, red 3V3, blue SDA, yellow SCL), up through "
                           "the lid's slot into the SHT45's front socket. A second one from the SHT45's back socket to "
                           "the DFRobot board's own Gravity cable: red to +, black to -, yellow to C/R, blue to D/T. "
                           "DFRobot switch on I2C."),
              ("Pod. ", "Two M3 inserts into the lid from the top, then the pod screwed down with two M3 × 8 before the "
                        "boards go in."),
              ("Boards. ", "SHT45 on its four posts (M2.5 brass). DFRobot board parts up, holes at the front, plug toward "
                           "you, two M3 × 6 brass screws. Brass or nylon only: steel bends the compass reading."),
              ("Roof ", "on with four more brass screws."),
              ("Check in Range Book: ", "Tools › BLIPR Chronograph shows a Conditions card. Lift the front: Level "
                                        "says nose up. Then calibrate the compass once (Settings › Compass), away "
                                        "from the truck and steel benches.")])
    para("From your seat, the screen is in the back corner on the gun side and the pod in the far front corner "
         "(picture on the cover).")
    doc.add_page_break()

    # ---------------------------------------------------------------- 11 range
    doc.add_heading("11. First power-up and first shot", 1)
    para("Press the holder's button. After the start-up animation the screen shows a bubble level (with the sensor "
         "kit), the weather for 10 s, READY for 2 s, and then BLIPR arms itself and the screen goes dark. Dark means "
         "listening. After each shot the speed and the string show for the \"Show each shot for\" time (Range Book's "
         "chronograph settings, default 3 s). BLIPR doesn't listen while the screen is lit: a lit screen adds noise "
         "the radar can hear, so keep that time short.")
    picture(PICS / "screen_sequence.png", 6.9)
    numbered([("Connect. ", "Range Book 2.44 or later: the Range Book app on iPhone and iPad (App Store), or Chrome on Android: Tools › BLIPR "
                            "Chronograph › Connect chronograph › RB BLIPR. Test shot should show 2,700 fps. Range Book "
                            "sets BLIPR's clock and units, and its settings show BLIPR's window and position."),
              ("Set the window ", "a little wider than your load, in Range Book's settings (a button sets it from the "
                                  "load) or on the Teensy: set vmin=950 vmax=1200 for .22 LR standard velocity."),
              ("Place it. ", "Beside the rifle, behind the muzzle, front window downrange and the screen corner nearest "
                             "you (about 1 o'clock from your seat), level and parallel to the bore. The first .22 tests "
                             "had it about 10 cm to the side and 10 cm behind the muzzle; for a rifle start further "
                             "back, out of the blast (about 30 cm behind, 12 cm to the side). Enter where it sits in "
                             "Range Book's settings."),
              ("Level it. ", "Shim it until the screen says LEVEL and hold 3 s. After each shot BLIPR checks it hasn't "
                             "been knocked (more than 1° tilt or 5° turn) and shows the level again if so. Re-level "
                             "and update the heading (Range Book) shows it any time; Disable the level is for "
                             "shooting at an angle."),
              ("One radar at a time. ", "Two 24 GHz radar chronographs side by side interfere: with an Athlon "
                                        "Rangecraft beside it, BLIPR saw a steady line near 1,700 fps. Use one at a "
                                        "time or set them well apart."),
              ("Shoot a string. ", "Compare with another chronograph if you have one: one session against it sets "
                                   "BLIPR's calibration (each radar differs by up to about 0.4%, around 10 fps at "
                                   "2,700 fps)."),
              ("Keep the recordings. ", "With set save=1 every shot is saved. With BLIPR on, plug the Teensy's USB "
                                        "into the computer: the SD card shows up as a drive (on a Mac with the free "
                                        "OpenMTP app), and shots pause until you unplug it. Copy the shots folder and "
                                        "log.csv.")])
    warn("never send commands or handle BLIPR while someone is on the rifle. Anything at the bench waits for a break "
         "between strings.")
    rich(("Later updates. ", True), "Range Book updates the ESP32 over Bluetooth (Settings › Firmware › Update the "
         "Bluetooth board, about 30 s with ESP32 0.2.12 or later, phone close). Over USB the computer sees the ESP32 "
         "only out of BLIPR's socket. The Teensy is updated over its USB cable with BLIPR switched on.")

    # ---------------------------------------------------------------- troubleshooting
    doc.add_heading("Troubleshooting", 1)
    table([("Symptom", "Likely cause"),
           ("Computer doesn't see the ESP32 at all (LED on)", "Charge-only USB-C cable: swap it. Also check for an "
                                                              "\"Allow accessory to connect?\" pop-up on the Mac"),
           ("Teensy says SD missing", "Card not seated, or a format the Teensy can't read: re-seat, or try another card"),
           ("Teensy not seen by the computer", "Since the VIN-VUSB cut it only runs with BLIPR switched on"),
           ("Nothing turns on", "Cell flat or reversed; holder output off (press its button)"),
           ("Holder switches itself off", "Mode switch not on \"power on\", or too little load before the modules go in"),
           ("Screen says NO RADAR", "ESP32 not hearing the Teensy: pin 35 → R23 → GPIO20, pin 34 → R24 → GPIO21, "
                                    "shared GND, Teensy powered"),
           ("Op-amp output stuck at 0 or 3.3 V", "Feedback part missing or bridged, or the op-amp in backwards"),
           ("U3 hot", "Short on 3.3 V, or the radar plug turned round"),
           ("Radar I/Q at 0 V", "Radar not powered (VCC at J2) or pin 1 the wrong way"),
           ("Every shot reads the same speed, or false shots", "Interference. On the Teensy type live (the strongest "
                                                         "line and its speed) or rec (record 100 ms). Check both 5 V "
                                                         "filters, set fs=500000, keep the window clear of the line"),
           ("A steady line near 1,700 fps", "Another 24 GHz radar chronograph close by: one at a time, or far apart"),
           ("Shots missed or \"weak\"", "Window (get) covers the speed? Screen time short? Level, close to the muzzle, "
                                       "parallel to the bore? Send the recordings"),
           ("Holder's button won't switch on after charging", "Seen once after a night on the charger: take the cell "
                                                              "out, put it back, press the button"),
           ("Computer doesn't see the ESP32 in BLIPR", "Seen on the v1.1 build with the hand-wired filter: flash it out of the socket, or "
                                                      "update over Bluetooth"),
           ("Bluetooth update stops partway", "Needs ESP32 0.2.12 or later (once over USB); phone close, screen on")],
          [2.6, 4.3], size=10.5)
    doc.add_heading("Where things are", 2)
    table([("What", "Where in the project"),
           ("Firmware", "firmware/BliprTeensy, firmware/BliprBLE (ready-made files in firmware/prebuilt)"),
           ("Case files", "case/out (STL, STEP and BLIPR_Case.3mf); case/blipr_case.py rebuilds them; on MakerWorld: makerworld.com/en/models/3697742"),
           ("Circuit board", "pcb/out: v1.2 (Gerbers, BOM, assembly drawing); pcb/v1.1: the v1.1 files"),
           ("Parts list with prices", "docs/RB_BLIPR_Parts_List.xlsx (docs/make_parts_list.py)"),
           ("Assembly video", "YouTube: https://youtu.be/nRWELvyEKN8 (tools/video makes it)"),
           ("Wiring pictures", "pictures/out"),
           ("Session logger, recordings", "tools/blipr_log.py, tools/pull_shots.py"),
           ("This guide", "docs/make_build_doc.py rebuilds it; docs/make_build_pdf.py makes the PDF")],
          [2.0, 4.9], size=10.5)

    doc.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
