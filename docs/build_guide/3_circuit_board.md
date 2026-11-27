# Circuit board (PCB)

A purpose-made board replaces the perfboard and almost all of the point-to-point wiring: every part solders into its own labelled holes, and the Teensy and ESP32 plug in. It is the same 70 × 90 mm with the same four M3 holes, so it fits the base you've printed. Five boards cost about $5 plus $15–$25 shipping from PCBWay.

It's worth it here: the amplifier is about 40 parts and 100 connections, and on perfboard one wrong hop is hard to find. Each version passes a design-rule check (0.25 mm clearance, every net connected), and its files are read back and drawn independently. **Order v1.2.** It is v1.1 with both 5 V noise filters on the board, so nothing is wired by hand and the ESP32 plugs in with all its pins. Never order v1.0: its ESP32 socket was mirrored, which would have put 5 V on one of its 3.3 V pins. The first v1.1 board is built and working (bench tests Nov 8, 2026; live .22 shots Nov 26). v1.2 changes only the filter parts and the few parts moved for them, but it hasn't been built yet. **Already have v1.1 boards?** They work: see "If you have a v1.1 board" at the end of this tab.

**What changed in v1.2:**

- The battery holder's filter is on the board: L1 (22 µH) sits between J1 pin 1 and the board's +5V, with C27 (470 µF) and C28 (1 µF) beside it. The holder's red and black wires go straight to J1.
- The ESP32's filter is on the board: L2 (22 µH), C29 (470 µF) and C30 (1 µF) sit between D1 and the ESP32's 5V pin. Nothing is cut on the module.
- To make room, R19–R22 and C26 moved up 2.5 mm and right 0.9 mm, and R23 and R24 now stand on end.
- Same size, holes, connectors and module positions: the v0.12 case fits. The new parts are up to 12 mm tall, with about 20 mm under the lid.
- Part sizes: inductors 22 µH, 1 A or more, round drum type up to 8.4 mm across, leads 5 mm apart (e.g. Würth 744772220) or 3.2 mm apart (small 6.7 mm drums): L1 and L2 have three holes in a row. 470 µF: 10 V or more, 8 mm across, leads 3.5 mm apart (e.g. Nichicon UKA1A471MPD1TD). Check yours before soldering.

**What changed in v1.1:**

- The ESP32-C3 socket's pin order is fixed, and the ESP32 moved to the front-left corner with its antenna at the board's edge.
- The Teensy talks to the ESP32 on pins 34 and 35 (Serial8) instead of 0 and 1, through two 1 kΩ resistors (R23, R24). This needs firmware 0.2.2.
- The four 22 pF capacitors (C13, C16, C20, C23) are gone. They cut the gain at the fastest speeds.
- C6 is gone, and the radar header J2 has 4 pins. Radar pin 5 (VCO) gets no wire.
- C8 and C9 sit right beside pin 8 of each op-amp.

## Ordering

1. Take **RBBLIPR\_PCB\_v1.2\_gerbers.zip** from the project's `pcb/out/` folder and upload it unopened.
2. pcbway.com › PCB Instant Quote › Quick-order PCB › Add Gerber file. It reads the size and layers by itself.
3. Leave the standard settings: 2 layers, FR-4, 1.6 mm, HASL lead-free, 1 oz copper, white silkscreen, any mask colour, quantity 5.
4. PCBWay reviews the files before making them and emails if anything looks wrong.

JLCPCB, OSH Park and Aisler take the same zip.

## Where each part goes

&#91;image: PCB v1.2 assembly drawing: L1, C27, C28 beside J1; L2, C29, C30 below them; L1 and L2 with three holes each; R23 and R24 standing\]

The BOM in the zip (**RBBLIPR\_BOM.csv**) lists every part by reference. Solder in this order, lowest parts first:

