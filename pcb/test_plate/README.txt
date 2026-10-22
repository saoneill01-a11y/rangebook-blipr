RB BLIPR PCB v1.1 - hole-check plate
=====================================

A 3D-printable copy of the circuit board with only its outline and holes: 70 x 90 x 1.6 mm, the same
size and thickness as the real board. Print it and push your actual parts into it before you order
the boards, to check that everything lines up.

PRINTING
  Lay it flat, 0.2 mm layers, 100% scale, no supports. PLA is fine. About 15 minutes.
  The holes are printed 0.3 mm bigger than the real drill sizes (header holes 1.1 mm, larger pins
  1.3 mm, screw holes 3.4 mm), because printers make small holes undersize. If header pins still
  won't go in, open the holes with a 1 mm drill bit or a pin; that's a printer issue, not a board one.

WHICH SIDE IS UP
  The triangle cut through the plate points at the FRONT (radar) edge. With the triangle pointing
  toward you, you're looking at the TOP, the side the parts go on. Same view as pcb_assembly.png.

WHAT TO CHECK
  - Teensy 4.1 on its 2 x 24 headers, and the ESP32-C3 SuperMini on its 2 x 8 headers. The ESP32
    sits at the front-left corner, chip side up, USB toward the back: its 5V pin (nearest the USB
    on the right-hand edge) must land in the back hole of the right-hand row (arrow in the preview).
  - The two DIP-8 sockets, the MCP1700, the electrolytic capacitors and the resistors (bend the legs
    the way you will on the real board).
  - The headers J1 to J5.
  - The four M3 holes over the posts of the case base.
  Small holes that carry no part (vias) are left out.
