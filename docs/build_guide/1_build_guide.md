# Range Book BLIPR – Build Guide

Nov 26, 2026 · @Sean

## Overview

You're building Range Book BLIPR (Ballistic Launch Inspection Portable Radar), a bench-side 24 GHz Doppler radar chronograph that sends each shot's velocity over Bluetooth to your web app. It sits beside the rifle on the bench, so nothing goes downrange.

How it works, in one pass: the RFbeam K-LC5 radar sends out a 24 GHz signal and outputs two very weak signals (called I and Q) whose frequency is proportional to the bullet's speed: about 161 Hz per m/s, so roughly 150 kHz for a 3,000 fps rifle bullet. A two-stage amplifier boosts each signal about 500 times. The Teensy 4.1 samples both signals with its two built-in ADCs, finds the frequency with an FFT, and works out velocity. An ESP32-C3 board sends the result to your phone over Bluetooth Low Energy.

&#91;embedded content: signal path · 5 hops, plus power\]

**What this guide covers:** the hardware: the circuit, soldering, wiring, the 3D-printed case, and electrical checks with a multimeter at each stage. The firmware for the Teensy and ESP32 and the Range Book connection are on the Firmware tab; do its bench tests before soldering (Step 1). **The usual build is now the circuit board v1.2** (Circuit board tab): it replaces the perfboard and most of the wiring below. The steps still apply, and where the circuit board differs they say so.

**Case files (v0.12):** `base`, `lid_oled` / `lid_plain` / `lid_sensors`, `front_cover`, `sensor_pod` and `sensor_pod_roof`, each as STEP and STL, plus `blipr_case.py`, the parametric script that generates them. v0.12 is the version built and used: the Teensy's USB hole fits the Teensy on its 8.5 mm sockets, and the lid's screen window is 13 mm tall, so the screen's top line shows (see Step 5). The case is also on [MakerWorld](https://makerworld.com/en/models/3697742-blipr-doppler-radar-chronograph#profileId-4248561).

**Firmware (Teensy 0.2.9, ESP32 0.2.20):** setup and bench tests are on the Firmware tab.

**You'll need Range Book:** BLIPR sends its shots to Range Book, a free, self-hosted shooting log and ballistics app. [rangebook.org](https://rangebook.org) shows how to install it. On iPhone and iPad, get the [Range Book app](https://apps.apple.com/app/id6837895002) (Range Book: Shooting Log) from the App Store; on Android, use Chrome.

