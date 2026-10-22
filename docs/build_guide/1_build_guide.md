# Range Book BLIPR – Build Guide

Oct 19, 2026 · @Sean

## Overview

You're building Range Book BLIPR (Ballistic Launch Inspection Portable Radar), a bench-side 24 GHz Doppler radar chronograph that sends each shot's velocity over Bluetooth to your web app. It sits beside the rifle on the bench, so nothing goes downrange.

How it works, in one pass: the RFbeam K-LC5 radar sends out a 24 GHz signal and outputs two very weak signals (called I and Q) whose frequency is proportional to the bullet's speed: about 161 Hz per m/s, so roughly 150 kHz for a 3,000 fps rifle bullet. A two-stage amplifier boosts each signal about 500 times. The Teensy 4.1 samples both signals with its two built-in ADCs, finds the frequency with an FFT, and works out velocity. An ESP32-C3 board sends the result to your phone over Bluetooth Low Energy.

&#91;embedded content: signal path · 5 hops, plus power\]

**What this guide covers:** the hardware. That means the circuit, soldering, wiring, the 3D-printed case, and electrical checks with a multimeter at each stage. **What comes later:** the firmware for the Teensy and ESP32, and the web app connection. Until the firmware exists, the checkpoints in this guide confirm the hardware is built right; the first real test with a moving target happens once the test firmware is written.

**Case files (v0.1 draft):** `base`, `lid_oled` / `lid_plain`, and `front_cover`, each as STEP and STL, plus `blipr_case.py`, the parametric script that generates them. The case is built from datasheet and typical sizes, so expect one round of adjustments after you measure your actual parts (see the last section).

**Firmware (v0.1.0):** setup and bench tests are on the Firmware tab.

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
| Hot glue, thin double-sided foam tape | Holding the battery shield, switch and OLED |
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
| BLE | ESP32-C3 SuperMini | 1 | Spares are handy |
| U1, U2 | MCP6022-E/P dual op-amp (DIP-8) | 2 | Buy 4 |
| U3 | MCP1700-3302E/TO, 3.3 V low-dropout regulator (TO-92) | 1 | **new**, buy 2, about $0.40 at DigiKey |
| — | DIP-8 IC sockets | 2 | **new**, so the op-amps can be swapped |
| BT1 | 18650 battery shield (5 V + 3.3 V outputs) + 18650 cell | 1 |  |
| SW1 | DPDT mini slide switch (two rows of 3 tabs) | 1 |  |
| OLED | 0.96" SSD1306 I2C display | 1 | Shows speed and battery level; white version reads best |
| R1 | 10 Ω resistor | 1 | Op-amp supply filter |
| R2, R3 | 10 kΩ | 2 | Mid-rail reference divider |
| R4, R7, R11, R14 | 4.7 kΩ | 4 | Input bias resistors |
| R5, R8, R12, R15 | 10 kΩ | 4 | Feedback resistors |
| R6, R9, R13, R16 | 470 Ω | 4 | Gain resistors |
| R10, R17 | 330 Ω | 2 | ADC input filter |
| C1, C2 | 1 µF ceramic | 2 | Regulator in/out |
| C14, C17, C21, C24 | 1 µF ceramic | 4 | Gain-leg capacitors |
| C3 | 100 µF electrolytic, 10 V or higher | 1 | **new**, regulator output |
| C4, C7, C10 | 10 µF electrolytic, 10 V or higher | 3 | **new** |
| C5, C8, C9, C11 | 100 nF ceramic | 4 | Decoupling |
| C12, C15, C19, C22 | 10 nF ceramic | 4 | Input coupling |
| R23, R24 | 1 kΩ | 2 | new (v1.1): one in each serial line between the Teensy and ESP32 |
| C18, C25 | 1 nF ceramic | 2 | ADC input filter |
| — | 70 × 90 mm double-sided perfboard | 1 | Or the RB BLIPR circuit board v1.1 (Circuit board tab) |
| — | Female headers 2.54 mm | 2×24, 2×8, 1×5, 1×4 | Teensy, ESP32, radar, OLED |
| — | M3 heat-set inserts (about 4.6–5 mm OD) | 8 | **new**, 4 lid + 4 board posts |
| — | M3 × 8 mm screws (lid), M3 × 6 mm screws (board) | 4 + 4 | **new** |
| — | 1/4-20 heat-set insert, 13 mm long or shorter | 1 | Tripod mount |
| — | 26–28 AWG stranded wire, 4+ colors | 1 set | **new** |

