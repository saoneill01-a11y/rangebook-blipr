Range Book BLIPR main board v1.2 (PCB)
================================

v1.2 (Nov 2026) is the board to order. It is v1.1 with the two 5 V noise filters ON the board:
  - L1 (22 uH) + C27 (470 uF) + C28 (1 uF): the battery holder's 5 V comes in at J1, through L1. On v1.1
    L1 sat in the holder's red wire and C27/C28 were soldered across J1.
  - L2 (22 uH) + C29 (470 uF) + C30 (1 uF): the ESP32's own 5 V, from D1 through L2 to the module's 5V
    pin. On v1.1 the ESP32's 5V pin had to be cut and L2/C29/C30 wired to the module by hand.
    (Why: the holder's boost converter and the ESP32's Bluetooth bursts both reached the radar through
    the shared 5 V; see the build guide.)
  - To make room: R19-R22 and C26 moved up 2.5 mm and right 0.9 mm; R23 and R24 now stand on end
    (one lead bent back down beside the body).
  - Same size, holes, connectors and module positions: the v1.1 case fits, and the ESP32 now plugs in
    with ALL its pins (nothing to cut).
  - The new parts are up to 12 mm tall; there is about 20 mm under the lid.
  Inductors: 22 uH, 1 A or more, round (drum) type up to 8.4 mm across with leads 5 mm apart, e.g. Wurth
  744772220 (8.3 mm, 2.3 A). 470 uF: 10 V or more, 8 mm across, leads 3.5 mm apart (e.g. Nichicon
  UKA1A471MPD1TD). Check yours fit those sizes before soldering.
  Building on a v1.1 board? Everything for v1.1 (Gerbers, pictures, the PCBA files and the source as it
  was) is kept in v1.1/, and the build guide still covers the v1.1 way of fitting the filters.

v1.1 history:
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
  RBBLIPR_PCB_v1.2_gerbers.zip   upload THIS to PCBWay (or JLCPCB, OSH Park, Aisler...)
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
  NOTE on J4 (sensors): fit a 1x4 FEMALE header at J4 (the STEMMA QT-to-pins cable ends in male pins), or
  solder its wires straight in.

ASSEMBLY ORDER (lowest parts first, so the board sits flat while you solder)
  1. Cut the VIN-VUSB trace on the underside of the Teensy (see the build guide) before it goes in,
     but only after the Firmware tab's bench tests: those run the Teensy from USB alone.
  2. Resistors (match the colour bands; picture 10 in the wiring pictures), then D1: its stripe goes
     to the right, on the SQUARE pad (the drawn band shows the same end). R23 and R24 are 1 k
     (brown, black, red) and stand on end: bend one lead back down beside the body, the body sits over
     the hole inside the drawn square.
  3. Ceramic capacitors (no polarity), then the two DIP-8 sockets (notch matches the drawing: it
     points RIGHT on this board, the opposite of the perfboard steps).
  4. U3 (MCP1700): flat face toward the board's front edge, legs GND - IN - OUT left to right.
     Its legs are closer together than the holes: spread the two outer legs a little.
  5. Electrolytic capacitors: the + leg goes in the SQUARE pad (the stripe on the can is the - side).
     That includes C27 and C29 (470 uF). Then L1 and L2 (either way round), pushed down flat.
  6. Headers J1 and J5 (or solder wires straight into them). Solder the wires straight into J2 (the radar,
     so nothing there can be plugged in backwards) and J3 (the screen: wires soldered to the OLED's pads,
     no header on the OLED, because a header plus plug-on jumpers stands too tall under the lid).
     J4 (sensor kit) gets a 1x4 FEMALE header. Then the female headers for the
     Teensy (2 x 24) and ESP32 (2 x 8). Plug the modules into their headers while you solder the
     headers, so they come out straight. The ESP32 goes in chip side UP (USB socket and buttons
     on top), USB toward the back, its antenna end at the board's front edge.
  7. Battery holder to J1 (no switch: the holder's own button is on/off). Before soldering its
     wires, meter its 5V and GND pads with the cell in: +5 V, not -5 V. Nothing on the board
     protects against those two swapped.
     v1.2: the filters are on the board, so the holder's red and black wires go straight to J1. (v1.1: the
     red wire runs through L1, C27/C28 go across J1, and the ESP32 gets L2/C29/C30 by hand; see v1.1/.)
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
  v1.1 was built and works (Nov 2026, with the filters wired by hand). v1.2 is not built yet: it changes
  only the filter parts and the few parts moved for them, but treat it as a first run of its own.
