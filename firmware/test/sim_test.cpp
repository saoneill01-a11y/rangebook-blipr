// Desktop test of radar_dsp: synthesises radar captures of a shot and checks the
// recovered muzzle velocity. Build: g++ -O2 -std=c++17 -I../BliprTeensy sim_test.cpp ../BliprTeensy/radar_dsp.cpp
#include "radar_dsp.h"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <vector>

struct Shot {
  double v0;        // m/s at the muzzle
  double accel;     // m/s^2 (negative)
  double lateral;   // radar offset from bore line (m)
  double behind;    // radar behind muzzle (m)
  double amp1m;     // echo amplitude (ADC counts) at 1 m
  double noise;     // noise per channel (counts rms)
  double blast;     // blast amplitude (counts)
  double f0;        // true radar frequency
  double t0Err;     // error in the muzzle-exit time given to the processor (s)
  double qGainDb;   // Q channel gain relative to I
};

static std::mt19937 rng(1234);

static void synth(const Shot& s, double fs, int n, int t0Sample, std::vector<uint16_t>& I, std::vector<uint16_t>& Q) {
  std::normal_distribution<double> g(0.0, 1.0);
  const double lam = 299792458.0 / s.f0;
  const double qg = pow(10.0, s.qGainDb / 20.0);
  I.resize(n); Q.resize(n);
  double blastLP = 0;
  for (int i = 0; i < n; i++) {
    double t = (i - t0Sample) / fs;
    double xi = 2048 + s.noise * g(rng), xq = 2048 + s.noise * g(rng);
    if (t >= 0) {
      double d = s.v0 * t + 0.5 * s.accel * t * t;
      double X = d + s.behind;
      double R = sqrt(X * X + s.lateral * s.lateral);
      double ph = 4 * M_PI * R / lam;
      // two-way spreading: amplitude ~ 1/R^2; beam falls off for the first few cm
      double a = s.amp1m / std::max(R * R, 0.04);
      if (R < 0.2) a *= R / 0.2;
      xi += a * cos(ph);
      xq += qg * a * sin(ph);
      // muzzle blast: broadband burst decaying over ~2 ms, plus a low thump
      double env = s.blast * exp(-t / 0.002);
      blastLP = 0.9 * blastLP + 0.1 * g(rng);
      xi += env * (0.6 * g(rng) + 3.0 * blastLP);
      xq += env * (0.6 * g(rng) + 3.0 * blastLP);
    }
    I[i] = (uint16_t)std::min(4095.0, std::max(0.0, round(xi)));
    Q[i] = (uint16_t)std::min(4095.0, std::max(0.0, round(xq)));
  }
}

int main(int argc, char** argv) {
  const double fs = 600000.0;  // the firmware default
  const int n = 78 * 1024;
  const int t0Sample = 12 * 1024 + 300;
  static rdsp::Processor proc;
  proc.begin();

  struct Case { const char* name; Shot s; };
  std::vector<Case> cases = {
    {"6.5CM 2700 fps, strong", {2700 * 0.3048, -320, 0.12, 0.15, 3000, 14, 1500, 24.150e9, 0, -2}},
    {"6.5CM 2700 fps, medium echo", {2700 * 0.3048, -320, 0.12, 0.15, 800, 14, 1500, 24.150e9, 0, -2}},
    {"6.5CM 2700 fps, weak echo", {2700 * 0.3048, -320, 0.12, 0.15, 250, 14, 1500, 24.150e9, 0, -2}},
    {"6.5CM 2700 fps, very weak", {2700 * 0.3048, -320, 0.12, 0.15, 90, 14, 1500, 24.150e9, 0, -2}},
    {"223 3100 fps, high drag", {3100 * 0.3048, -600, 0.10, 0.10, 400, 14, 1200, 24.150e9, 0, -2}},
    {"308 2600 fps", {2600 * 0.3048, -280, 0.15, 0.20, 800, 14, 2000, 24.150e9, 0, -2}},
    {"9mm 1150 fps", {1150 * 0.3048, -150, 0.12, 0.10, 500, 14, 1500, 24.150e9, 0, -2}},
    {"22LR 1050 fps", {1050 * 0.3048, -120, 0.10, 0.05, 150, 14, 300, 24.150e9, 0, -2}},
    {"300 BLK sub 1020 fps", {1020 * 0.3048, -100, 0.12, 0.15, 900, 14, 2500, 24.150e9, 0, -2}},
    {"6.5CM, t0 1 ms late", {2700 * 0.3048, -320, 0.12, 0.15, 800, 14, 1500, 24.150e9, 0.001, -2}},
    {"6.5CM, radar 24.20 GHz (uncalibrated)", {2700 * 0.3048, -320, 0.12, 0.15, 800, 14, 1500, 24.20e9, 0, -2}},
    {"6.5CM, radar 0.4 m in front", {2700 * 0.3048, -320, 0.12, -0.40, 800, 14, 1500, 24.150e9, 0, -2}},
  };

  printf("%-40s %9s %9s %7s %5s %7s %6s %6s %5s\n", "case", "true fps", "got fps", "err", "pts", "spanms", "snr", "rms", "code");
  for (auto& c : cases) {
    int trials = 5;
    for (int tr = 0; tr < trials; tr++) {
      std::vector<uint16_t> I, Q;
      synth(c.s, fs, n, t0Sample, I, Q);
      rdsp::Params p;
      p.fs = (float)fs;
      p.lateralM = (float)c.s.lateral;
      p.behindM = (float)c.s.behind;
      p.t0Sec = (float)((t0Sample) / fs + c.s.t0Err);
      p.vminMps = 100; p.vmaxMps = 1500;
      rdsp::Result r = proc.analyze(I.data(), Q.data(), n, p);
      double trueFps = c.s.v0 / 0.3048, got = r.v0Mps / 0.3048;
      printf("%-40s %9.1f %9.1f %7.1f %5d %7.1f %6.1f %6.2f %5d\n", tr == 0 ? c.name : "", trueFps, got,
             got - trueFps, r.npts, r.spanMs, r.snrDb, r.rmsMps, r.code);
    }
  }
  // Noise only: must not report a shot
  {
    Shot s{0, 0, 0.1, 0, 0, 14, 1500, 24.150e9, 0, 0};
    int falses = 0;
    for (int tr = 0; tr < 20; tr++) {
      std::vector<uint16_t> I, Q;
      synth(s, fs, n, t0Sample, I, Q);
      rdsp::Params p; p.fs = (float)fs; p.t0Sec = (float)(t0Sample / fs); p.vminMps = 100; p.vmaxMps = 1500;
      rdsp::Result r = proc.analyze(I.data(), Q.data(), n, p);
      if (r.code == rdsp::OK) { falses++; printf("FALSE SHOT %.1f fps pts %d span %.1f snr %.1f rms %.2f acc %.0f d0 %.1f d1 %.1f\n", r.v0Mps / 0.3048, r.npts, r.spanMs, r.snrDb, r.rmsMps, r.accel, r.d0, r.d1); }
    }
    printf("blast-only captures reported as shots: %d / 20\n", falses);
  }
  return 0;
}