**Added after an independent design review (v0.2):** **D1**, a 1N5817 Schottky diode in the ESP32's 5 V feed, so plugging USB into the ESP32 can't push power back into the rest of the unit. **R18**, a second 10 Ω resistor in front of U3, which with C4 filters the battery shield's switching noise before it reaches the radar. And the four feedback capacitors (C13, C16, C20, C23) are now **22 pF** instead of 47 pF, which keeps about 4 dB more gain at the fastest velocities.

**Added for the battery gauge (v0.3):** SW1 is now a **DPDT** slide switch (two rows of three tabs) instead of SPDT, plus **R19, R20** (100 kΩ each) and **C26** (100 nF).

**Changed when the firmware was written (v0.4):** the OLED and the battery sense now connect to the **ESP32-C3** instead of the Teensy. The Teensy's two converters sample the radar nonstop, so reading the battery on them would interrupt the radar, and the screen's slow updates could make it miss samples. The ESP32 has time to spare for both.

**Changed after two independent reviews (v0.5, Oct 20):** the four 22 pF capacitors (C13, C16, C20, C23) are left out, because they cut the gain at the fastest speeds. C6 is gone and radar pin 5 (VCO) gets no wire. **R23, R24** (1 kΩ) go in the two serial lines, which move to Teensy pins 34 and 35. **R25** (10 kΩ) is soldered right on the cell's + tab, so a damaged gauge wire can't short the battery. These need firmware 0.2.2.

The resistor and ceramic capacitor assortment kits from the spreadsheet should cover every value above. Before you start, check your ceramic kit actually includes 22 pF, 1 nF, 10 nF, 100 nF and 1 µF, and get an electrolytic kit (or individual parts) for the 10 µF and 100 µF values.

&#91;image: Resistor colour bands and capacitor codes\]

## Schematic and how the circuit works

The circuit has three parts: clean power for the radar and amplifiers, two identical amplifier channels (I and Q), and plain wiring between the modules.

&#91;image: Schematic v0.5: power with battery sense, I-channel amplifier, Q-channel parts and module connections\]

