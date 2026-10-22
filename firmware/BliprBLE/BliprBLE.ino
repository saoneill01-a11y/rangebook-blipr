// Range Book BLIPR (Ballistic Launch Inspection Portable Radar) - ESP32-C3 firmware (Bluetooth, OLED, battery gauge)
// Talks to the Teensy over a serial link and to your phone over Bluetooth Low Energy.
//
// Board settings (Arduino IDE, esp32 by Espressif 3.x):
//   Tools > Board > esp32 > "Nologo ESP32C3 Super Mini" (or "ESP32C3 Dev Module")
//   USB CDC On Boot: Enabled
// Libraries (Library Manager): "Adafruit SSD1306" (it asks to add Adafruit GFX and BusIO: say yes)
//
// Wiring: GPIO20 (RX) <- 1 kOhm <- Teensy pin 35 (TX8)   GPIO21 (TX) -> 1 kOhm -> Teensy pin 34 (RX8)
//         GPIO6 -> OLED SDA, GPIO7 -> OLED SCL, 3V3 -> OLED VCC, GND -> OLED GND
//         GPIO3 <- BATT_SENSE (cell + -> 10k at the cell tab -> switch -> 100k -> BATT_SENSE -> 100k -> GND)
//
// Copyright (c) 2026 Sean O'Neill. AGPL-3.0-or-later (same as Range Book).

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Fonts/FreeSansBold9pt7b.h>     // smooth outline fonts for the big text (the small text stays in the
#include <Fonts/FreeSansBold12pt7b.h>    // built-in 5x7 font, which is already crisp at its own size)
#include <Fonts/FreeSansBold18pt7b.h>
#include <Fonts/FreeSansBold24pt7b.h>
#include <Preferences.h>
#include <math.h>
#include <Update.h>
#include "esp_ota_ops.h"
#include "sensors.h"

#define FW_VERSION "0.2.2"
#define DEVICE_NAME "RB BLIPR"

// Bluetooth service and characteristics (Range Book looks for these)
#define SVC_UUID    "239d0001-5192-4fb5-95ad-180af63137b3"
#define SHOT_UUID   "239d0002-5192-4fb5-95ad-180af63137b3"  // notify/read: one JSON per shot
#define STATUS_UUID "239d0003-5192-4fb5-95ad-180af63137b3"  // notify/read: battery, armed, ...
#define CMD_UUID    "239d0004-5192-4fb5-95ad-180af63137b3"  // write: text commands
#define CONFIG_UUID "239d0005-5192-4fb5-95ad-180af63137b3"  // notify/read: settings JSON
#define ENV_UUID    "239d0006-5192-4fb5-95ad-180af63137b3"  // notify/read: add-on sensor readings
#define OTA_UUID    "239d0007-5192-4fb5-95ad-180af63137b3"  // write/read/notify: firmware update for this board (see PROTOCOL.md)

static const int PIN_LINK_RX = 20, PIN_LINK_TX = 21;
static const int PIN_SDA = 6, PIN_SCL = 7;
static const int PIN_BAT = 3;
static const int PIN_LED = 8;  // on-board blue LED, lit when LOW
static const int PIN_ONEWIRE = 10;  // ammo temperature probe (optional)
static const uint32_t LINK_BAUD = 460800;

HardwareSerial& Link = Serial1;
Adafruit_SSD1306 oled(128, 64, &Wire, -1);
Preferences prefs;
static bool oledOk = false;

static BLEServer* server = nullptr;
static BLECharacteristic *chShot, *chStatus, *chCmd, *chConfig, *chEnv;
static volatile bool connected = false;
static volatile bool needAdvertise = false;

// ---------------- shots ----------------
struct Shot {
  uint32_t n;
  float fps, accel, snr, rms, d0, d1;
  int16_t pts, code;
  bool test;
  char why[14];
  char b[12];     // the Teensy's boot id when this shot was taken
};
static const int MAX_SHOTS = 200;
static Shot shots[MAX_SHOTS];
static int shotCount = 0;              // shots stored (ring)
static uint32_t lastShotN = 0;
static bool haveLast = false;
static Shot last;
// string statistics for the screen (reset with the STRING command)
static int sN = 0;
static double sSum = 0, sSum2 = 0;
static float sMin = 1e9, sMax = -1e9;

static void clearShots() {
  memset(shots, 0, sizeof(shots));
  shotCount = 0;
  lastShotN = 0;
}

// ---------------- Teensy status ----------------
static uint32_t teensySeenMs = 0;
static int tArmed = 1, tSd = 0, tReady = 1;
static uint32_t tShots = 0, tOvr = 0, tFs = 0;
static float tNoise = 0;
static char tFw[12] = "?";
static char tBoot[12] = "";
static char configJson[340] = "{}";

// ---------------- battery ----------------
static float batV = 0, batCal = 1.0f;
static int batPct = -1;
static bool unitsMps = false;
static int bright = 3;   // screen: 0 = off, 1 = dim .. 4 = brightest
// Screen look (THEME): 0 Classic, 1 Big number, 2 Stats, 3 Retro (the old blocky font). INVERT 1: dark on lit.
enum { THEME_CLASSIC, THEME_BIG, THEME_STATS, THEME_RETRO, THEME_COUNT };
static int screenTheme = THEME_CLASSIC;
static bool screenInv = false;
static bool shotAnim = false;   // ANIM 1: after each good shot a bullet flies across and writes the velocity
static uint32_t animStart = 0;  // millis() when the shot animation started (0 = not running)

static int pctFromVolts(float v) {
  // resting Li-ion curve, close enough for a gauge
  static const float V[] = {3.30f, 3.45f, 3.60f, 3.70f, 3.75f, 3.80f, 3.87f, 3.95f, 4.05f, 4.15f, 4.20f};
  static const int P[] = {0, 5, 15, 30, 40, 50, 60, 70, 80, 92, 100};
  if (v <= V[0]) return 0;
  for (int i = 1; i < 11; i++)
    if (v <= V[i]) return P[i - 1] + (int)((v - V[i - 1]) / (V[i] - V[i - 1]) * (P[i] - P[i - 1]) + 0.5f);
  return 100;
}

static float readBatteryRaw() {
  uint32_t mv = 0;
  for (int i = 0; i < 16; i++) mv += analogReadMilliVolts(PIN_BAT);
  return mv / 16.0f * 2.1f / 1000.0f;  // (10k + 100k + 100k) / 100k: the divider plus the 10k at the cell tab
}

