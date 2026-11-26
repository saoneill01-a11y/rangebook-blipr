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

## Where things stand (Nov 11, 2026)

- **Bench tests, Nov 8:** Teensy flashed with 0.2.2 (0 overruns, SD ok on a 32 GB A1 card; an 8 GB card wasn't
  read). Fake-bullet test passed: 2800/1100/3300 fps read 2800.1/1100.0/3299.9. Saving a shot took 2.2-3.6 s:
  check later whether a shot during a save is missed. ESP32 flashed with 0.2.3; Bluefy connects to RB BLIPR.
  Teensy-ESP32 link test passed (fake shots reach the ESP32 and Bluefy). Radar not tested yet. VIN-VUSB trace
  cut and checked Nov 9: from now on the Teensy runs (and can be programmed) only with BLIPR switched on.
  Battery gauge checked Nov 9 (no modules in): cell 3.58 V, ESP32 GPIO3 hole 1.70 V (ratio 2.106, as designed);
  use this pair if the gauge needs calibrating.
- **First power-up with the radar, Nov 10:** works (DC mid-scale, no clipping), but a steady tone at 105.8 kHz
  (reads 2149 fps, 22-35 dB SNR) came from the battery holder's boost converter (real frequency ~494 kHz, aliased).
  It stays with the radar unplugged or covered and with the ESP32 out; a USB power bank instead gave its own tones
  (126/252 kHz). Likely path: the Teensy's unfiltered 5 V (its ADC reference). Fix ordered (arrives Wed Nov 11):
  22 uH inductor in the holder's red wire + 470 uF and 1 uF across J1 (`pictures/out/power_filter.png`); retest with
  `live` and `rec`. Backups: fs=500000 moves the holder tone to ~110 fps; the planned pre-trigger tone rejection.
  The ESP32 also adds broadband noise (rms ~20 -> 8 counts with it out): look at that next. Right now the holder is
  off J1 and a power bank is wired there instead. ESP32 0.2.4 (screen flipped 180) is flashed.