**Watch the build:** the narrated assembly video (about 39 minutes) is on YouTube: [youtu.be/nRWELvyEKN8](https://youtu.be/nRWELvyEKN8). It follows this guide step by step; pause at each step and build along.

**Status (Nov 27, 2026):** one BLIPR is built on circuit board v1.1 and has been tested live. On .22 LR (CCI Standard Velocity) its first two strings read 9 of 10 shots, averaging 1029 fps (SD 22), within about 1% of an Athlon chronograph with the same rifle and ammo on another day. On Nov 27 it shot beside an Athlon on the same shots (.38 Special 158 gr handloads from a lever-action rifle): 19 of 20 read, and each string averaged within about 3 fps of the Athlon. Supersonic rifle ammo is next. Board v1.2, which puts both 5 V filters on the board, is designed but not built yet; this guide covers both boards. This guide also comes as a PDF and a Word file (`docs/` in the project), and there is a narrated [assembly video on YouTube](https://youtu.be/nRWELvyEKN8).

&#91;image: BLIPR and an Athlon radar chronograph on the same 20 shots of .38 Special: BLIPR read 19 of 20 (one seen but held back as unsure), +0.3 fps overall vs the Athlon, a typical gap of 4.1 fps (0.4%) on any one shot\]

&#91;image: The first BLIPR on a small tripod: screen window in the lid's back corner, sensor pod in front\]

&#91;image: The same BLIPR from the radar side: the square radar window on the front face\]

## Tools, supplies and safety

You need a temperature-controlled soldering iron, a multimeter, and calipers; everything else is cheap or optional.

| Tool or supply | Why |
| --- | --- |
| Soldering iron with a fine chisel tip, set around 330 °C | Perfboard joints and header pins |
| Rosin-core solder (0.6–0.8 mm) and flux pen | Clean joints on small pads |
| Multimeter with DC volts and continuity beep | Every checkpoint in this guide |
| Digital calipers | Measuring parts so the case can be adjusted |
| Flush cutters, wire strippers, tweezers | Trimming leads, stripping 26 AWG wire |
| Hobby knife | Cutting the Teensy's VIN/VUSB trace |
| Solder-tip for heat-set inserts (or the plain iron tip) | Setting the M3 and 1/4-20 inserts |
| 26–28 AWG stranded wire in at least 4 colors | Point-to-point wiring (red = power, black = ground, other colors = signals) |
| Hot glue, 4 × M2 × 4 mm screws, 4 × M3 × 6 mm self-tapping screws | Holding the radar in its pocket, the screen to the lid, and the battery holder to the base |
| Isopropyl alcohol and an old toothbrush | Cleaning flux off the amplifier area |

**Safety and handling**

- **18650 cell:** only use a name-brand cell from a reputable seller. Never short its terminals, never solder directly to the cell, and insert it in the shield's marked direction (reversing it can destroy the charging chip). Charge it inside the shield, not unattended overnight the first time.
- **Radar module (K-LC5):** it is static-sensitive. Touch a grounded metal object before handling it, hold it by the edges, and never solder directly to its pins. You'll plug a female header onto them instead.
- **Power while soldering:** the battery stays out of the shield until the first power checkpoint. Never solder with the battery in.
- **Radio transmitter:** the radar transmits whenever it has power. It's low power, but don't put your eye right up against the antenna, and keep the unit switched off when not in use. These modules are components, not certified finished devices, so treat this as a personal device used at the range.

## Parts list

The spreadsheet has prices and links; this table adds the reference names (R1, C3, U1…) used in the schematic and the steps. Items marked **new** were added for this design.

**Important:** order the radar as **K-LC5-RFB-00C**. RFbeam makes the K-LC5 in a 3.3 V version and a 5 V version, and DigiKey lists the -00C at 3.13–3.47 V, which is what this circuit is built for. Don't substitute another suffix without checking its supply voltage first.

| Ref | Part | Qty | Notes |
| --- | --- | --- | --- |
| RADAR | RFbeam K-LC5-RFB-00C radar module | 1 | 3.3 V version |
| MCU | Teensy 4.1 with pins | 1 |  |
| BLE | ESP32-C3 SuperMini | 1 | Buy a pack: a spare is worth having (the first build's module got an intermittent USB joint after its 5V pin was cut) |
| U1, U2 | MCP6022-E/P dual op-amp (DIP-8) | 2 | Buy 4 |
| U3 | MCP1700-3302E/TO, 3.3 V low-dropout regulator (TO-92) | 1 | **new**, buy 2, about $0.40 at DigiKey |
| — | DIP-8 IC sockets | 2 | **new**, so the op-amps can be swapped |
| BT1 | 18650 battery holder (5 V output, its own power button) + name-brand 18650 cell | 1 |  |
| OLED | 0.96" SSD1306 I2C display | 1 | Shows speed and battery level; white reads best. Four wires into J3: female jumper wires on its pins, or wires soldered to its pads (Step 4) |
| — | microSD card, 8–32 GB, name brand, A1 or Class 10, FAT32 or exFAT | 1 | In the Teensy. An 8 GB card that had been in another device wasn't read; a 32 GB A1 card worked |
| — | Micro-USB and USB-C data cables | 1 each | Charge-only cables light the boards but the computer can't see them |
| R1 | 10 Ω resistor | 1 | Op-amp supply filter |
| R2, R3 | 10 kΩ | 2 | Mid-rail reference divider |
| R4, R7, R11, R14 | 4.7 kΩ | 4 | Input bias resistors |
| R5, R8, R12, R15 | 10 kΩ | 4 | Feedback resistors |
| R6, R9, R13, R16 | 470 Ω | 4 | Gain resistors |
| R10, R17 | 330 Ω | 2 | ADC input filter |
| C1, C2 | 1 µF ceramic | 2 | Regulator in/out |
| C14, C17, C21, C24 | 1 µF ceramic | 4 | Gain-leg capacitors |
| C3 | 100 µF electrolytic, 10 V or higher, 6.3 mm across (16 V or 25 V types; a 50 V one is 8 mm and crowds C4) | 1 | **new**, regulator output |
| C4, C7, C10 | 10 µF electrolytic, 10 V or higher (25 V ones are smaller than 50 V) | 3 | **new** |
| C5, C8, C9, C11 | 100 nF ceramic | 4 | Decoupling |
| C12, C15, C19, C22 | 10 nF ceramic | 4 | Input coupling |
| R23, R24 | 1 kΩ | 2 | new (v1.1): one in each serial line between the Teensy and ESP32 |
| D1 | 1N5817 Schottky diode | 1 | ESP32's 5 V feed. The bag may say "IN5817": same part |
| L1, L2 | 22 µH inductor, 1 A or more, through-hole | 2 | new (Nov 2026), either way round. Board v1.2: on the board; radial drum type up to 8.4 mm across, leads 5 mm or 3.2 mm apart (three holes each; e.g. Würth 744772220, or small 6.7 mm drums). Board v1.1: off the board, L1 in the holder's red wire, L2 in the ESP32's 5 V feed |
| C27, C29 | 470 µF electrolytic, 10 V or higher | 2 | new (Nov 2026), stripe to GND. Board v1.2: on the board, 8 mm across, leads 3.5 mm apart (e.g. Nichicon UKA1A471MPD1TD). Board v1.1: C27 across J1, C29 across the ESP32's 5V and GND |
| C28, C30 | 1 µF ceramic | 2 | new (Nov 2026): beside C27 and C29 |
| R25 | 10 kΩ | 1 | Soldered on the battery holder's + tab (battery gauge) |
| C18, C25 | 1 nF ceramic | 2 | ADC input filter |
| — | 70 × 90 mm double-sided perfboard | 1 | Or the RB BLIPR circuit board v1.2 (Circuit board tab; v1.1 also works) |
| — | Female headers 2.54 mm | 2×24, 2×8, 1×5 | Teensy, ESP32, radar plug, none for J2, J3 or J4: their wires solder straight into the board (a header plus plug stands too tall under the lid) |
| — | M3 heat-set inserts (about 4.6–5 mm OD) | 8 | **new**, 4 lid + 4 board posts |
| — | M3 × 8 mm screws (lid), M3 × 6 mm screws (board) | 4 + 4 | **new** |
| — | 1/4-20 heat-set insert, 13 mm long or shorter | 1 | Tripod mount |
| — | 26–28 AWG stranded wire, 4+ colors | 1 set | **new** |

**Added after an independent design review (v0.2):** **D1**, a 1N5817 Schottky diode in the ESP32's 5 V feed, so plugging USB into the ESP32 can't push power back into the rest of the unit. **R18**, a second 10 Ω resistor in front of U3, which with C4 filters the battery shield's switching noise before it reaches the radar. And the four feedback capacitors (C13, C16, C20, C23) are now **22 pF** instead of 47 pF, which keeps about 4 dB more gain at the fastest velocities.

**Added for the battery gauge (v0.3):** SW1 is now a **DPDT** slide switch (two rows of three tabs) instead of SPDT, plus **R19, R20** (100 kΩ each) and **C26** (100 nF).

**Changed when the firmware was written (v0.4):** the OLED and the battery sense now connect to the **ESP32-C3** instead of the Teensy. The Teensy's two converters sample the radar nonstop, so reading the battery on them would interrupt the radar, and the screen's slow updates could make it miss samples. The ESP32 has time to spare for both.

**Changed after two independent reviews (v0.5, Oct 20):** the four 22 pF capacitors (C13, C16, C20, C23) are left out, because they cut the gain at the fastest speeds. C6 is gone and radar pin 5 (VCO) gets no wire. **R23, R24** (1 kΩ) go in the two serial lines, which move to Teensy pins 34 and 35. **R25** (10 kΩ) is soldered right on the cell's + tab, so a damaged gauge wire can't short the battery. These need firmware 0.2.2.

**Added after the first power-up (Nov 2026):** two 5 V noise filters, both off the board in the wires. **L1** (22 µH) goes in the battery holder's red wire, with **C27** (470 µF) and **C28** (1 µF) across J1. **L2** (22 µH) goes in the ESP32's own 5 V feed, with **C29** (470 µF) and **C30** (1 µF) at the module. Without them, the holder's boost converter showed up at the radar as a steady tone, and the ESP32's Bluetooth bursts set off false triggers about 30 times a second. Also, the screen is now wired with soldered wires instead of a header and plug-on jumpers, which stood too tall under the lid. Board v1.2 puts L1, C27, C28, L2, C29 and C30 on the board, so nothing is wired by hand and the ESP32's 5V pin isn't cut.

The resistor and ceramic capacitor assortment kits from the spreadsheet should cover every value above. Before you start, check your ceramic kit actually includes 22 pF, 1 nF, 10 nF, 100 nF and 1 µF, and get an electrolytic kit (or individual parts) for the 10 µF and 100 µF values.

&#91;image: Resistor colour bands and capacitor codes\]

## Schematic and how the circuit works

The circuit has three parts: clean power for the radar and amplifiers, two identical amplifier channels (I and Q), and plain wiring between the modules.

&#91;image: Schematic, main board v1.2: power with both 5 V filters and the battery gauge, I-channel amplifier, Q-channel parts and module and header connections\]

The full-size schematic is `pcb/out/schematic_v1.2.png` (and `.pdf`) in the project.

**Power.** The battery holder makes 5 V, and its own button turns everything on and off (there is no separate switch). 5 V feeds the Teensy, the ESP32 (through diode D1, which blocks power flowing back from the ESP32's USB port) and, through filter resistor R18, a separate low-noise 3.3 V regulator (U3) that powers only the radar and the amplifiers. Keeping the radar off the Teensy's own 3.3 V keeps digital noise out of the weakest signals in the build. R1 and C7 filter the op-amp supply a second time.

**5 V filters.** The holder's 5 V passes L1 (22 µH) before it reaches J1, where C27 (470 µF) and C28 (1 µF) smooth it. The ESP32 gets its 5 V from D1 through L2 (22 µH), with C29 and C30 at its pins. Together they keep the holder's converter noise (about 494 kHz) and the ESP32's radio bursts out of the supply the radar and Teensy share.

**Mid-rail reference (VREF).** The op-amps run from a single 3.3 V supply, so the signals swing around the middle, 1.65 V. R2 and R3 split the supply in half, and C10 and C11 hold it steady.

**Battery level.** R19 and R20, with R25 at the cell, divide the cell voltage by 2.1 (4.2 V full becomes 2.0 V) so the ESP32-C3 can read it on GPIO3 without exceeding its input limit. C26 steadies the reading. With no separate switch the divider stays connected to the cell, so it draws about 18 µA even when BLIPR is off: a few months to drain a full cell. Take the cell out for longer storage. The 100 kΩ resistors keep the current into a powered-down ESP32 tiny, which is safe.

**Amplifier.** Each channel is two identical stages, each boosting the signal about 22 times (about 500 total). In each stage:

- The input capacitor (C12) and bias resistor (R4) block DC and cut anything under about 3.4 kHz. That removes the radar's 0.2 V DC offset plus slow motion and hum. 3.4 kHz corresponds to about 70 fps, well below anything you'll shoot.
- R5 and R6 set the gain. C14 in the gain leg makes the DC gain 1, so the output idles at exactly 1.65 V.
- Nothing sits across R5: the op-amp itself rolls the gain off at the top, about 3 dB down near 245 kHz (5,000 fps). The firmware samples each channel 500,000 times per second (with fs=500000, Step 6; the factory default is 600,000), above twice the fastest signal.

R10 and C18 at the end form a small filter right at the Teensy pin, which keeps the ADC's sampling from disturbing the amplifier.

**Pins that might move.** A0 and A1 are chosen so both of the Teensy's ADCs can sample I and Q at the same moment. I'll confirm this when writing the firmware; if a different pin turns out better, it's a one-wire move.

## Step 1: Prepare the boards

Test each module on its own before it gets soldered into anything, then lay out the perfboard so the case lines up.

**On the circuit board (v1.1 or v1.2):** do items 1 to 4 here, then follow the Circuit board tab's soldering order instead of 5 to 7. The Teensy's VIN–VUSB cut (item 3) comes after the Firmware tab's bench tests.

1. **Sort and check parts.** Measure every resistor with the multimeter before it goes in (10 Ω, 330 Ω, 470 Ω, 4.7 kΩ, 10 kΩ look alike). Bag the capacitors by value. Electrolytics have a stripe marking the **negative** lead, and the longer lead is positive.
2. **Test the Teensy.** Plug it into your computer with a micro-USB data cable. The orange LED should blink (factory test program). If nothing happens, try another cable before blaming the board. Then load the firmware and do the Firmware tab's bench tests.
3. **Cut the Teensy's VIN–VUSB link.** Do the Firmware tab's bench tests first: they run the Teensy from USB alone, which stops working once this link is cut. On the underside near the USB connector are two pads joined by a thin trace, labeled VIN and VUSB on PJRC's pinout card. Cut that trace with a hobby knife, a few light strokes. Confirm with the continuity beep: no beep between VIN and VUSB. This stops the battery and your computer's USB from fighting each other. From now on, the Teensy only runs when the chronograph is turned on (the holder's button), including when you program it.
4. **Test the ESP32-C3.** Plug it into USB-C; a power LED should light. If its pins aren't soldered on yet, fit them with the black plastic and the long pins on the side with the printed pin names (the underside), and solder them on the chip side, so the module can sit chip side up. While it's on USB, find the pin that reads 5 V to G with the meter and mark it: on the circuit board that pin goes in the back hole of the right-hand row, next to D1's square pad. If the computer doesn't see it at all while its LED is on, the USB-C cable is charge-only: swap it. Load its firmware now, over USB (Firmware tab). On the first (v1.1) build, once its 5 V filter was fitted the computer saw the ESP32 only when it was out of BLIPR's socket; later updates go over Bluetooth from Range Book either way.
5. **Check the perfboard holes (perfboard only).** Most 70 × 90 mm boards have a 2–3 mm hole in each corner about 3 mm in from both edges, which is what the case posts expect. If yours don't, mark centers 3 mm in from each edge and drill 3.2 mm.
6. **Mark the layout zones** on the top of the perfboard with a fine marker, with the board positioned as it will sit in the case: the 70 mm side is the front edge, facing the radar.

| Zone | Where on the board (front edge = 0) | What goes there |
| --- | --- | --- |
| Amplifier and power | Front 28 mm, full width | U3 and its capacitors, VREF divider, U1 (I channel) on the left half, U2 (Q channel) on the right half |
| Teensy 4.1 | Lying left-to-right across the rear of the board, centered 75 mm back from the front edge, with its USB connector at the board's right edge (it lines up with the hole in the case's right wall) | Two 1×24 female headers, 15.2 mm (6 rows) apart |
| ESP32-C3 | Left side, about 6–24 mm from the left edge, 34–57 mm back | Two 1×8 female headers; its antenna end toward the rear, away from the radar |
| Keep clear underneath | Left 13 mm strip, 30 to 44 mm back from the front edge | The tripod insert post sits 3.8 mm under here (case v0.8), so trim solder tails to 2 mm or less (on the circuit board: R19 to R22, C26, J3 and J4) |
| Corners | 6 mm circle around each mounting hole | Screw heads and posts |

7. **Solder the sockets.** Plug the female headers onto the Teensy's pins, set the whole assembly on the board in its zone, and solder the header pins from underneath. Doing it with the Teensy in place keeps the rows perfectly spaced. Remove the Teensy, then do the same for the ESP32. Solder the two DIP-8 sockets in the amplifier zone with their notches facing the same way (toward the left edge), and mark pin 1 next to each. On the circuit board the notches point right instead, as printed on it: put each chip's dot (pin 1) beside the square pad.

## Step 2: Build the power section

Build and test power before anything expensive is plugged in; a wiring mistake here is the one most likely to damage the radar.

&#91;image: Battery holder wired straight to J1, R25 at the cell tab\]

&#91;image: Power and VREF parts\]

All the wiring pictures, with notes, are also on the Wiring pictures tab.

1. **Lay down the rails.** Along the front edge of the board, run a bare tinned-wire ground (GND) bus the full width, soldered every few holes. Above it, run short separate buses for **+5V**, **+3V3A**, **+3V3OP** and **VREF**. Label them with a marker. Every part that says "to GND" on the schematic goes to the GND bus by the shortest path.
2. **Fit U3 (MCP1700).** Hold it with the flat, printed face toward you and the leads down: per Microchip's datasheet the leads are **GND, VIN, VOUT** from left to right. Sources online disagree on this pinout, so check the diagram in the datasheet on U3's DigiKey page before soldering. VOUT goes to +3V3A; VIN connects in the next step.
3. **Add the regulator capacitors.** R18 (10 Ω) from the +5V bus to U3's VIN. C1 (1 µF) and C4 (10 µF, stripe to GND) from U3's VIN to GND, right at U3. R18 and C4 together filter the shield's switching noise. C2 (1 µF) and C3 (100 µF, stripe to GND) from +3V3A to GND, close to U3's output.
4. **Op-amp supply filter.** R1 (10 Ω) from +3V3A to +3V3OP. C7 (10 µF, stripe to GND) from +3V3OP to GND.
5. **VREF divider.** R2 (10 kΩ) from +3V3OP to VREF, R3 (10 kΩ) from VREF to GND. C10 (10 µF, stripe to GND) and C11 (100 nF) from VREF to GND.
6. **Battery holder.** First check the holder's output with the meter: cell in, holder on, red probe on its 5 V pad and black on GND must read about +5 V, not −5 V. Nothing on the board protects against these two swapped. Then take the cell out. With no cell in the holder, solder a red wire to the holder's 5 V output pad and a black wire to its GND pad (use the solder pads or header pins, not the USB-A socket). The red wire goes to J1 +5V and the black one to J1 GND, side by side. On board v1.2 the holder's filter (L1, C27, C28) is already on the board beside J1. On a v1.1 board or perfboard the red wire runs through L1 first: see "If you have a v1.1 board" below this list. There is no separate switch: the holder's own button turns BLIPR on and off, so set the holder's mode switch to "power on" (it then stays on until you press the button). Next, with the cell still out, tin the **+** end tab of the holder and quickly solder one leg of a 10 kΩ resistor (**R25**) straight onto it. Cover it with heat-shrink and solder a wire (orange works well) to its other leg; that way a nicked wire can't short the cell. Run that wire to the board (J1 BAT). On the board, solder R19 (100 kΩ) from that wire to a point labeled **BATT\_SENSE**, then R20 (100 kΩ) and C26 (100 nF) from BATT\_SENSE to GND, and a wire from BATT\_SENSE to the ESP32-C3's GPIO3 pin. About 10 cm of wire reaches from the holder's mounts to the board.
7. **Leave the Teensy, ESP32, op-amps and radar unplugged.**

**If you have a v1.1 board (or perfboard): the holder's filter by hand.** Cut the red wire and put L1 (22 µH, 1 A or more, either way round) in the gap. Solder C27 (470 µF, stripe to GND) and C28 (1 µF) across J1's +5V and GND, on the board side of L1 and as close to J1 as you can. Keep the red and black wires side by side and heat-shrink every joint.

&#91;image: 5 V noise filter at the battery holder: L1 in the red wire, C27 and C28 across J1\]

**Checkpoint 1: power rails (multimeter on DC volts, black probe on GND)**

Insert the cell, then press the holder's button to turn it on. If the output switches itself off after about 30 seconds with almost no load, check the holder's mode switch is on "power on", or press the button again to re-measure.

| Measure at | Expect | If not |
| --- | --- | --- |
| +5V bus | 4.9–5.2 V | Holder output off (press its button), or cell flat |
| +3V3A bus | 3.25–3.35 V | **Switch off now.** Reads \~5 V or 0 V: U3 is in backwards or its pins are swapped. U3 hot to the touch: short on +3V3A |
| +3V3OP bus | Same as +3V3A, within 0.05 V | R1 missing or the wrong value |
| VREF bus | 1.60–1.70 V | R2/R3 wrong value or not connected to GND |

Also measure **BATT\_SENSE**: it should read the cell voltage divided by 2.1 (about 1.4–2.0 V). It reads the same with the unit off, because the gauge is wired straight to the cell. Write down the cell voltage and the BATT\_SENSE reading; the firmware uses them to calibrate the battery gauge. All good? Turn it off and remove the cell before soldering anything else.

## Step 3: Build the I and Q amplifier channels

Build the I channel completely, check it, then copy it for Q. Short leads and parts packed tight around each socket matter more here than anywhere else in the build.

**Socket pins (MCP6022, top view, notch to the left):** pin 1 is bottom-left beside the notch, counting counter-clockwise: 1, 2, 3, 4 along the bottom and 5, 6, 7, 8 along the top (8 is above 1). On the circuit board the notch is on the right, so pin 1 is the square pad at the top right.

&#91;image: MCP6022 pin map\]

| Pin | Signal |
| --- | --- |
| 1 | Stage 1 output (A) |
| 2 | Stage 1 − input (A) |
| 3 | Stage 1 + input (A) |
| 4 | GND |
| 5 | Stage 2 + input (B) |
| 6 | Stage 2 − input (B) |
| 7 | Stage 2 output (B) |
| 8 | +3V3OP |

&#91;image: I channel amplifier\]

&#91;image: Q channel amplifier\]

1. **Supply first.** Wire pin 8 of U1's socket to +3V3OP and pin 4 to GND. Solder C8 (100 nF) directly between pins 8 and 4, as short as possible.
2. **Stage 1 (I channel).**
   - R4 (4.7 kΩ) from pin 3 to VREF.
   - C12 (10 nF) from pin 3 to a solder point labeled **I-IN**, at the front edge of the board. The radar's I wire lands here later.
   - R5 (10 kΩ) from pin 2 to pin 1. (Older versions had a 22 pF capacitor beside it; leave it out.)
   - R6 (470 Ω) from pin 2 to one end of C14 (1 µF); the other end of C14 to GND.
3. **Stage 2 (I channel).**
   - C15 (10 nF) from pin 1 to pin 5.
   - R7 (4.7 kΩ) from pin 5 to VREF.
   - R8 (10 kΩ) from pin 6 to pin 7 (no capacitor beside it).
   - R9 (470 Ω) from pin 6 to C17 (1 µF), C17's other end to GND.
4. **Output filter (I).** R10 (330 Ω) from pin 7 to a point labeled **A0**. C18 (1 nF) from A0 to GND. Run a short wire from A0 to Teensy pin 14 (A0) on the Teensy's header.
5. **Q channel.** Repeat steps 1–4 on U2's socket with the Q-channel parts: C9, C19, R11, R12, R13, C21, C22, R14, R15, R16, C24, then R17 and C25 to a point labeled **A1**, wired to Teensy pin 15. The input point is **Q-IN**.
6. **Clean and inspect.** Scrub the amplifier area with isopropyl alcohol to remove flux, then check every joint with a magnifier. Look for solder bridges between neighboring holes, especially around the sockets.

**Checkpoint 2: amplifier DC levels**

Plug U1 and U2 into their sockets, each chip's dot at pin 1 (the square pad on the circuit board). Leave the radar, Teensy and ESP32 out. Insert the cell and switch on.

| Measure at | Expect | If not |
| --- | --- | --- |
| U1 and U2 pin 8 | 3.25–3.35 V | Supply wiring to the socket |
| U1 and U2 pins 3 and 5 | 1.60–1.70 V (same as VREF) | R4/R7/R11/R14 not reaching VREF |
| U1 and U2 pins 1 and 7 | 1.60–1.70 V | Stuck near 0 V or 3.3 V: a feedback part is missing or bridged; check R5/R8 and that C14/C17 aren't shorted |
| A0 and A1 points | 1.60–1.70 V | R10/R17 open, or C18/C25 shorted |
| U1, U2 by touch after a minute | Not warm | Warm op-amp: oriented backwards. **Switch off and remove it** |

All good? Switch off and pull the cell. The amplifier can't be tested further until the radar and test firmware are in.

## Step 4: Wire the radar, Teensy, ESP32 and OLED

Everything left is point-to-point wiring; the table at the end of this section is the complete list to check off.

&#91;image: How everything connects\]

&#91;image: Radar K-LC5 to J2, four wires\]

&#91;image: Teensy pins used\]

&#91;image: ESP32-C3 pins used, chip side up\]

&#91;image: Battery gauge, sensor kit (SHT45 and DFRobot 10-DoF) and ammo jack\]

1. **Radar pigtail.** Take a 1×5 female header. Find pin 1 on the K-LC5 (marked on the module and in the outline drawing of RFbeam's datasheet) and mark the matching end of the header. Mark pin 1 on the module too, with a paint pen. This plug is the one that can kill the radar: pins 2 (power) and 4 (ground) mirror each other, so a plug turned round swaps them, and no beep test catches it. It only ever goes on pin 1 to pin 1. Solder five wires about 8–10 cm long to the back of the header:
   - pin 1 → Q (one color), pin 3 → I (another color), pin 2 → +3V3A (red), pin 5 → nothing at all (VCO stays unconnected), pin 4 → **one black ground wire**.
   - Solder C5 (100 nF) directly across header pins 2 and 4 (on the circuit board, C5 is already beside J2). Insulate with heat-shrink or a dab of hot glue.
   - Keep the wires short: just long enough to reach J2 with a little slack. One ground wire is enough, and they don't need twisting (the first build uses short, untwisted wires).
2. **Land the radar wires on the board.** I → **I-IN**, Q → **Q-IN**, red → +3V3A bus, ground → the GND bus right next to the amplifier. On the circuit board, solder the four wires straight into J2's holes rather than using a plug there: a 4-way plug turned round on J2 would put 3.3 V on the radar's I output. Keep this bundle away from the ESP32.
3. **ESP32-C3.** It sits chip side up. Wire its **5V** pin (the one you marked in Step 1) to +5V through D1 (1N5817 diode, striped end toward the ESP32), **GND** to GND, **GPIO20** (its RX) through a 1 kΩ resistor (R23) to Teensy **pin 35** (TX8), and **GPIO21** (its TX) through R24 (1 kΩ) to Teensy **pin 34** (RX8). TX always goes to RX. Firmware 0.2.2 and later use these pins. On board v1.2 the ESP32's own 5 V filter (L2, C29, C30) is on the board between D1 and the socket, so the module plugs in with all its pins. On a v1.1 board, see "If you have a v1.1 board" below this list.
4. **Teensy power.** Teensy **VIN** to +5V and a Teensy **GND** pin to GND.
5. **OLED.** OLED **VCC** to the ESP32-C3's **3V3** pin, **GND** to GND, **SDA** to ESP32 **GPIO6** and **SCL** to ESP32 **GPIO7**. These modules don't all put the pins in the same order, so go by the labels printed on yours. Use four wires about 15 cm long, soldered straight into J3 on the board. If your OLED came with pins fitted, plug female jumper wires onto them: they clear the lid (the first build does this). If it has bare pads, solder the wires to the pads.

&#91;image: The radar's plug with four short wires (one ground, not twisted), and the radar held in its pocket with hot glue at the sides\]

&#91;image: A screen with pins: female jumper wires plugged on, their other ends soldered into J3\]

**If you have a v1.1 board: the ESP32's filter by hand.** With its firmware loaded and the module out of BLIPR, cut its 5V pin off under the black plastic with flush cutters, holding the module flat (don't lever it). Run L2 (22 µH) from the socket's 5V hole (solder a short header pin to L2 and push it in) or from D1's leg on the square-pad side, to the pin's stub on top of the module. Solder C29 (470 µF, stripe to GND) and C30 (1 µF) across the module's 5V stub and its GND pin, close in, and lay L2 and C29 flat so the lid clears them. Beep test: the 5V stub to D1's square pad beeps; 5V to GND must not.

&#91;image: 5 V noise filter at the ESP32: its 5V pin cut, L2 from the socket's 5V hole to the pin stub, C29 and C30 at the module\]

&#91;image: The first build with the lid off: the screen's four soldered wires (no header), the board with the Teensy and the ESP32, the 18650 cell in its holder\]

**Checkpoint 3: everything powered**

Before the radar goes on, use the beep test to confirm header pin 2 connects to +3V3A and pin 4 to GND. That only checks the wires: it can't tell if the plug is turned round on the radar, so check by eye that the two pin-1 marks meet. Then plug in the Teensy and the ESP32, and the radar plug onto the module. Put the meter on +3V3A, keep it there, and be ready to cut power at once (pull the cell if the holder's button needs a double press). Insert the cell and switch on: if +3V3A doesn't read 3.3 V within a second, or U3 gets warm, cut power.

| Check | Expect | If not |
| --- | --- | --- |
| Teensy orange LED | Blinking, if it still has the factory program. With BLIPR firmware it stays dark between shots: READY on the screen (not NO RADAR) shows the Teensy is running | No VIN power: check VIN wire, or the VIN–VUSB cut went wrong |
| ESP32 LED | On | 5V/GND wiring |
| +5V bus with everything on | 4.8 V or more | Weak cell or thin wires from the battery holder |
| +3V3A bus with the radar on | 3.25–3.35 V; U3 warm at most | Radar header on backwards: **switch off at once** |
| Radar I and Q at the header (pins 3 and 1) | Roughly 0.1–0.4 V DC | The datasheet gives a typical 0.2 V offset. 0 V or 3.3 V means a wiring fault |
| A0 and A1 | Still 1.60–1.70 V | Radar wires shorted to a bus |

Passing all three checkpoints means the hardware is ready for test firmware.

### Complete wiring list

| From | To | Notes |
| --- | --- | --- |
| Battery holder 5V out | J1 +5V → L1 (22 µH) → +5V bus (v1.1: L1 in the wire, before J1) | C27 (470 µF) and C28 (1 µF) across J1 +5V and GND |
| Holder GND | J1 GND (GND bus) | Side by side with the red wire |
| +5V bus | Teensy VIN; D1 → L2 (22 µH) → ESP32 5V; R18 → U3 VIN (C1, C4 at U3) | v1.2: L2, C29 (470 µF), C30 (1 µF) on the board. v1.1: the ESP32's 5V pin is cut and they're wired at the module |
| U3 VOUT | +3V3A bus, C2, C3 |  |
| +3V3A | Radar pin 2 (VCC), R1 |  |
| R1 | +3V3OP bus, C7, U1 pin 8, U2 pin 8 | C8, C9 at the sockets |
| +3V3OP | R2 → VREF → R3 → GND | C10, C11 on VREF |
| Radar pin 3 (I) | I-IN → C12 → U1 pin 3 | Short wire |
| Radar pin 1 (Q) | Q-IN → C19 → U2 pin 3 | Short wire |
| Radar pin 5 (VCO) | nothing | Leave it unconnected |
| Radar pin 4 | GND bus (two wires) |  |
| U1 pin 7 | R10 → A0 point → Teensy pin 14 | C18 to GND at A0 |
| U2 pin 7 | R17 → A1 point → Teensy pin 15 | C25 to GND at A1 |
| Teensy pin 35 (TX8) | R23 (1 kΩ) → ESP32 GPIO20 (RX) |  |
| Teensy pin 34 (RX8) | R24 (1 kΩ) ← ESP32 GPIO21 (TX) |  |
| ESP32 3V3 pin | OLED VCC | Soldered wires into J3 |
| ESP32 GPIO6 / GPIO7 | OLED SDA / SCL | Soldered wires into J3 |
| All GND pins | GND bus | Teensy, ESP32, OLED, U1/U2 pin 4 |
| Battery holder + tab | R25 (10 kΩ, right at the tab) → J1 BAT → R19 → BATT\_SENSE → ESP32 GPIO3 | R20 and C26 from BATT\_SENSE to GND |

## Step 5: Print and assemble the case

The v0.12 case is 118.8 × 130.8 mm and 38.8 mm tall with the lid, and prints in four parts with no supports (six with the sensor pod and its roof).

&#91;image: The base v0.12 from the front (radar window), from the rear, and from above\]

&#91;image: Base v0.8: the battery holder's four pads and the tripod post; the left wall's USB-C hole and 14 × 10 mm button slot\]

&#91;image: Base v0.11 side walls from outside: the battery USB-C hole and power-button slot on the left wall, the Teensy USB hole 24-32 mm up on the right wall\]

&#91;image: Base v0.11: the leftover stubs beside the two left battery pads cleared (before and after, from above, front at the top)\]

**What's where.** The radar sits in a pocket behind the front window, facing forward, held by hot glue at its sides, with a thin replaceable cover in front of it. The battery holder screws to four 8 mm round pads on the floor on the left (no walls around it; 2.9 mm screw holes); its power button lines up with the rounded 14 × 10 mm slot toward the back of the left wall, and its USB-C charge port with the square opening toward the front. The main board screws onto four 12 mm posts on the right, and the Teensy's USB port comes out of the right wall. A 1/4-20 insert in the floor takes a tripod screw. The base is Sean's own CAD design. v0.9 made the battery pads 8 mm across with 2.9 mm holes. v0.10 raised the Teensy's USB hole to 24–32 mm above the case bottom (13.5 × 8 mm), to match the Teensy on its 8.5 mm sockets and fit a 12 × 5.5 mm plug. v0.11 cleared the leftover wall stubs beside the two left battery pads. v0.12 made the lid's screen window 13 mm tall (1 mm more toward the front), because the old edge hid the screen's top line.

| File | Print orientation | Settings (ASA) |
| --- | --- | --- |
| base | Floor on the bed, open top up | 0.2 mm layers, 6 walls (makes the 2.4 mm walls solid), 4 top/bottom layers, 25% gyroid infill. Bridges are 34 mm or shorter |
| lid\_oled or lid\_plain | Top face on the bed | Same settings. Print one lid: with or without the screen window |
| front\_cover | Flat, smooth outside face on the bed | 0.15 mm layers, 100% infill. **Natural, white or gray filament**, not black or any filled filament. The window is 0.9 mm thick |

ASA warps, so use an enclosure or a draft shield, a brim on the base, and a bed around 100 °C.

**On MakerWorld:** the case is also on [MakerWorld](https://makerworld.com/en/models/3697742-blipr-doppler-radar-chronograph#profileId-4248561), with Sean's print project (`BLIPR_Case.3mf`, also in `case/out/`) ready to open in Bambu Studio.

&#91;image: Lid v0.12 with the 13 mm screen window, and its underside: screen pocket with four M2 screw pads\]

&#91;image: lid\_sensors v0.12 underside: screen screw pads and the radar hold-down rib\]

**Assembly order**

1. **Inserts.** Press M3 heat-set inserts into the four corner columns and the four board posts (all holes 4.1 mm across and 7.5 mm deep, so inserts up to 7 mm long fit). Press the 1/4-20 insert into the hole under the floor (7.15 mm across, 9 mm deep). Push them in straight and slightly below flush, and let each cool before moving on.
2. **Fit the radar.** Press it into its pocket from above, antenna face forward and flat against the window frame, pins pointing back. It sits on a 3 mm ledge. Hold it square and run hot glue down both sides, where the module meets the pocket; keep glue off the antenna face and the pins. Hot glue holds it far better than foam tape (the first build), and still peels off if the radar has to come out.
3. **Battery holder.** Set its mode switch to "power on" first. Screw it to the four mounts in the left bay with M3 × 6 mm self-tapping screws, its USB-C port and button lined up with the holes in the side wall. Drive the screws gently: they cut their own thread in the 2.9 mm holes.
4. **Power button.** Nothing to fit: press the holder's own button through the hole in the side wall to turn BLIPR on and off.
5. **Main board.** Screw the board onto the posts with four M3 × 6 mm pan-head screws (no wider than 5.5 mm in the back-right corner, next to the Teensy socket), the Teensy's USB facing the right-wall opening.
6. **Radar connection.** Plug the radar pigtail onto the module (pin 1 to pin 1). Dress the wires down along the pocket and away from the ESP32.
7. **Front cover.** Slide it down into the slot behind the front wall, recessed side toward the radar and the wider frame edge at the top.
8. **OLED.** Seat the module (its four wires already soldered on) in the pocket under the lid's window, wires toward the board, and screw it to the four corner pads with M2 × 4 mm screws. Snug only: the pilot holes are plastic.
9. **Lid.** Tuck the screen wires in so nothing gets pinched, then four M3 × 8 mm screws into the corner inserts. The lid also holds the front cover down, and the rib under it sits just above the radar.

&#91;image: Front cover as printed: the recessed area is the 0.9 mm window\]

**Changing the case.** Every size lives at the top of `blipr_case.py`. Edit a number and run `python3 blipr_case.py`; it rebuilds all the STEP and STL files. From v0.8 the base starts from Sean's own CAD model (in user\_edits/) with a few edits made on top, which needs three Python packages: `pip install trimesh manifold3d cadquery-ocp`. The STEP files open in Fusion, FreeCAD or Onshape as solids. Curved surfaces like the screw holes come through as many small flat faces, which is fine for measuring and simple edits.

## Step 6: First power-up and first shot

BLIPR is ready when it powers up to READY and goes dark: that means it's listening. These steps take it from the bench to its first real shot.

**What the screen does.** Press the holder's button. After the start-up animation the screen shows a bubble level (up to a minute; shim BLIPR until it says LEVEL and hold it there 3 s), then the weather for 10 s (with the sensor kit), then READY for 2 s. BLIPR then arms itself and the screen goes dark. After a shot, the speed and the string (n, average, SD, ES) show for the "Show each shot for" time in Range Book's chronograph settings (default 3 s), then the screen goes dark again. BLIPR doesn't listen while the screen is lit: a lit screen adds noise the radar can hear, so keep that time short.

&#91;image: What BLIPR's screen does: level, weather 10 s, READY 2 s, dark and listening, each shot for 3 s\]

**Re-level and the level check.** After each shot BLIPR checks it hasn't been knocked: tilted more than 1°, or turned more than 5° from where it was levelled. If so, the level comes back once the shot has been shown. In Range Book's chronograph settings, **Re-level and update the heading** shows the level now (and updates the direction of fire), and **Disable the level** turns the level off for shooting at an angle: no level at power-up and no re-level after shots, and the heading just follows the compass.

**Settings to check once** (Teensy Serial Monitor, Firmware tab; each is saved):

1. `set fs=500000`: then reboot (the new rate starts after a restart): samples at 500 kHz instead of 600 kHz. The battery holder's converter whistles at about 494 kHz, which at 600 kHz lands near 2,150 fps; at 500 kHz it lands near 100 fps, below any window.
2. The velocity window, a little wider than your load, with the low end well below your slowest shot (BLIPR only hears speeds inside the window: a 733 fps shot with the window starting at 800 never triggered). For example `set vmin=950 vmax=1200` for .22 LR standard velocity. Range Book's chronograph settings show BLIPR's window and have a button that sets it from the load (75–125%).
3. `stat`: overruns should be 0 and the SD card found. `get` lists every setting.

**Where it sits.** Beside the rifle, behind the muzzle, front window downrange and the screen corner nearest you (about 1 o'clock from your seat). On a tripod or the bench, level, and pointing straight downrange, parallel to the bore: use the bench edge or the rifle as a guide. The first .22 tests had it about 10 cm to the side and 10 cm behind the muzzle; the .38 tests 15 cm (6") beside the bore and 8 cm (3") behind the muzzle. For a rifle, start further back, out of the blast (about 30 cm behind and 12 cm to the side). Enter where it sits in Range Book's chronograph settings (sideways and behind the muzzle), so BLIPR corrects for the angle. Measure both (from the radar's centre sideways to the bore, and back from the muzzle): on the .38 tests, entering 10 cm instead of 15 cm read about 3 fps slow. The best match to the Athlon came from a little less than the measured sideways distance (13 cm for 15 cm measured), so if BLIPR reads a few fps off a reference chronograph, try a centimetre or two less.

**Keep other radars away.** Two 24 GHz radar chronographs side by side interfere: with an Athlon Rangecraft next to it, BLIPR saw a steady line near 1,700 fps. Use one at a time, or set them well apart. On Nov 27 an Athlon used on the same shots caused no noise, tones or false triggers, so how close they sit matters: check with BLIPR armed and no shots before you rely on both.

**First shot.** Connect Range Book (Tools › BLIPR Chronograph), check the screen has gone dark, and fire. The speed appears on BLIPR's screen and on the phone. If you have another chronograph, shoot a string with both (one at a time, or apart) and compare; Range Book's settings can calibrate BLIPR against it. To help tune the velocity code, turn on saving (`set save=1`) and keep the SD card's `shots` folder (Firmware tab, section 9).

Plugging the Teensy into a computer turns on USB drive mode and pauses shots (the screen says PAUSED); unplug it, or send `arm`.

## When your parts arrive: measure, then adjust

The case is built from datasheet and typical sizes, so one round of measuring before printing the final version will save reprints. Send me these numbers (a photo of each part next to calipers also helps), and I'll update the script and send new files.

- [ ] **Battery holder:** does it sit on its four mounts with the USB-C port and button lined up with the side holes?
- [ ] **Radar glued in:** is its face flat against the window frame, and does the lid close without lifting? Glue on the antenna face: peel it off.
- [ ] **OLED module:** board size; where the glass sits on the board (distance from each edge); which edge the pins are on.
- [ ] **Radar module:** do the pins come out of the back face or an edge? Where is pin 1? Total thickness including pins.
- [ ] **Perfboard:** actual size and mounting hole centers.
- [x] **Teensy on its headers:** height from the perfboard surface to the top of the Teensy's USB connector. Done on the first build: on its 8.5 mm sockets the USB sits about 27.5 mm above the case bottom, and v0.10 moved the hole to match.
- [ ] **ESP32-C3:** length and width if it isn't 22.5 × 18 mm.
- [ ] **Heat-set inserts:** outer diameter and length of the M3 and 1/4-20 inserts, and the seller's recommended hole size.

A quick first print of just the lid or the front cover is a cheap way to check your printer's hole sizes before committing to the base.

**Troubleshooting**

| Symptom | Likely cause |
| --- | --- |
| Nothing turns on | Cell flat or reversed; holder output off (press its button) |
| Shield output switches off by itself | Too little load before the modules are fitted; normal until the Teensy and radar are connected |
| Teensy doesn't run on battery | VIN not wired to +5V, or VIN–VUSB cut damaged a nearby trace |
| Teensy not seen by the computer when plugged in | Expected when BLIPR is off: it now only runs on battery power, so press the holder's button to turn it on before programming |
| An op-amp output stuck at 0 V or 3.3 V | Missing or bridged feedback part; op-amp in backwards; the gain-leg capacitor shorted |
| U3 hot | Short on +3V3A, or the radar header reversed |
| Radar I/Q at 0 V | Radar not powered (check pin 2 at the header) or pin 1 orientation wrong |
| Screen says NO RADAR | The ESP32 isn't hearing the Teensy: check Teensy pin 35 → R23 → GPIO20, pin 34 → R24 → GPIO21 and the shared GND, and that the Teensy has power |
| Computer doesn't see the ESP32 at all, though its LED is on | Charge-only USB-C cable: swap it. On a Mac, also look for an "Allow accessory to connect?" pop-up |
| Teensy reports SD missing | It only looks at start-up: re-seat the card and replug. Still missing: a format it can't read, so try another card (8–32 GB, A1) |
| False shots at the same speed every time, or no shots and a steady line in live | Interference: a switching converter, the ESP32 or a lit screen. Type live in the Teensy's monitor (or live 114000 to watch one frequency) and rec to record 100 ms; the strongest line and its speed show. Check both 5 V filters are fitted, set fs=500000, and keep the window clear of the line's speed |
| A steady line near 1,700 fps with another chronograph beside it | Two 24 GHz radars beat against each other. Use one at a time, or move them well apart |
| Shots missed or read "weak" | Check the window (get) covers the speed, the screen time is short, and BLIPR is level, close to the muzzle and parallel to the bore. Record with set save=1 and send the SD card's recordings |
| The holder's button won't switch BLIPR on after charging | Seen once after a night on the charger: take the cell out, put it back, and press the button |
| Computer doesn't see the ESP32 while it's in BLIPR | Seen on the v1.1 build with the hand-wired filter. Take it out of its socket to flash it over USB, or update it over Bluetooth from Range Book |
| Bluetooth update stops partway | Needs ESP32 0.2.12 or later on the board (install it once over USB). Keep the phone close with its screen on, and try again: nothing changes until the whole file has arrived |

Still stuck? Measure at the checkpoints again, in order: the first reading that's off points to the problem. Recordings of real shots (`set save=1`, then the SD card's `shots` folder) are the most useful thing to send with a question.