static void updateBattery() {
  float v = readBatteryRaw() * batCal;
  if (v < 1.0f) { batV = 0; batPct = -1; return; }  // not wired
  batV = (batV == 0) ? v : 0.8f * batV + 0.2f * v;
  batPct = pctFromVolts(batV);
}

// ---------------- link to the Teensy ----------------
static uint8_t xorSum(const char* s, size_t n) { uint8_t c = 0; for (size_t i = 0; i < n; i++) c ^= (uint8_t)s[i]; return c; }
static void toTeensy(const char* cmd) {
  char buf[200];
  snprintf(buf, sizeof(buf), "!%s*%02X\n", cmd, xorSum(cmd, strlen(cmd)));
  Link.write((const uint8_t*)buf, strlen(buf));
}

// ---------------- Bluetooth ----------------
// ---------------- firmware update over Bluetooth ----------------
// Range Book sends a new app image for this board in small numbered pieces. It goes into the spare app slot;
// the board only switches to it if every byte arrived and the MD5 matches. After the restart the new firmware
// has to run for 15 s before it's kept: if it crashes or resets before then, the board goes back to the old one.
static BLECharacteristic* chOta = nullptr;
static volatile bool otaActive = false;
static volatile uint32_t otaSize = 0, otaGot = 0, otaLastMs = 0;
static uint32_t otaRebootAt = 0;
static void otaSay(const char* state, const char* why = nullptr, bool notify = true) {
  char m[128];
  if (why) snprintf(m, sizeof(m), "{\"ota\":\"%s\",\"got\":%lu,\"size\":%lu,\"why\":\"%s\"}", state, (unsigned long)otaGot, (unsigned long)otaSize, why);
  else snprintf(m, sizeof(m), "{\"ota\":\"%s\",\"got\":%lu,\"size\":%lu}", state, (unsigned long)otaGot, (unsigned long)otaSize);
  if (!chOta) return;
  chOta->setValue((uint8_t*)m, strlen(m));
  if (notify && connected) chOta->notify();
}
static void otaStop(const char* why) {
  if (otaActive) Update.abort();
  otaActive = false;
  otaSay("error", why);
}
class OtaCB : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* c) override {
    uint8_t* d = c->getData();
    size_t n = c->getLength();
    if (!d || !n) return;
    otaLastMs = millis();
    if (d[0] == 'B') {                          // B<size> <md5 hex>: start
      char a[64] = {0};
      memcpy(a, d + 1, n - 1 < sizeof(a) - 1 ? n - 1 : sizeof(a) - 1);
      unsigned long sz = 0;
      char md5[40] = {0};
      if (sscanf(a, "%lu %39s", &sz, md5) != 2 || strlen(md5) != 32 || sz < 1024) { otaStop("bad start message"); return; }
      if (otaActive) Update.abort();
      otaActive = false;
      otaGot = 0;
      otaSize = sz;
      if (!Update.begin(sz, U_FLASH)) { otaStop(Update.errorString()); return; }
      Update.setMD5(md5);
      otaActive = true;
      otaSay("ready");
    } else if (d[0] == 'D') {                   // D + 4-byte offset (little-endian) + data
      if (!otaActive || n < 6) { otaSay("error", "not started", false); return; }
      uint32_t off = d[1] | (d[2] << 8) | (d[3] << 16) | ((uint32_t)d[4] << 24);
      if (off != otaGot) { otaSay("resend", nullptr, false); return; }   // a piece went missing: Range Book goes back
      size_t len = n - 5;
      if (otaGot + len > otaSize) { otaStop("too much data"); return; }
      if (Update.write(d + 5, len) != len) { otaStop(Update.errorString()); return; }
      otaGot += len;
      otaSay("rx", nullptr, false);             // readable progress, no notification per piece
    } else if (d[0] == 'E') {                   // E: finish, check, switch on the next restart
      if (!otaActive || otaGot != otaSize) { otaStop("incomplete"); return; }
      otaActive = false;
      if (!Update.end()) { otaSay("error", Update.errorString()); return; }   // includes the MD5 and image check
      otaSay("done");
      otaRebootAt = millis() + 1500;
    } else if (d[0] == 'A') {                   // A: abort
      if (otaActive) Update.abort();
      otaActive = false;
      otaSay("idle");
    }
  }
};

// The Arduino core normally accepts a new firmware as soon as it starts. Ask it to wait: loop() keeps it
// after 15 s of normal running (see keepFirmwareIfRunning), so a firmware that crashes early rolls back.
extern "C" bool verifyRollbackLater() { return true; }
static void keepFirmwareIfRunning() {
  static bool done = false;
  if (done || millis() < 15000) return;
  done = true;
  const esp_partition_t* run = esp_ota_get_running_partition();
  esp_ota_img_states_t st;
  if (esp_ota_get_state_partition(run, &st) == ESP_OK && st == ESP_OTA_IMG_PENDING_VERIFY) {
    esp_ota_mark_app_valid_cancel_rollback();
    Serial.println("New firmware kept.");
  }
}

class ServerCB : public BLEServerCallbacks {
  void onConnect(BLEServer*) override { connected = true; }
  void onDisconnect(BLEServer*) override {
    connected = false;
    needAdvertise = true;
    if (otaActive) { Update.abort(); otaActive = false; otaSay("idle", nullptr, false); }   // start again next time
  }
};

// Commands arrive in a Bluetooth callback; queue them for loop().
static const int QN = 8;
static char cmdQueue[QN][160];
static volatile int qHead = 0, qTail = 0;
static portMUX_TYPE qMux = portMUX_INITIALIZER_UNLOCKED;
class CmdCB : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* c) override {
    String v = c->getValue();
    portENTER_CRITICAL(&qMux);
    int next = (qHead + 1) % QN;
    if (next != qTail) {
      size_t n = v.length() < 159 ? v.length() : 159;
      memcpy(cmdQueue[qHead], v.c_str(), n);
      cmdQueue[qHead][n] = 0;
      qHead = next;
    }
    portEXIT_CRITICAL(&qMux);
  }
};

static void notifyText(BLECharacteristic* ch, const char* s) {
  ch->setValue((uint8_t*)s, strlen(s));
  if (connected) ch->notify();
}