**Power.** The battery shield makes 5 V. The slide switch (SW1) turns everything on. 5 V feeds the Teensy, the ESP32 (through diode D1, which blocks power flowing back from the ESP32's USB port) and, through filter resistor R18, a separate low-noise 3.3 V regulator (U3) that powers only the radar and the amplifiers. Keeping the radar off the Teensy's own 3.3 V keeps digital noise out of the weakest signals in the build. R1 and C7 filter the op-amp supply a second time.

**Mid-rail reference (VREF).** The op-amps run from a single 3.3 V supply, so the signals swing around the middle, 1.65 V. R2 and R3 split the supply in half, and C10 and C11 hold it steady.

**Battery level.** R19 and R20 halve the cell voltage (4.2 V full becomes 2.1 V) so the ESP32-C3 can read it on GPIO3 without exceeding its input limit. C26 steadies the reading. The divider connects through the second half of the power switch, so it draws nothing when the unit is off and can't feed voltage into a powered-down ESP32.

**Amplifier.** Each channel is two identical stages, each boosting the signal about 22 times (about 500 total). In each stage:

- The input capacitor (C12) and bias resistor (R4) block DC and cut anything under about 3.4 kHz. That removes the radar's 0.2 V DC offset plus slow motion and hum. 3.4 kHz corresponds to about 70 fps, well below anything you'll shoot.
- R5 and R6 set the gain. C14 in the gain leg makes the DC gain 1, so the output idles at exactly 1.65 V.
- Nothing sits across R5: the op-amp itself rolls the gain off at the top, about 3 dB down near 245 kHz (5,000 fps). The firmware samples each channel 600,000 times per second, above twice the fastest signal.

R10 and C18 at the end form a small filter right at the Teensy pin, which keeps the ADC's sampling from disturbing the amplifier.

**Pins that might move.** A0 and A1 are chosen so both of the Teensy's ADCs can sample I and Q at the same moment. I'll confirm this when writing the firmware; if a different pin turns out better, it's a one-wire move.

## Step 1: Prepare the boards

Test each module on its own before it gets soldered into anything, then lay out the perfboard so the case lines up.

1. **Sort and check parts.** Measure every resistor with the multimeter before it goes in (10 Ω, 330 Ω, 470 Ω, 4.7 kΩ, 10 kΩ look alike). Bag the capacitors by value. Electrolytics have a stripe marking the **negative** lead, and the longer lead is positive.
2. **Test the Teensy.** Plug it into your computer with a micro-USB data cable. The orange LED should blink (factory test program). If nothing happens, try another cable before blaming the board.
3. **Cut the Teensy's VIN–VUSB link.** On the underside near the USB connector are two pads joined by a thin trace, labeled VIN and VUSB on PJRC's pinout card. Cut that trace with a hobby knife, a few light strokes. Confirm with the continuity beep: no beep between VIN and VUSB. This stops the battery and your computer's USB from fighting each other. From now on, the Teensy only runs when the chronograph's power switch is on, including when you program it.
4. **Test the ESP32-C3.** Plug it into USB-C; a power LED should light. If its pin headers came loose, solder them on now (short side into the board).
5. **Check the perfboard holes.** Most 70 × 90 mm boards have a 2–3 mm hole in each corner about 3 mm in from both edges, which is what the case posts expect. If yours don't, mark centers 3 mm in from each edge and drill 3.2 mm.
6. **Mark the layout zones** on the top of the perfboard with a fine marker, with the board positioned as it will sit in the case: the 70 mm side is the front edge, facing the radar.

| Zone | Where on the board (front edge = 0) | What goes there |
| --- | --- | --- |
| Amplifier and power | Front 28 mm, full width | U3 and its capacitors, VREF divider, U1 (I channel) on the left half, U2 (Q channel) on the right half |
| Teensy 4.1 | Lying left-to-right across the rear of the board, centered 75 mm back from the front edge, with its USB connector at the board's right edge (it lines up with the hole in the case's right wall) | Two 1×24 female headers, 15.2 mm (6 rows) apart |
| ESP32-C3 | Left side, about 6–24 mm from the left edge, 34–57 mm back | Two 1×8 female headers; its antenna end toward the rear, away from the radar |
| Keep clear underneath | Left 7 mm strip between 28 and 48 mm back | The tripod insert boss sits under here, so no solder tails |
| Corners | 6 mm circle around each mounting hole | Screw heads and posts |

7. **Solder the sockets.** Plug the female headers onto the Teensy's pins, set the whole assembly on the board in its zone, and solder the header pins from underneath. Doing it with the Teensy in place keeps the rows perfectly spaced. Remove the Teensy, then do the same for the ESP32. Solder the two DIP-8 sockets in the amplifier zone with their notches facing the same way (toward the left edge), and mark pin 1 next to each.

## Step 2: Build the power section

Build and test power before anything expensive is plugged in; a wiring mistake here is the one most likely to damage the radar.

&#91;image: Battery shield, R25 at the cell tab, DPDT switch and J1\]

&#91;image: Power and VREF parts\]

All the wiring pictures, with notes, are also on the Wiring pictures tab.

