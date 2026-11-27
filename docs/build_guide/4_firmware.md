# Firmware: setup and bench tests

Today's goal is to load both programs, check that the Teensy measures a fake bullet correctly, and see shots arrive on your phone over Bluetooth. You don't need the radar, amplifier or battery for any of it. Do it before you cut the Teensy's VIN–VUSB trace (build guide Step 1): these tests run the Teensy from USB alone, and once the trace is cut it only runs when BLIPR is switched on. On a v1.1 board, do it before the ESP32's hand-wired 5 V filter too (build guide Step 4): after that, the computer only saw the ESP32 when it was out of BLIPR's socket. The current firmware is **Teensy 0.2.9** and **ESP32 0.2.20**, in the project's `firmware/` folder, with ready-made files in `firmware/prebuilt/`. Circuit boards v1.1 and v1.2 need 0.2.2 or later: the Teensy talks to the ESP32 on pins 34 and 35 (Serial8), not 0 and 1.

## What you need

- Teensy 4.1 and a micro-USB **data** cable (some cables only charge)
- ESP32-C3 SuperMini and a USB-C data cable
- A microSD card, 8–32 GB, name brand, marked A1 or Class 10 (FAT32 or exFAT), pushed into the Teensy's slot with its gold contacts toward the board
- 4 jumper wires, plus two 1 kΩ resistors if you have them
- The free **nRF Connect** app on your phone (iPhone or Android)
- The OLED, if it has arrived (optional today)

## 1. Install the software (once)

