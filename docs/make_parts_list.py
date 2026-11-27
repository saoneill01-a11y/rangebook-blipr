"""Rebuild docs/RB_BLIPR_Parts_List.xlsx (the builder's parts list) from the table below.

Run:  python docs/make_parts_list.py
Keeps the workbook's look (header colours, yellow Bought? column, $ formats) and rewrites every row.
Prices are rough estimates before shipping and tax; edit them in the table or in the sheet.
"""
import os
from copy import copy
import openpyxl
from openpyxl.worksheet.datavalidation import DataValidation

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "RB_BLIPR_Parts_List.xlsx")

AMZ = "https://www.amazon.com/s?k="
# (part, group, where, search term / part no., qty, low, high, link, notes)
ROWS = [
    # ---------------- main build
    ("RFbeam K-LC5-RFB-00C radar module (3.3 V version)", "Required", "DigiKey", "DigiKey 2012-K-LC5-RFB-00C-ND", 1, 40, 50,
     "https://www.digikey.com/en/products/result?keywords=K-LC5-RFB-00C",
     "Order the -00C: it is the 3.3 V version the circuit is built for. Check the supply voltage before substituting another suffix. Not sold on Amazon/AliExpress."),
    ("RB BLIPR circuit board v1.1 (5 boards)", "Required", "PCBWay (or JLCPCB, OSH Park, Aisler)", "RBBLIPR_PCB_v1.1_gerbers.zip (pcb/out/)", 1, 20, 30,
     "https://www.pcbway.com/orderonline.aspx",
     "Upload the Gerber zip unopened, standard settings (2 layers, FR-4, 1.6 mm, HASL, 1 oz). About $5 plus $15-25 shipping. Order v1.1, never v1.0. Or hand-wire the circuit on a 70 x 90 mm double-sided perfboard."),
    ("Teensy 4.1 (with pins)", "Required", "PJRC", "TEENSY41_PINS", 1, 35.5, 35.5,
     "https://pjrc.com/store/teensy41_pins.html", "Buy direct; Amazon resellers often mark it up."),
    ("ESP32-C3 SuperMini (2-3 pack)", "Required", "Amazon / AliExpress", "ESP32-C3 SuperMini", 1, 8, 12,
     AMZ + "ESP32-C3+SuperMini",
     "Buy the 16-pin SuperMini: 22.5 x 18 mm, USB-C at one end, ceramic antenna at the other, pin names on the underside. Get a pack: a spare is worth having (the first build's module got an intermittent USB joint after its 5V pin was cut). Boards sold as ESP32-C3 Mini, Pro Mini or HW-466 can have other pinouts."),
    ("Microchip MCP6022-E/P op-amp (DIP-8)", "Required", "DigiKey", "MCP6022-E/P", 4, 1.86, 1.86,
     "https://www.digikey.com/en/products/detail/microchip-technology/MCP6022-E-P/683219",
     "U1, U2. Two needed, two spares. Order with the radar to save shipping."),
    ("Microchip MCP1700-3302E/TO 3.3 V regulator (TO-92)", "Required", "DigiKey", "MCP1700-3302E/TO", 2, 0.4, 0.6,
     "https://www.digikey.com/en/products/detail/microchip-technology/MCP1700-3302E-TO/652680",
     "U3: quiet 3.3 V for the radar and amplifiers. One spare."),
    ("18650 battery holder with 5 V boost output, own power button and USB-C charging", "Required", "Amazon / AliExpress", "18650 battery shield 5V USB-C button", 1, 5, 8,
     AMZ + "18650+battery+shield+5V+USB-C",
     "BT1. Its button is BLIPR's on/off switch (no separate switch); set its mode switch to 'power on'. Screws to the 4 pads in the base. Its converter whistles at ~494 kHz: the L1 filter below is needed."),
    ("18650 cell, button top", "Required", "Battery retailer", "18650 battery button top (Samsung, Molicel, LG)", 1, 8, 12,
     AMZ + "18650+battery+button+top+Samsung+Molicel", "Name brand. Avoid '9900 mAh' fakes."),
    ("microSD card, 32 GB, A1", "Required", "Amazon / AliExpress", "microSD 32GB A1 (SanDisk, Samsung)", 1, 6, 8,
     AMZ + "microSD+card+32GB+A1",
     "In the Teensy; stores raw shot recordings. A name-brand 32 GB A1 card worked on the first build; an 8 GB card that had been in another device wasn't read. FAT32 or exFAT."),
    ("Resistor + ceramic capacitor assortment kits", "Required", "Amazon / AliExpress", "resistor assortment kit 1/4W; ceramic capacitor assortment kit", 1, 15, 20,
     AMZ + "resistor+assortment+kit+1%2F4W",
     "Resistors: 10, 100, 330, 470, 1k, 4.7k, 10k, 100k. Ceramic: 1 nF, 10 nF, 100 nF, 1 uF (the 1 uF also covers C28 and C30 in the filters). No 22 pF needed (board v1.1)."),
    ("Electrolytic capacitor assortment kit", "Required", "Amazon / AliExpress", "electrolytic capacitor assortment kit", 1, 10, 15,
     AMZ + "electrolytic+capacitor+assortment+kit",
     "10 uF (C4, C7, C10) and 100 uF (C3), 10 V or more; C3 no wider than 6.3 mm (16 V or 25 V types)."),
    ("470 uF electrolytic capacitor, 10 V or more", "Required", "Amazon / DigiKey", "470uF 16V radial electrolytic", 2, 0.3, 1,
     AMZ + "470uF+16V+radial+electrolytic+capacitor",
     "C27 (battery filter, across J1) and C29 (ESP32 filter, across the module's 5V and GND). Stripe (-) to GND. Often in the assortment kit."),
    ("22 uH inductor, 1 A or more, through-hole", "Required", "Amazon / DigiKey", "22uH radial inductor 1A", 2, 0.5, 1.5,
     AMZ + "22uH+radial+power+inductor+1A",
     "L1 in the battery holder's red 5 V wire, L2 in the ESP32's own 5 V feed. Either way round. Added Nov 2026: the holder's converter and the ESP32's Bluetooth bursts reached the radar through the 5 V supply."),
    ("1N5817 Schottky diodes", "Required", "Amazon / AliExpress", "1N5817 schottky diode", 1, 5, 7,
     AMZ + "1N5817+schottky+diode", "D1: stops the ESP32's USB back-feeding the battery rail. The bag may say IN5817: same part."),
    ("DIP-8 IC sockets", "Required", "Amazon / AliExpress", "DIP 8 pin IC socket", 1, 5, 7,
     AMZ + "DIP+8+pin+IC+socket", "Two needed, so the op-amps can be swapped."),
    ("Female header strips, 2.54 mm", "Required", "Amazon / AliExpress", "female header pins 2.54mm", 1, 6, 6,
     AMZ + "female+header+pins+2.54mm",
     "Teensy (2 x 24), ESP32 (2 x 8), the radar's 1 x 5 plug (only pins 1-4 get wires) and, with the sensor kit, J4 (1 x 4 female: the sensor cable ends in male pins)."),
    ("0.96\" OLED SSD1306 I2C display, 4-pin", "Required", "Amazon / AliExpress", "0.96 inch OLED SSD1306 I2C", 1, 6, 8,
     AMZ + "0.96+inch+OLED+SSD1306+I2C",
     "White reads best. Wired directly: solder 4 wires (about 15 cm) to its pads and into J3. If it came with header pins fitted, remove them: under the lid a header plus plug-on (Dupont) jumpers stands too tall."),
    ("26 AWG stranded hookup wire, several colours", "Required", "Amazon / AliExpress", "26 AWG silicone wire kit", 1, 10, 14,
     AMZ + "26+AWG+silicone+stranded+wire+kit", "Radar, battery and screen wires; red/black plus 2+ signal colours."),
    ("Heat-shrink tubing assortment", "Required", "Amazon / AliExpress", "heat shrink tubing assortment", 1, 5, 8,
     AMZ + "heat+shrink+tubing+assortment", "Covers R25 at the cell tab and every joint of the two 5 V filters."),
    ("M3 heat-set inserts (4.6-5 mm OD, up to 7 mm long)", "Required", "Amazon / AliExpress", "M3 heat set inserts", 1, 8, 10,
     AMZ + "M3+heat+set+inserts+brass", "8: 4 in the base corners for the lid, 4 in the board posts (+2 for the sensor pod). Holes are 4.1 mm across, 7.5 mm deep."),
    ("M3 screw assortment (M3x6, M3x8, self-tapping M3x6)", "Required", "Amazon / AliExpress", "M3 screw assortment kit", 1, 8, 12,
     AMZ + "M3+screw+assortment+kit",
     "4 x M3x8 for the lid, 4 x M3x6 pan head for the board (no wider than 5.5 mm in the back-right corner), 4 x M3x6 self-tapping for the battery holder."),
    ("M2 x 4 mm screws", "Required", "Amazon / AliExpress", "M2 screw assortment", 1, 4, 7,
     AMZ + "M2+screw+assortment+kit", "4, hold the OLED to the pads under the lid. Snug only."),
    ("1/4-20 heat-set insert, 13 mm long or shorter", "Required", "Amazon / AliExpress", "1/4-20 heat set threaded insert", 1, 8, 8,
     AMZ + "1%2F4-20+heat+set+threaded+insert", "Tripod mount. Hole is 7.15 mm across and 9 mm deep (check the seller's size)."),
    ("Foam tape, 1 mm thick x 5 mm wide", "Required", "Amazon", "1mm foam tape 5mm", 1, 4, 7,
     AMZ + "1mm+thick+foam+tape+5mm", "About 150 mm: holds the radar snug in its pocket (sides, back and a 20 mm strip on top)."),
    ("ASA filament (plus natural/white for the front cover)", "Required", "Amazon / any", "ASA filament 1kg", 1, 20, 28,
     AMZ + "ASA+filament", "Base, lid and pod. The front cover (radar window) must be natural, white or grey, never black or filled filament."),
    ("Breadboard + jumper wire kit", "Required", "Amazon / AliExpress", "breadboard jumper wire kit", 1, 8, 10,
     AMZ + "breadboard+jumper+wire+kit", "Bench tests only (the fake-bullet test and the Teensy-ESP32 link). Nothing in the finished BLIPR uses plug-on jumpers."),
    # ---------------- sensor kit
    ("Adafruit SHT45 temperature + humidity (STEMMA QT)", "Sensor kit", "Adafruit / DigiKey", "Adafruit 5665", 1, 12.5, 12.5,
     "https://www.adafruit.com/product/5665", "Air temperature (+/-0.1 C) and humidity. In the vented pod on the lid."),
    ("DFRobot Gravity 10-DoF IMU (BMI323 + BMM350 + BMP581)", "Sensor kit", "DFRobot / Amazon", "DFRobot SEN0696", 1, 19.9, 19.9,
     "https://www.dfrobot.com/product-3126.html",
     "Level, compass and air pressure on one board; replaces the earlier Adafruit BMP390 and 9-DoF IMU. In the pod, at the end toward the gun. Don't fit a pin header on it: too tall for the pod."),
    ("STEMMA QT cable to male header pins, 150 mm", "Sensor kit", "Adafruit / DigiKey", "Adafruit 4209", 2, 0.95, 0.95,
     "https://www.adafruit.com/product/4209",
     "One from J4 up through the lid's cable slot to the SHT45; one from the SHT45's second socket into the DFRobot's own Gravity cable, whose wires end in female sockets."),
    ("STEMMA QT cable, 100 mm (only if needed)", "Sensor kit", "Adafruit / DigiKey", "Adafruit 4210", 0, 0.95, 0.95,
     "https://www.adafruit.com/product/4210", "Only if your DFRobot's Gravity cable has bare wire ends instead of sockets."),
    ("M2.5 x 6 mm brass screws (pan head)", "Sensor kit", "Amazon / AliExpress", "M2.5 x 6mm brass pan head screws", 1, 4, 9,
     AMZ + "M2.5+x+6mm+brass+pan+head+screws", "8: 4 for the SHT45, 4 for the pod roof. Brass, not steel: they sit next to the compass."),
    ("M3 x 6 mm brass screws", "Sensor kit", "Amazon / AliExpress", "M3 x 6mm brass screws", 1, 4, 7,
     AMZ + "M3+x+6mm+brass+screws", "2, hold the DFRobot board on its posts. Brass, not steel."),
    ("M3 x 8 screws + 2 M3 heat-set inserts (pod to lid)", "Sensor kit", "from the kits above", "", 1, 0, 0,
     "", "Your M3 screw and insert kits already have them."),
]

