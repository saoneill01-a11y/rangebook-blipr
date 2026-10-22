# Sensor kit (optional)

The sensor kit adds air temperature, humidity, pressure, a compass and a level for about $47 to $61 in parts. Everything plugs into the ESP32 with STEMMA QT cables, and the firmware finds each sensor by itself, so you can add them one at a time. The chronograph works the same without them. There's no ammo-temperature probe: your ammo sits at air temperature, so the air reading covers it.

## What each sensor gives you

| Sensor | Measures | Used for in Range Book |
| --- | --- | --- |
| SHT45 | Air temperature (±0.1 °C) and humidity | Trip and ladder temperature, density altitude |
| BMP390 | Air pressure at the bench | Density altitude, and the profile's altitude via **Use this air in the profile** |
| LIS3MDL compass | Which way the radar points | Direction of fire for Coriolis |
| LSM6DSOX accelerometer | Tilt (level) | Keeps the compass right when the chronograph isn't level; shows if it's tipped |

The compass doesn't need to be precise: at 1,000 yd a 15° heading error changes the Coriolis correction by less than 0.7 in. Wind gauges and GPS aren't worth adding: the wind that matters is downrange, and your phone already knows the latitude.

## Parts

All are on the parts spreadsheet under **Sensor kit**.

| Part | Qty | Approx. price |
| --- | --- | --- |
| [Adafruit SHT45](https://www.adafruit.com/product/5665) (5665) | 1 | $12.50 |
| [Adafruit BMP390](https://www.adafruit.com/product/4816) (4816); DigiKey or Mouser if Adafruit is out | 1 | $10.95 |
| [Adafruit LSM6DSOX + LIS3MDL](https://www.adafruit.com/product/4517) (4517) | 1 | $19.95 |
| [STEMMA QT to male pins, 150 mm](https://www.adafruit.com/product/4209) (4209) | 1 | $0.95 |
| [STEMMA QT cable, 200 mm](https://www.adafruit.com/product/4401) (4401): not needed with case v0.4 | 0 | $1.25 |
| [STEMMA QT cable, 100 mm](https://www.adafruit.com/product/4210) (4210) | 2 | $0.95 |
| 1x4 female header, 2 × M3x8 screws and 2 M3 heat-set inserts for the pod, 16 × M2.5x6 mm brass screws (4 per sensor board, 4 for the roof) |  | from your kits |

Prices from Adafruit on Oct 20, 2026, before shipping.

## Printed parts

Re-run the case script (or use the new files in the case package):

- **lid\_sensors**: the OLED lid with the screen in the back corner nearest you (the gun side), plus the pod's cable slot and two 6 mm risers underneath for its heat-set inserts, in the front corner on the far side from the gun. Print it top-face down instead of lid\_oled; the risers point up. Case v0.7 moved the screen and the pod, so reprint any older lid\_sensors.
- **sensor\_pod** (66 × 50 × 20 mm): a louvred box that screws to the lid and holds all three boards side by side, long sides front-to-back: the SHT45 at the end away from the gun, the BMP390 in the middle and the IMU at the end toward the gun, with a small arrow in front of it pointing to the front. Each board sits on four 5 mm posts and is held by four M2.5 brass screws that thread straight into them, so air flows underneath. Print upright, as it sits.
- **sensor\_pod\_roof**: the shade roof; its lip drops inside the pod. Print flat side down, in white or light grey.
- **base** (v0.4): the IMU pegs are gone from the floor; nothing else changed. A base v0.3 you've already printed is fine: just leave its floor pegs empty. imu\_mount is no longer used.

&#91;image: Sensor pod v0.4: SHT45, BMP390 and IMU side by side\]

&#91;image: The lid seen from your seat: screen in the back corner on the gun side, pod in the front corner on the far side\]

&#91;image: From your seat at the bench: nothing between you and the screen\]

The posts suit Adafruit's 1.0 × 0.7 in boards, whose holes sit 0.1 in from each corner. Check yours when they arrive and tell me if the holes don't line up. The screws cut their own thread in the posts: turn each one slowly until the board is snug, then stop. Use brass or nylon screws, not steel: steel next to the IMU would bend the magnetic field the compass measures.

## Wiring

1. On the main board, add a 1x4 female header wired, in this order: **GND, 3V3, GPIO6 (SDA), GPIO7 (SCL)**. These are the same four wires the OLED uses; tap them anywhere on those runs.
2. Plug the 150 mm QT-to-pins cable into it: black to GND, red to 3V3, blue to SDA, yellow to SCL. Its QT end goes up through the lid's cable slot into the SHT45 in the pod.
3. Inside the pod, 100 mm cables join the SHT45 to the BMP390 and the BMP390 to the IMU.

## Mounting

1. **IMU**: in the pod, on the posts at the gun-side end (farthest from the battery), long side front-to-back, sensor side up. Not on the case floor: there the 18650's steel can, the battery shield's converter and the 5 V wiring upset the compass.
2. **Pod**: press an M3 heat-set insert into each of the pod's two screw holes in the lid, from the top (the risers underneath give them 8 mm of plastic). Thread the 150 mm cable up through the slot, then screw the pod down with two M3×8 screws. Screw the SHT45 onto the posts away from the gun, the BMP390 onto the middle and the IMU onto the gun-side posts, sensor side up, with the brass screws. Plug in the two 100 mm cables, then screw the roof on with 4 more brass screws into the pod's corner columns.

## Firmware and first checks

1. Load firmware v0.2.2 on the ESP32 (it already has the sensor code; see the Firmware tab for the libraries).
2. Open the ESP32's Serial Monitor and type `STATUS`. The status line's `sens` should list the letters for what's fitted: **T** SHT45, **P** BMP390, **C** compass, **L** level. A sensor plugged in later is found within 15 s.
3. In Range Book, **Tools › BLIPR Chronograph** shows a **Conditions** card. Check the level: lift the front and **Level** should say *nose up*; tip it right and it should say *tipped right*. If not, change Sensor board turned (Settings › Compass) until it does; it covers however the board went onto its posts (the angle counts counter-clockwise, seen from above). This needs ESP32 firmware 0.2.2.
4. **Calibrate the compass** once: Settings › Compass › **Calibrate compass**, turn the chronograph slowly through a full circle on the bench (for the best heading when it's tilted, also tip it well over on the way: nose up, nose down and onto each side), then **Finish**. Do it away from the truck, steel benches and the rifle.
5. **Match my phone**: hold the phone flat, pointing the same way as the radar, and tap it; the chronograph copies the phone's heading. With this IMU there's no Turns backwards switch: its level sensor already knows which way is up.

## Using it

**Levelling it on the bench.** For the first minute after you switch it on, the chronograph's screen shows a bubble level. Shim the case until the bubble sits in the middle circle and the screen says **LEVEL** (within 0.5° front-to-back and side to side). Hold it there for 3 seconds and the screen goes back to normal. A shot also brings the normal screen back. To show the level again, tap **Show the level on its screen** in Settings › Level, or send `LEVEL`. The top of the screen is the front (downrange). The bubble floats to the high side, like a real bubble level, and the text tells you which way to move: *Lower nose* or *Lift nose*, and *Lift left* or *Lift right*. This needs ESP32 firmware 0.2.2 and the IMU fitted.

&#91;image: The bubble level on the chronograph's screen: off level (left) and level (right)\]

- Keep the chronograph in the shade if you can; even with the roof, sun on the case reads warm. Give the air temperature 10 minutes after you set it out.
- Range trips and ladders fill an empty temperature from it, and a trip's air (humidity, pressure, density altitude) too.
- **Use this air in the profile** (Tools › BLIPR Chronograph) sets a Shooting profile's temperature and altitude; **Use … for Coriolis** sets its direction of fire.
