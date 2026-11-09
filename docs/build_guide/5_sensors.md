# Sensor kit (optional)

The sensor kit adds air temperature, humidity, pressure, a compass and a level for about $40 to $60 in parts, on two boards: an Adafruit SHT45 and a DFRobot Gravity 10-DoF IMU (compass, level and pressure on one board; it replaced the BMP390 and the Adafruit IMU in October 2026). They plug into the ESP32 in one chain of cables, and the firmware finds each by itself, so you can add them one at a time. The chronograph works the same without them. There's no ammo-temperature probe: your ammo sits at air temperature, so the air reading covers it.

## What each sensor gives you

| Sensor | Measures | Used for in Range Book |
| --- | --- | --- |
| SHT45 | Air temperature (±0.1 °C) and humidity | Trip and ladder temperature, density altitude |
| BMP581 (on the DFRobot board) | Air pressure at the bench | Density altitude, and the profile's altitude via **Use this air in the profile** |
| BMM350 compass (on the DFRobot board) | Which way the radar points | Direction of fire for Coriolis |
| BMI323 accelerometer (on the DFRobot board) | Tilt (level) | Keeps the compass right when the chronograph isn't level; shows if it's tipped |

The compass doesn't need to be precise: at 1,000 yd a 15° heading error changes the Coriolis correction by less than 0.7 in. Wind gauges and GPS aren't worth adding: the wind that matters is downrange, and your phone already knows the latitude.

## Parts

All are on the parts spreadsheet under **Sensor kit**.