def main():
    wb = openpyxl.load_workbook(PATH)
    ws = wb.active
    # style templates from the existing first data row and totals
    tpl = {c: copy(ws.cell(5, c)._style) for c in range(1, 13)}
    tot_lbl, tot_val = copy(ws["H37"]._style), copy(ws["I37"]._style)
    note_style = copy(ws["A42"]._style)
    height = ws.row_dimensions[5].height
    for row in ws.iter_rows(min_row=5, max_row=ws.max_row):
        for c in row:
            c.value = None; c.hyperlink = None; c._style = copy(ws["M1"]._style)
    ws.data_validations.dataValidation = []

    ws["A1"] = "Range Book BLIPR — Parts List"
    ws["A2"] = ("Updated Nov 26, 2026 for circuit board v1.1, case v0.12, Teensy firmware 0.2.8 and ESP32 0.2.20. New since the first "
                "build: the two 5 V noise filters (L1, C27, C28 at the battery holder; L2, C29, C30 at the ESP32), the DFRobot "
                "10-DoF sensor board, and the screen wired directly. Prices are estimates before shipping and tax. Set Bought? "
                "to Yes as you order; the Remaining total updates.")
    r = 5
    for (part, grp, where, term, qty, lo, hi, link, notes) in ROWS:
        vals = ["No", part, grp, where, term, qty, lo, hi, "=F%d*G%d" % (r, r), "=F%d*H%d" % (r, r), "Open" if link else "", notes]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(r, c, v)
            cell._style = copy(tpl[c])
        if link:
            ws.cell(r, 11).hyperlink = link
        ws.row_dimensions[r].height = height
        r += 1
    last = r - 1
    dv = DataValidation(type="list", formula1='"Yes,No"', allow_blank=True)
    dv.add("A5:A%d" % last)
    ws.add_data_validation(dv)
    r += 1
    for lbl, f in (("Total (all parts)", "=SUM({c}5:{c}%d)" % last),
                   ("Total (required only)", '=SUMIFS({c}5:{c}%d,C5:C%d,"Required")' % (last, last)),
                   ("Sensor kit (optional)", '=SUMIFS({c}5:{c}%d,C5:C%d,"Sensor kit")' % (last, last)),
                   ("Remaining to buy", '=SUMIFS({c}5:{c}%d,A5:A%d,"<>Yes")' % (last, last))):
        ws.cell(r, 8, lbl)._style = copy(tot_lbl)
        for col in ("I", "J"):
            c = ws["%s%d" % (col, r)]
            c.value = f.format(c=col); c._style = copy(tot_val)
        r += 1
    r += 1
    ws.cell(r, 1, "Legend: yellow = mark Yes/No as you buy · blue = editable inputs (qty, prices) · black = formulas.")._style = copy(note_style)
    ws.cell(r + 1, 1, "Sources: DigiKey (MCP6022-E/P $1.86; K-LC5-RFB-00C part no. and 3.3 V rating; MCP1700), PJRC (Teensy 4.1 with pins "
            "$35.50), Adafruit (Oct 20, 2026) and DFRobot (Oct 23, 2026) sensor prices; other prices are typical marketplace "
            "estimates. Reference names (R1, C27, L1 ...) match the build guide and pcb/out/RBBLIPR_BOM.csv.")._style = copy(note_style)
    wb.save(PATH)
    print("wrote", PATH, "rows", 5, "-", last)

if __name__ == "__main__":
    main()
