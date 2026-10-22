// Radar chronograph signal processing (Teensy 4.1 and desktop test builds).
// Plain C++ with no Arduino calls, so the same file can be tested on a PC.
//
// How it works, in short:
//  1. The capture holds ~100 ms of the radar's I and Q outputs around a shot.
//  2. It is cut into overlapping 2048-sample frames. Each frame gets an FFT.
//  3. In every frame we look for the strongest narrow peak inside the velocity
//     band the user set (vmin..vmax). A bullet moving away gives one clean line.
//  4. Peaks from frame to frame are linked into a track (the bullet slowing down).
//  5. Each tracked frequency becomes a speed (f * wavelength / 2). Because the
//     radar sits beside the barrel, not on the bore line, each speed is divided
//     by the cosine of the angle to the bullet at that moment.
//  6. A straight line through speed vs time is extended back to the moment the
//     bullet left the muzzle. That is the muzzle velocity.
#pragma once
#include <stdint.h>

namespace rdsp {

constexpr int NFFT = 2048;      // samples per frame
constexpr int HOP = 512;        // frame step
constexpr int MAX_FRAMES = 256; // a 133 ms capture at 600 kS/s is 153 frames

struct Params {
  float fs = 600000.0f;       // sample rate, Hz (both channels; the firmware passes the measured rate)
  float f0 = 24.150e9f;       // radar transmit frequency, Hz (K-LC5 typical; 24.050-24.250 GHz)
  float calPpm = 0.0f;        // velocity correction, parts per million (+1000 = +0.1 %)
  float vminMps = 120.0f;     // ignore anything slower (m/s)
  float vmaxMps = 1600.0f;    // ignore anything faster (m/s)
  float snrMinDb = 12.0f;     // a peak must stand this far above the frame's median
  float lateralM = 0.10f;     // radar's sideways distance from the bore line (m)
  float behindM = 0.00f;      // radar's distance behind the muzzle (m); negative = in front
  float minDistM = 0.5f;      // ignore points closer than this to the muzzle (blast)
  float t0Sec = 0.0f;         // time the bullet left the muzzle, from capture start (s)
};

struct Peak {
  float t;      // frame centre time from capture start (s)
  float f;      // Doppler frequency (Hz)
  float snrDb;  // peak over median
  bool used;    // part of the final track
};

enum Code : int {
  OK = 0,
  NO_SIGNAL = 1,   // nothing stood out from the noise
  TOO_FEW = 2,     // a track, but too few points
  TOO_SHORT = 3,   // track too short in time
  NOISY = 4,       // points scatter too much around the fit
  OUT_OF_RANGE = 5 // result outside vmin..vmax
};

struct Result {
  int code = NO_SIGNAL;
  float v0Mps = 0;      // muzzle velocity (m/s)
  float accel = 0;      // m/s^2 (negative = slowing)
  int npts = 0;         // points in the track
  float spanMs = 0;     // time covered by the track
  float snrDb = 0;      // median SNR of the track
  float rmsMps = 0;     // scatter of points around the fit
  float d0 = 0, d1 = 0; // bullet's distance from the muzzle at first / last point (m)
  float vFirstMps = 0;  // speed at the first tracked point
  int nframes = 0;      // frames analysed
};

// Shared work memory (about 50 KB). Call begin() once.
class Processor {
 public:
  void begin();
  // I and Q: raw ADC samples (0..4095 at 12 bits), n samples each, starting at the same time.
  // peaksOut (optional, MAX_FRAMES long) receives every frame's peak for logging.
  Result analyze(const uint16_t* I, const uint16_t* Q, int n, const Params& p,
                 Peak* peaksOut = nullptr, int* npeaksOut = nullptr);
  static float halfWavelength(const Params& p);  // metres per Hz of Doppler
  // Strongest frequency (Hz) above fminHz in the last NFFT samples (for the bench readout).
  float peakHz(const uint16_t* I, const uint16_t* Q, float dcI, float dcQ, float fs, float fminHz);

 private:
  void fft(float* re, float* im);
  float win_[NFFT];
  float cos_[NFFT / 2];
  float sin_[NFFT / 2];
  uint16_t rev_[NFFT];
  float re_[NFFT];
  float im_[NFFT];
  float pw_[NFFT / 2];
  float tmp_[NFFT / 2];
  Peak peaks_[MAX_FRAMES];
};

}  // namespace rdsp
