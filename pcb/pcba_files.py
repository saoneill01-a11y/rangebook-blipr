#!/usr/bin/env python3
"""Files for a PCBWay assembly (PCBA) quote of the BLIPR board v1.1: parts list (BOM) with manufacturer part
numbers, part positions (centroid), assembly drawing and a README with the quote-form answers.
    python3 pcba_files.py            ->  out/pcba/
Everything on the board is through-hole. Fitted: all resistors and capacitors, D1, U3, the two DIP-8 sockets
with the MCP6022s in them, and the female socket strips for the Teensy (U5) and the ESP32 (U4).
Not fitted (DNP): J1-J5, the wire headers; the builder solders wires or headers there to suit."""
import csv, os, shutil
import design as D
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "pcba")

RES = ("Yageo", "MFR-25FBF52-{}", "Resistor, metal film, 1/4 W, 1 %, axial, 10.16 mm (0.4 in) lead spacing, lay flat")
LINES = [
    # (refs, value, manufacturer, part number, description, package, notes)
    (["R1", "R18"], "10 ohm", RES[0], RES[1].format("10R"), RES[2], "Axial, 10.16 mm", "Equivalent OK"),
    (["R22"], "100 ohm", RES[0], RES[1].format("100R"), RES[2], "Axial, 10.16 mm", "Equivalent OK"),
    (["R10", "R17"], "330 ohm", RES[0], RES[1].format("330R"), RES[2], "Axial, 10.16 mm", "Equivalent OK"),
    (["R6", "R9", "R13", "R16"], "470 ohm", RES[0], RES[1].format("470R"), RES[2], "Axial, 10.16 mm", "Equivalent OK"),
    (["R23", "R24"], "1 kohm", RES[0], RES[1].format("1K"), RES[2], "Axial, 10.16 mm", "Equivalent OK"),
    (["R4", "R7", "R11", "R14", "R21"], "4.7 kohm", RES[0], RES[1].format("4K7"), RES[2], "Axial, 10.16 mm", "Equivalent OK"),
    (["R2", "R3", "R5", "R8", "R12", "R15"], "10 kohm", RES[0], RES[1].format("10K"), RES[2], "Axial, 10.16 mm", "Equivalent OK"),
    (["R19", "R20"], "100 kohm", RES[0], RES[1].format("100K"), RES[2], "Axial, 10.16 mm", "Equivalent OK"),
    (["C18", "C25"], "1 nF", "KEMET", "C330C102J5G5TA", "Ceramic capacitor, C0G/NP0, 50 V, radial", "Radial, 5.08 mm lead spacing",
     "Equivalent OK: C0G/NP0, 50 V or more, 5.0/5.08 mm leads"),
    (["C12", "C15", "C19", "C22"], "10 nF", "KEMET", "C330C103J5G5TA", "Ceramic capacitor, C0G/NP0, 50 V, radial", "Radial, 5.08 mm lead spacing",
     "Equivalent OK: C0G/NP0 or X7R, 50 V or more, 5.0/5.08 mm leads"),
    (["C5", "C8", "C9", "C11", "C26"], "100 nF", "KEMET", "C330C104K1R5TA", "Ceramic capacitor, X7R, 100 V, radial", "Radial, 5.08 mm lead spacing",
     "Equivalent OK: X7R, 25 V or more, 5.0/5.08 mm leads"),
    (["C1", "C2", "C14", "C17", "C21", "C24"], "1 uF", "KEMET", "C330C105K5R5TA", "Ceramic capacitor, X7R, 50 V, radial", "Radial, 5.08 mm lead spacing",
     "Equivalent OK: X7R, 25 V or more, 5.0/5.08 mm leads"),
    (["C4", "C7", "C10"], "10 uF", "Nichicon", "UVR1C100MDD", "Aluminium electrolytic capacitor, 16 V, 5 x 11 mm", "Radial, 5 mm dia, 2.0 mm lead spacing",
     "POLARISED: + lead in the SQUARE pad. Equivalent OK: 10 V or more, 5 mm dia, 2.0 mm leads"),
    (["C3"], "100 uF", "Nichicon", "UPW1C101MED", "Aluminium electrolytic capacitor, 16 V, 6.3 x 11 mm", "Radial, 6.3 mm dia, 2.5 mm lead spacing",
     "POLARISED: + lead in the SQUARE pad. Must be 6.3 mm diameter (8 mm crowds C4). Equivalent OK: 16 or 25 V, 6.3 mm, 2.5 mm leads"),
    (["D1"], "1N5817", "onsemi", "1N5817RLG", "Schottky diode, 20 V, 1 A, DO-41", "Axial DO-41, 10.16 mm",
     "POLARISED: stripe (cathode) on the SQUARE pad (right-hand end, as drawn)"),
    (["U3"], "MCP1700-3302E/TO", "Microchip", "MCP1700-3302E/TO", "3.3 V LDO regulator", "TO-92",
     "Flat face toward the board's front edge (as drawn); pins GND-IN-OUT left to right. No substitute."),
    (["U1", "U2"], "MCP6022-E/P", "Microchip", "MCP6022-E/P", "Dual op-amp", "DIP-8 (in socket)",
     "Insert into the U1/U2 sockets after soldering them, NOT soldered: pin 1 (dot) at the SQUARE pad. No substitute."),
    (["U1", "U2"], "DIP-8 socket", "On Shore Technology", "ED08DT", "IC socket, 8 pin, 7.62 mm (0.3 in) rows", "DIP-8",
     "Notch as printed on the board (points RIGHT). Solder the socket only; the op-amp is pushed in afterwards."),
    (["U5"], "1x24 female header (2 per board)", "Sullins", "PPTC241LFBN-RC", "Female header, 24 pos, 2.54 mm, single row, straight",
     "Through hole", "2 strips per board for the Teensy 4.1 socket, rows 15.24 mm apart. Solder square and straight (use a "
     "jig or a spare Teensy). Do NOT install a Teensy."),
    (["U4"], "1x8 female header (2 per board)", "Sullins", "PPTC081LFBN-RC", "Female header, 8 pos, 2.54 mm, single row, straight",
     "Through hole", "2 strips per board for the ESP32-C3 SuperMini socket, rows 15.24 mm apart. Solder square and straight. "
     "Do NOT install a module."),
    (["J1", "J2", "J3", "J4", "J5"], "DNP", "", "", "Wire headers: do not fit", "", "DO NOT PLACE (DNP): leave the holes empty; the builder solders wires or headers."),
]