- **Nov 11, filter fitted** (22 uH in the holder's red wire, 470 uF + 1 uF on J1): the tone is gone with the radar
  unplugged, but with the radar on it still reaches 12-13 dB, picked up through the air from the holder's converter
  itself (gone with the holder held away; moving its wires or a grounded foil wall did nothing). **The Teensy is now
  set to `fs=500000`** (saved setting; `defaults` puts it back to 600000): the holder tone lands at ~99 fps, below
  vmin, and `rec` says "no signal". `sim_test 500000` reads every case as well as 600k (22LR +1.9 fps; weak echo
  4/5 vs 2/5; 0/20 false shots). Noise floor with the radar on and the ESP32 out: rms ~7.5 counts. Next: ESP32 back in.
- **Nov 11 evening, ESP32 back in** (recordings in `recordings/2026-11-11_bench_noise/`, `tools/tones.py` lists the lines):
  ESP32 0.2.5 runs I2C at 250 kHz (the 400/100 kHz bus showed as 2035 fps). A real 94.3 kHz line (1921 fps, 10-13 dB;
  same frequency at fs 400/500/600k) comes from the ESP32 itself (stays with display and sensors unplugged, weaker
  without the sensor cable). **First live fire (.22LR subsonic, ~1067 fps on Sean's Rangecraft)**, session
  `sessions/2026-11-11_1934`: BLIPR armed false-triggered ~2x a second with no shots (432 triggers; not the SD saves,
  not the Rangecraft): the trigger is broadband and fires on the ESP32's I2C bursts (screen redraw every 500 ms).
  Triggered captures read a steady ~1134 fps line (likely 2x the I2C byte rate) and, with the Rangecraft on, ~1695 fps
  (gone with it off: two 24 GHz radars side by side beat). Sean's real shot wasn't identified yet (fired ~19:35; the
  SD card has the captures). Teensy left disarmed with save=0, fs=500000. Plan: ESP32 quiet while armed (no screen
  redraws or sensor reads until a shot result arrives), Teensy trigger on in-band energy only, then the planned
  pre-trigger line rejection; bench-test armed with no shots (should stay silent) before live fire again.
- **Later Nov 11:** ESP32 0.2.6 (quiet mode) flashed: the ~1134 fps false readings are gone, but armed with no shots
  BLIPR still triggers ~2x a second on Bluetooth bursts (no phone: advertising; phone connected: also a steady
  115 kHz line, 2344 fps at 16 dB). Bursts (s00522-s00999): ~18 dB broadband, +26 dB below 15 kHz, but in-band
  bins reach 25-31 dB at 15-21 kHz; they last 1-2 blocks (2-4 ms). Range Book on connect pushes its own settings
  (window 300-4500, arm 0). The .22 shot (19:35) isn't in any capture (no 46-54.5 kHz track): likely missed while
  BLIPR was busy with a false trigger. The Teensy saves only up to s00999 (later captures weren't saved: check).
  Next: Teensy quick-reject (a trigger must show a sustained in-band line for several ms before a full capture,
  so bursts cost milliseconds, not ~0.6 s), Bluetooth slower while armed (longer connection interval), then the
  pre-trigger line rejection in `radar_dsp.cpp`.
- **Nov 11, 20:30: Teensy 0.2.3 + ESP32 0.2.7 flashed** (quick check after each trigger; slow Bluetooth while quiet).
  Bench, armed, ESP32 in its socket, no shots: no phone 0 shots / 29 dropped triggers in ~70 s; phone connected 0 shots /
  0 dropped in ~75 s. The analysis can still lock onto steady lines (94 kHz = 1921 fps, 115 kHz = 2344 fps with the
  phone) if a real shot passes the quick check: keep the window clear of them (.22: 600-1800) until the pre-trigger line
  rejection is in `analyze()`. Next: live fire to see the real echo.
- **Nov 11, 20:37-20:46, live fire outside (.22LR subsonic, ~1067 fps on the Rangecraft).** Phone connected: ~35
  dropped triggers a second (the phone link stayed fast outside, though inside it went quiet); phone disconnected: ~1 a
  second. Range Book resets the window to 300-4500 and can disarm on connect, and connecting/disconnecting the phone
  makes a short ~2333 fps line that passes the quick check (3 false shots). **The string fired 20:43-20:45 (phone off,
  quick check on) recorded no shots**: dropped triggers stayed at the background rate, so the .22 shots either didn't
  trigger or the quick check dropped them (dropped triggers aren't saved). Sean fired 4 shots about 5 s apart. Teensy 0.2.4
  (flashed) adds `set qc=0` (quick check off, RAM only, back to 11 dB after a restart) and prints each shot's quick-check
  line. With qc=0 and the ESP32 in, Bluetooth triggers (~1/s) keep BLIPR busy, so: **next session, start here:**
  0. Done Nov 25 (new Mac; needed Rosetta for arduino-cli's ctags): **Teensy 0.2.6 + ESP32 0.2.9 flashed**. Bench,
     armed, no shots: no phone 0 triggers / 2 min; phone connected 0 shots, 1 dropped trigger / 5 min (Range Book left
     the window alone). The in-band check takes ~640 of 2048 us per block. Teensy left armed, 600-1800, save=1.
     ESP32 USB prints didn't show on the Mac (connect lines expected): check later. New Mac ports: Teensy
     `/dev/cu.usbmodem208996901` / upload `usb:1130000`, ESP32 `/dev/cu.usbmodem101`.
  1. Pull the SD card into `recordings/` (s00999 was not a fault: the logs show s01000-s01015 saved later).
  1b. Agreed with Sean: run the ESP32 out of its socket on ~30 cm female-female jumpers, powered by BLIPR (5V, GND,
     GPIO20 = RX from the Teensy, GPIO21 = TX to the Teensy; display/sensors not needed for the test), armed, no shots,
     phone connected and not. Bursts gone = they travel through the air (shield or move the ESP32 in the case);
     still there = they come through the shared 5 V/ground (filter the ESP32's 5 V like the holder's).
  2. A .22 string with the ESP32 **out** (no Bluetooth noise), `set qc=0`, window **950-1200** (`set vmin=950 vmax=1200`),
     to record real echoes. Ammo: CCI Standard Velocity, expected 1000-1100 fps. (Sean, Nov 12: never needs more than
     600-3500 fps overall; tomorrow's testing only 950-1200. The old ~1134 fps I2C line falls inside this window, but
     quiet mode removed it; if 1134 shows up, the ESP32 isn't quiet.)
  3. Tune the quick check (and the broadband trigger) on those real echoes; check whether the shot even triggers.
  4. ESP32 link: plug the ESP32's USB into the Mac to see "Bluetooth link: every X ms"; ask for the fast link only
     during OTA; find out why the slow link didn't hold outside.
  5. Range Book overriding the window/arm on connect; the pre-trigger line rejection in `analyze()`.
  Teensy was left disarmed (arm=0 saved; the ESP32 arms it after setup), window 600-1800, save=1, fs=500000.
- **Nov 12: second opinion (Fable session) and fixes, built and tested on the computer only.** Review notes:
  `sessions/2026-11-11_review_fixes/` holds the before/after `sim_test` and `replay` tables. Teensy 0.2.5: in-band
  trigger (`set band=15`, saved; `band=0` = old trigger), quick check from the trigger frame, line rejection in
  `analyze()` (pre-trigger lines scored against their own level; a track that runs to the capture's end without
  fading, or starts past 8 m, is code 6 "interference", never sent; `set fade=0` off; skipped for `sim`). ESP32 0.2.8:
  the slow-link request is repeated until the phone grants 90 ms or more (90-120 ms, latency 6), 0 dBm while quiet (-12 dBm dropped the phone, Nov 25),
  quiet mode also after a compass calibration. Replay of the 999 Nov 11 recordings: false "ok" reads 611 -> 40, the
  bench fake bullets unchanged; sim: all cases as before, bursts trigger 0/50 (old trigger 50/50). The review's bench
  idea for conducted vs radiated: also count triggers with a USB power bank in the ESP32's own USB-C (the ESP32's
  diode then keeps BLIPR's 5 V out of the radio's current pulses); the jumper test alone is ambiguous if bursts stay.
  Range Book side (stop pushing window/arm on connect) was handed to the Range Book session.
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
  can edit the doc through the docs connector (load the docs skill first); keep the Markdown copy in step with it.
  `docs/BLIPR Build Guide.docx` is a Word version (circuit board build), rebuilt by `docs/make_build_doc.py`.
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

Teensy commands: `stat`, `get`, `set key=value` (vmin vmax fps, lat behind m, cal ppm, snr trig band dB, save 0/1,
arm 0/1, fs Hz, f0 Hz; qc and fade dB, not saved), `arm`/`disarm`, `live` (twice-a-second readout of the radar signal: noise, DC, clipping,
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

- Mac (Apple silicon, macOS 26). Repo at `~/Claude/Developer/rangebook-blipr`.
- arduino-cli 1.5.1 (Homebrew), teensy:avr 1.62.0, esp32:esp32 3.3.12. DFRobot_Multi_DOF_IMU and DFRobot_RTU
  are git clones in `~/Documents/Arduino/libraries/` (no unsafe-install setting needed).
- Build into `~/Library/Caches/blipr-build/` (`--build-path`) so build files stay out of the repo.
- Nov 1, 2026: both sketches compile (ESP32 777373 bytes); `sim_test` passes, 0/20 false shots.
- Serial ports: Teensy `/dev/cu.usbmodem208996901` (upload port `usb:130000`), ESP32 `/dev/cu.usbmodem1101`
  (on the port Sean used; a charge-only USB-C cable showed nothing at all). The ESP32 prints its startup line
  only once, before a monitor can reopen the port after an upload. Python tools: venv at `~/Library/Caches/blipr-venv`
  (Python 3.12; trimesh, manifold3d, cadquery-ocp, pyserial). A Bluetooth scan from Python crashed (no permission).
