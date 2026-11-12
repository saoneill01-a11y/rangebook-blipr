# Range Book BLIPR Bluetooth interface (v0.2, firmware 0.2.2)

Device name: **RB BLIPR** (earlier test firmware called itself RB Blip or RB Chrono). One custom service; all values are UTF-8 text (JSON or plain commands).

| Characteristic | UUID | Properties | Contents |
|---|---|---|---|
| Service | `239d0001-5192-4fb5-95ad-180af63137b3` | | |
| Shot | `239d0002-5192-4fb5-95ad-180af63137b3` | read, notify | one JSON object per shot |
| Status | `239d0003-5192-4fb5-95ad-180af63137b3` | read, notify (every 2 s) | battery, armed, link health, sensors fitted |
| Command | `239d0004-5192-4fb5-95ad-180af63137b3` | write, write without response | a text command |
| Config | `239d0005-5192-4fb5-95ad-180af63137b3` | read, notify (on change) | current settings |
| Sensors | `239d0006-5192-4fb5-95ad-180af63137b3` | read, notify (every 2 s, only if a sensor is fitted) | add-on sensor readings |

**Long messages:** a notification only carries as much as the phone's Bluetooth packet size allows (about 180 bytes on an
iPhone). Config can be longer than that. If a notification doesn't parse as JSON, read the characteristic instead: a read
always returns the whole value. Range Book does this automatically.

## Shot

