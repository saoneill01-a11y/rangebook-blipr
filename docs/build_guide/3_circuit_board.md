# Circuit board (PCB)

A purpose-made board replaces the perfboard and almost all of the point-to-point wiring: every part solders into its own labelled holes, and the Teensy and ESP32 plug in. It is the same 70 × 90 mm with the same four M3 holes, so it fits the base you've printed. Five boards cost about $5 plus $15–$25 shipping from PCBWay.

It's worth it here: the amplifier is about 40 parts and 100 connections, and on perfboard one wrong hop is hard to find. Each version passes a design-rule check (0.25 mm clearance, every net connected), and its files are read back and drawn independently. **Order v1.1, not v1.0.** Two independent reviews found that v1.0's ESP32 socket was mirrored, which would have put 5 V on one of its 3.3 V pins. v1.1 hasn't been built yet, so treat it as a first run.

**What changed in v1.1:**

- The ESP32-C3 socket's pin order is fixed, and the ESP32 moved to the front-left corner with its antenna at the board's edge.
- The Teensy talks to the ESP32 on pins 34 and 35 (Serial8) instead of 0 and 1, through two 1 kΩ resistors (R23, R24). This needs firmware 0.2.2.
- The four 22 pF capacitors (C13, C16, C20, C23) are gone. They cut the gain at the fastest speeds.
- C6 is gone, and the radar header J2 has 4 pins. Radar pin 5 (VCO) gets no wire.
- C8 and C9 sit right beside pin 8 of each op-amp.

## Ordering

1. Unzip **RB\_Blip\_PCB\_v1.1.zip**. Inside is **RBBlip\_PCB\_v1.1\_gerbers.zip**: upload that one, unopened.
2. pcbway.com › PCB Instant Quote › Quick-order PCB › Add Gerber file. It reads the size and layers by itself.
3. Leave the standard settings: 2 layers, FR-4, 1.6 mm, HASL lead-free, 1 oz copper, white silkscreen, any mask colour, quantity 5.
4. PCBWay reviews the files before making them and emails if anything looks wrong.

JLCPCB, OSH Park and Aisler take the same zip.

## Where each part goes

&#91;image: PCB v1.1 assembly drawing\]

The BOM in the zip (**RBBlip\_BOM.csv**) lists every part by reference. Solder in this order, lowest parts first:

1. Resistors (colour bands on the Wiring pictures tab; R23 and R24 are 1 kΩ), then D1: stripe to the right, on the square pad.
2. Ceramic capacitors (either way round), then the two 8-pin sockets, notch matching the drawing.
3. U3 (MCP1700): flat face toward the front edge, legs GND – IN – OUT left to right. Spread its outer legs a little to reach the holes.
4. Electrolytic capacitors: + leg in the square pad.
5. Headers J1–J5 (or solder the wires straight in), then the female headers for the Teensy (2 × 24) and ESP32 (2 × 8). Plug the modules in while soldering their headers so they come out straight.
6. Power test before the chips go in: 5 V at J1, 3.3 V at U3's OUT leg, about 1.65 V at the + leg of C10.
7. Op-amps, Teensy (VIN–VUSB trace cut first) and ESP32 in; then the radar, OLED, switch and battery wires, as on the Wiring pictures tab.

**The ESP32 goes in chip side up**, with its USB socket toward the back and its antenna at the front edge. Its pin names are printed on the underside, so from above they read the other way round. Don't match them by eye. Seen from above, its 5V pin is the one nearest the USB on the right-hand edge, and it goes in the back hole of the right-hand row, next to D1's square pad. Seat the module without power and use the meter's beep test: its 5V pin to D1's square pad, and its G pin to J1 pin 2. Both must beep before you power up.

Use a pan-head M3 screw no wider than 5.5 mm in the back-right corner; it sits close to the Teensy's header. You can 3D-print the hole-check plate (RB\_Blip\_PCB\_v1.1\_hole\_check.zip) to test-fit every part before ordering.

## What the factory will make

&#91;image: Top side, drawn from the v1.1 Gerber files\]

&#91;image: Bottom side (ground plane), drawn from the v1.1 Gerber files\]