static void shotJson(const Shot& s, char* out, size_t n) {
  if (s.code == 0)
    snprintf(out, n, "{\"n\":%lu,\"ok\":1,\"v\":%.1f,\"a\":%.0f,\"p\":%d,\"q\":%.1f,\"r\":%.2f,\"d0\":%.1f,\"d1\":%.1f%s,\"b\":\"%s\"}",
             (unsigned long)s.n, s.fps, s.accel, s.pts, s.snr, s.rms, s.d0, s.d1, s.test ? ",\"test\":1" : "", s.b);
  else
    snprintf(out, n, "{\"n\":%lu,\"ok\":0,\"why\":\"%s\",\"p\":%d,\"q\":%.1f%s,\"b\":\"%s\"}",
             (unsigned long)s.n, s.why, s.pts, s.snr, s.test ? ",\"test\":1" : "", s.b);
}

static void statusJson(char* out, size_t n) {
  bool alive = millis() - teensySeenMs < 6000 && teensySeenMs != 0;
  snprintf(out, n,
           "{\"bat\":%d,\"bv\":%.2f,\"arm\":%d,\"shots\":%lu,\"t\":%d,\"rdy\":%d,\"fs\":%lu,\"nz\":%.1f,\"ovr\":%lu,"
           "\"sd\":%d,\"fw\":\"%s\",\"efw\":\"" FW_VERSION "\",\"b\":\"%s\",\"sens\":\"%s\",\"cc\":%d}",
           batPct, batV, tArmed, (unsigned long)tShots, alive ? 1 : 0, tReady, (unsigned long)tFs, tNoise,
           (unsigned long)tOvr, tSd, tFw, tBoot, sensors::letters().c_str(), sensors::get().compassCal);
}

static void pushStatus() {
  char js[240];
  statusJson(js, sizeof(js));
  notifyText(chStatus, js);
}

static void envJson(char* out, size_t n) {
  const EnvReading& e = sensors::get();
  size_t o = snprintf(out, n, "{");
  auto add = [&](const char* k, float v, int dec) {
    if (o < n - 16) o += snprintf(out + o, n - o, "%s\"%s\":%.*f", o > 1 ? "," : "", k, dec, v);
  };
  if (e.hasTH) { add("t", e.tempC, 2); add("rh", e.rh, 1); }
  else if (e.hasP) add("t", e.tempC, 2);  // pressure sensor's own thermometer: rough
  if (e.hasP) add("p", e.hPa, 2);
  if (e.hasAmmo) add("am", e.ammoC, 2);
  if (e.hasHeading) add("hd", e.heading, 1);
  if (e.hasLevel) { add("pi", e.pitch, 1); add("ro", e.roll, 1); }
  if (o < n - 10) o += snprintf(out + o, n - o, "%s\"cc\":%d", o > 1 ? "," : "", e.compassCal);
  snprintf(out + o, n - o, "}");
}

static void pushEnv() {
  char js[200];
  envJson(js, sizeof(js));
  notifyText(chEnv, js);
}

static void applyBrightness() {
  if (!oledOk) return;
  if (bright <= 0) { oled.ssd1306_command(SSD1306_DISPLAYOFF); return; }
  static const uint8_t contrast[] = {0, 1, 40, 140, 255};
  oled.ssd1306_command(SSD1306_DISPLAYON);
  oled.ssd1306_command(SSD1306_SETCONTRAST);
  oled.ssd1306_command(contrast[bright > 4 ? 4 : bright]);
}

// ---------------- screen ----------------
static uint32_t flashUntil = 0;

static void drawBattery(int x, int y) {
  oled.drawRect(x, y, 18, 8, SSD1306_WHITE);
  oled.fillRect(x + 18, y + 2, 2, 4, SSD1306_WHITE);
  if (batPct >= 0) oled.fillRect(x + 2, y + 2, (14 * batPct + 50) / 100, 4, SSD1306_WHITE);
}

// Big text in a smooth font, centred in [x0, x0 + w), with its baseline (the bottom of the capitals) at y.
static void centerFont(const GFXfont* f, const char* s, int baseline, int x0 = 0, int w = 128) {
  oled.setTextSize(1);
  oled.setFont(f);
  int16_t bx, by;
  uint16_t bw, bh;
  oled.getTextBounds(s, 0, baseline, &bx, &by, &bw, &bh);
  oled.setCursor(x0 + (w - (int)bw) / 2 - bx, baseline);
  oled.print(s);
  oled.setFont(nullptr);
}

static void centerText(const char* s, int y, int size) {
  oled.setTextSize(size);
  int w = strlen(s) * 6 * size;
  oled.setCursor((128 - w) / 2 < 0 ? 0 : (128 - w) / 2, y);
  oled.print(s);
}

// ---------------- boot animation ----------------
// A bullet flies across the screen from left to right and "writes" BLIPR behind it, then the screen
// blinks once. About 2 s; it runs once at power-up, before the bubble level.
static const int BOOT_Y = 25;   // bullet centre line (middle of the size-2 name)

// Bullet side view, tail to nose: half-height of each 1-px column (boat tail, bearing surface, spitzer nose)
static const uint8_t BULLET_PROFILE[] = {3, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
                                         5, 5, 5, 5, 4, 4, 4, 4, 3, 3, 3, 3, 2, 2, 2, 1, 0};
static const int BULLET_LEN = sizeof(BULLET_PROFILE);

static void drawBullet(int x, int y) {          // x = tail, nose to the right
  for (int i = 0; i < BULLET_LEN; i++) {
    int h = BULLET_PROFILE[i];
    oled.drawFastVLine(x + i, y - h, 2 * h + 1, SSD1306_WHITE);
  }
}

static void bootAnimation() {
  oled.invertDisplay(screenInv);
  char ver[16];
  snprintf(ver, sizeof(ver), "v%s", FW_VERSION);
  for (int x = -BULLET_LEN; x <= 132; x += 6) {
    oled.clearDisplay();
    if (screenTheme == THEME_RETRO) centerText("BLIPR", 14, 3); else centerFont(&FreeSansBold18pt7b, "BLIPR", 38);
    centerText(ver, 44, 1);
    if (x < 128) oled.fillRect(x < 0 ? 0 : x, 0, 128, 64, SSD1306_BLACK);     // not written yet
    int wake = x - 22;                                                           // the wake hides the text briefly
    oled.fillRect(wake < 0 ? 0 : wake, 9, x - (wake < 0 ? 0 : wake), 31, SSD1306_BLACK);
    for (int k = 0; k < 3; k++) {                                                // speed lines
      int len = 8 + (((x + BULLET_LEN) / 6 + k * 5) % 3) * 5;
      int y = BOOT_Y - 3 + k * 3;
      oled.drawFastHLine(x - 3 - len, y, len, SSD1306_WHITE);
    }
    drawBullet(x, BOOT_Y);
    oled.display();
    delay(12);
  }
  oled.clearDisplay();
  if (screenTheme == THEME_RETRO) centerText("BLIPR", 14, 3); else centerFont(&FreeSansBold18pt7b, "BLIPR", 38);
  centerText(ver, 44, 1);
  oled.display();
  oled.invertDisplay(!screenInv);   // the "blip"
  delay(70);
  oled.invertDisplay(screenInv);
  delay(600);
}