def qty_per_board(refs, value):
    if "2 per board" in value:
        return 2
    return len(refs)


def main():
    os.makedirs(OUT, exist_ok=True)
    # ---------- BOM ----------
    wb = Workbook()
    ws = wb.active
    ws.title = "BOM"
    head = ["Item", "Qty per board", "Designators", "Value", "Manufacturer", "Manufacturer part number", "Description",
            "Package / footprint", "Type", "Notes for assembly"]
    ws.append(["Range Book BLIPR main board v1.1 (70 x 90 mm, 2 layers): PCBA bill of materials. All parts through-hole, top side."])
    ws.append([])
    ws.append(head)
    for c in range(1, len(head) + 1):
        ws.cell(3, c).font = Font(bold=True)
        ws.cell(3, c).fill = PatternFill("solid", fgColor="DDEBF7")
    tht = 0
    for i, (refs, value, mfr, mpn, desc, pkg, notes) in enumerate(LINES, 1):
        q = 0 if value == "DNP" else qty_per_board(refs, value)
        if value != "DNP" and not mpn.startswith("MCP6022"):
            tht += q
        if mpn.startswith("MCP6022"):
            tht += 0
        ws.append([i, q, ", ".join(refs), value, mfr, mpn, desc, pkg, "THT" if value != "DNP" else "DNP", notes])
    ws.append([])
    ws.append(["Off the board (not part of this order): R25 (10 k, soldered at the battery holder), the Teensy 4.1, the ESP32-C3 "
               "SuperMini and all wiring are fitted by the builder."])
    widths = [6, 8, 30, 22, 18, 22, 44, 30, 7, 70]
    for c, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(c)].width = w
    for row in ws.iter_rows(min_row=4):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    wb.save(os.path.join(OUT, "RBBLIPR_v1.1_PCBA_BOM.xlsx"))

    # ---------- part positions (centroid) ----------
    fitted = [r for refs, value, *_ in LINES if value != "DNP" for r in refs]
    seen = []
    with open(os.path.join(OUT, "RBBLIPR_v1.1_PCBA_positions.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X (mm)", "Mid Y (mm)", "Layer", "Rotation"])
        for r in fitted:
            if r in seen:
                continue
            seen.append(r)
            p = D.P[r]
            w.writerow([r, "%.2f" % p["x"], "%.2f" % p["y"], "Top", p["rot"] % 360])

    # ---------- drawing and Gerbers ----------
    shutil.copy(os.path.join(HERE, "out", "pcb_assembly.png"), os.path.join(OUT, "RBBLIPR_v1.1_assembly_drawing.png"))
    shutil.copy(os.path.join(HERE, "out", "RBBLIPR_PCB_v1.1_gerbers.zip"), os.path.join(OUT, "RBBLIPR_PCB_v1.1_gerbers.zip"))
    unique = len([l for l in LINES if l[1] != "DNP"])
    parts = sum(qty_per_board(l[0], l[1]) for l in LINES if l[1] != "DNP")
    print("BOM lines (unique parts): %d, parts per board: %d (%d soldered, %d op-amps pushed into sockets), positions: %d"
          % (unique, parts, parts - 2, 2, len(seen)))


if __name__ == "__main__":
    main()
