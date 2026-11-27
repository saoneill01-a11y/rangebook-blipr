# Range Book BLIPR

**Ballistic Launch Inspection Portable Radar.** A do-it-yourself 24 GHz Doppler radar chronograph that sits on
the bench beside the rifle and sends each shot's muzzle velocity over Bluetooth to
[Range Book](https://github.com/saoneill01-a11y/rangebook). Nothing goes downrange.

**Status (Nov 26, 2026):** one unit built and tested live on .22 LR (CCI Standard Velocity). On its first two live
strings it read 9 of 10 shots, averaging 1029 fps (SD 22); an Athlon chronograph with the same rifle and ammo
averaged 1017 fps on another day, so the two agree within about 1%. Rifles haven't been tested yet. Expect changes
as more real shots come in.

| | Version |
|---|---|
| Circuit board | v1.2 (the two 5 V noise filters on the board; v1.1 boards fit them in the wiring) |
| Case | v0.12 |
| Teensy firmware | 0.2.8 |
| ESP32 firmware | 0.2.20 (also delivered by Range Book over Bluetooth) |
| Sensor kit (optional) | Adafruit SHT45 + DFRobot Gravity 10-DoF (BMI323 / BMM350 / BMP581) |

## Build one

- **Build guide (PDF):** [docs/BLIPR Build Guide.pdf](docs/BLIPR%20Build%20Guide.pdf). Parts, printing, firmware and
  bench tests, soldering, the 5 V filters, wiring, the case, first power-up and first shot, troubleshooting. The same
  guide as Word: [docs/BLIPR Build Guide.docx](docs/BLIPR%20Build%20Guide.docx); a longer reference in five parts:
  [docs/build_guide/](docs/build_guide/).
- **Parts list with prices:** [docs/RB_BLIPR_Parts_List.xlsx](docs/RB_BLIPR_Parts_List.xlsx); the board's own list is
  `pcb/out/RBBLIPR_BOM.csv`.
- **Assembly video:** a narrated, step-by-step build on circuit board v1.2 (about 38 minutes), coming to YouTube soon. Chapters and
  how it's made: [tools/video/README.md](tools/video/README.md).
- **Circuit board:** upload `pcb/out/RBBLIPR_PCB_v1.2_gerbers.zip` to PCBWay (or JLCPCB, OSH Park, Aisler) with the
  standard settings; `pcb/README.txt` has the details and the soldering order.
- **Firmware:** ready-made files in `firmware/prebuilt/`; source and the change history in `firmware/`.

See [BUILDING.md](BUILDING.md) for what to expect before you start.

## Bluetooth API

Any app or script can read BLIPR's shots, status and weather and change its settings over Bluetooth Low Energy: the
interface Range Book uses is documented in [firmware/PROTOCOL.md](firmware/PROTOCOL.md) (interface version 0.3, still
subject to change while BLIPR is tested). [tools/blipr_ble_example.py](tools/blipr_ble_example.py) is a short Python
client to start from.

## What's in here

| Folder | What it is |
|---|---|
| `firmware/` | `BliprTeensy` (Teensy 4.1: samples the radar, finds shots, measures velocity, saves raw captures) and `BliprBLE` (ESP32-C3 SuperMini: Bluetooth, OLED, battery gauge, optional sensors, firmware updates over Bluetooth). `prebuilt/` has ready-made files; `PROTOCOL.md` is the Bluetooth interface; `test/` has the shot simulator and `replay` (runs real SD-card recordings through the velocity code). |
| `tools/` | `blipr_log.py` logs a shooting session from the USB serial port, `pull_shots.py` copies recordings off the SD card, `tones.py` lists interference lines in recordings, `video/` makes the assembly video from the design files. |
| `pcb/` | The 70 x 90 mm two-layer through-hole main board: Gerbers, BOM, assembly drawing, and the scripts that make them (`design.py` netlist and placement, `route.py` Freerouting, `fab.py` Gerbers and checks). `test_plate/` is a printable plate with every hole, to test-fit parts. |
| `case/` | The 3D-printed case (ASA). `out/` has STL and STEP files for every part and preview pictures; `blipr_case.py` regenerates them (edit a size at the top, run it). `README.txt` has print settings and hardware. |
| `pictures/` | Wiring pictures, the two 5 V filters, the screen sequence and OLED previews, and the scripts that draw them. |
| `docs/` | The build guide (PDF, Word, Markdown), the parts list, and the scripts that build them. |
| `recordings-kept/` | A few raw radar recordings of real shots, for testing the velocity code with `firmware/test/replay`. |

## The design in one paragraph

An RFbeam K-LC5-RFB-00C radar module feeds two MCP6022 amplifier stages per channel (I and Q, about 480x).
A Teensy 4.1 samples both channels at 500 kSa/s, finds each shot, fits its velocity and saves a raw recording to its
SD card, then sends the result over a serial link to an ESP32-C3. The ESP32 handles Bluetooth LE (device name
**RB BLIPR**), a 0.96" OLED that stays dark while BLIPR listens, the battery gauge and an optional sensor kit (SHT45
plus a DFRobot 10-DoF for level, compass and pressure) in a vented pod on the lid. Power is one 18650 cell in a holder
with a 5 V boost output; small LC filters keep the holder's converter and the ESP32's radio out of the radar's supply.
Range Book connects over Bluetooth (the Range Book app on iPhone and iPad, Bluefy, or Chrome) and can update the ESP32's firmware over
Bluetooth.

## Working on it with Claude Code

See [docs/claude-code-setup.md](docs/claude-code-setup.md). `CLAUDE.md` holds the project notes Claude Code reads
when it starts in this folder, including the full test history.

## Licence

GNU Affero General Public License v3.0 or later ([LICENSE](LICENSE)), the same as Range Book. It covers the
firmware, tools, circuit board, case and documentation.