// After a good shot (when ANIM is on): the same bullet crosses the velocity line and writes the number
// behind it, then the screen blinks once. It runs from loop() a frame at a time, so Bluetooth and the
// Teensy link keep working; a new shot just restarts it.
static const uint32_t ANIM_MS = 620;          // bullet crossing time
static const uint32_t ANIM_BLINK_MS = 70;     // the blink at the end
static bool animRunning() { return animStart && millis() - animStart < ANIM_MS + ANIM_BLINK_MS; }

// ---------------- bubble level ----------------
// Shown for up to 60 s after power-up (and on the LEVEL command) when the level sensor is fitted.
// The screen is read from behind the chronograph, so its top edge is the FRONT (downrange) and its
// right edge is the right-hand side. The bubble floats to the high side, like a real bubble level.
static const float LEVEL_OK_DEG = 0.5f;       // within this on both axes counts as level
static const float LEVEL_FULL_DEG = 5.0f;     // tilt that puts the bubble at the edge of the ring
static uint32_t levelUntil = 0;               // millis() when the level screen ends (0 = not showing)
static uint32_t levelOkSince = 0;             // when it last became level (0 = not level)
static uint32_t levelDoneAt = 0;              // when it was held level long enough (shows "LEVEL" briefly)
static uint32_t levelStart = 0;

static void startLevel(uint32_t ms) {
  levelStart = millis();
  levelUntil = levelStart + ms;
  if (levelUntil == 0) levelUntil = 1;
  levelOkSince = 0;
  levelDoneAt = 0;
}

static bool levelShowing() {
  if (!levelUntil) return false;
  const EnvReading& e = sensors::get();
  uint32_t now = millis();
  if (!e.hasLevel) {                       // no level sensor (give it 3 s to answer after power-up)
    if (now - levelStart > 3000) levelUntil = 0;
    return false;
  }
  if ((int32_t)(now - levelUntil) >= 0 || (levelDoneAt && now - levelDoneAt > 1500)) {
    levelUntil = 0;
    return false;
  }
  return true;
}

static void drawLevel() {
  const EnvReading& e = sensors::get();
  uint32_t now = millis();
  float p = e.pitch, r = e.roll;                       // nose up +, right side down +
  bool ok = fabsf(p) <= LEVEL_OK_DEG && fabsf(r) <= LEVEL_OK_DEG;
  if (ok) { if (!levelOkSince) levelOkSince = now; } else { levelOkSince = 0; levelDoneAt = 0; }
  if (ok && !levelDoneAt && now - levelOkSince >= 3000) levelDoneAt = now;   // held level for 3 s

  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  // ring, crosshair and the target circle
  const int cx = 32, cy = 32, R = 30, B = 5;
  oled.drawCircle(cx, cy, R, SSD1306_WHITE);
  oled.drawCircle(cx, cy, B + 2, SSD1306_WHITE);
  oled.drawFastHLine(cx - R + 2, cy, R - B - 4, SSD1306_WHITE);
  oled.drawFastHLine(cx + B + 3, cy, R - B - 4, SSD1306_WHITE);
  oled.drawFastVLine(cx, cy - R + 2, R - B - 4, SSD1306_WHITE);
  oled.drawFastVLine(cx, cy + B + 3, R - B - 4, SSD1306_WHITE);
  // bubble: nose up = front high = bubble toward the top; right side down = left high = bubble to the left
  float k = (R - B - 1) / LEVEL_FULL_DEG;
  float bx = -r * k, by = -p * k;                       // screen y grows downward
  float d = sqrtf(bx * bx + by * by), dmax = (float)(R - B - 1);
  if (d > dmax) { bx *= dmax / d; by *= dmax / d; }
  oled.fillCircle(cx + (int)lroundf(bx), cy + (int)lroundf(by), B, SSD1306_WHITE);

  // right-hand side: what to do
  oled.setTextSize(1);
  oled.setCursor(68, 0);
  oled.print("LEVEL");
  if (batPct >= 0) drawBattery(108, 0);
  if (levelDoneAt || ok) {
    oled.fillRect(66, 22, 62, 20, SSD1306_WHITE);
    oled.setTextColor(SSD1306_BLACK);
    if (screenTheme == THEME_RETRO) { oled.setTextSize(2); oled.setCursor(67, 25); oled.print("LEVEL"); oled.setTextSize(1); }
    else centerFont(&FreeSansBold9pt7b, "LEVEL", 38, 66, 62);
    oled.setTextColor(SSD1306_WHITE);
    oled.setTextSize(1);
  } else {
    // at most 10 characters a line fit beside the ring
    oled.setCursor(66, 12); oled.print(fabsf(p) <= LEVEL_OK_DEG ? "Nose ok" : (p > 0 ? "Lower nose" : "Lift nose"));
    if (fabsf(p) > LEVEL_OK_DEG) { oled.setCursor(72, 21); oled.printf("%.1f deg", fabsf(p)); }
    oled.setCursor(66, 33); oled.print(fabsf(r) <= LEVEL_OK_DEG ? "Sides ok" : (r > 0 ? "Lift right" : "Lift left"));
    if (fabsf(r) > LEVEL_OK_DEG) { oled.setCursor(72, 42); oled.printf("%.1f deg", fabsf(r)); }
  }
  oled.setCursor(66, 56);
  oled.printf("%lus", (unsigned long)((levelUntil - now) / 1000 + 1));
  oled.display();
}

