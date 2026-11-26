# Range Book BLIPR firmware (ESP32 0.2.18, Teensy 0.2.7)

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
- `set band=15`: in-band trigger level (dB; `band=0` = the old whole-block trigger at `trig`); `set qc=11` quick check,
  `set fade=6` interference check (both dB, 0 = off, not saved)
- Settings outside sensible ranges are refused (for example `vmin` and `vmax` 100 to 5,500 fps with `vmin` below `vmax`, `f0` 23.9 to 24.4 GHz)
- `arm` / `disarm`, `live`, `rec`, `sim 2800`, `test`, `defaults`, `reboot`
- `drive` / `drive off`: USB drive mode (below; it turns on by itself when you plug into a computer)
- `time 1792480000`: set the clock (Range Book does this every time it connects), so raw recordings have the date and time

ESP32-only commands: `STATUS`, `SYNC n`, `STRING`, `UNITS fps|mps`, `BATV 3.97`, `BRIGHT 0-4`, `THEME 0-3`, `INVERT 0|1`, `FLIP 0|1`, `QUIET 0|1`, `ANIM 0|1`, `LEVEL` / `LEVEL OFF`, `COMPASS CAL START|STOP`, `COMPASS MATCH deg`, `COMPASS OFFSET deg`, `COMPASS REVERSE 0|1`, `COMPASS ROT 0|90|180|270`.

## What changed in ESP32 0.2.17 and 0.2.18 (Nov 25)

- 0.2.18: test shots also run the after-shot level check (so it can be tried on the bench).

- After each shot BLIPR checks it hasn't been knocked: tilted more than 1 degree, or turned more than 5 degrees from
  the heading it had when it was last levelled, and the level comes back on its screen (disarmed) once the shot has
  been shown, then READY and quiet. That also updates the heading in the app. The weather screen shows only at
  power-up; LEVEL from the app (now "Re-level and update the heading") goes straight to READY after the level.

## What changed in ESP32 0.2.15 and 0.2.16 (Nov 25)

- 0.2.16: after the level, the screen shows the weather for 10 s (with sensors fitted), then READY for 2 s, then BLIPR
  arms and goes dark. BLIPR stays disarmed until then, so those screens can't set off a false shot. After a shot the
  screen shows the string (n, avg, SD, ES) instead of the weather; the app has the weather.
- 0.2.15: `SHOW s` sets how long a shot stays on the screen (1-60 s, 0 = until the next shot; saved; config "show").
  Range Book's chronograph settings have it as "Show each shot for". A lit screen adds noise (bench: rms 7.8 -> 12.2
  counts and a ~11.7 kHz tone), so 3 s is the default.

## What changed in ESP32 0.2.14 (Nov 25)

- While quiet, a shot shows on the screen for 3 s (was 1.5 s), then it goes dark. Screen redraws read as false
  shots, so none happen between shots.

## What changed in ESP32 0.2.11-0.2.13 (Nov 25)

- 0.2.12: Bluetooth firmware updates no longer stop part-way ("update stopped (not started)"): the 20 s stall check
  could see a negative time and cancel a running update. 0.2.13 is the same code, used to test a real update.
- 0.2.11: logs on USB why a Bluetooth link dropped and why the ESP32 last restarted, and update progress every 10%;
  the screen redraws once a second (not ten times) during an update.

## What changed in Teensy 0.2.7 and ESP32 0.2.10 (Nov 25)

- Teensy: `live <Hz>` also shows the strongest line above 10 kHz and the strength of the tone at `<Hz>` (dB over the
  median), for hunting interference. Velocity code unchanged.
- ESP32: while quiet, loop() rests 2 ms per pass. Spinning flat out, its current draw showed up at the radar as a
  steady ~114 kHz tone (2322 fps; gone with the ESP32 held in reset).

## What changed in Teensy 0.2.6 and ESP32 0.2.9 (Nov 25, first bench test of 0.2.5/0.2.8)

- ESP32: while quiet, only a shot (and BRIGHT) lights the screen, for 1.5 s. The app's commands on connect (UNITS,
  SYNC, STRING) each redrew it, and each redraw read as a false shot at ~1136 or ~1697 fps (8 of them after
  connecting). Radio at 0 dBm while quiet (-12 dBm kept dropping the phone). Prints a line on each phone
  connect/disconnect.
- Teensy: the SD card is shared with the computer (MTP) only in drive mode; with the new Mac reading it while armed,
  saves failed ("SD card problem").
