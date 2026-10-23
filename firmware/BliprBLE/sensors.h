// Optional add-on sensors for BLIPR (ESP32-C3). Each one is found
// automatically at start-up; anything not plugged in is simply skipped.
//   SHT45   temperature + humidity      I2C 0x44
//   DFRobot Gravity 10-DoF IMU (SEN0696): compass + level + BMP581 pressure, I2C 0x4A (0x4B-0x4D)
//           (the 9-DoF SEN0694 works too, without pressure). Recommended from firmware 0.2.3.
//   BMP390  air pressure                I2C 0x77 (or 0x76)     used if there's no 10-DoF board
//   LSM6DSOX accelerometer (level)      I2C 0x6A (or 0x6B)     the earlier Adafruit IMU, still supported
//   LIS3MDL magnetometer (compass)      I2C 0x1C (or 0x1E)
//   DS18B20 ammo temperature probe      1-Wire on GPIO10 (4.7k pull-up to 3V3)
#pragma once
#include <Arduino.h>

struct EnvReading {
  bool hasTH = false, hasP = false, hasAmmo = false, hasHeading = false, hasLevel = false;
  float tempC = 0, rh = 0;      // air
  float hPa = 0;                // station pressure
  float ammoC = 0;              // probe
  float heading = 0;            // degrees, 0 = north (magnetic, plus your offset)
  float pitch = 0, roll = 0;    // degrees; 0,0 = sitting level
  int compassCal = 0;           // 0 = never calibrated, 1 = calibrating now, 2 = calibrated
};

namespace sensors {
void begin(int pinOneWire);
void update();               // call often; it paces itself
const EnvReading& get();
String letters();            // e.g. "THPAC" for what's fitted
// Compass calibration: start, then turn the chronograph slowly through a full circle, then stop.
// The vertical axis is only recalibrated if the unit was also tipped well over (nose up and down,
// side to side) during the turn; otherwise its previous calibration is kept.
void compassCalStart();
bool compassCalStop();       // false if it didn't see enough turning
void setHeadingOffset(float deg);   // added to the raw heading
float headingRaw();          // heading before the offset
void setHeadingReverse(bool r);   // mirror the heading (if it goes down when the unit turns clockwise)
float headingOffset();
bool headingReverse();
void setImuRotation(int deg);   // 0/90/180/270: how far the IMU board is turned COUNTER-CLOCKWISE (seen from above) on its mount
int imuRotation();
}