static void drawScreen() {
  if (!oledOk) return;
  oled.invertDisplay(screenInv);
  if (otaActive || otaRebootAt) {               // firmware update in progress
    oled.clearDisplay();
    oled.setTextColor(SSD1306_WHITE);
    centerFont(&FreeSansBold12pt7b, otaRebootAt ? "UPDATED" : "UPDATING", 27);
    uint32_t pct = otaSize ? (uint64_t)otaGot * 100 / otaSize : 0;
    oled.drawRect(4, 34, 120, 10, SSD1306_WHITE);
    oled.fillRect(6, 36, (int)(116 * pct / 100), 6, SSD1306_WHITE);
    char b[24];
    snprintf(b, sizeof(b), otaRebootAt ? "restarting" : "%lu%%  keep close", (unsigned long)pct);
    centerText(b, 50, 1);
    oled.display();
    return;
  }
  if (levelShowing()) { drawLevel(); return; }
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  // top bar: shot number, Bluetooth, battery
  oled.setTextSize(1);
  oled.setCursor(0, 0);
  if (haveLast) oled.printf("#%lu", (unsigned long)last.n);
  if (connected) { oled.setCursor(44, 0); oled.print("BT"); }
  if (batPct >= 0) {
    char b[12];
    snprintf(b, sizeof(b), "%d%%", batPct);
    oled.setCursor(104 - 6 * strlen(b), 0);
    oled.print(b);
  }
  drawBattery(108, 0);

  const bool retro = screenTheme == THEME_RETRO;
  auto bigWord = [&](const char* w, int baseline) {     // a status word in the theme's big font
    if (retro) centerText(w, baseline - 14, 2); else centerFont(&FreeSansBold12pt7b, w, baseline);
  };
  const char* units = unitsMps ? "m/s" : "fps";
  const float k = unitsMps ? 0.3048f : 1.0f;
  const double mean = sN ? sSum / sN : 0, var = sN ? sSum2 / sN - mean * mean : 0;
  const double sd = sqrt(var > 0 ? var : 0);
  const EnvReading& e = sensors::get();
  const bool haveWx = e.hasTH || e.hasP || e.hasAmmo || e.hasHeading;
  auto wxLine1 = [&]() {
    if (e.hasTH || e.hasP) {
      if (unitsMps) oled.printf("%.1fC", e.tempC); else oled.printf("%.1fF", e.tempC * 1.8f + 32);
      if (e.hasTH) oled.printf(" %.0f%%", e.rh);
      if (e.hasP) { if (unitsMps) oled.printf(" %.0fhPa", e.hPa); else oled.printf(" %.2fin", e.hPa * 0.02953f); }
    }
  };
  auto wxLine2 = [&]() {
    if (e.hasAmmo) { if (unitsMps) oled.printf("Ammo %.1fC", e.ammoC); else oled.printf("Ammo %.1fF", e.ammoC * 1.8f + 32); }
    if (e.hasHeading) oled.printf("%sHdg %03.0f", e.hasAmmo ? "  " : "", e.heading);
  };
  // where the velocity sits, for the shot animation: [0, ax) x [ay0, ay1), bullet centre line ayc
  int ax = 128, ay0 = 9, ay1 = 40, ayc = 25;

  bool alive = teensySeenMs && millis() - teensySeenMs < 6000;
  char big[16];
  if (!alive) {
    bigWord("NO RADAR", 33);
    centerText("Teensy not talking", 40, 1);
  } else if (haveLast && last.code == 0) {
    float v = last.fps * k;
    snprintf(big, sizeof(big), "%.0f", v);
    oled.setTextSize(1);
    int16_t bx, by;
    uint16_t bw, bh;
    if (screenTheme == THEME_BIG) {               // the number as big as it goes, units on its baseline
      oled.setFont(&FreeSansBold24pt7b);
      oled.getTextBounds(big, 0, 46, &bx, &by, &bw, &bh);
      int x = (128 - ((int)bw + 3 + 18)) / 2;
      oled.setCursor(x - bx, 46);
      oled.print(big);
      oled.setFont(nullptr);
      oled.setCursor(x + bw + 3, 46 - 7);
      oled.print(units);
      ay1 = 49; ayc = 30;
    } else if (screenTheme == THEME_STATS) {      // a smaller number on the left, the whole string on the right
      oled.setFont(&FreeSansBold12pt7b);
      oled.getTextBounds(big, 0, 28, &bx, &by, &bw, &bh);
      int x = (72 - (int)bw) / 2;
      oled.setCursor(x - bx, 28);
      oled.print(big);
      oled.setFont(nullptr);
      oled.setCursor((72 - 18) / 2, 32);
      oled.print(units);
      ax = 72; ay1 = 41; ayc = 21;
    } else if (retro) {                           // the original 5x7 font, three times size
      oled.setTextSize(3);
      int w = strlen(big) * 18;
      int x = (104 - w) / 2;
      oled.setCursor(x < 0 ? 0 : x, 14);
      oled.print(big);
      oled.setTextSize(1);
      oled.setCursor(x + w + 3 > 104 ? 104 : x + w + 3, 28);
      oled.print(units);
    } else {                                      // Classic
      oled.setFont(&FreeSansBold18pt7b);
      oled.getTextBounds(big, 0, 37, &bx, &by, &bw, &bh);
      int x = (128 - ((int)bw + 3 + 18)) / 2;
      oled.setCursor(x - bx, 37);
      oled.print(big);
      oled.setFont(nullptr);
      oled.setCursor(x + bw + 3, 37 - 7);
      oled.print(units);
    }
  } else if (haveLast) {
    bigWord("NO READ", 30);
    centerText(last.why, 36, 1);
  } else {
    bigWord(tArmed ? "READY" : "PAUSED", 33);
  }

  oled.setTextSize(1);
  if (alive && screenTheme == THEME_STATS && haveLast && last.code == 0) {
    // right-hand column: the string; bottom left: the weather
    const int cx = 78;
    oled.setCursor(cx, 10); oled.printf("n %d", sN);
    if (sN > 0) {
      oled.setCursor(cx, 19); oled.printf("avg %.0f", mean * k);
      if (sN > 1) {
        oled.setCursor(cx, 28); oled.printf("SD %.1f", sd * k);
        oled.setCursor(cx, 37); oled.printf("ES %.0f", (sMax - sMin) * k);
      }
      oled.setCursor(cx, 46); oled.printf("lo %.0f", sMin * k);
      oled.setCursor(cx, 55); oled.printf("hi %.0f", sMax * k);
    }
    if (haveWx) { oled.setCursor(0, 47); wxLine1(); oled.setCursor(0, 56); wxLine2(); }
  } else if (alive && screenTheme == THEME_BIG) {
    // one line under the big number: the string, taking turns with the weather
    oled.setCursor(0, 56);
    if (haveWx && (sN == 0 || (millis() / 4000) % 2)) wxLine1();
    else if (sN > 1) oled.printf("n%d avg %.0f SD %.1f", sN, mean * k, sd * k);
    else if (sN == 1) oled.printf("n1 avg %.0f", mean * k);
  } else if (alive) {
    // Classic and Retro: two lines of string stats, taking turns with the weather when sensors are fitted
    bool showWx = haveWx && (sN == 0 || (millis() / 4000) % 2);
    if (showWx) {
      oled.setCursor(0, 47); wxLine1();
      oled.setCursor(0, 56); wxLine2();
    } else if (sN > 0) {
      oled.setCursor(0, 47);
      oled.printf("n %d  avg %.0f", sN, mean * k);
      oled.setCursor(0, 56);
      if (sN > 1) oled.printf("SD %.1f  ES %.0f", sd * k, (sMax - sMin) * k);
    }
  }

  // the shot animation: the bullet crosses the velocity and writes it behind itself
  if (animStart && haveLast && last.code == 0) {
    uint32_t t = millis() - animStart;
    if (t < ANIM_MS) {
      int bx = -BULLET_LEN + (int)((ax + BULLET_LEN) * t / ANIM_MS);
      if (bx < ax) oled.fillRect(bx < 0 ? 0 : bx, ay0, ax - (bx < 0 ? 0 : bx), ay1 - ay0, SSD1306_BLACK);   // not written yet
      int wake = bx - 22;
      oled.fillRect(wake < 0 ? 0 : wake, ay0, bx - (wake < 0 ? 0 : wake), ay1 - ay0, SSD1306_BLACK);
      for (int j = 0; j < 3; j++) {
        int len = 8 + (((bx + BULLET_LEN) / 6 + j * 5) % 3) * 5;
        oled.drawFastHLine(bx - 3 - len, ayc - 3 + j * 3, len, SSD1306_WHITE);
      }
      drawBullet(bx, ayc);
    }
  }
  if (batPct >= 0 && batPct < 10 && (millis() / 700) % 2) {
    oled.fillRect(0, 46, 128, 18, SSD1306_BLACK);
    centerText("LOW BATTERY", 50, 1);
  }
  oled.display();
  bool blink = false;
  if (animStart) {
    uint32_t t = millis() - animStart;
    blink = t >= ANIM_MS && t < ANIM_MS + ANIM_BLINK_MS;
    if (t >= ANIM_MS + ANIM_BLINK_MS) animStart = 0;
  }
  oled.invertDisplay(blink ? !screenInv : screenInv);
}

