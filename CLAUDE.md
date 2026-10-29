# Range Book BLIPR: notes for Claude Code

BLIPR (Ballistic Launch Inspection Portable Radar) is Sean's DIY 24 GHz radar chronograph for Range Book.
Sean is a target shooter, not a programmer: explain things in plain words, keep answers short, and ask
before anything that costs money or can't be undone. The private repo is saoneill01-a11y/rangebook-blipr;
Sean will make it public once BLIPR is proven.

## What's where

| Folder | What |
|---|---|
| `firmware/BliprTeensy/` | Teensy 4.1: samples the radar (I/Q, 600 kS/s), finds shots, measures velocity (`radar_dsp.cpp`), saves raw recordings to SD |
| `firmware/BliprBLE/` | ESP32-C3 SuperMini: Bluetooth to Range Book, OLED, battery gauge, sensor kit (SHT45 + DFRobot 10-DoF), OTA updates |
| `firmware/test/` | `sim_test.cpp` (simulated shots), `replay.cpp` (runs real recordings through `radar_dsp.cpp`) |
| `firmware/PROTOCOL.md` | Bluetooth and serial interface; `firmware/README.md` has the commands and the change history |
| `tools/` | `blipr_log.py` (session logger), `pull_shots.py` (copy recordings off the SD), `make_test_recordings.py` |
| `case/` | 3D-printed case: `blipr_case.py` builds every part (`out/`); the base starts from Sean's CAD in `user_edits/` |
| `pcb/` | Circuit board v1.1 (ordered from PCBWay: don't change the copper without asking) |
| `pictures/` | Wiring pictures (`pics.py`) |
| `docs/` | This setup guide, ideas for later |

The Range Book web app (the `chrono` branch of saoneill01-a11y/rangebook) is a separate repo. It ships the
ESP32 firmware file in `public/blipr/` for Bluetooth updates; changing that is not part of this repo.

## Build and flash

Board packages (arduino-cli): add `https://www.pjrc.com/teensy/package_teensy_index.json` and
`https://espressif.github.io/arduino-esp32/package_esp32_index.json`, then install `teensy:avr` and
`esp32:esp32` version 3.3.x.

Libraries (Library Manager names, one `arduino-cli lib install "<name>"` each: a name it can't find stops the
rest of a combined install): "Adafruit SSD1306" (+ GFX, BusIO), "Adafruit SHT4x Library", "Adafruit BMP3XX Library",
"Adafruit LSM6DS", "Adafruit LIS3MDL", "Adafruit Unified Sensor", "OneWire", "DallasTemperature", plus
DFRobot_Multi_DOF_IMU and DFRobot_RTU from github.com/DFRobot (`arduino-cli lib install --git-url ...` with
`library.enable_unsafe_install` on, or `--zip-path`).

- Teensy: FQBN `teensy:avr:teensy41:usb=serialmtp` (USB type **Serial + MTP Disk (Experimental)**, defines
  `USB_MTPDISK_SERIAL`). Plain Serial (`usb=serial`) works too, without drive mode.
- ESP32: FQBN `esp32:esp32:nologo_esp32c3_super_mini` with **USB CDC On Boot: Enabled** (the default for this board, so no option is needed).
- Build: `arduino-cli compile --fqbn <fqbn> firmware/BliprTeensy` (or `firmware/BliprBLE`);
  upload with `arduino-cli upload -p <port> --fqbn <fqbn> <sketch>`.
- First flash: the Teensy may need its program button pressed; the ESP32-C3 may need BOOT held while RESET
  is tapped. Tell Sean when to press which.
- Bump `FW_VERSION` in the sketch you change (Teensy and ESP32 have separate versions), and add a
  "What changed" entry to `firmware/README.md`. Update `firmware/prebuilt/` when a version is final.

## Talking to the boards

Both run at 115200 baud. Teensy USB vendor ID 0x16C0, ESP32-C3 0x303A (`python tools/blipr_log.py --list`).
Only one program can have a port open: stop the logger before uploading or opening a monitor.

Teensy commands: `stat`, `get`, `set key=value` (vmin vmax fps, lat behind m, cal ppm, snr trig dB, save 0/1,
arm 0/1, fs Hz, f0 Hz), `arm`/`disarm`, `live` (twice-a-second readout of the radar signal: noise, DC, clipping,
strongest frequency), `rec` (record 100 ms now), `sim [fps]` (fake bullet on pin 2, amplifier disconnected),
`test`, `time`, `defaults`, `drive [off]`, `reboot`. **Plugging the Teensy into a computer turns on USB drive
mode, which pauses shots**: send `arm` (the logger does) before shooting.

Each shot prints `Shot #N: ok  2701.7 fps (823.48 m/s)` and a line with points, span, SNR, scatter, accel,
tracked distance and processing time, then `saved as s00012.bin` when saving is on.

## A shooting session

1. `python tools/blipr_log.py --note "<ammo, rifle, where BLIPR sits>" --cmd "set save=1"` (add `--live` to
   watch the noise floor). It writes `sessions/<date_time>/teensy.log` and `shots.csv`. To send a command
   while it runs, append a line to that session's `commands.txt`.
2. Sean shoots; if he reads out another chronograph's numbers, record them next to the shot numbers in
   `sessions/<date_time>/reference.csv` (shot,fps).
3. Recordings: `python tools/pull_shots.py <SD card or copied shots folder>` into `recordings/<date>/`.

Safety: Sean is shooting. Never send commands or ask him to handle the hardware while he's on the rifle;
anything that needs him at the bench waits for a break between strings.

## Changing the velocity code (`firmware/BliprTeensy/radar_dsp.cpp`)

Before flashing a change:
1. Build and run `firmware/test/sim_test.cpp` (all simulated cases still read; no false shots on noise).
2. Build `firmware/test/replay` and run it on **every** recording in `recordings/` (and `recordings-kept/`),
   before and after the change. Good shots must stay put (or move toward the reference chronograph);
   report shots gained or lost. Keep the before/after tables in the session folder.
3. Only then flash, and tell Sean what changed in one or two sentences.
`replay --peaks out.csv` gives every frame's peak (time, Doppler frequency, m/s, SNR, used) for plotting.

Known weakness (pre-build review, Oct 29, 2026, https://claude.ai/artifact/XTZ8YEr7pFUwjrV5oKxFYJ): a steady
tone inside the velocity window (converter, clock or Bluetooth interference), even one smaller than the noise,
forms a long flat track that beats the real bullet, so every shot reads the tone's speed. Planned fix, to tune on
the first real recordings: ignore lines already present in the pre-trigger frames, and accept only tracks that
slow down. The same review estimates the bullet echo may be marginal for this radar; check real echo strength in
the first recordings before tuning anything else.

## Git

Commit as Sean (his normal git identity). Keep `recordings/` and `sessions/` out of git (they're large);
copy recordings worth keeping into `recordings-kept/` with a short README line. Push to `main` after each
piece of work so nothing lives only on the laptop.

## This computer

(Claude Code: fill this in during the first session: OS, serial port names for the Teensy and ESP32,
anything that needed a workaround.)