1. Resistors (colour bands on the Wiring pictures tab), then D1: stripe to the right, on the square pad. (D1 is a 1N5817; the bag may say "IN5817", the same part.) R23 and R24 are 1 kΩ and stand on end: bend one lead back down beside the body, with the body over the hole inside the drawn square.
2. Ceramic capacitors (either way round, including C28 and C30), then the two 8-pin sockets, notch matching the drawing (pointing right).
3. U3 (MCP1700): flat face toward the front edge, legs GND – IN – OUT left to right. Spread its outer legs a little to reach the holes.
4. Electrolytic capacitors: + leg in the square pad. C3 (100 µF): 16 V or 25 V, no wider than 6.3 mm. C4, C7, C10 (10 µF): 25 V ones, smaller than 50 V. C27 and C29 (470 µF): 8 mm across. Then L1 and L2 (22 µH, either way round), pushed down flat. Each has three holes in a row: the two outer holes are 5 mm apart, and the left and middle holes 3.2 mm apart for small drums. Use whichever pair fits; the third hole stays empty.
5. Headers J1 and J5 (or solder the wires straight in). Solder the wires straight into J2 (the radar, so nothing there can be plugged in backwards) and J3 (the screen, build guide Step 4), then the female headers for the Teensy (2 × 24) and ESP32 (2 × 8). Plug the modules in while soldering their headers so they come out straight. The Teensy sits on these 8.5 mm sockets, and the case's USB hole (v0.10 and later) is placed for that height. J4 (sensor kit) gets no header either: snip the pins off the sensor cable and solder its wires straight in (a header plus plug stands too tall under the lid); J5 (ammo-probe jack) can stay empty.
6. Battery holder to J1, red and black wires straight in (no switch: its button is on/off). Before soldering its wires, check its 5 V and GND pads with the meter: +5 V, not −5 V. Then the power test before the chips go in: 5 V at J1, 3.3 V at U3's OUT leg, about 1.65 V at the + leg of C10.
7. Op-amps (each chip's dot beside the square pad), Teensy (VIN–VUSB trace cut first, after the Firmware tab's bench tests) and ESP32 in, all its pins; then the radar and OLED wires, as on the Wiring pictures tab.

**The ESP32 goes in chip side up**, with its USB socket toward the back and its antenna at the front edge. Its pin names are printed on the underside, so from above they read the other way round. Don't match them by eye. Seen from above, its 5V pin is the one nearest the USB on the right-hand edge, and it goes in the back hole of the right-hand row, next to D1's square pad. Before soldering its socket, power the ESP32 from USB alone and find the pin that reads 5 V to G with the meter: that's the pin for this hole. Fitted labels-up, the rows would be mirrored and 5 V would land on GPIO5. Then seat the module without power and use the meter's beep test: its 5V pin to D1's square pad, and its G pin to J1 pin 2. Both must beep before you power up.

**The radar plug goes on pin 1 to pin 1, only.** The radar's power and ground pins (2 and 4) mirror each other, so a plug turned round swaps them, and no beep test catches it. Mark pin 1 on the radar and on its plug, and watch +3V3A on the meter the first time it's powered (build guide Step 4 and Checkpoint 3).

Use a pan-head M3 screw no wider than 5.5 mm in the back-right corner; it sits close to the Teensy's header. You can 3D-print the hole-check plate (RB\_BLIPR\_PCB\_v1.2\_hole\_check.stl in pcb/test\_plate/) to test-fit every part before ordering.

## What the factory will make

&#91;image: Top side, drawn from the v1.2 Gerber files\]

&#91;image: Bottom side (ground plane), drawn from the v1.2 Gerber files\]

## If you have a v1.1 board

v1.1 boards work fine; the first BLIPR is built on one. The difference is the two 5 V filters: on v1.1 they go in the wires, by hand. Everything for v1.1 (Gerbers, BOM, pictures and the PCBA files) is kept in the project's `pcb/v1.1/` folder. Don't order v1.1 again: order v1.2.

- Solder order: as above, but R23 and R24 lie flat, and there are no L1, L2, C27–C30 footprints.
- Battery holder: its red wire runs through L1, with C27 and C28 across J1 (build guide Step 2, "If you have a v1.1 board").
- ESP32: load its firmware over USB first, then cut its 5V pin and wire L2, C29 and C30 at the module (build guide Step 4, "If you have a v1.1 board").

&#91;image: PCB v1.1 assembly drawing\]