// ---------------- messages from the Teensy ----------------
static void handleTeensy(char* line) {
  // line is the body without '@' and checksum, fields split by commas
  char* f[16];
  int nf = 0;
  for (char* p = strtok(line, ","); p && nf < 16; p = strtok(nullptr, ",")) f[nf++] = p;
  if (nf == 0) return;
  teensySeenMs = millis();
  if (!strcmp(f[0], "S") && nf >= 12) {
    Shot s = {};
    s.n = strtoul(f[1], nullptr, 10);
    s.fps = atof(f[2]);
    s.accel = atof(f[4]);
    s.pts = atoi(f[5]);
    s.snr = atof(f[6]);
    s.rms = atof(f[7]);
    s.d0 = atof(f[8]);
    s.d1 = atof(f[9]);
    s.code = atoi(f[10]);
    s.test = !strcmp(f[11], "test");
    strncpy(s.why, f[11], sizeof(s.why) - 1);
    strncpy(s.b, tBoot, sizeof(s.b) - 1);
    // shot numbers only go up within one Teensy start; if it went back, the Teensy restarted
    if (shotCount > 0 && s.n <= lastShotN) { clearShots(); toTeensy("stat"); }  // and ask for its new boot id
    shots[s.n % MAX_SHOTS] = s;
    if (shotCount < MAX_SHOTS) shotCount++;
    lastShotN = s.n;
    last = s;
    haveLast = true;
    if (s.code == 0 && !s.test) {   // test shots show on the screen but stay out of the string's numbers
      sN++; sSum += s.fps; sSum2 += (double)s.fps * s.fps;
      if (s.fps < sMin) sMin = s.fps;
      if (s.fps > sMax) sMax = s.fps;
    }
    levelUntil = 0;   // a shot always replaces the level screen
    animStart = (shotAnim && s.code == 0) ? (millis() | 1) : 0;
    char js[220];
    shotJson(s, js, sizeof(js));
    notifyText(chShot, js);
    Serial.println(js);
    digitalWrite(PIN_LED, LOW);
    flashUntil = millis() + 150;
    drawScreen();
  } else if (!strcmp(f[0], "T") && nf >= 10) {
    tArmed = atoi(f[1]);
    tShots = strtoul(f[2], nullptr, 10);
    tFs = strtoul(f[3], nullptr, 10);
    tNoise = atof(f[4]);
    tOvr = strtoul(f[5], nullptr, 10);
    tSd = atoi(f[6]);
    strncpy(tFw, f[7], sizeof(tFw) - 1);
    // a new boot id means the Teensy restarted: its shot numbers start again at 1, so the stored
    // shots from the old start must not be re-sent (by SYNC) as if they belonged to the new one
    if (tBoot[0] && strcmp(tBoot, f[8]) != 0) clearShots();
    strncpy(tBoot, f[8], sizeof(tBoot) - 1);
    tReady = atoi(f[9]);
  } else if (!strcmp(f[0], "C")) {
    // "C,vmin=300,vmax=4500,..." -> {"vmin":300,"vmax":4500,...}
    // Built in a scratch buffer and only copied over when everything fitted, so an odd value
    // can never write past the end or leave half a message behind.
    char tmp[sizeof(configJson)];
    const size_t cap = sizeof(tmp);
    size_t o = 0;
    bool fits = true;
    auto add = [&](int w) { if (w < 0 || (size_t)w >= cap - o) fits = false; else o += (size_t)w; };
    add(snprintf(tmp, cap, "{"));
    for (int i = 1; i < nf && fits; i++) {
      char* eq = strchr(f[i], '=');
      if (!eq || strlen(eq + 1) > 16) continue;   // no sensible setting is that long
      *eq = 0;
      add(snprintf(tmp + o, cap - o, "%s\"%s\":%s", o > 1 ? "," : "", f[i], eq + 1));
    }
    if (fits)
      add(snprintf(tmp + o, cap - o, "%s\"units\":\"%s\",\"batcal\":%.4f,\"bright\":%d,\"anim\":%d,\"theme\":%d,\"inv\":%d,\"hoff\":%.1f,\"hrev\":%d,\"hrot\":%d}",
                   o > 1 ? "," : "", unitsMps ? "mps" : "fps", batCal, bright, shotAnim ? 1 : 0, screenTheme, screenInv ? 1 : 0, sensors::headingOffset(),
                   sensors::headingReverse() ? 1 : 0, sensors::imuRotation()));
    if (!fits) return;
    memcpy(configJson, tmp, o + 1);
    notifyText(chConfig, configJson);
  }
}