| Part | Qty | Approx. price |
| --- | --- | --- |
| [Adafruit SHT45](https://www.adafruit.com/product/5665) (5665) | 1 | $12.50 |
| [DFRobot Gravity 10-DoF IMU](https://www.dfrobot.com/product-3126.html) (SEN0696; also on Amazon) | 1 | $19.90 |
| [STEMMA QT to male pins, 150 mm](https://www.adafruit.com/product/4209) (4209) | 2 | $0.95 |
| [STEMMA QT cable, 100 mm](https://www.adafruit.com/product/4210) (4210): only if the DFRobot's Gravity cable has bare wire ends | 1 | $0.95 |
| 1x4 female header, 2 × M3x8 screws and 2 M3 heat-set inserts for the pod, 8 × M2.5x6 mm brass screws (4 for the SHT45, 4 for the roof), 2 × M3x6 mm brass screws for the DFRobot board |  | from your kits |

Prices from Adafruit on Oct 20, 2026 and DFRobot on Oct 23, 2026, before shipping.

## Printed parts

Re-run the case script (or use the new files in the case package):

- **lid\_sensors**: the OLED lid with the screen in the back corner nearest you (the gun side), plus the pod's cable slot and two 7 mm risers underneath for its heat-set inserts (holes 7.5 mm deep), in the front corner on the far side from the gun. Print it top-face down instead of lid\_oled; the risers point up. Case v0.8 moved the pod's two screws and its cable slot (now at the pod's back corner, nearer the main board), so reprint any older lid\_sensors.
- **sensor\_pod** (66 × 50 × 20 mm): a louvred box that screws to the lid and holds both boards, long sides front-to-back, so air flows underneath. The SHT45 sits at the end away from the gun on four 5 mm posts, held by four M2.5 brass screws that thread straight into them. The DFRobot board sits at the end toward the gun, parts up, its two holes at the front on 5 mm posts (two M3 brass screws) and its plug end toward you on two plain posts, with 14 mm behind the plug for the cable to bend. The cable slot is in the back corner on the far side; the two pod-to-lid screws sit between the boards. Print upright, as it sits.
- **sensor\_pod\_roof**: the shade roof; its lip drops inside the pod. Print flat side down, in white or light grey.
- **base**: nothing in it changes for the sensor kit.

&#91;image: Sensor pod v0.8: SHT45 posts, DFRobot 10-DoF posts, cable slot at the back\]

&#91;image: Pod from above with the boards and cables in place (front at the top, you at the bottom)\]

&#91;image: The lid seen from your seat: screen in the back corner on the gun side, pod in the front corner on the far side\]

&#91;image: From your seat at the bench: nothing between you and the screen\]

The SHT45's posts suit Adafruit's 1.0 × 0.7 in boards, whose holes sit 0.1 in from each corner. The DFRobot board's posts suit its two 3 mm holes, 20 mm apart, 3.5 mm in from the front edge. Check yours when they arrive and tell me if the holes don't line up. The screws cut their own thread in the posts: turn each one slowly until the board is snug, then stop. Use brass or nylon screws, not steel: steel next to the DFRobot board would bend the magnetic field its compass measures.

## Wiring

1. On the main board, add a 1x4 female header wired, in this order: **GND, 3V3, GPIO6 (SDA), GPIO7 (SCL)**. These are the same four wires the OLED uses; tap them anywhere on those runs.
2. Plug the 150 mm QT-to-pins cable into it: black to GND, red to 3V3, blue to SDA, yellow to SCL. Its QT end goes up through the lid's cable slot (at the back of the pod), along the side of the SHT45 and into its front socket.
3. Inside the pod, a second QT-to-pins cable goes from the SHT45's back socket to the DFRobot board's own Gravity cable (plugged into the board). The Gravity cable's wires end in female sockets (checked when the board arrived on Nov 4), so the pins plug straight in. Don't fit a pin header on the DFRobot board instead: its pin row is on a long edge, and straight pins plus sockets stand taller than the 20 mm pod. Match by the DFRobot's pin labels: red to **+**, black to **−**, yellow (SCL) to **C/R**, blue (SDA) to **D/T**. Set the DFRobot's I2C/UART switch to I2C and leave A0 and A1 on 0.

## Mounting

1. **DFRobot 10-DoF board**: in the pod at the gun-side end (farthest from the battery), parts up, its two holes at the front and its plug toward you. The firmware expects it that way round. Not on the case floor: there the 18650's steel can, the battery holder's converter and the 5 V wiring upset the compass.
2. **Pod**: press an M3 heat-set insert into each of the pod's two screw holes in the lid, from the top (the risers underneath give them 9.4 mm of plastic, enough for 7 mm long inserts). Thread the 150 mm cable up through the slot, then screw the pod down with two M3×8 screws; they sit between the two boards, so do this before the boards go in. Screw the SHT45 onto the posts away from the gun with four brass M2.5 screws, and the DFRobot board onto its two front posts with two brass M3×6 screws (the back posts just hold it up). Plug in the cables, then screw the roof on with 4 more brass screws into the pod's corner columns.

## Firmware and first checks

1. Load firmware v0.2.3 on the ESP32: it has the DFRobot board's code (the Firmware tab lists the libraries). Once 0.2.2 or later is on it, Range Book can install 0.2.3 over Bluetooth from Settings › Firmware.
2. Open the ESP32's Serial Monitor and type `STATUS`. The status line's `sens` should list the letters for what's fitted: **T** SHT45, **P** pressure (the DFRobot's BMP581), **C** compass, **L** level. A sensor plugged in later is found within 15 s.
3. In Range Book, **Tools › BLIPR Chronograph** shows a **Conditions** card. Check the level: lift the front and **Level** should say *nose up*; tip it right and it should say *tipped right*. If not, change Sensor board turned (Settings › Compass) until it does; it covers however the board went onto its posts (the angle counts counter-clockwise, seen from above). This needs ESP32 firmware 0.2.2 or later (0.2.3 for the DFRobot board).
4. **Calibrate the compass** once: Settings › Compass › **Calibrate compass**, turn the chronograph slowly through a full circle on the bench (for the best heading when it's tilted, also tip it well over on the way: nose up, nose down and onto each side), then **Finish**. Do it away from the truck, steel benches and the rifle.
5. **Match my phone**: hold the phone flat, pointing the same way as the radar, and tap it; the chronograph copies the phone's heading. Then turn the chronograph slowly clockwise: the heading should go up. If it goes down, turn on Turns backwards (Settings › Compass) and match your phone again.

## Using it

**Levelling it on the bench.** For the first minute after you switch it on, the chronograph's screen shows a bubble level. Shim the case until the bubble sits in the middle circle and the screen says **LEVEL** (within 0.5° front-to-back and side to side). Hold it there for 3 seconds and the screen goes back to normal. A shot also brings the normal screen back. To show the level again, tap **Show the level on its screen** in Settings › Level, or send `LEVEL`. The top of the screen is the front (downrange). The bubble floats to the high side, like a real bubble level, and the text tells you which way to move: *Lower nose* or *Lift nose*, and *Lift left* or *Lift right*. This needs ESP32 firmware 0.2.2 or later and the compass/level board fitted.

&#91;image: The bubble level on the chronograph's screen: off level (left) and level (right)\]

- Keep the chronograph in the shade if you can; even with the roof, sun on the case reads warm. Give the air temperature 10 minutes after you set it out.
- Range trips and ladders fill an empty temperature from it, and a trip's air (humidity, pressure, density altitude) too.
- **Use this air in the profile** (Tools › BLIPR Chronograph) sets a Shooting profile's temperature and altitude; **Use … for Coriolis** sets its direction of fire.
