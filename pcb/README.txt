Range Book BLIPR main board v1.1 (PCB)
================================

v1.1 replaces v1.0. Do not order v1.0: its ESP32-C3 socket was mirrored and would have put 5 V on GPIO5.
What changed in v1.1:
  - U4 (ESP32-C3 SuperMini) pin order fixed. Seen from the chip side with the USB at the top, the
    real module has 5V, GND, 3V3, 4, 3, 2, 1, 0 down its RIGHT edge; the board now matches that.
  - U4 moved to the front-left corner with its antenna end at the board's front edge, and no
    copper pour (and no tracks between its pin rows) under the antenna.
  - The Teensy <-> ESP32 serial link now uses Teensy Serial8 (pins 34 and 35, at the left end of
    the Teensy's front row) instead of pins 0 and 1, with a 1 k resistor (R23, R24) in each line.
    Firmware 0.2.2 or newer is needed.
  - C13, C16, C20 and C23 (22 pF) removed: they cut the amplifier's gain at the fastest speeds.
  - C6 removed and the radar header J2 is now 4 pins (Q, VCC, I, GND): radar pin 5 (VCO) is left
    unconnected, which RFbeam's datasheet allows.
  - C8 and C9 moved right beside pin 8 of each op-amp.
  - J3, J4, J5, D1 and the battery-divider parts moved to make room.

A two-layer, through-hole circuit board that replaces the 70 x 90 mm perfboard. Same size and the same four
M3 holes 3 mm in from the corners, so it drops onto the posts of the base you've already printed. Every part
from the parts list solders straight into it; the Teensy 4.1 and ESP32-C3 plug into female headers.

FILES
  RBBLIPR_PCB_v1.1_gerbers.zip   upload THIS to PCBWay (or JLCPCB, OSH Park, Aisler...)
  RBBLIPR_BOM.csv                what goes where, by reference (R1, C3, ...)
  pcb_assembly.png                where each part goes (print it and keep it on the bench)
  pcb_top.png, pcb_bottom.png     the copper, for reference
  gerber_view_top.png / _bottom   the Gerber files drawn back out (what the factory will make)
  source/                         the Python that made it (placement, netlist, routing, Gerbers)

ORDERING ON PCBWAY (pcbway.com > PCB Instant Quote > Quick-order PCB > Add Gerber file)
  It reads the size (70 x 90 mm) and layers from the zip. Leave everything at the standard choice:
    Layers: 2                 Material: FR-4            Thickness: 1.6 mm
    Min track/spacing: 6/6 mil (the board uses 0.25 mm = 10 mil)   Min hole: 0.3 mm
    Solder mask: any colour   Silkscreen: white          Surface finish: HASL lead-free
    Copper: 1 oz              Quantity: 5 (the minimum; it costs about the same as 1)
  Typical price: about US $5 for 5 boards plus shipping ($15 to $25 by the cheapest courier),
  1 to 2 weeks to your door. PCBWay checks the files before making them and emails you if
  anything looks wrong.

ASSEMBLED BOARDS (PCBA)
  out/pcba/ has what PCBWay needs to quote boards with the parts already soldered on (everything except
  the wire headers J1-J5): BOM with part numbers, part positions, assembly drawing and README_PCBA.txt
  with the quote-form answers. Rebuild them with python3 pcba_files.py.
  NOTE on J4 (sensors): the BOM below lists a 1x4 MALE header, but the STEMMA QT-to-pins cable also ends
  in male pins. Fit a 1x4 FEMALE header at J4 if you want that cable to plug in, or solder its wires straight in.

ASSEMBLY ORDER (lowest parts first, so the board sits flat while you solder)
  1. Cut the VIN-VUSB trace on the underside of the Teensy (see the build guide) before it goes in,
     but only after the Firmware tab's bench tests: those run the Teensy from USB alone.
  2. Resistors (match the colour bands; picture 10 in the wiring pictures), then D1: its stripe goes
     to the right, on the SQUARE pad (the drawn band shows the same end). R23 and R24 are 1 k
     (brown, black, red).
  3. Ceramic capacitors (no polarity), then the two DIP-8 sockets (notch matches the drawing: it
     points RIGHT on this board, the opposite of the perfboard steps).
  4. U3 (MCP1700): flat face toward the board's front edge, legs GND - IN - OUT left to right.
     Its legs are closer together than the holes: spread the two outer legs a little.
  5. Electrolytic capacitors: the + leg goes in the SQUARE pad (the stripe on the can is the - side).
  6. Headers J1 to J5 (or solder wires straight into them; do that for J2, the radar, so nothing
     there can be plugged in backwards), then the female headers for the
     Teensy (2 x 24) and ESP32 (2 x 8). Plug the modules into their headers while you solder the
     headers, so they come out straight. The ESP32 goes in chip side UP (USB socket and buttons
     on top), USB toward the back, its antenna end at the board's front edge.
  7. Battery holder to J1 (no switch: the holder's own button is on/off). Before soldering its
     wires, meter its 5V and GND pads with the cell in: +5 V, not -5 V. Nothing on the board
     protects against those two swapped.
  8. Power test BEFORE plugging in the op-amps and modules (the build guide's Step 2 checkpoint):
     +5 V at J1, 3.3 V at U3's OUT leg, about 1.65 V at VREF (the + leg of C10).
  9. Op-amps into the sockets (each chip's dot beside the SQUARE pad), Teensy and ESP32 in, then
     wire the radar and OLED.

THE RADAR PLUG
  The radar's power (pin 2) and ground (pin 4) mirror each other around pin 3, so a 5-way plug
  turned round on the radar swaps them, and no beep test can tell. Paint-mark pin 1 on the module
  and on the plug, and watch +3V3A on the meter the first time it's powered: anything but 3.3 V,
  or U3 warming, means cut power at once.

CHECK BEFORE SOLDERING THE ESP32
  The SuperMini's pin names are printed on its UNDERSIDE, so from above they read mirrored.
  Don't match the printed names to the board by eye. Instead:
    1. Hold the module chip side up, USB socket pointing away from you (toward the board's back).
       Its 5V pin is the one nearest the USB socket on the RIGHT-hand edge.
    2. Turn it over to confirm: on the underside, with the USB still pointing away from you, the
       pin marked 5V is now on the LEFT, nearest the USB.
    3. On the board, the hole marked 5V is at the back of the RIGHT-hand row (beside D1's square pad).
    4. Electrical check that doesn't depend on the labels: power the module from USB alone and
       find the pin that reads 5 V to G with the meter. That is the pin for the 5V hole.
  With the module seated (not powered), beep from the module's 5V pin to D1's square pad and from
  its G pin to J1 pin 2. Both must beep. If either doesn't, stop and ask.

WHAT WAS CHECKED
  - Netlist matches schematic v0.5 (including the sensor kit parts R21, R22, J4, J5).
  - Design-rule check on tracks and pads: 0.25 mm clearance, 0 problems; every net fully connected.
    The ground pour keeps 0.35 mm from other copper and its thermal spokes at least 0.3 mm.
    (PCBWay's minimum is 0.1 mm.) The five vias are 0.3 mm drill / 0.6 mm pad.
  - Oct 29, 2026: a second, independent check rebuilt every connection from the Gerber files
    themselves and checked each part's pin order and polarity against its datasheet: all match.
  - Ground pour on the bottom with thermal reliefs; no pour, and no tracks between the pin rows,
    under the ESP32's antenna end.
  - The ESP32 pin order was checked against top and bottom photos of the real module.
  - The Gerbers were read back and drawn independently (gerber_view_*.png).
  The M3 screw at the back-right corner sits close to the Teensy's header: use a pan-head
  screw no wider than 5.5 mm.
  Before ordering: print pcb_assembly.png at 100% (or the 3D-printed hole-check plate), lay the
  ESP32 on it chip side up and confirm its 5V pin sits over the hole marked 5V.
  Not built yet: treat v1.1 as a first run. Order 5, build one, and tell Claude what you find.