static char lnk[220];
static size_t lnkLen = 0;
static void readTeensy() {
  while (Link.available()) {
    char c = Link.read();
    if (c == '@') { lnkLen = 0; lnk[lnkLen++] = c; continue; }
    if (c == '\n') {
      lnk[lnkLen] = 0;
      char* star = strrchr(lnk, '*');
      if (lnkLen > 3 && lnk[0] == '@' && star) {
        uint8_t want = (uint8_t)strtoul(star + 1, nullptr, 16);
        *star = 0;
        if (xorSum(lnk + 1, strlen(lnk + 1)) == want) handleTeensy(lnk + 1);
      }
      lnkLen = 0;
    } else if (lnkLen > 0 && lnkLen < sizeof(lnk) - 1) lnk[lnkLen++] = c;
  }
}

// ---------------- commands (Bluetooth and USB) ----------------
static void handleCommand(char* cmd) {
  while (*cmd == ' ') cmd++;
  size_t L = strlen(cmd);
  while (L && (cmd[L - 1] == '\r' || cmd[L - 1] == '\n' || cmd[L - 1] == ' ')) cmd[--L] = 0;
  if (!L) return;
  char word[16] = {0};
  sscanf(cmd, "%15s", word);
  for (char* c = word; *c; c++) *c = toupper(*c);
  const char* arg = cmd + strlen(word);
  while (*arg == ' ') arg++;

  if (!strcmp(word, "SYNC")) {
    // re-send stored shots newer than the number given (after a reconnect)
    uint32_t after = strtoul(arg, nullptr, 10);
    uint32_t from = lastShotN > (uint32_t)shotCount ? lastShotN - shotCount + 1 : 1;
    if (after + 1 > from) from = after + 1;
    for (uint32_t n = from; n <= lastShotN; n++) {
      const Shot& s = shots[n % MAX_SHOTS];
      if (s.n != n) continue;
      char js[220];
      shotJson(s, js, sizeof(js));
      notifyText(chShot, js);
      delay(20);
    }
  } else if (!strcmp(word, "STRING")) {
    sN = 0; sSum = sSum2 = 0; sMin = 1e9; sMax = -1e9;
    haveLast = false;
    drawScreen();
  } else if (!strcmp(word, "UNITS")) {
    unitsMps = (toupper(arg[0]) == 'M');
    prefs.putBool("mps", unitsMps);
    drawScreen();
    toTeensy("get");
  } else if (!strcmp(word, "BATV")) {
    // "BATV 3.97": the battery voltage you measured with a multimeter
    float actual = atof(arg);
    float raw = readBatteryRaw();
    if (actual > 2.5f && actual < 4.5f && raw > 1.0f) {
      batCal = actual / raw;
      prefs.putFloat("batcal", batCal);
      batV = 0;
      updateBattery();
    }
    toTeensy("get");
    pushStatus();
  } else if (!strcmp(word, "STATUS")) {
    pushStatus();
    pushEnv();
  } else if (!strcmp(word, "LEVEL")) {
    // LEVEL: show the bubble level for 60 s.  LEVEL OFF: back to the normal screen.
    if (toupper(arg[0]) == 'O' && toupper(arg[1]) == 'F') levelUntil = 0; else startLevel(60000);
    drawScreen();
  } else if (!strcmp(word, "THEME")) {
    // THEME 0-3 or CLASSIC / BIG / STATS / RETRO: how the screen looks
    static const char* names[] = {"CLASSIC", "BIG", "STATS", "RETRO"};
    int t = -1;
    if (isdigit((unsigned char)arg[0])) t = atoi(arg);
    else for (int i = 0; i < THEME_COUNT; i++) if (!strncasecmp(arg, names[i], strlen(names[i]))) t = i;
    if (t >= 0 && t < THEME_COUNT) { screenTheme = t; prefs.putInt("theme", t); drawScreen(); }
    toTeensy("get");
  } else if (!strcmp(word, "INVERT")) {
    // INVERT 1: dark text on a lit screen.  INVERT 0: light text on black (the usual)
    screenInv = atoi(arg) != 0 || (arg[0] && toupper(arg[1]) == 'N');
    prefs.putBool("inv", screenInv);
    oled.invertDisplay(screenInv);
    toTeensy("get");
  } else if (!strcmp(word, "ANIM")) {
    // ANIM 1: play the bullet animation after each good shot.  ANIM 0: just show the number.
    shotAnim = atoi(arg) != 0 || (arg[0] && toupper(arg[1]) == 'N');   // also takes ON / OFF
    prefs.putBool("anim", shotAnim);
    toTeensy("get");   // the config notification carries "anim"
  } else if (!strcmp(word, "BRIGHT")) {
    bright = atoi(arg);
    if (bright < 0) bright = 0;
    if (bright > 4) bright = 4;
    prefs.putInt("bright", bright);
    applyBrightness();
    toTeensy("get");
  } else if (!strcmp(word, "COMPASS")) {
    // COMPASS CAL START | COMPASS CAL STOP | COMPASS MATCH <deg> | COMPASS OFFSET <deg> | COMPASS REVERSE 0/1 | COMPASS ROT 0/90/180/270
    char a1[12] = {0}, a2[12] = {0};
    sscanf(arg, "%11s %11s", a1, a2);
    for (char* c = a1; *c; c++) *c = toupper(*c);
    for (char* c = a2; *c; c++) *c = toupper(*c);
    if (!strcmp(a1, "CAL") && !strcmp(a2, "START")) sensors::compassCalStart();
    else if (!strcmp(a1, "CAL") && !strcmp(a2, "STOP")) {
      bool ok = sensors::compassCalStop();
      char js[60];
      snprintf(js, sizeof(js), "{\"compass\":\"%s\"}", ok ? "calibrated" : "not enough turning");
      notifyText(chEnv, js);
    }
    else if (!strcmp(a1, "MATCH")) {
      // the phone says the chronograph is pointing at <deg>: set the offset so it agrees
      float want = atof(a2);
      float off = want - sensors::headingRaw();
      while (off < -180) off += 360;
      while (off > 180) off -= 360;
      sensors::setHeadingOffset(off);
    }
    else if (!strcmp(a1, "OFFSET")) sensors::setHeadingOffset(atof(a2));
    else if (!strcmp(a1, "REVERSE")) sensors::setHeadingReverse(atoi(a2) != 0);
    else if (!strcmp(a1, "ROT")) sensors::setImuRotation(atoi(a2));
    toTeensy("get");
    pushEnv();
  } else {
    toTeensy(cmd);  // everything else is for the Teensy (SET, GET, ARM, DISARM, TEST, REC, STAT ...)
  }
}

