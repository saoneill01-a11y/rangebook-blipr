# Firmware: setup and bench tests

Today's goal is to load both programs, check that the Teensy measures a fake bullet correctly, and see shots arrive on your phone over Bluetooth. You don't need the radar, amplifier or battery for any of it. Everything is in **RB\_Blip\_firmware\_v0.2.2.zip**. Version 0.2.2 is needed for circuit board v1.1: the Teensy now talks to the ESP32 on pins 34 and 35 (Serial8), not 0 and 1. It also fixes the compass calibration and sets the radar frequency default to 24.150 GHz.

## What you need

- Teensy 4.1 and a micro-USB **data** cable (some cables only charge)
- ESP32-C3 SuperMini and a USB-C data cable
- A microSD card (FAT32 or exFAT) pushed into the Teensy's slot
- 4 jumper wires, plus two 1 kΩ resistors if you have them
- The free **nRF Connect** app on your phone (iPhone or Android)
- The OLED, if it has arrived (optional today)

## 1. Install the software (once)

1. Install **Arduino IDE 2**.
2. File › Preferences › *Additional boards manager URLs*: add these two lines:
   - `https://www.pjrc.com/teensy/package_teensy_index.json`
   - `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
3. Boards Manager (left side bar): install **Teensy** (by Paul Stoffregen) and **esp32** (by Espressif, version 3.3.x).
4. Library Manager: install **Adafruit SSD1306**. When it asks to install Adafruit GFX and Adafruit BusIO too, choose *Install all*. Then install Adafruit SHT4x, Adafruit BMP3XX, Adafruit LSM6DS, Adafruit LIS3MDL, OneWire and DallasTemperature the same way. The firmware needs them to compile even without the sensor kit; it skips any sensor that isn't plugged in.

## 2. Load the Teensy

1. Unzip the firmware and open `BlipTeensy/BlipTeensy.ino`.
2. Tools menu: Board **Teensy 4.1**, USB Type **Serial + MTP Disk (Experimental)**, CPU Speed **600 MHz**, and the Teensy's Port. (The MTP part lets the SD card show up as a drive, see section 9. Plain **Serial** also works, just without the drive.)
3. Click Upload (→). The first time, a small Teensy Loader window may ask you to press the button on the Teensy.
4. Open the Serial Monitor (magnifying glass, top right). Press the Teensy's button or replug it if the screen is blank. You should see:

```
Range Book Blip, Teensy firmware 0.2.2
Sample rate 600000 Hz (asked for 600000). SD card found.
```

5. Type `stat` and press Enter. **overruns** should be 0.

If the IDE won't build it, use the ready-made file instead. Open the Teensy Loader app, choose File › Open HEX File › `prebuilt/BlipTeensy.hex`, then press the Teensy's button.

## 3. Fake bullet test (Teensy only)

The Teensy can play a fake bullet's Doppler tone on pin 2 and measure it like a real shot. This tests the whole measuring chain.

1. Unplug the Teensy. Connect a jumper from **pin 2** to **A0 (pin 14)** and another from **pin 2** to **A1 (pin 15)**, through a 1 kΩ resistor each if you have them.
2. Plug it back in and type `sim 2800`. Within a second you should see something like:

```
Shot #1: ok  2801.3 fps (853.84 m/s)
  points 40, span 30.1 ms, SNR 25.0 dB, ...
  saved as s00001.bin