- Bench, armed, no shots: no phone 0 triggers in 2 min; phone connected 0 shots and 1 dropped trigger in 5 min,
  window left at 600-1800 by Range Book 2.44.2.

## What changed in Teensy 0.2.5 and ESP32 0.2.8

From the second-opinion review of the first live fire (Nov 11): the trigger listened mostly where the Bluetooth noise
is, the quick check started too late for a weak .22 echo, the analysis could lock onto steady lines, and the phone
didn't always accept the slow Bluetooth link.

- Teensy, **in-band trigger** (`set band=15`, saved; `band=0` goes back to the old whole-block trigger, which `trig`
  still sets). Each block, the last 4 ms get an FFT and every frequency inside the velocity window is compared with
  its own usual level and with its neighbours (`rdsp::Processor::bandScan`). A bullet is a new narrow line there;
  Bluetooth bursts (broadband, mostly low-pitched) and steady lines aren't. Simulated: bursts that set off the old
  trigger 50 of 50 times set off this one 0 of 50; a .22 echo of 5 counts at 1 m still triggers 19 of 20. On the 999
  Nov 11 recordings (window 600-1800) it fired at the original burst trigger in 9. `stat` shows how long the check takes per block;
  `live` shows its reading.
- Teensy, **quick check starts at the trigger** (`CONFIRM_FIRST` 2 -> 0): a weak echo is strongest right at the
  muzzle. Simulated .22 at 8 counts: passes 20 of 20 (was about 3 of 20).
- Teensy, **line rejection in the analysis**: a line already there before the trigger is scored against its own
  earlier level, so it can't pass for the bullet; a track that runs to the end of the capture without fading, or
  that starts more than 8 m out, is "interference" (result code 6, not sent to the phone). `set fade=0` turns
  that check off (not saved; back to 6 dB after a restart); captures set off by `sim` skip it (the bench tone
  doesn't fade). Nov 11 recordings: 611 read "ok" before (almost all Bluetooth and I2C lines), 40 now. The seven
  bench fake bullets (s00001-s00007) read the same to 0.1 fps; every simulated shot reads within 0.15 fps of before.
- Teensy default speed window is now 600-3500 fps (was 300-4500; only after `defaults` or on a fresh board).
- Teensy settings gained `band` (EEPROM layout version 2; older settings are kept and `band` added).
- ESP32 0.2.8: the slow-link request is repeated (every 5 s, then every 30 s) until the phone reports a link of
  90 ms or more; the slow numbers have more margin (90-120 ms, latency 6, 6 s timeout). While quiet the radio
  transmits at 0 dBm instead of +9 dBm (0.2.9: -12 dBm kept dropping the phone). Quiet mode now also starts when a compass calibration or a failed
  update ends after setup.
- Not tested on the hardware yet. Tune `band`, `qc` and `fade` on the first real echoes (the review's estimate
  of the real .22 echo is rough: about 3 counts at 1 m, maybe 1-10).

## What changed in Teensy 0.2.4

- `set qc=<dB>`: the quick check's threshold (default 11; `qc=0` turns it off and records every trigger, for
  collecting real shots while the check is tuned). Not saved: back to 11 after a restart.
- Each shot's printout adds the quick check's result (line strength, frequency, frames).

## What changed in Teensy 0.2.3 and ESP32 0.2.7

- Teensy: a quick check after every trigger (`rdsp::Processor::confirm`). About 18 ms after the trigger it looks for a
  narrow line inside the velocity window that wasn't there before the trigger and holds in at least 2 of 6 frames. Bursts
  (the ESP32's Bluetooth radio set off false shots twice a second on the first build) and steady interference lines
  are dropped in milliseconds instead of keeping BLIPR busy ~0.5 s with a full capture. `stat` shows "dropped
  triggers". A capture that only just passed and then didn't measure isn't sent to the phone. On the Nov 11
  recordings it rejected all 478 Bluetooth false triggers and passed every fake-bullet capture; the velocity code is
  unchanged (all 999 recordings replay to the same speeds). `replay` and `sim_test` print the quick check too.
- ESP32 0.2.7: while quiet, Bluetooth slows down: connected, the phone is asked for a ~120 ms interval with latency 15
  (the ESP32 wakes about every 2 s when idle; shots still go out within ~120 ms); not connected, it advertises every
  ~1 s. Fast again for setup and firmware updates. Bench, armed, no shots: 0 false shots and 0-29 dropped triggers a
  minute (before: about 2 false shots a second).

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
