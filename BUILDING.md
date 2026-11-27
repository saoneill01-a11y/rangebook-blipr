# Building your own BLIPR

BLIPR is a hobby project shared as it is. One unit has been built and tested on .22 LR; it hasn't been tested on
rifles yet. If you build one, you're helping test it.

**What it takes.** About $250-340 in parts (the spreadsheet in `docs/` has prices), a 3D printer that handles PETG (ASA for hot climates),
a temperature-controlled soldering iron and a multimeter. Every part is through-hole, and the guide has a meter
check after each stage. Plan on a few evenings. The two parts most worth care: the radar plug (pin 1 to pin 1 only)
and the ESP32's direction in its socket (chip side up). The guide explains both.

**Start here.** Read the build guide PDF in `docs/` once, end to end, before ordering. Do the firmware bench tests
(fake bullet, phone link) before soldering anything permanent, and before cutting the Teensy's VIN–VUSB trace.

**What helps the project most.** Recordings of real shots. Turn on saving (`set save=1` on the Teensy), and keep the
SD card's `shots` folder with a note of the rifle, load, where BLIPR sat, and any other chronograph's numbers for the
same shots. Those recordings are what the velocity code is tuned on.

**Problems and ideas.** Open an issue on GitHub with the Teensy's start-up lines, the output of `get`, and what you
saw. For interference, the output of `live` and a `rec` capture help most.

**Safety.** You build and use this at your own risk. It contains a lithium cell and a low-power 24 GHz radio module
sold as a component, not a certified finished device. Never handle BLIPR or send it commands while someone is on
the rifle.