// ---------------- setup / loop ----------------
void setup() {
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, HIGH);
  Serial.begin(115200);
  Link.setRxBufferSize(1024);  // must come before begin()
  Link.begin(LINK_BAUD, SERIAL_8N1, PIN_LINK_RX, PIN_LINK_TX);

  prefs.begin("chrono", false);
  batCal = prefs.getFloat("batcal", 1.0f);
  unitsMps = prefs.getBool("mps", false);
  bright = prefs.getInt("bright", 3);
  shotAnim = prefs.getBool("anim", false);
  screenTheme = prefs.getInt("theme", THEME_CLASSIC);
  if (screenTheme < 0 || screenTheme >= THEME_COUNT) screenTheme = THEME_CLASSIC;
  screenInv = prefs.getBool("inv", false);
  analogReadResolution(12);
  analogSetPinAttenuation(PIN_BAT, ADC_11db);

  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(400000);
  oledOk = oled.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  if (oledOk) {
    oled.clearDisplay();
    oled.setTextColor(SSD1306_WHITE);
    applyBrightness();
    bootAnimation();            // ends on the name and version, which stay up while Bluetooth starts
  }
  sensors::begin(PIN_ONEWIRE);

  BLEDevice::init(DEVICE_NAME);
  BLEDevice::setMTU(185);
  server = BLEDevice::createServer();
  server->setCallbacks(new ServerCB());
  BLEService* svc = server->createService(BLEUUID(SVC_UUID), 30);
  chShot = svc->createCharacteristic(SHOT_UUID, BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);
  chStatus = svc->createCharacteristic(STATUS_UUID, BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);
  chConfig = svc->createCharacteristic(CONFIG_UUID, BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);
  chCmd = svc->createCharacteristic(CMD_UUID, BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR);
  chEnv = svc->createCharacteristic(ENV_UUID, BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);
  chOta = svc->createCharacteristic(OTA_UUID, BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_WRITE |
                                              BLECharacteristic::PROPERTY_WRITE_NR | BLECharacteristic::PROPERTY_NOTIFY);
#ifdef CONFIG_BLUEDROID_ENABLED
  chOta->addDescriptor(new BLE2902());
  chShot->addDescriptor(new BLE2902());
  chStatus->addDescriptor(new BLE2902());
  chConfig->addDescriptor(new BLE2902());
  chEnv->addDescriptor(new BLE2902());
#endif
  chEnv->setValue("{}");
  chCmd->setCallbacks(new CmdCB());
  chOta->setCallbacks(new OtaCB());
  otaSay("idle", nullptr, false);
  chShot->setValue("{}");
  chConfig->setValue(configJson);
  svc->start();
  BLEAdvertising* adv = BLEDevice::getAdvertising();
  adv->addServiceUUID(SVC_UUID);
  adv->setScanResponse(true);
  BLEDevice::startAdvertising();

  updateBattery();
  pushStatus();
  Serial.printf("BLIPR ESP32-C3 firmware %s ready. Sensors found: %s\n"
                "Commands: STATUS, SYNC n, STRING, UNITS fps|mps, BATV volts, BRIGHT 0-4, THEME 0-3, INVERT 0|1, ANIM 0|1, LEVEL [OFF], COMPASS ...,\n"
                "or any Teensy command (STAT, GET, SET ..., ARM, DISARM, TEST, REC, TIME).\n", FW_VERSION,
                sensors::letters().length() ? sensors::letters().c_str() : "none");
  delay(300);
  toTeensy("get");
  toTeensy("stat");
  startLevel(60000);   // only shows if the level sensor answers (levelShowing() checks)
}

void loop() {
  readTeensy();

  // commands from Bluetooth
  while (qTail != qHead) {
    char c[160];
    portENTER_CRITICAL(&qMux);
    memcpy(c, cmdQueue[qTail], sizeof(c));
    qTail = (qTail + 1) % QN;
    portEXIT_CRITICAL(&qMux);
    handleCommand(c);
  }
  // commands typed in the Serial Monitor
  static char usb[160];
  static size_t usbLen = 0;
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n' || ch == '\r') { if (usbLen) { usb[usbLen] = 0; handleCommand(usb); usbLen = 0; } }
    else if (usbLen < sizeof(usb) - 1) usb[usbLen++] = ch;
  }

  if (needAdvertise) {
    needAdvertise = false;
    delay(200);
    BLEDevice::startAdvertising();
  }
  if (flashUntil && millis() > flashUntil) { digitalWrite(PIN_LED, HIGH); flashUntil = 0; }

  keepFirmwareIfRunning();
  if (otaRebootAt && millis() > otaRebootAt) { Serial.println("Restarting into the new firmware..."); delay(100); ESP.restart(); }
  if (otaActive && millis() - otaLastMs > 20000) { Update.abort(); otaActive = false; otaSay("idle"); }   // sender gave up

  sensors::update();
  static uint32_t lastBat = 0, lastStat = 0, lastDraw = 0, lastEnv = 0;
  static bool wasConnected = false;
  uint32_t now = millis();
  if (now - lastBat >= 2000) { lastBat = now; updateBattery(); }
  if (now - lastStat >= 2000 || connected != wasConnected) {
    lastStat = now;
    if (connected && !wasConnected) { notifyText(chConfig, configJson); }
    wasConnected = connected;
    pushStatus();
  }
  if (now - lastDraw >= (animStart ? 15u : (levelUntil || otaActive) ? 100u : 500u)) { lastDraw = now; drawScreen(); }
  if (now - lastEnv >= 2000) { lastEnv = now; if (sensors::letters().length()) pushEnv(); }
}
