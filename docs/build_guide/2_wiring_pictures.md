# Wiring pictures

Every connection, drawn with the parts as they look. They fit both builds: on the circuit board (v1.1, Circuit board tab) the off-board wires land on headers J1 to J5; on perfboard they land on the same points named in Step 4. Updated for board v1.1 and firmware 0.2.2: the serial link is on Teensy pins 34 and 35 through 1 kΩ resistors, the radar has 4 wires, and there are no 22 pF capacitors.

How to read them: each coloured line is one wire (or one solder trail on perfboard). A black dot joins wires; lines that cross without a dot don't touch. Pins with a red ring are the ones this project uses. Red is +5 V, black ground, orange 3.3 V, green radar I, blue radar Q (and SDA), yellow SCL and data.

On board v1.2 the two 5 V noise filters are on the board (Circuit board tab). On a v1.1 board they sit in the wires, as in sections 12 and 13; they aren't drawn in the other pictures. The screen's four wires are soldered at both ends (OLED pads and J3): no header, no plug-on jumpers.

## 1. Everything that leaves the main board

&#91;image: How everything connects\]

## 2. Power and battery (no separate switch)

&#91;image: Battery holder wired straight to J1, R25 at the cell tab\]

## 3. Radar

&#91;image: Radar K-LC5 to J2, four wires\]

The plug on the radar goes on pin 1 to pin 1 only: pins 2 (power) and 4 (ground) mirror each other, so a plug turned round swaps them. Mark pin 1 on the module and the plug, and solder the other ends straight into J2.

## 4. Teensy 4.1

&#91;image: Teensy pins used\]

## 5. ESP32-C3 SuperMini

&#91;image: ESP32-C3 pins used, chip side up\]

This is the chip side, the way the module sits on the board. The pin names are printed on the underside, so they read the other way round from this side: here 5V is the right-hand pin nearest the USB. Before powering up, beep the module's 5V pin to D1's square pad.

## 6. Amplifier, I channel

&#91;image: I channel amplifier\]

## 7. Amplifier, Q channel

&#91;image: Q channel amplifier\]

## 8. Op-amp sockets, pin by pin

&#91;image: MCP6022 pin map\]

## 9. Power and reference

&#91;image: Power and VREF parts\]

## 10. Battery gauge, sensor kit, ammo jack

&#91;image: Battery gauge, sensor kit (SHT45 and DFRobot 10-DoF) and ammo jack\]

## 11. Telling the parts apart

&#91;image: Resistor colour bands and capacitor codes\]

## 12. Board v1.1 only: 5 V filter at the battery holder (L1, C27, C28)

&#91;image: 5 V noise filter at the battery holder: L1 in the red wire, C27 and C28 across J1\]

## 13. Board v1.1 only: 5 V filter at the ESP32 (L2, C29, C30)

&#91;image: 5 V noise filter at the ESP32: its 5V pin cut, L2 from the socket's 5V hole to the pin stub, C29 and C30 at the module\]

Flash the ESP32 over USB before cutting its 5V pin: afterwards the computer sees it only out of BLIPR's socket, and Range Book updates it over Bluetooth.