1. **Lay down the rails.** Along the front edge of the board, run a bare tinned-wire ground (GND) bus the full width, soldered every few holes. Above it, run short separate buses for **+5V**, **+3V3A**, **+3V3OP** and **VREF**. Label them with a marker. Every part that says "to GND" on the schematic goes to the GND bus by the shortest path.
2. **Fit U3 (MCP1700).** Hold it with the flat, printed face toward you and the leads down: per Microchip's datasheet the leads are **GND, VIN, VOUT** from left to right. Sources online disagree on this pinout, so check the diagram in the datasheet on U3's DigiKey page before soldering. VOUT goes to +3V3A; VIN connects in the next step.
3. **Add the regulator capacitors.** R18 (10 Ω) from the +5V bus to U3's VIN. C1 (1 µF) and C4 (10 µF, stripe to GND) from U3's VIN to GND, right at U3. R18 and C4 together filter the shield's switching noise. C2 (1 µF) and C3 (100 µF, stripe to GND) from +3V3A to GND, close to U3's output.
4. **Op-amp supply filter.** R1 (10 Ω) from +3V3A to +3V3OP. C7 (10 µF, stripe to GND) from +3V3OP to GND.
5. **VREF divider.** R2 (10 kΩ) from +3V3OP to VREF, R3 (10 kΩ) from VREF to GND. C10 (10 µF, stripe to GND) and C11 (100 nF) from VREF to GND.
6. **Battery shield and switch.** With **no cell in the shield**, solder a red wire to the shield's 5 V output pad and a black wire to its GND pad (use the solder pads or header pins, not the USB-A socket). The black wire goes to the GND bus. SW1 has two rows of three tabs; each row is one half of the switch (row A and row B). The red wire goes to an end tab of row A, and a second red wire goes from row A's middle tab to the +5V bus. Next, with the cell still out, tin the \*\*+\*\* end tab of the shield's battery holder and quickly solder one leg of a 10 kΩ resistor (\*\*R25\*\*) straight onto it. Cover it with heat-shrink and solder a wire (orange works well) to its other leg; that way a nicked wire can't short the cell. Run that wire to the end tab of row B on the same side you used in row A, then run a wire from row B's middle tab to the board. On the board, solder R19 (100 kΩ) from that wire to a point labeled \*\*BATT\_SENSE\*\*, then R20 (100 kΩ) and C26 (100 nF) from BATT\_SENSE to GND, and a wire from BATT\_SENSE to the ESP32-C3's GPIO3 pin. Make the switch and battery-holder wires about 10 cm long so the switch can reach the rear wall slot.
7. **Leave the Teensy, ESP32, op-amps and radar unplugged.**

**Checkpoint 1: power rails (multimeter on DC volts, black probe on GND)**

Insert the cell, then switch on. Some shields also need their button pressed once to turn on the output, and some switch themselves off after about 30 seconds with almost no load. That's normal at this stage; press the button again to re-measure.

| Measure at | Expect | If not |
| --- | --- | --- |
| +5V bus | 4.9–5.2 V | Shield output off (press its button), switch wired to the wrong tab, or cell flat |
| +3V3A bus | 3.25–3.35 V | **Switch off now.** Reads \~5 V or 0 V: U3 is in backwards or its pins are swapped. U3 hot to the touch: short on +3V3A |
| +3V3OP bus | Same as +3V3A, within 0.05 V | R1 missing or the wrong value |
| VREF bus | 1.60–1.70 V | R2/R3 wrong value or not connected to GND |

Also measure \*\*BATT\_SENSE\*\*: it should read half the cell voltage (1.6–2.1 V), and 0 V with the switch off. Write down the cell voltage and the BATT\_SENSE reading; the firmware uses them to calibrate the battery gauge. All good? Switch off and remove the cell before soldering anything else.

## Step 3: Build the I and Q amplifier channels

Build the I channel completely, check it, then copy it for Q. Short leads and parts packed tight around each socket matter more here than anywhere else in the build.

**Socket pins (MCP6022, top view, notch to the left):** pin 1 is bottom-left beside the notch, counting counter-clockwise: 1, 2, 3, 4 along the bottom and 5, 6, 7, 8 along the top (8 is above 1).

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

Plug U1 and U2 into their sockets (notch matching the socket). Leave the radar, Teensy and ESP32 out. Insert the cell and switch on.