Good read:
```json
{"n":12,"ok":1,"v":2712.4,"a":-310,"p":38,"q":18.2,"r":0.31,"d0":0.6,"d1":19.8,"b":"1a2b3c4d"}
```
No read (the radar saw something but couldn't measure it):
```json
{"n":13,"ok":0,"why":"weak","p":4,"q":11.0,"b":"1a2b3c4d"}
```
- `n` shot number since the chronograph was switched on; `b` the Teensy boot id the shot was measured under (it changes at
  every power-up, and `n` restarts). Shots are unique by (`b`, `n`). When `b` changes, the ESP32 drops its stored shots from
  the old boot, so `SYNC 0` after a new `b` only returns shots from the new one.
- `v` muzzle velocity in **fps** (always fps; the app converts)
- `a` deceleration (m/s²), `p` points in the track, `q` signal strength (dB), `r` scatter (m/s), `d0`/`d1` metres tracked
- `why`: `weak`, `short`, `noisy`, `out of range`, `no signal` (`interference`, Teensy 0.2.5 on, is never sent: it isn't a shot)
- `"test":1` marks a made-up shot from the `TEST` command (it does not count in the screen's string statistics)

## Status
```json
{"bat":87,"bv":3.98,"arm":1,"shots":12,"t":1,"rdy":1,"fs":600000,"nz":12.3,"ovr":0,"sd":1,"fw":"0.2.0","efw":"0.2.0","b":"1a2b3c4d","sens":"TPACL","cc":2}
```
`bat` percent (−1 = not wired), `bv` volts, `arm` listening for shots, `shots` last shot number, `t` Teensy is talking,
`rdy` ready for the next shot, `sd` SD card found, `ovr` missed sample blocks (should stay 0), `fw`/`efw` Teensy / ESP32
firmware, `sens` add-on sensors found (T = SHT45 temperature/humidity, P = pressure (DFRobot 10-DoF's BMP581, or a BMP390), A = ammo probe,
C = compass, L = level), `cc` compass calibration (0 never, 1 calibrating now, 2 calibrated).

## Config
```json
{"vmin":300,"vmax":4500,"lat":0.100,"behind":0.100,"cal":0,"f0":24150000000,"snr":12.0,"trig":9.0,"fs":600000,"save":1,"arm":1,"band":15.0,"units":"fps","batcal":1.0000,"bright":2,"anim":0,"theme":0,"inv":0,"hoff":0.0,"hrev":0,"hrot":0}
```
`bright` screen brightness 0–4, `anim` bullet animation after each shot (1 = on), `theme` screen look (0–3), `inv` screen inverted (1 = on), `hoff` compass offset (degrees), `hrev` compass turns backwards (only used without an
accelerometer), `hrot` IMU board rotation (0/90/180/270, counter-clockwise seen from above).

## Sensors
```json
{"t":21.50,"rh":40.1,"p":980.21,"am":24.12,"hd":271.3,"pi":0.3,"ro":-1.2,"cc":2}
```
Only the fitted sensors appear. `t` air °C (from the SHT45; from the BMP390 if there's no SHT45, which reads warm in
the case), `rh` % humidity, `p` station pressure hPa (not sea-level), `am` ammo probe °C, `hd` heading in degrees
(0 = north, magnetic plus your offset), `pi` nose-up pitch, `ro` right-side-down roll (degrees), `cc` as in Status.
After `COMPASS CAL STOP` it sends `{"compass":"calibrated"}` or `{"compass":"not enough turning"}` once.

## Firmware update (ESP32), characteristic `239d0007-…`
Read / write / notify. Every write starts with one letter:
- `B<size> <md5>`: start an update of `<size>` bytes whose MD5 is `<md5>` (32 hex digits). Answer `{"ota":"ready",...}`.
- `D` + 4-byte offset (little-endian) + up to 176 bytes of the app image: one piece. A piece whose offset isn't the
  next one expected is ignored and the value says `"resend"`; read the value's `got` and carry on from there.
- `E`: finish. BLIPR checks the size, the MD5 and the image, answers `{"ota":"done"}` and restarts 1.5 s later.
- `A`: abort.
Read the value at any time for `{"ota":"idle|ready|rx|resend|done|error","got":N,"size":N,"why":"..."}`. A dropped
connection or 20 s without a piece abandons the update; the old firmware keeps running. After the restart the new
firmware is kept once it has run for 15 s; a crash or reset before that rolls back to the previous one.

## Commands (write as text)

| Command | Effect |
|---|---|
| `ARM` / `DISARM` | listen for shots or not |
| `SET vmin=1500 vmax=3500` | velocity window (fps) |
| `SET lat=0.10 behind=0.10` | radar position (m): sideways from the bore, behind the muzzle |
| `SET cal=350` | calibration (ppm; +1000 reads 0.1 % faster) |
| `SET f0=24150000000` | radar frequency (Hz); default 24.150 GHz. Values outside a sensible range are refused |
| `SET save=0` | stop saving raw captures |
| `SET trig=9 snr=12` | trigger level and minimum signal (dB) |
| `SET band=15` | in-band trigger level (dB, Teensy 0.2.5 on); `band=0` uses the old whole-block trigger at `trig`. Config `"band"` |
| `GET` / `STAT` / `STATUS` | send config / status (and sensors) now |
| `TIME 1792480000` | set the clock (seconds since 1970, UTC); the app sends this at every connect |
| `SYNC 10` | re-send stored shots newer than #10 (after a reconnect; up to 200 kept) |
| `STRING` | start a new string on the screen (clears its average/SD/ES) |
| `UNITS fps` / `UNITS mps` | screen units |
| `BRIGHT 0`…`BRIGHT 4` | screen brightness |
| `BATV 3.97` | calibrate the battery gauge to a multimeter reading |
| `COMPASS CAL START` / `COMPASS CAL STOP` | compass calibration: start, turn it slowly through a full circle, stop. To recalibrate the vertical axis too, also tip it well over (nose up and down, onto each side) during the turn |
| `COMPASS MATCH 271` | the chronograph is pointing at 271°: set the offset so it agrees (e.g. from the phone's compass) |
| `COMPASS OFFSET 12.5` | set the offset directly |
| `COMPASS REVERSE 1` | heading turns the wrong way: only for a magnetometer with **no** accelerometer, mounted upside down. Ignored when the accelerometer is fitted, because it already knows which way is up |
| `COMPASS ROT 90` | the IMU board is turned 0, 90, 180 or 270 degrees **counter-clockwise, seen from above**, on its mount (90 = the board's X arrow points left instead of forward). After setting it, lift the front: pitch must read positive (nose up) |
| `THEME 0`…`THEME 3` | screen look: 0 Classic, 1 Big number, 2 Stats, 3 Retro (also takes the names). Remembered; the config JSON carries `"theme"` |
| `INVERT 1` / `INVERT 0` | dark text on a lit screen, or the usual light on black. Remembered; config `"inv"` |
| `FLIP 1` / `FLIP 0` | screen turned 180 degrees (default 1, the right way up in the case) or not. Remembered |
| `QUIET 1` / `QUIET 0` | after setup, screen dark and sensors paused while waiting for shots (default 1), or always on. Remembered; config `"quiet"` |
| `ANIM 1` / `ANIM 0` | bullet animation on the chronograph's screen after each good shot, or not (default off; remembered). The config JSON carries `"anim":1` or `0` |
| `LEVEL` / `LEVEL OFF` | show the bubble level on the chronograph's screen for 60 s / go back to the normal screen (needs the level sensor) |
| `DRIVE` / `DRIVE OFF` | USB drive mode: pause shot detection and refresh the SD card file list on the USB-connected computer / resume (status reports armed 0 while paused). It also turns on by itself when the Teensy is plugged into a computer, and off when unplugged. `ARM` and `sim` also end it. Needs the Teensy built with USB Type Serial + MTP Disk |
| `TEST` | send a made-up shot |
| `REC` | record 100 ms now (bench testing) |

Web Bluetooth (Chrome on Android/desktop, Bluefy on iPhone/iPad; the page must be https):
```js
const dev = await navigator.bluetooth.requestDevice({ filters: [{ services: ["239d0001-5192-4fb5-95ad-180af63137b3"] }] });
const svc = await (await dev.gatt.connect()).getPrimaryService("239d0001-5192-4fb5-95ad-180af63137b3");
const shot = await svc.getCharacteristic("239d0002-5192-4fb5-95ad-180af63137b3");
shot.addEventListener("characteristicvaluechanged", e => console.log(JSON.parse(new TextDecoder().decode(e.target.value))));
await shot.startNotifications();
const cmd = await svc.getCharacteristic("239d0004-5192-4fb5-95ad-180af63137b3");
await cmd.writeValue(new TextEncoder().encode("TEST"));
```
