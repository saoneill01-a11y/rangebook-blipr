# Ideas for after the first build works

## AMOLED display upgrade (decided: wait until BLIPR v1.1 is proven)
- Replace the ESP32-C3 SuperMini + 0.96" OLED with a **Waveshare ESP32-S3-AMOLED-1.91** (536x240 RM67162 AMOLED,
  ESP32-S3 16 MB flash / 8 MB PSRAM, BLE 5, two 0.1" headers, 57.5 x 24.5 mm). Avoid the 1.8" touch model (1 mm pads only).
- Board v1.1 stays: leave U4 empty and run 8 jumpers from its socket to the S3 board in the lid:
  5V, GND, 3V3 (feeds J4 sensors), GPIO20 (RX from Teensy via R23), GPIO21 (TX via R24), GPIO3 (battery sense),
  GPIO6/7 (I2C SDA/SCL to J4). J3 (OLED) goes unused.
- Firmware: port BliprBLE to the S3; BLE, Teensy link, sensors, battery and OTA carry over; redo the screens with
  Arduino_GFX (colour, higher resolution). Range Book's bundled firmware file switches to the S3 build.
- Case: new lid window and board mounts; base, pod and roof unchanged.
- Power: roughly 50-150 mA for the display vs about 20 mA now; dark backgrounds keep it low.
- Don't use the S3 board's own IMU, SD slot or battery charger (the IMU stays in the pod; power comes from the 18650 shield).

## Other
- Teensy firmware updates from Range Book (FlasherX via the ESP32 or from the SD card).
- Standalone BLIPR web app (self-hosted PWA), then app-store builds (Capacitor) if others want one.
- Chronograph settings editable before BLIPR connects (sent on the next connection).
- Battery shield standoffs in the base, once the shield is measured.
- rangebook.org somewhere on the case (maybe the bottom).
