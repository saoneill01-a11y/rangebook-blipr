# Ideas for after the first build works

## AMOLED display upgrade (decided: wait until BLIPR is proven at the range)
- Replace the ESP32-C3 SuperMini + 0.96" OLED with a **Waveshare ESP32-S3-AMOLED-1.91** (536x240 RM67162 AMOLED,
  ESP32-S3 16 MB flash / 8 MB PSRAM, BLE 5, two 0.1" headers, 57.5 x 24.5 mm). Avoid the 1.8" touch model (1 mm pads only).
- The main board (v1.1 or v1.2) stays: leave U4 empty and run 8 jumpers from its socket to the S3 board in the lid:
  5V, GND, 3V3 (feeds J4 sensors), GPIO20 (RX from Teensy via R23), GPIO21 (TX via R24), GPIO3 (battery sense),
  GPIO6/7 (I2C SDA/SCL to J4). J3 (OLED) goes unused.
- Firmware: port BliprBLE to the S3; BLE, Teensy link, sensors, battery and OTA carry over; redo the screens with
  Arduino_GFX (colour, higher resolution). Range Book's bundled firmware file switches to the S3 build.
- Case: new lid window and board mounts; base, pod and roof unchanged.
- Power: roughly 50-150 mA for the display vs about 20 mA now; dark backgrounds keep it low.
- Don't use the S3 board's own IMU, SD slot or battery charger (the IMU stays in the pod; power comes from the 18650 shield).

## Pre-soldered boards for other builders (decided: only after BLIPR is proven; Oct 24, 2026)
- Still DIY: no finished units. Builders buy their own radar, Teensy, ESP32, screen, battery holder and sensors,
  and print the case. A board with only passives and sockets isn't a radio device, so no FCC certification question.
- What comes soldered: all resistors, capacitors, D1 and U3; the DIP-8 sockets with the MCP6022s in them; the
  Teensy (2 x 24) and ESP32 (2 x 8) sockets; headers J1-J5. The builder plugs in the Teensy and ESP32, solders the
  ESP32's pins, wires radar / OLED / battery holder / sensors.
- Ways to do it: (1) PCBWay shared project, so people order straight from PCBWay (small credit per order; check
  whether shared projects can include assembly); (2) order a batch of 20-50 assembled and sell them (e.g. Tindie):
  assembly falls to a few dollars a board, but stock and shipping are on Sean; (3) just publish the files in the
  public repo.
- Before any of it: build and range-test BLIPR, and fix anything on the main board first (now v1.2).
- If volume ever goes well past that, a surface-mount version of the board would be cheaper to machine-assemble.
- Cost of a second BLIPR for Sean (Oct 24): about $80-90 (radar ~$45, Teensy $35.50, filament and screws); he has
  spare boards, ESP32, OLED, battery holder, 18650, op-amps, regulator and passives. Sensor kit about $35 more.

## Teensy updates over Bluetooth (decided: later; Nov 27, 2026)
- For builders who need a Teensy update without a USB cable and Teensy Loader (today only the ESP32 updates by Bluetooth).
- Path: Range Book sends the Teensy file to the ESP32 over Bluetooth (like the ESP32 OTA), the ESP32 passes it to the
  Teensy over the existing serial link (GPIO20/21), and the Teensy writes it with FlasherX (Joe Pasquariello's
  library): new program into spare flash, check it, then copy over the old one. ~145 KB, under a minute.
- Risk: power lost during the final copy leaves BLIPR not starting; USB + Teensy Loader always recovers a Teensy
  (its bootloader chip is separate), so USB stays the fallback.
- Work: Teensy (FlasherX receive + check), ESP32 (relay), Range Book chrono (a "Teensy" entry in firmware.json and
  the upload), bench tests including a pulled-power test mid-update.

## Other
- Teensy firmware updates from Range Book (FlasherX via the ESP32 or from the SD card).
- Standalone BLIPR web app (self-hosted PWA), then app-store builds (Capacitor) if others want one.
- Chronograph settings editable before BLIPR connects (sent on the next connection).
- rangebook.org somewhere on the case (maybe the bottom).