1. Install **Arduino IDE 2**.
2. File › Preferences › *Additional boards manager URLs*: add these two lines:
   - `https://www.pjrc.com/teensy/package_teensy_index.json`
   - `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
3. Boards Manager (left side bar): install **Teensy** (by Paul Stoffregen) and **esp32** (by Espressif, version 3.3.x).
4. Library Manager: install **Adafruit SSD1306**. When it asks to install Adafruit GFX and Adafruit BusIO too, choose *Install all*. Then install Adafruit SHT4x, Adafruit BMP3XX, Adafruit LSM6DS, Adafruit LIS3MDL, OneWire and DallasTemperature the same way, and DFRobot\_Multi\_DOF\_IMU and DFRobot\_RTU for the DFRobot 10-DoF sensor board (if Library Manager doesn't list them, download each as a ZIP from github.com/DFRobot and add it with Sketch › Include Library › Add .ZIP Library). The firmware needs them to compile even without the sensor kit; it skips any sensor that isn't plugged in.

## 2. Load the Teensy

1. Unzip the firmware and open `BliprTeensy/BliprTeensy.ino`.
2. Tools menu: Board **Teensy 4.1**, USB Type **Serial + MTP Disk (Experimental)**, CPU Speed **600 MHz**, and the Teensy's Port. (The MTP part lets the SD card show up as a drive, see section 9. Plain **Serial** also works, just without the drive.)
3. Click Upload (→). The first time, a small Teensy Loader window may ask you to press the button on the Teensy.
4. Open the Serial Monitor (magnifying glass, top right). Press the Teensy's button or replug it if the screen is blank. You should see:

```
Range Book BLIPR, Teensy firmware 0.2.9
Sample rate 600000 Hz (asked for 600000). SD card found. Type 'help' for commands.
```

5. Type `stat` and press Enter. **overruns** should be 0. If the status says SD missing, unplug, re-seat the card and plug in again (it only looks at start-up). Still missing: try another card. On the first build an 8 GB card from another device wasn't read; a 32 GB A1 card worked.

6) Type `set fs=500000`. It's saved; type reboot so it takes effect, and the start-up line then says 500000 Hz. The battery holder's converter whistles at about 494 kHz: at 600 kHz sampling that lands near 2,150 fps, at 500 kHz near 100 fps, out of the way (build guide Step 6). `defaults` puts 600000 back.

If the IDE won't build it, use the ready-made file instead. Open the Teensy Loader app, choose File › Open HEX File › `prebuilt/BliprTeensy.hex`, then press the Teensy's button.

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

1. Open `BliprBLE/BliprBLE.ino` in a **second** IDE window, so each board keeps its own Serial Monitor.
2. Tools menu: Board **Nologo ESP32C3 Super Mini** (or ESP32C3 Dev Module), **USB CDC On Boot: Enabled**, and its Port.
3. Click Upload. If it can't connect: hold the **BOOT** button, tap **RESET**, let go of BOOT, and upload again. Tap RESET once it's done. If the computer doesn't see the ESP32 at all while its red LED is on, the USB-C cable is charge-only: swap it (on a Mac, also look for an "Allow accessory to connect?" pop-up).
4. Serial Monitor at **115200**: you should see *BLIPR ESP32-C3 firmware 0.2.20 ready*.

Load the ESP32 over USB now. From then on Range Book can update it over Bluetooth (section 10). On a v1.1 board with the hand-wired filter, the computer saw the ESP32 only out of BLIPR's socket.

## 5. Connect the two boards

Leave both on their USB cables and add three wires. **Don't** connect 5V or VIN between them today.

| Teensy | ESP32-C3 |
| --- | --- |
| pin 35 (TX8), through 1 kΩ | GPIO20 |
| pin 34 (RX8), through 1 kΩ | GPIO21 |
| GND | GND |

In the ESP32's Serial Monitor type `TEST`. The Teensy makes up a shot, and the ESP32 prints it as a line like `{"n":2,"ok":1,"v":2703.4,...,"test":1}`. Then type `sim 2800` in the **Teensy's** monitor: the measured fake shot should appear in the ESP32's monitor too.

## 6. See it on your phone

1. In nRF Connect, scan, find **RB BLIPR** and tap Connect.
2. Open the service whose number starts **239D0001** (it shows as an unknown service).
3. Turn on notifications for **239D0002** (shots) and **239D0003** (status): the triple-arrow icon on Android, *Subscribe* on iPhone.
4. On **239D0004**, tap the write (up-arrow) button, pick **Text / UTF-8**, type `TEST` and send it. A shot appears under 239D0002.
5. The status line updates every 2 seconds. It shows `"bat":-1` until the battery sense is wired.
6. Run `sim 2800` on the Teensy again and watch the shot arrive on your phone.

## 7. OLED (if it has arrived)

In BLIPR the OLED gets four wires soldered into J3 (build guide Step 4): VCC → ESP32 **3V3**, GND → GND, SDA → **GPIO6**, SCL → **GPIO7**. If yours has pins, female jumper wires plug onto them, here and in BLIPR (they clear the lid). Press RESET on the ESP32: it plays its start-up, shows *READY*, then goes dark (it lights only for a shot). After a `TEST` shot it shows a big speed with the string's count, average, SD and ES underneath for 3 seconds.

## 8. Connect from Range Book

Range Book 2.44 or later talks to the chronograph directly. Open Range Book: on an iPhone or iPad, the Range Book app from the App Store (Range Book: Shooting Log); on Android, Chrome, through Range Book's https:// address (rangebook.org shows how to install Range Book), go to **Tools › BLIPR Chronograph** and tap **Connect chronograph**, then pick **RB BLIPR**. Tap **Test shot**: a 2,700 fps shot appears in big numbers and in the string. The same button is on each range trip (under Chronograph) and on each ladder group.

When it connects, Range Book sets the chronograph's clock and screen units. Its settings (the pill at the bottom right) show BLIPR's own velocity window and radar position, and change them when you type a value (a button sets the window from the load). They also have the battery, calibration against another chronograph, screen brightness, **Show each shot for** (default 3 s), **Re-level and update the heading**, **Disable the level** and, with the sensor kit, compass calibration.

## 9. Copy recordings off the SD card (USB drive mode)

You don't need to open the case or take the card out.

1. Switch the chronograph on. The Teensy runs from the battery, and the USB cable only carries data.
2. Plug a USB cable from the Teensy's port into the computer.
3. Find the drive:
   - **Windows:** in File Explorer, under This PC, open **Teensy**, then **BLIPR SD**.
   - **Mac:** install the free **OpenMTP** app and open it.
4. Nothing to type. About a second after it's plugged into a computer, the chronograph pauses shot detection by itself and its screen shows PAUSED.
5. Copy the `shots` folder and `log.csv`. Each recording is about 320 KB, and MTP is slower than a card reader, so a big folder can take a minute or more.
6. Unplug the cable. About 3 seconds later it's listening for shots again. A USB charger or power bank doesn't count as a computer, so it won't pause anything.

The bench tests above still work while plugged in, because `sim` and `arm` switch the pause off. PJRC still calls MTP experimental. If the drive doesn't appear, unplug and plug it in again, or fall back to a card reader.

## 10. Later updates to the Bluetooth board

Once firmware 0.2.2 or later is on the ESP32 (with the USB-C cable, step 4), Range Book can update it over Bluetooth. In the chronograph settings, scroll to **Firmware** and tap **Update the Bluetooth board**. It takes about 30 seconds with ESP32 0.2.12 or later (older versions could stop partway, so install 0.2.12 or later over USB first): keep the phone close with its screen on, and don't shoot until it's done. BLIPR's screen shows UPDATING and a progress bar, then restarts and reconnects by itself.

If the connection drops partway, nothing changes: BLIPR stays on its old firmware, and you try again. It only switches once the whole file has arrived and checks out, and if the new firmware doesn't start properly it goes back to the old one. The radar board (Teensy) is still updated with the USB cable.

This is the normal way to update the ESP32 once it's in BLIPR (on the first v1.1 build, the computer didn't see it over USB while it was in its socket).

## 11. Commands worth knowing

Type these in the Teensy's Serial Monitor (BLIPR switched on, USB plugged in). Settings changed with `set` are saved.

| Command | What it does |
| --- | --- |
| `stat` | Status: armed, shots, overruns (should be 0), SD card |
| `get` | Every setting: window, position, calibration, sample rate, trigger levels |
| `set vmin=950 vmax=1200` | The velocity window, in fps. Keep it a little wider than your load, the low end well below your slowest shot (BLIPR only hears speeds inside it) |
| `set fs=500000` | Sample rate (500000 recommended; then reboot; `defaults` puts 600000 back) |
| `set save=1` | Save every shot's raw recording to the SD card (for tuning) |
| `live` / `live 114000` | Twice a second: noise, DC level, clipping and the strongest line; with a number, also the level at that frequency. `live` again stops it |
| `rec` | Record 100 ms now and say what's in it: the way to find an interference tone |
| `arm` / `disarm` | Start or stop listening for shots |
| `sim 2800` | A fake bullet on pin 2 (bench test only, amplifier disconnected) |

## Asking for help

- The Teensy's two start-up lines, `get`, and one `sim 2800` result.
- Any red error text from building or uploading, copied and pasted as text.
- From the range: the `/shots` folder from the SD card (the `.bin` files and `log.csv`), with what you shot and where BLIPR sat.

## Limits of this version

- **Tested on .22 LR and .38 Special so far.** .22 LR (Nov 26, 2026, Teensy 0.2.8): 9 of 10 shots read, average 1029 fps, about 1% from an Athlon chronograph with the same rifle and ammo on another day. .38 Special 158 gr handloads from a lever-action rifle (Nov 27), with an Athlon on the same shots: 19 of 20 read; the two strings averaged 3.1 fps below and 3.4 fps above the Athlon. Supersonic rifle ammo hasn't been tested yet.
- **The window is also the trigger.** BLIPR only listens for speeds inside `vmin`–`vmax`, so a shot below the window isn't heard at all (a 733 fps .38 with the window starting at 800 never triggered). Set the low end well below your slowest shot.
- **A pause after each shot.** From Teensy 0.2.9, BLIPR waits 1.5 s after a shot before it listens again (`set hold=<ms>` changes it until a restart). On 0.2.8 the ESP32 drawing the result on the screen could cause a false read near 1,135 fps about half a second after a shot.
- **Calibration.** Each radar module's exact frequency varies a little from unit to unit, which can shift readings by up to about 0.4% (around 10 fps at 2,700 fps). A session beside a known chronograph sets the `cal` value.
- **Interference.** The radar hears switching converters, the ESP32 and a lit screen. The two 5 V filters, `fs=500000`, the dark screen while listening and the firmware's rejection of steady lines deal with what the first build met; `live` and `rec` show anything new (build guide Troubleshooting).
- **Saving.** Saving a shot to the card takes 0.3–3.6 s; whether a shot that arrives during a save is missed is still to check.