```

3. Try `sim 1100` and `sim 3300`. Each should come back within a few fps of the number you typed; the test tone itself is a little coarse.
4. Type `live` for a twice-a-second readout of the inputs, and `live` again to stop it.
5. **Remove the pin 2 jumpers before the amplifier is ever connected.**

With nothing on A0/A1 the inputs pick up stray noise, so touching the board can occasionally cause a "no signal" capture. That's harmless; `disarm` stops it.

## 4. Load the ESP32-C3

1. Open `BlipBLE/BlipBLE.ino` in a **second** IDE window, so each board keeps its own Serial Monitor.
2. Tools menu: Board **Nologo ESP32C3 Super Mini** (or ESP32C3 Dev Module), **USB CDC On Boot: Enabled**, and its Port.
3. Click Upload. If it can't connect: hold the **BOOT** button, tap **RESET**, let go of BOOT, and upload again. Tap RESET once it's done.
4. Serial Monitor at **115200**: you should see *RB Blip ESP32-C3 firmware 0.2.2 ready*.

## 5. Connect the two boards

Leave both on their USB cables and add three wires. **Don't** connect 5V or VIN between them today.

| Teensy | ESP32-C3 |
| --- | --- |
| pin 35 (TX8), through 1 kΩ | GPIO20 |
| pin 34 (RX8), through 1 kΩ | GPIO21 |
| GND | GND |

In the ESP32's Serial Monitor type `TEST`. The Teensy makes up a shot, and the ESP32 prints it as a line like `{"n":2,"ok":1,"v":2703.4,...,"test":1}`. Then type `sim 2800` in the **Teensy's** monitor: the measured fake shot should appear in the ESP32's monitor too.

## 6. See it on your phone

1. In nRF Connect, scan, find **RB Blip** and tap Connect.
2. Open the service whose number starts **239D0001** (it shows as an unknown service).
3. Turn on notifications for **239D0002** (shots) and **239D0003** (status): the triple-arrow icon on Android, *Subscribe* on iPhone.
4. On **239D0004**, tap the write (up-arrow) button, pick **Text / UTF-8**, type `TEST` and send it. A shot appears under 239D0002.
5. The status line updates every 2 seconds. It shows `"bat":-1` until the battery sense is wired.
6. Run `sim 2800` on the Teensy again and watch the shot arrive on your phone.

## 7. OLED (if it has arrived)

OLED VCC → ESP32 **3V3**, GND → GND, SDA → **GPIO6**, SCL → **GPIO7**. Press RESET on the ESP32. It shows *READY*, and after a `TEST` shot a big speed with the string's count, average, SD and ES underneath.

## 8. Connect from Range Book

Range Book 2.43 talks to the chronograph directly. Open Range Book through its https:// address in Chrome on the Android phone (or in the Bluefy app on the iPhone), go to **Tools › Chronograph** and tap **Connect chronograph**, then pick **RB Blip**. Tap **Test shot**: a 2,700 fps shot appears in big numbers and in the string. The same button is on each range trip (under Chronograph) and on each ladder group.

When it connects, Range Book sets the chronograph's clock, its screen units, the velocity window and the radar position. Settings (the pill at the bottom right) has the battery, calibration against another chronograph, screen brightness and, with the sensor kit, compass calibration.

## 9. Copy recordings off the SD card (USB drive mode)

You don't need to open the case or take the card out.

1. Switch the chronograph on. The Teensy runs from the battery, and the USB cable only carries data.
2. Plug a USB cable from the Teensy's port into the computer.
3. Find the drive:
   - **Windows:** in File Explorer, under This PC, open **Teensy**, then **RB Blip SD**.
   - **Mac:** install the free **OpenMTP** app and open it.
4. Nothing to type. About a second after it's plugged into a computer, the chronograph pauses shot detection by itself and its screen shows PAUSED.
5. Copy the `shots` folder and `log.csv`. Each recording is about 320 KB, and MTP is slower than a card reader, so a big folder can take a minute or more.
6. Unplug the cable. About 3 seconds later it's listening for shots again. A USB charger or power bank doesn't count as a computer, so it won't pause anything.

The bench tests above still work while plugged in, because `sim` and `arm` switch the pause off. PJRC still calls MTP experimental. If the drive doesn't appear, unplug and plug it in again, or fall back to a card reader.

## Send me

- The Teensy's two start-up lines and one `sim 2800` result.
- Any red error text from building or uploading, copied and pasted as text.
- Later, from the range: the `/shots` folder from the SD card (the `.bin` files and `log.csv`).

## Limits of this version

- **Calibration.** Each radar module's exact frequency varies a little from unit to unit, which can shift readings by up to about 0.4% (around 10 fps at 2,700 fps). One session beside a known chronograph, such as someone's Garmin, will set the `cal` value.
- **Tuned on simulated shots.** The shot detection was tested only against simulated shots: it read them within about 1 fps and rejected muzzle blast. Real captures from the SD card will be used to tune it.
- **Not in Range Book yet.** The Range Book connection comes next, once this part works.
