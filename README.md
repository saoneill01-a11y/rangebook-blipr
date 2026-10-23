# Range Book BLIPR

**Ballistic Launch Inspection Portable Radar.** A do-it-yourself 24 GHz Doppler radar chronograph that sits on
the bench beside the rifle and sends each shot's muzzle velocity over Bluetooth to
[Range Book](https://github.com/saoneill01-a11y/rangebook). Nothing goes downrange.

**Status:** designed, not built yet. Circuit board v1.1, firmware 0.2.3, case v0.8. Expect changes after the
first build.

## What's in here

| Folder | What it is |
|---|---|
| `firmware/` | `BliprTeensy` (Teensy 4.1: samples the radar, finds shots, measures velocity, saves raw captures) and `BliprBLE` (ESP32-C3 SuperMini: Bluetooth, OLED, battery gauge, optional sensors, firmware updates over Bluetooth). `prebuilt/` has ready-made files; `PROTOCOL.md` is the Bluetooth interface; `test/` is the shot simulator. |
| `pcb/` | The 70 x 90 mm two-layer through-hole main board. `out/RBBLIPR_PCB_v1.1_gerbers.zip` is what you upload to PCBWay; `README.txt` has the ordering settings and soldering order. `design.py` is the netlist and placement, `route.py` runs Freerouting, `fab.py` writes the Gerbers and checks them. `test_plate/` is a 3D-printable plate with every hole, to test-fit parts before ordering. |
| `case/` | The 3D-printed case (ASA recommended). `out/` has STL and STEP files for every part and preview pictures; `blipr_case.py` regenerates them all with plain Python (edit a size at the top, run it). `README.txt` has print settings and hardware. |
| `pictures/` | The wiring pictures used in the build guide, the OLED animation previews, and the scripts that draw them. |
| `docs/` | The build guide (exported from the live doc) and the parts list. |

## The design in one paragraph

An RFbeam K-LC5-RFB-00C radar module feeds two MCP6022 amplifier stages per channel (I and Q, about 480x).
A Teensy 4.1 samples both channels at about 600 kSa/s, runs an FFT on each shot and fits the velocity, then
sends it over a serial link to an ESP32-C3, which handles Bluetooth LE (device name **RB BLIPR**), a 0.96"
OLED, the battery gauge and an optional sensor kit (SHT45, BMP390, LSM6DSOX + LIS3MDL) in a vented pod on
the lid. Power is one 18650 battery shield. Range Book connects with Web Bluetooth (Chrome, or Bluefy on iPhone)
and can update the ESP32's firmware over Bluetooth.

## Licence

Not chosen yet; this repo is private for now. The firmware files carry AGPL-3.0-or-later, the same as Range Book.