| Measure at | Expect | If not |
| --- | --- | --- |
| U1 and U2 pin 8 | 3.25–3.35 V | Supply wiring to the socket |
| U1 and U2 pins 3 and 5 | 1.60–1.70 V (same as VREF) | R4/R7/R11/R14 not reaching VREF |
| U1 and U2 pins 1 and 7 | 1.60–1.70 V | Stuck near 0 V or 3.3 V: a feedback part is missing or bridged; check R5/R8 and that C14/C17 aren't shorted |
| A0 and A1 points | 1.60–1.70 V | R10/R17 open, or C18/C25 shorted |
| U1, U2 by touch after a minute | Not warm | Warm op-amp: oriented backwards. **Switch off and remove it** |

All good? Switch off and pull the cell. The amplifier can't be tested further until the radar and test firmware are in.

## Step 4: Wire the radar, Teensy, ESP32, OLED and switch

Everything left is point-to-point wiring; the table at the end of this section is the complete list to check off.

&#91;image: How everything connects\]

&#91;image: Radar K-LC5 to J2, four wires\]

&#91;image: Teensy pins used\]

&#91;image: ESP32-C3 pins used, chip side up\]

&#91;image: Battery gauge, sensors and ammo jack\]

1. **Radar pigtail.** Take a 1×5 female header. Find pin 1 on the K-LC5 (marked on the module and in the outline drawing of RFbeam's datasheet) and mark the matching end of the header. Solder five wires about 8–10 cm long to the back of the header:
   - pin 1 → Q (one color), pin 3 → I (another color), pin 2 → +3V3A (red), pin 5 → nothing at all (VCO stays unconnected), pin 4 → **two** black ground wires.
   - Solder C5 (100 nF) directly across header pins 2 and 4 (on the circuit board, C5 is already beside J2). Insulate with heat-shrink or a dab of hot glue.
   - Twist the I wire with one ground wire and the Q wire with the other. Twisting pairs cuts pickup of digital noise.
2. **Land the radar wires on the board.** I → **I-IN**, Q → **Q-IN**, red → +3V3A bus, both grounds → the GND bus right next to the amplifier. Keep this bundle away from the ESP32.
3. **ESP32-C3.** It sits chip side up. Wire its **5V** pin to +5V through D1 (1N5817 diode, striped end toward the ESP32), **GND** to GND, **GPIO20** (its RX) through a 1 kΩ resistor (R23) to Teensy **pin 35** (TX8), and **GPIO21** (its TX) through R24 (1 kΩ) to Teensy **pin 34** (RX8). TX always goes to RX. Firmware 0.2.2 uses these pins; pins 0 and 1 are no longer used.
4. **Teensy power.** Teensy **VIN** to +5V and a Teensy **GND** pin to GND.
5. **OLED.** OLED **VCC** to the ESP32-C3's **3V3** pin, **GND** to GND, **SDA** to ESP32 **GPIO6** and **SCL** to ESP32 **GPIO7**. These modules don't all put the pins in the same order, so go by the labels printed on yours. Use wires about 15 cm long, since the OLED mounts in the lid's back corner. It sits about 5 mm above the Teensy, so solder the wires straight to the OLED's pads (or bend its header pins flat); a straight header with plug-on wires won't fit.

**Checkpoint 3: everything powered**

Before the radar goes on, use the beep test to confirm header pin 2 connects to +3V3A and pin 4 to GND; a reversed header can destroy the module. Then plug in the Teensy and the ESP32, and the radar header onto the module (pin 1 to pin 1). Insert the cell and switch on.

| Check | Expect | If not |
| --- | --- | --- |
| Teensy orange LED | Blinking (factory program) | No VIN power: check VIN wire, or the VIN–VUSB cut went wrong |
| ESP32 LED | On | 5V/GND wiring |
| +5V bus with everything on | 4.8 V or more | Weak cell or thin wires to the switch |
| +3V3A bus with the radar on | 3.25–3.35 V; U3 warm at most | Radar header on backwards: **switch off at once** |
| Radar I and Q at the header (pins 3 and 1) | Roughly 0.1–0.4 V DC | The datasheet gives a typical 0.2 V offset. 0 V or 3.3 V means a wiring fault |
| A0 and A1 | Still 1.60–1.70 V | Radar wires shorted to a bus |

Passing all three checkpoints means the hardware is ready for test firmware.

### Complete wiring list

| From | To | Notes |
| --- | --- | --- |
| Shield 5V out | SW1 row A end tab |  |
| SW1 row A middle tab | +5V bus |  |
| Shield GND | GND bus |  |
| +5V bus | Teensy VIN; D1 → ESP32 5V; R18 → U3 VIN (C1, C4 at U3) |  |
| U3 VOUT | +3V3A bus, C2, C3 |  |
| +3V3A | Radar pin 2 (VCC), R1 |  |
| R1 | +3V3OP bus, C7, U1 pin 8, U2 pin 8 | C8, C9 at the sockets |
| +3V3OP | R2 → VREF → R3 → GND | C10, C11 on VREF |
| Radar pin 3 (I) | I-IN → C12 → U1 pin 3 | Twisted with a ground |
| Radar pin 1 (Q) | Q-IN → C19 → U2 pin 3 | Twisted with a ground |
| Radar pin 5 (VCO) | nothing | Leave it unconnected |
| Radar pin 4 | GND bus (two wires) |  |
| U1 pin 7 | R10 → A0 point → Teensy pin 14 | C18 to GND at A0 |
| U2 pin 7 | R17 → A1 point → Teensy pin 15 | C25 to GND at A1 |
| Teensy pin 35 (TX8) | R23 (1 kΩ) → ESP32 GPIO20 (RX) |  |
| Teensy pin 34 (RX8) | R24 (1 kΩ) ← ESP32 GPIO21 (TX) |  |
| ESP32 3V3 pin | OLED VCC | Optional |
| ESP32 GPIO6 / GPIO7 | OLED SDA / SCL | Optional |
| All GND pins | GND bus | Teensy, ESP32, OLED, U1/U2 pin 4 |
| Battery holder + tab | R25 (10 kΩ, right at the tab) → SW1 row B end tab; row B middle → R19 → BATT\_SENSE → ESP32 GPIO3 | R20 and C26 from BATT\_SENSE to GND |

## Step 5: Print and assemble the case

The v0.1 case is 118.8 × 130.8 mm and 38.8 mm tall with the lid, and prints in four parts with no supports.

&#91;image: The base from the front (radar window), from the rear (ports), and from above\]

**What's where.** The radar sits in a pocket behind the front window, facing forward, with a thin replaceable cover in front of it. The battery shield goes in the long bay on the left, with its charge port at the rear wall. The main board screws onto four 12 mm posts on the right. The Teensy's USB port comes out of the right wall, and the power switch and charge port are on the rear wall. A 1/4-20 insert in the floor takes a tripod screw.

| File | Print orientation | Settings (ASA) |
| --- | --- | --- |
| base | Floor on the bed, open top up | 0.2 mm layers, 6 walls (makes the 2.4 mm walls solid), 4 top/bottom layers, 25% gyroid infill. Bridges are 34 mm or shorter |
| lid\_oled or lid\_plain | Top face on the bed | Same settings. Print one lid: with or without the screen window |
| front\_cover | Flat, smooth outside face on the bed | 0.15 mm layers, 100% infill. **Natural, white or gray filament**, not black or any filled filament. The window is 0.9 mm thick |

ASA warps, so use an enclosure or a draft shield, a brim on the base, and a bed around 100 °C.

&#91;image: Lid with OLED window and its underside pocket\]

**Assembly order**

1. **Inserts.** Press M3 heat-set inserts into the four corner columns (holes 4.1 mm, 6 mm deep) and the four board posts (4.1 mm, 5 mm deep). Press the 1/4-20 insert into the hole under the floor (8.4 mm, 13.4 mm deep). Push them in straight and slightly below flush, and let each cool before moving on.
2. **Test-fit the radar.** Drop the module into its pocket from above, antenna face forward against the window frame, pins pointing back. It sits on a 3 mm ledge. Don't glue it yet; we may rotate it 90° after the first tests (the datasheet is unclear about which axis has the 80° beam, and the pocket is square for that reason).
3. **Battery shield.** Slide it into the left bay with its charge port lined up with the rear-wall slot. Hold it with double-sided foam tape for now. Standoffs that match its mounting holes will be added once the shield arrives and is measured.
4. **Switch.** Push the lever through the small rear slot from inside and hot-glue the switch body to the wall.
5. **Main board.** Screw the board onto the posts with four M3 × 6 mm screws, the Teensy's USB facing the right-wall opening.
6. **Radar connection.** Plug the radar pigtail onto the module (pin 1 to pin 1). Dress the wires down along the pocket and away from the ESP32.
7. **Front cover.** Slide it down into the slot behind the front wall, recessed side toward the radar and the wider frame edge at the top.
8. **OLED.** Seat the module in the pocket under the lid's window and hold it with a few dabs of hot glue on the board edges, not on the glass.
9. **Lid.** Four M3 × 8 mm screws into the corner inserts. The lid also holds the front cover down.

&#91;image: Front cover as printed: the recessed area is the 0.9 mm window\]

**Changing the case.** Every size lives at the top of `blipr_case.py`. Edit a number and run `python3 blipr_case.py`; it rebuilds all the STEP and STL files in a few seconds with plain Python. No CAD software is needed, and no extra packages. The STEP files open in Fusion, FreeCAD or Onshape as solids. Curved surfaces like the screw holes come through as many small flat faces, which is fine for measuring and simple edits.

## When your parts arrive: measure, then adjust

The case is built from datasheet and typical sizes, so one round of measuring before printing the final version will save reprints. Send me these numbers (a photo of each part next to calipers also helps), and I'll update the script and send new files.

- [ ] **Battery shield with the cell in:** length, width, height; where the charge port sits (distance from the nearest edge, height above the bottom of the board); mounting hole positions, if any.
- [ ] **Slide switch:** body length, width, height; lever width and travel; mounting hole spacing, if any.
- [ ] **OLED module:** board size; where the glass sits on the board (distance from each edge); which edge the pins are on.
- [ ] **Radar module:** do the pins come out of the back face or an edge? Where is pin 1? Total thickness including pins.
- [ ] **Perfboard:** actual size and mounting hole centers.
- [ ] **Teensy on its headers:** height from the perfboard surface to the top of the Teensy's USB connector.
- [ ] **ESP32-C3:** length and width if it isn't 22.5 × 18 mm.
- [ ] **Heat-set inserts:** outer diameter and length of the M3 and 1/4-20 inserts, and the seller's recommended hole size.

A quick first print of just the lid or the front cover is a cheap way to check your printer's hole sizes before committing to the base.

**Troubleshooting**

| Symptom | Likely cause |
| --- | --- |
| Nothing turns on | Cell flat or reversed; shield needs its button pressed; SW1 wired to the wrong tabs |
| Shield output switches off by itself | Too little load before the modules are fitted; normal until the Teensy and radar are connected |
| Teensy doesn't run on battery | VIN not wired to +5V, or VIN–VUSB cut damaged a nearby trace |
| Teensy not seen by the computer when plugged in | Expected with the switch off: it now only runs on battery power, so switch on to program it |
| An op-amp output stuck at 0 V or 3.3 V | Missing or bridged feedback part; op-amp in backwards; the gain-leg capacitor shorted |
| U3 hot | Short on +3V3A, or the radar header reversed |
| Radar I/Q at 0 V | Radar not powered (check pin 2 at the header) or pin 1 orientation wrong |
| Screen says NO RADAR | The ESP32 isn't hearing the Teensy: check Teensy pin 35 → R23 → GPIO20, pin 34 → R24 → GPIO21 and the shared GND, and that the Teensy has power |

Next up, whenever you're ready: test firmware that records raw radar data to the SD card and shows a live signal, then the velocity calculation, then the Bluetooth link into your web app.
