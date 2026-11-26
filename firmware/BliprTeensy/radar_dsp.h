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
constexpr int HOP = 256;        // frame step (512 before Teensy 0.2.8: a .22 echo lasts only ~6 ms)
constexpr int MAX_FRAMES = 384; // a 160 ms capture at 500 kS/s with HOP 256 is 305 frames (133 ms at 600k: 305)
constexpr float SHORT_TRACK_MS = 6.0f;   // shorter tracks (a .22: 3-5 ms) get an assumed slow-down instead of a fitted one
constexpr float SHORT_TRACK_SNR = 14.0f;  // a track shorter than 3 ms / 2 m must be at least this strong (median dB), among other things
constexpr float LOOKBACK_SEC = 0.010f;   // analyze() looks this far before t0Sec for the bullet (the trigger can be late)

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
  float confirmDb = 11.0f;    // quick check after a trigger: a line this far above the pre-trigger level and the frame median...
  int confirmNeed = 2;        // ...in at least this many of the CONFIRM_FRAMES frames just after it, agreeing on the frequency
  bool lineReject = true;     // analyze(): a line already there before the trigger can't be the bullet
  float fadeMinDb = 6.0f;     // analyze(): a track that runs to the end of the capture must have faded this many dB from its
                              // near third to its far third (a bullet's echo does); otherwise it's a steady line. 0 = don't check
};

// Quick check after a trigger (Processor::confirm): frames of NFFT samples, CONFIRM_STEP apart.
constexpr int CONFIRM_STEP = 1024;
constexpr int CONFIRM_FIRST = 0;    // first frame starts this many steps after the trigger (0.2.4 and before: 2, which missed weak echoes)
constexpr int CONFIRM_FRAMES = 6;   // frames CONFIRM_FIRST.. on, so (CONFIRM_FIRST + CONFIRM_FRAMES + 1) steps are needed after it

struct Confirm {
  int hits = 0;       // frames with the line
  float bestDb = 0;   // strongest line over the pre-trigger level
  float f = 0;        // its frequency (Hz)
  int refFrames = 0;  // pre-trigger frames used as the reference
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
  OUT_OF_RANGE = 5, // result outside vmin..vmax
  STEADY_LINE = 6   // interference, not a bullet: a track that doesn't fade with distance, or starts far from the muzzle
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
  // Is there a bullet-like line right after a trigger? I and Q start some samples before the trigger (trigSample)
  // and run at least (CONFIRM_FIRST + CONFIRM_FRAMES + 1) * CONFIRM_STEP samples past it. True: go ahead with the full capture.
  bool confirm(const uint16_t* I, const uint16_t* Q, int n, int trigSample, const Params& p, Confirm* out = nullptr);
  void (*idle)() = nullptr;   // called between FFT frames in confirm() (the firmware keeps its ADC buffers emptied)
  // In-band trigger (0.2.5 on). One NFFT-sample frame made of two halves (I0/Q0 then I1/Q1, NFFT/2 samples each: the
  // firmware's last two blocks). Each bin kmin..kmax is compared with the larger of its own running average (avg[],
  // NFFT/2 long, kept by the caller) and the average of its neighbouring bins; returns the best ratio in dB, its bin in *kOut.
  // avg[] then moves toward this frame by alpha (each bin's step clipped to 4x its level, so a shot barely moves it).
  float bandScan(const uint16_t* I0, const uint16_t* Q0, const uint16_t* I1, const uint16_t* Q1, float dcI, float dcQ,
                 int kmin, int kmax, float* avg, float alpha, int* kOut);
  static void bandBins(const Params& p, int& kmin, int& kmax);   // FFT bins of the velocity window
  // Bench readout ("live <Hz>"): strongest line above fminHz (*fOut, Hz) and its level over the median of the bins above
  // fminHz (dB, returned); *atDb gets the level at atHz (+-2 bins, 0 = skip) the same way.
  float lineScan(const uint16_t* I, const uint16_t* Q, float dcI, float dcQ, float fs, float fminHz, float atHz,
                 float* fOut, float* atDb);
  // Strongest frequency (Hz) above fminHz in the last NFFT samples (for the bench readout).
  float peakHz(const uint16_t* I, const uint16_t* Q, float dcI, float dcQ, float fs, float fminHz);

 private:
  void fft(float* re, float* im);
  void localFloor(int kmin, int kmax);   // loc_[k]: neighbouring bins' average power
  float win_[NFFT];
  float cos_[NFFT / 2];
  float sin_[NFFT / 2];
  uint16_t rev_[NFFT];
  float re_[NFFT];
  float im_[NFFT];
  float pw_[NFFT / 2];
  float tmp_[NFFT / 2];
  float ref_[NFFT / 2];
  float loc_[NFFT / 2];
  Peak peaks_[MAX_FRAMES];
};

}  // namespace rdsp
