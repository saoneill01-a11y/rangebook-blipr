# Range Book BLIPR firmware v0.2.3 (ESP32 0.2.3, Teensy 0.2.2)

Firmware for Range Book BLIPR (Ballistic Launch Inspection Portable Radar), the DIY radar chronograph. Step-by-step setup and the bench tests are in the
build guide's **Firmware** tab; this file is the quick reference.

| Folder | Board | What it does |
|---|---|---|
| `BliprTeensy/` | Teensy 4.1 | Samples the radar, finds shots, measures muzzle velocity, saves raw captures to the SD card |
| `BliprBLE/` | ESP32-C3 SuperMini | Bluetooth link to your phone, the OLED screen, the battery gauge, the optional sensors |
| `prebuilt/` | both | Ready-made files if the Arduino IDE gives you trouble (see below) |
| `test/` | your computer | The shot simulator (`sim_test.cpp`) and `replay.cpp`, which runs the SD card's raw recordings through the velocity code (not needed for the build) |
| `PROTOCOL.md` | | The Bluetooth interface, for Range Book and for testing with nRF Connect |

## Arduino IDE setup (once)

1. Install Arduino IDE 2.x.
2. File > Preferences > Additional boards manager URLs, add (one per line):
   - `https://www.pjrc.com/teensy/package_teensy_index.json`
   - `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
3. Boards Manager: install **Teensy** (by Paul Stoffregen) and **esp32** (by Espressif, version 3.3.x).
4. Library Manager: install these, and accept the extra libraries each asks for (Adafruit GFX, Adafruit BusIO, Adafruit Unified Sensor):
   - **Adafruit SSD1306** (the screen)
   - **Adafruit SHT4x**, **Adafruit BMP3XX**, **Adafruit LSM6DS**, **Adafruit LIS3MDL** (the optional sensors)
   - **DFRobot_Multi_DOF_IMU** and **DFRobot_RTU** (the DFRobot 10-DoF compass/level/pressure board). If Library Manager
     doesn't list them, download each as a ZIP from github.com/DFRobot/DFRobot_Multi_DOF_IMU and github.com/DFRobot/DFRobot_RTU
     (Code > Download ZIP) and add them with Sketch > Include Library > Add .ZIP Library.
   - **OneWire** (by Paul Stoffregen) and **DallasTemperature** (by Miles Burton) (the optional ammo probe)

   The sensor libraries are needed to compile even if you never fit the sensors; the firmware skips any sensor it doesn't find.
   The Teensy libraries (ADC, SD, EEPROM) come with the Teensy package.

## Board settings

| | Teensy | ESP32-C3 |
|---|---|---|
| Board | Teensy 4.1 | Nologo ESP32C3 Super Mini (or ESP32C3 Dev Module) |
| USB Type / USB CDC On Boot | Serial + MTP Disk (Experimental) | Enabled |
| CPU Speed | 600 MHz | (default) |
| Serial Monitor speed | any | 115200 |

With the Teensy set to **Serial + MTP Disk**, the SD card shows up on the computer as a drive (see below). Plain **Serial** also works; you just don't get the drive.

## Commands

Type these in the Teensy's Serial Monitor (or send them over Bluetooth, see PROTOCOL.md):

- `help`, `stat`, `get`
- `set vmin=1500 vmax=3500`: only accept speeds in this window (fps)
- `set lat=0.10 behind=0.10`: radar's sideways offset from the bore and distance behind the muzzle (metres)
- `set cal=0`: calibration in parts per million (+1000 reads 0.1 % faster)
- Settings outside sensible ranges are refused (for example `vmin` and `vmax` 100 to 5,500 fps with `vmin` below `vmax`, `f0` 23.9 to 24.4 GHz)
- `arm` / `disarm`, `live`, `rec`, `sim 2800`, `test`, `defaults`, `reboot`
- `drive` / `drive off`: USB drive mode (below; it turns on by itself when you plug into a computer)
- `time 1792480000`: set the clock (Range Book does this every time it connects), so raw recordings have the date and time

ESP32-only commands: `STATUS`, `SYNC n`, `STRING`, `UNITS fps|mps`, `BATV 3.97`, `BRIGHT 0-4`, `THEME 0-3`, `INVERT 0|1`, `FLIP 0|1`, `QUIET 0|1`, `ANIM 0|1`, `LEVEL` / `LEVEL OFF`, `COMPASS CAL START|STOP`, `COMPASS MATCH deg`, `COMPASS OFFSET deg`, `COMPASS REVERSE 0|1`, `COMPASS ROT 0|90|180|270`.

## What changed in 0.2.6 (ESP32 only; the Teensy stays 0.2.2)

- Quiet mode (`QUIET 1`, the default): after setup (the level held, or 60 s, or 3 s without a level sensor) the screen
  goes dark and the ESP32 stops all screen and sensor traffic while it waits for shots. On the first live fire that
  traffic set off false shots twice a second and read as a steady ~1134 fps. After each shot the sensors are read once
  and the result shows for 5 s. The Teensy is held disarmed during setup and armed when the quiet starts.
  `LEVEL` starts setup again; `QUIET 0` keeps the screen and sensors on (bench work).

## What changed in 0.2.5 (ESP32 only; the Teensy stays 0.2.2)

- The screen and sensors (I2C) run at 250 kHz instead of 400/100 kHz. The radar wires picked up the bus clock, and
  with the Teensy at 500 kS/s (`set fs=500000`, used on the first build to move the battery holder's converter tone
  out of the way) both old speeds showed up as a false track near 2035 fps. 250 kHz lands outside the velocity window.

## What changed in 0.2.4 (ESP32 only; the Teensy stays 0.2.2)

- The screen is turned 180 degrees so it reads the right way up in the case (it was upside down on the first build).
  `FLIP 0` turns it back; the choice is remembered.

## What changed in 0.2.3 (ESP32 only; the Teensy stays 0.2.2)

- Sensor kit: the DFRobot Gravity 10-DoF IMU (SEN0696: BMI323 accelerometer, BMM350 compass, BMP581 pressure) is supported
  and is now the recommended board. It replaces both the Adafruit LSM6DSOX + LIS3MDL board and the BMP390; the 9-DoF version
  (SEN0694, no pressure) works too. It's found automatically at I2C 0x4A-0x4D (set its switch to I2C). Pressure comes from it
  when it's there, otherwise from a BMP390. The older Adafruit boards still work.
- The firmware assumes the DFRobot board sits in the sensor pod as the case files have it: holes at the front, plug at the
  back, parts up. On the first minute sitting still it works out which way its accelerometer reports gravity and remembers it.
- `COMPASS REVERSE 1` (Turns backwards in Range Book) now works with any compass, including one with a level sensor: if the
  heading goes down when you turn the unit clockwise, turn it on, then Match my phone again.

## What changed in 0.2.2

- New name: **Range Book BLIPR** (Ballistic Launch Inspection Portable Radar). The Bluetooth name is now RB BLIPR (was RB Chrono), the sketches are `BliprTeensy` and `BliprBLE`, and the SD card shows up as BLIPR SD. Range Book finds it by its Bluetooth service, so the name change doesn't affect connecting.
- Teensy: USB drive mode. With USB Type "Serial + MTP Disk", the SD card shows up on the computer as a drive; it turns on by itself about a second after the Teensy is plugged into a computer (shots pause, the screen shows PAUSED) and off 3 seconds after unplugging. `drive` refreshes the file list, `drive off` or `arm` resumes shots while plugged in.

Needs circuit board v1.1 (or the matching hand wiring): the serial link moved.
- Teensy: the link to the ESP32 is now **Serial8** (pin 35 TX8 to ESP32 GPIO20, pin 34 RX8 from ESP32 GPIO21), each through a 1 kOhm resistor. On board v1.0 or the old wiring it was Serial1 (pins 1 and 0); 0.2.2 won't talk over those.
- Teensy: the radar frequency default is now 24.150 GHz, the K-LC5's typical value (it can be anywhere from 24.050 to 24.250 GHz, so readings can be up to about 0.5 % off until you set `cal` once against another chronograph).
- Teensy: `set` refuses values outside sensible ranges.
- ESP32: each stored shot keeps the Teensy boot id it was measured under, and the stored shots are cleared when the Teensy restarts, so `SYNC` can never re-send old shots as new ones.
- ESP32: `TEST` shots still show on the screen but no longer count in the string's average, SD and spread.
- ESP32: compass calibration no longer guesses the vertical axis from a flat turn (it keeps the old vertical values unless you also tipped the unit well over), and scales against the two horizontal axes only.
- ESP32: `COMPASS REVERSE` is ignored when the accelerometer is fitted (the accelerometer already knows which way is up). `COMPASS ROT` is counter-clockwise seen from above.
- ESP32: the battery gauge expects the 10 kOhm resistor at the cell's + tab (divider ratio 2.1). `BATV` calibration still fine-tunes it.
- ESP32: the settings message can no longer overrun its buffer.
- ESP32: screen looks. `THEME 0`–`THEME 3` (or Range Book's chronograph settings › Look) picks Classic, Big number, Stats (a smaller number with the whole string beside it) or Retro (the old blocky font); `INVERT 1` shows dark text on a lit screen. Both are remembered.
- ESP32: the big text on the screen (the velocity, BLIPR, READY / PAUSED, NO READ, NO RADAR, UPDATING, the LEVEL box) uses a smooth font (FreeSans Bold, part of the Adafruit GFX library) instead of the 5x7 font scaled up. The small text stays 5x7, which is already sharp at its own size.
- ESP32: at power-up a bullet flies across the screen and writes "BLIPR" behind it, then the screen blinks once (about 2 s), before the bubble level.
- ESP32: firmware updates over Bluetooth. Range Book (chronograph settings › Firmware) sends the new firmware in numbered pieces to a spare slot; the board checks each piece's place and the whole file's MD5, switches on the next restart, and keeps the new firmware only after it has run for 15 s (if it crashes or resets sooner, it goes back to the old one). The first 0.2.2 has to go on with the USB cable; after that, Range Book can do it. The Teensy is still updated over USB.
- ESP32: `ANIM 1` (or the switch in Range Book's chronograph settings) plays a short version after each good shot: the bullet crosses the screen and writes the velocity behind it, then the screen blinks. Off by default; `ANIM 0` turns it off. Bluetooth and the radar link keep working while it plays.
- ESP32: with the level sensor fitted, the screen shows a bubble level for 60 s after power-up (and on `LEVEL`). It goes back to the normal screen once it has been level within 0.5 degrees for 3 s, when a shot comes in, or on `LEVEL OFF`.

## What changed in 0.2.1

- ESP32 only: `COMPASS ROT` tells it how the IMU board is turned on its mount, so the level and compass read right whichever way the board went in. Range Book sets it from the chronograph's settings.

## What changed in 0.2.0

- The screen, battery gauge and Bluetooth all live on the ESP32 (wiring v0.4); the Teensy only does the radar.
- Clock: the app sets it on connect; `log.csv` and each recording's header carry the date and time.
- Screen brightness (`BRIGHT`).
- Optional sensors on the ESP32's I2C bus (SHT45, BMP390, LSM6DSOX + LIS3MDL) and an ammo probe (DS18B20 on GPIO10), all found automatically; readings on the new Sensors characteristic and on the screen. See the build guide's **Sensors** tab.

## Getting the recordings off the SD card (USB drive mode)

You don't need to open the case or take the card out.
1. Switch the chronograph on (the Teensy runs from the battery; the USB cable only carries data), then plug a USB cable from the Teensy's port into the computer.
2. On Windows, open File Explorer: under This PC there is a device called **Teensy** with a storage called **BLIPR SD**. On a Mac, install **OpenMTP** (free) and open it. On Linux, most file managers show it.
3. Nothing to type: about a second after it's plugged into a computer, the Teensy goes into drive mode by itself. Shot detection pauses and the chronograph's screen shows PAUSED.
4. Copy the `shots` folder and `log.csv` to the computer. Each recording is about 320 KB, so 100 of them are about 32 MB; MTP is slower than a card reader, so a big folder can take a minute or more.
5. Unplug the cable. About 3 seconds later the chronograph is listening for shots again. A USB charger or power bank doesn't count as a computer, so it won't pause anything.

Notes:
- The file list on the computer is read when you plug in. If you record something while plugged in (for example `rec`), type `drive` to make the computer re-read it.
- Bench testing over USB: `sim` and `arm` switch drive mode off, so the fake-bullet tests still work while plugged in. `drive off` does the same. It comes back the next time you plug in.
- Deleting files from the computer works too, but copy them first.
- MTP support in the Teensy package is marked experimental by PJRC. If the drive doesn't appear, unplug and plug in again, or use the card reader.

## Prebuilt files

- `prebuilt/BliprTeensy.hex` (built with USB Type Serial + MTP Disk): open the Teensy Loader app (installed with the Teensy package), File > Open HEX File, press the Teensy's button.
- `prebuilt/BliprBLE.app.bin`: the app image alone, the file Range Book sends for a Bluetooth update (not for the web flasher).
- `prebuilt/BliprBLE.merged.bin`: flash with the web flasher at https://espressif.github.io/esptool-js/ in Chrome (address 0x0).

## Raw capture files (SD card, `/shots/`)

`sNNNNN.bin` = a 512-byte text header (JSON: sample rate, settings, result) followed by `n` I samples and
then `n` Q samples, each a 16-bit little-endian number (0 to 4095). `log.csv` has one line per capture.
Send these files to Claude to tune the shot detection.
