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
ESP32 firmware file in `public/blipr/` for Bluetooth updates; changing that is not part of this repo
(see "Range Book" below for its rules).

## Working with Sean

- Plain words, short answers. He asks good practical questions; answer the question, then stop.
- **Show a mockup before any physical change** (case, PCB, wiring): a picture he can check first, then build
  after he says yes. 2D views of the case are drawn from above with the front edge at the top (he caught a
  mirrored mockup once; both axes are flipped to match how he holds it).
- Ask before anything that costs money (orders, PCBWay) or can't be undone (force-push, deleting files,
  wiping the SD card or settings).
- Never change the PCB copper without asking; v1.1 is already made.

## Range Book (only if Sean asks for app work)

- BLIPR code in the app lives only on the `chrono` branch (version 2.44.x). `dev` and `main` are 2.43.x.
- Merges go one way: `dev` into `chrono` after dev changes. **Never** merge chrono into dev or main, and
  never release dev to main unless Sean says so. Sean calls chrono "private": keep BLIPR features off dev/main.
- Test the server only against a copy of the data folder (`DATA_DIR=<copy>`), never his real data.
- An ESP32 firmware release for Bluetooth updates: copy the built `BliprBLE-<ver>.bin` into
  `public/blipr/` and update the `esp` entry in `public/blipr/firmware.json` (version, file, size in bytes, md5; the app image `BliprBLE.ino.bin`, not the merged file). The app
  checks the md5, and the ESP32 rolls back if the new firmware doesn't confirm within 15 s.
  Currently shipped: 0.2.3 (757440 bytes, md5 28fcaa5cb1bc6a1e4dba07b00c923024).

## Where things stand (Nov 1, 2026)

- **Bench tests, Nov 8:** Teensy flashed with 0.2.2 (0 overruns, SD ok on a 32 GB A1 card; an 8 GB card wasn't
  read). Fake-bullet test passed: 2800/1100/3300 fps read 2800.1/1100.0/3299.9. Saving a shot took 2.2-3.6 s:
  check later whether a shot during a save is missed. ESP32 flashed with 0.2.3; Bluefy connects to RB BLIPR.
  Teensy-ESP32 link test and the radar itself not tested yet. VIN-VUSB trace not cut yet.
- PCB v1.1 bare boards ordered from PCBWay. Sean is also getting a PCBWay quote for assembled boards
  (files and form answers in `pcb/out/pcba/`, made by `pcb/pcba_files.py`; PCBWay wants the assembly
  drawing as PDF, not PNG). J1-J5 are left empty on those boards.
- J4 (sensor cable): the parts list says a male 1x4 header, but the STEMMA QT-to-pins cable also ends in male pins
  so fit a female 1x4 header or solder the wires (noted in `pcb/README.txt`).
- Sensors: SHT45 plus the DFRobot Gravity 10-DoF (BMI323 + BMM350 + BMP581), which replaced the Adafruit
  IMU and BMP390. It arrived Nov 4: its own Gravity cable ends in female jumper sockets, so a STEMMA QT-to-male-pins
  cable from the SHT45's second port plugs into them (as the build guide says). A pin header on the 10-DoF won't fit:
  its pin row is on a long edge and straight pins plus sockets stand taller than the 20 mm pod.
- Case v0.11 (`case/`; Teensy USB hole 24-32 mm up, Nov 8; left pad corners cleaned up, Nov 9; pod in the 10-DoF layout, `POD_BMP390 = False`). Tripod insert hole 7.15 x 9 mm at
  the estimated balance point; M3 insert holes 7.5 mm deep; power button slot 14 x 10 mm.
- Build guide: the shared doc https://claude.ai/artifact/Cg7tRsb5ndJPPZLUZa3bSN is the main copy (tabs:
  build guide, firmware, sensors, circuit board, wiring). `docs/build_guide/` is a Markdown copy. Claude Code
  probably can't edit the doc: change the Markdown copy and tell Sean which section of the doc to update.
- Open questions: whether Range Book should let him change chronograph settings while BLIPR isn't
  connected (never decided). Ideas for later, including pre-soldered boards for other builders, are in
  `docs/ideas.md`.

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

- Mac (Apple silicon, macOS 26). Repo at `~/Library/CloudStorage/OneDrive-CSI/Claude Stuff/Claude Code/rangebook-blipr`
  (inside OneDrive: if git acts oddly, set the folder to "Always keep on this device").
- arduino-cli 1.5.1 (Homebrew), teensy:avr 1.62.0, esp32:esp32 3.3.12. DFRobot_Multi_DOF_IMU and DFRobot_RTU
  are git clones in `~/Documents/Arduino/libraries/` (no unsafe-install setting needed).
- Build into `~/Library/Caches/blipr-build/` (`--build-path`) so build files stay out of OneDrive.
- Nov 1, 2026: both sketches compile (ESP32 777373 bytes); `sim_test` passes, 0/20 false shots.
- Serial ports: Teensy `/dev/cu.usbmodem208996901` (upload port `usb:130000`), ESP32 `/dev/cu.usbmodem1101`
  (on the port Sean used; a charge-only USB-C cable showed nothing at all). The ESP32 prints its startup line
  only once, before a monitor can reopen the port after an upload. Python tools: venv at `~/Library/Caches/blipr-venv`
  (Python 3.12; trimesh, manifold3d, cadquery-ocp, pyserial). A Bluetooth scan from Python crashed (no permission).
