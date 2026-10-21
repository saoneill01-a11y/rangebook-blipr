#include "sensors.h"
#include <Wire.h>
#include <Preferences.h>
#include <Adafruit_SHT4x.h>
#include <Adafruit_BMP3XX.h>
#include <Adafruit_LSM6DSOX.h>
#include <Adafruit_LIS3MDL.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <math.h>

namespace sensors {

static Adafruit_SHT4x sht;
static Adafruit_BMP3XX bmp;
static Adafruit_LSM6DSOX imu;
static Adafruit_LIS3MDL mag;
static OneWire* ow = nullptr;
static DallasTemperature* dallas = nullptr;
static bool haveSht = false, haveBmp = false, haveImu = false, haveMag = false, haveProbe = false;
static int owPin = -1;
static EnvReading env;
static Preferences pref;

// compass calibration (hard-iron offset and simple per-axis scale)
static float mOff[3] = {0, 0, 0}, mScl[3] = {1, 1, 1};
static float mMin[3], mMax[3];
static bool calibrating = false;
static uint32_t calSamples = 0;
static float hdgOffset = 0;
// How the IMU board is turned on its mount, in degrees COUNTER-CLOCKWISE seen from above:
// 0 = the board's X arrow points forward (toward the target), 90 = X points left, 180 = back, 270 = right.
static int imuRot = 0;
static void rotXY(float& x, float& y) {
  float a = x, b = y;
  switch (imuRot) {
    case 90:  x = -b; y = a; break;
    case 180: x = -a; y = -b; break;
    case 270: x = b;  y = -a; break;
    default: break;
  }
}
static bool hdgReverse = false;
static float rawHeading = 0;
// smoothed heading as a unit vector, so 359 -> 1 doesn't average to 180
static float hx = 0, hy = 0;
static float ax_ = 0, ay_ = 0, az_ = 9.8f;

static bool i2cPresent(uint8_t a) {
  Wire.beginTransmission(a);
  return Wire.endTransmission() == 0;
}

static void probeI2C() {
  if (!haveSht && i2cPresent(0x44) && sht.begin(&Wire)) {
    sht.setPrecision(SHT4X_HIGH_PRECISION);
    sht.setHeater(SHT4X_NO_HEATER);
    haveSht = true;
  }
  if (!haveBmp) {
    for (uint8_t a : {(uint8_t)0x77, (uint8_t)0x76}) {
      if (i2cPresent(a) && bmp.begin_I2C(a, &Wire)) {
        bmp.setTemperatureOversampling(BMP3_OVERSAMPLING_2X);
        bmp.setPressureOversampling(BMP3_OVERSAMPLING_16X);
        bmp.setIIRFilterCoeff(BMP3_IIR_FILTER_COEFF_3);
        haveBmp = true;
        break;
      }
    }
  }
  if (!haveImu) {
    for (uint8_t a : {(uint8_t)0x6A, (uint8_t)0x6B})
      if (i2cPresent(a) && imu.begin_I2C(a, &Wire)) { haveImu = true; break; }
  }
  if (!haveMag) {
    for (uint8_t a : {(uint8_t)0x1C, (uint8_t)0x1E}) {
      if (i2cPresent(a) && mag.begin_I2C(a, &Wire)) {
        mag.setPerformanceMode(LIS3MDL_ULTRAHIGHMODE);
        mag.setOperationMode(LIS3MDL_CONTINUOUSMODE);
        mag.setDataRate(LIS3MDL_DATARATE_10_HZ);
        mag.setRange(LIS3MDL_RANGE_4_GAUSS);
        haveMag = true;
        break;
      }
    }
  }
}

static void probeOneWire() {
  if (haveProbe || owPin < 0) return;
  if (!ow) { ow = new OneWire(owPin); dallas = new DallasTemperature(ow); }
  dallas->begin();
  if (dallas->getDeviceCount() > 0) {
    dallas->setResolution(12);
    dallas->setWaitForConversion(false);
    dallas->requestTemperatures();
    haveProbe = true;
  }
}

void begin(int pinOneWire) {
  owPin = pinOneWire;
  pref.begin("compass", false);
  for (int i = 0; i < 3; i++) {
    char k[6];
    snprintf(k, sizeof(k), "o%d", i); mOff[i] = pref.getFloat(k, 0);
    snprintf(k, sizeof(k), "s%d", i); mScl[i] = pref.getFloat(k, 1);
  }
  hdgOffset = pref.getFloat("off", 0);
  hdgReverse = pref.getBool("rev", false);
  imuRot = pref.getInt("irot", 0);
  env.compassCal = pref.getBool("cal", false) ? 2 : 0;
  probeI2C();
  probeOneWire();
}

const EnvReading& get() { return env; }

String letters() {
  String s;
  if (haveSht) s += "T";
  if (haveBmp) s += "P";
  if (haveProbe) s += "A";
  if (haveMag) s += "C";
  if (haveImu) s += "L";
  return s;
}

static float wrap360(float d) { while (d < 0) d += 360; while (d >= 360) d -= 360; return d; }

void update() {
  static uint32_t tSlow = 0, tFast = 0, tProbe = 0, tAmmo = 0;
  uint32_t now = millis();
  // look for sensors plugged in after start-up (every 15 s)
  if (now - tProbe > 15000) { tProbe = now; probeI2C(); probeOneWire(); }

  // accelerometer + compass, 10 times a second
  if (now - tFast >= 100) {
    tFast = now;
    if (haveImu) {
      sensors_event_t a, g, t;
      if (imu.getEvent(&a, &g, &t)) {
        float rx = a.acceleration.x, ry = a.acceleration.y;
        rotXY(rx, ry);
        ax_ = 0.8f * ax_ + 0.2f * rx;
        ay_ = 0.8f * ay_ + 0.2f * ry;
        az_ = 0.8f * az_ + 0.2f * a.acceleration.z;
        // pitch: nose up positive; roll: right side down positive (board X axis = forward)
        env.pitch = atan2f(ax_, sqrtf(ay_ * ay_ + az_ * az_)) * 57.2958f;
        env.roll = atan2f(ay_, az_) * 57.2958f;
        env.hasLevel = true;
      }
    }
    if (haveMag) {
      sensors_event_t m;
      if (mag.getEvent(&m)) {
        float v[3] = {m.magnetic.x, m.magnetic.y, m.magnetic.z};
        if (calibrating) {
          for (int i = 0; i < 3; i++) {
            if (calSamples == 0 || v[i] < mMin[i]) mMin[i] = v[i];
            if (calSamples == 0 || v[i] > mMax[i]) mMax[i] = v[i];
          }
          calSamples++;
        }
        float c[3];
        for (int i = 0; i < 3; i++) c[i] = (v[i] - mOff[i]) * mScl[i];
        rotXY(c[0], c[1]);
        // Board axes: X forward (toward the radar's aim), Y left, Z up; at rest the accelerometer reads +g on Z.
        // Heading = angle of the magnetic field's horizontal part, measured clockwise from the forward direction
        // to north, so 0 = pointing north, 90 = east. Tilt compensation: "horizontal" comes from the
        // accelerometer's up vector (if fitted), otherwise the board is assumed level.
        float u[3] = {0, 0, 1};
        if (haveImu) {
          float n = sqrtf(ax_ * ax_ + ay_ * ay_ + az_ * az_);
          if (n > 1.0f) { u[0] = ax_ / n; u[1] = ay_ / n; u[2] = az_ / n; }
        }
        float mu = c[0] * u[0] + c[1] * u[1] + c[2] * u[2];
        float mh[3] = {c[0] - mu * u[0], c[1] - mu * u[1], c[2] - mu * u[2]};   // field, horizontal part
        float fh[3] = {1 - u[0] * u[0], -u[0] * u[1], -u[0] * u[2]};          // forward, horizontal part
        float lh[3] = {u[1] * fh[2] - u[2] * fh[1], u[2] * fh[0] - u[0] * fh[2], u[0] * fh[1] - u[1] * fh[0]};  // up x forward = left
        float north = mh[0] * fh[0] + mh[1] * fh[1] + mh[2] * fh[2];
        float left = mh[0] * lh[0] + mh[1] * lh[1] + mh[2] * lh[2];
        // north to the left of where it points means it points east of north
        float h = atan2f(left, north) * 57.2958f;
        // REVERSE is only for a magnetometer with no accelerometer, mounted upside down. With the
        // accelerometer fitted, "up" comes from gravity, so an upside-down board already reads right.
        if (hdgReverse && !haveImu) h = -h;
        h = wrap360(h);
        rawHeading = h;
        hx = 0.85f * hx + 0.15f * cosf(h / 57.2958f);
        hy = 0.85f * hy + 0.15f * sinf(h / 57.2958f);
        env.heading = wrap360(atan2f(hy, hx) * 57.2958f + hdgOffset);
        env.hasHeading = true;
      }
    }
  }

  // temperature, humidity, pressure every 2 s
  if (now - tSlow >= 2000) {
    tSlow = now;
    if (haveSht) {
      sensors_event_t hum, tmp;
      if (sht.getEvent(&hum, &tmp)) { env.tempC = tmp.temperature; env.rh = hum.relative_humidity; env.hasTH = true; }
      else { haveSht = false; env.hasTH = false; }
    }
    if (haveBmp) {
      if (bmp.performReading()) {
        env.hPa = bmp.pressure / 100.0f;
        env.hasP = true;
        if (!haveSht) { env.tempC = bmp.temperature; }  // rough air temperature if there's no SHT45
      } else { haveBmp = false; env.hasP = false; }
    }
  }

  // ammo probe: start a reading, collect it about a second later
  if (haveProbe && now - tAmmo >= 1000) {
    tAmmo = now;
    if (dallas->isConversionComplete()) {
      float c = dallas->getTempCByIndex(0);
      if (c > -100 && c < 125) { env.ammoC = c; env.hasAmmo = true; }
      else { haveProbe = false; env.hasAmmo = false; }
      dallas->requestTemperatures();
    }
  }
  env.compassCal = calibrating ? 1 : (env.compassCal == 1 ? 0 : env.compassCal);
}

void compassCalStart() {
  calibrating = true;
  calSamples = 0;
  env.compassCal = 1;
}

bool compassCalStop() {
  calibrating = false;
  if (calSamples < 30) { env.compassCal = pref.getBool("cal", false) ? 2 : 0; return false; }
  float span[3];
  for (int i = 0; i < 3; i++) span[i] = (mMax[i] - mMin[i]) / 2;
  // need a real turn: the horizontal axes should each have swung through a decent range
  if (span[0] < 5 || span[1] < 5) { env.compassCal = pref.getBool("cal", false) ? 2 : 0; return false; }
  // Scale against the two horizontal axes only. On a flat turn the vertical (Z) reading hardly
  // changes, so its min/max say nothing about Z's offset (its middle would just be Earth's vertical
  // field). Only update Z when it swung about as much as X and Y (the unit was tipped well over
  // during calibration); otherwise keep the Z values it already had.
  float avg = (span[0] + span[1]) / 2;
  bool zOk = span[2] >= 0.6f * avg;
  for (int i = 0; i < 3; i++) {
    if (i == 2 && !zOk) continue;
    mOff[i] = (mMax[i] + mMin[i]) / 2;
    mScl[i] = avg / span[i];
    char k[6];
    snprintf(k, sizeof(k), "o%d", i); pref.putFloat(k, mOff[i]);
    snprintf(k, sizeof(k), "s%d", i); pref.putFloat(k, mScl[i]);
  }
  pref.putBool("cal", true);
  env.compassCal = 2;
  return true;
}

void setHeadingOffset(float d) { hdgOffset = d; pref.putFloat("off", d); }
float headingOffset() { return hdgOffset; }
float headingRaw() { return rawHeading; }
void setHeadingReverse(bool r) {
  // the old offset was matched to the other direction: clear it (match the phone again)
  if (r != hdgReverse) { hdgOffset = 0; pref.putFloat("off", 0); }
  hdgReverse = r; pref.putBool("rev", r);
}
bool headingReverse() { return hdgReverse; }
void setImuRotation(int deg) {
  deg = ((deg % 360) + 360) % 360;
  if (deg != 0 && deg != 90 && deg != 180 && deg != 270) return;
  imuRot = deg; pref.putInt("irot", deg);
}
int imuRotation() { return imuRot; }

}  // namespace sensors
