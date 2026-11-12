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
// Extra interference (set before synth): a steady line present the whole time, and a short burst at the trigger
// like the ESP32's Bluetooth bursts on the first build (2-4 ms, broadband, mostly low-pitched).
static double gLineHz = 0, gLineAmp = 0, gBurstMs = 0, gBurstWhite = 0, gBurstLow = 0;

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
    if (gLineAmp > 0) { double ph = 2 * M_PI * gLineHz * i / fs; xi += gLineAmp * cos(ph); xq += gLineAmp * sin(ph); }
    if (gBurstMs > 0 && t >= 0 && t < gBurstMs * 1e-3) {
      static double lp = 0;
      lp = 0.97 * lp + 0.03 * g(rng);
      double lo = gBurstLow * lp * 8.0;
      xi += gBurstWhite * g(rng) + lo;
      xq += gBurstWhite * g(rng) + 0.7 * lo;
    }
    I[i] = (uint16_t)std::min(4095.0, std::max(0.0, round(xi)));
    Q[i] = (uint16_t)std::min(4095.0, std::max(0.0, round(xq)));
  }
}

int main(int argc, char** argv) {
  const double fs = argc > 1 ? atof(argv[1]) : 600000.0;  // the firmware default; "sim_test 500000" tries another rate
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

  printf("%-40s %9s %9s %7s %5s %7s %6s %6s %5s %s\n", "case", "true fps", "got fps", "err", "pts", "spanms", "snr", "rms", "code", "confirm(hits,dB)");
  const int trigSample = (t0Sample / 1024) * 1024;   // the firmware checks from the start of the trigger block
  int confirmMiss = 0;
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
      rdsp::Confirm cf;
      bool ok = proc.confirm(I.data(), Q.data(), n, trigSample, p, &cf);
      rdsp::Result r = proc.analyze(I.data(), Q.data(), n, p);
      if (!ok && r.code == rdsp::OK) confirmMiss++;
      double trueFps = c.s.v0 / 0.3048, got = r.v0Mps / 0.3048;
      printf("%-40s %9.1f %9.1f %7.1f %5d %7.1f %6.1f %6.2f %5d %s(%d,%.1f)\n", tr == 0 ? c.name : "", trueFps, got,
             got - trueFps, r.npts, r.spanMs, r.snrDb, r.rmsMps, r.code, ok ? "yes" : "NO ", cf.hits, cf.bestDb);
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
  printf("measured shots the quick check would have thrown away: %d\n", confirmMiss);
  // Quick check on captures with no bullet: must reject (blast only, Bluetooth-like bursts, a steady line)
  {
    struct NB { const char* name; double lineAmp, burstMs, white, low, blast; };
    NB nbs[] = {{"blast only", 0, 0, 0, 0, 1500},
                {"burst 3 ms", 0, 3, 40, 60, 0},
                {"burst 2 ms, strong", 0, 2, 80, 150, 0},
                {"steady line 94 kHz + burst", 4, 3, 40, 60, 0},
                {"steady line 94 kHz, strong + burst", 12, 3, 40, 60, 0}};
    for (auto& b : nbs) {
      int pass = 0;
      float worst = -99;
      for (int tr = 0; tr < 50; tr++) {
        gLineHz = 94300; gLineAmp = b.lineAmp; gBurstMs = b.burstMs; gBurstWhite = b.white; gBurstLow = b.low;
        Shot s{0, 0, 0.1, 0, 0, 14, b.blast, 24.150e9, 0, 0};
        std::vector<uint16_t> I, Q;
        synth(s, fs, n, t0Sample, I, Q);
        rdsp::Params p; p.fs = (float)fs; p.vminMps = 300 * 0.3048; p.vmaxMps = 4500 * 0.3048;
        rdsp::Confirm cf;
        if (proc.confirm(I.data(), Q.data(), n, trigSample, p, &cf)) pass++;
        if (cf.bestDb > worst) worst = cf.bestDb;
      }
      printf("no bullet, %-36s quick check passed %d / 50 (strongest line %.1f dB)\n", b.name, pass, worst);
    }
    // ...and a real bullet with the steady line and a burst on top must still pass
    int pass = 0;
    for (int tr = 0; tr < 20; tr++) {
      gLineHz = 94300; gLineAmp = 12; gBurstMs = 3; gBurstWhite = 40; gBurstLow = 60;
      Shot s{2700 * 0.3048, -320, 0.12, 0.15, 250, 14, 1500, 24.150e9, 0, -2};
      std::vector<uint16_t> I, Q;
      synth(s, fs, n, t0Sample, I, Q);
      rdsp::Params p; p.fs = (float)fs; p.lateralM = 0.12f; p.behindM = 0.15f; p.vminMps = 300 * 0.3048; p.vmaxMps = 4500 * 0.3048;
      if (proc.confirm(I.data(), Q.data(), n, trigSample, p)) pass++;
    }
    printf("weak-echo bullet with steady line and burst: quick check passed %d / 20\n", pass);
    gLineAmp = 0; gBurstMs = 0;
  }

  // ---- Trigger (firmware 0.2.5 on: in-band, rdsp::Processor::bandScan) compared with the old whole-block energy trigger ----
  // Each capture is run block by block as the firmware does: learn on the first 8 blocks, then look for a trigger.
  const double bandDb = argc > 2 ? atof(argv[2]) : 12.0, oldDb = 9.0;
  static float avg[rdsp::NFFT / 2];
  auto trig = [&](const std::vector<uint16_t>& I, const std::vector<uint16_t>& Q, const rdsp::Params& p, int fromB, int toB,
                  int& bandHit, int& oldHit, float& bandMax) {
    const int B = rdsp::NFFT / 2, nb = (int)I.size() / B;
    int k0, k1;
    rdsp::Processor::bandBins(p, k0, k1);
    for (auto& a : avg) a = 0;
    double floorE = 0;
    bandHit = oldHit = -1; bandMax = -99;
    for (int b = 1; b < nb && b <= toB; b++) {
      double s2 = 0;
      for (int i = 0; i < B; i++) { double a = I[b * B + i] - 2048.0, q = Q[b * B + i] - 2048.0; s2 += a * a + q * q; }
      int kb;
      float db = proc.bandScan(&I[(b - 1) * B], &Q[(b - 1) * B], &I[b * B], &Q[b * B], 2048, 2048, k0, k1, avg,
                               b < 8 ? 0.125f : 1.0f / 64, &kb);
      if (b < 8) { floorE = b == 1 ? s2 : 0.7 * floorE + 0.3 * s2; continue; }
      if (b < fromB) { if (s2 < 2 * floorE) floorE = 0.99 * floorE + 0.01 * s2; continue; }
      if (db > bandMax) bandMax = db;
      if (bandHit < 0 && db > bandDb) bandHit = b;
      if (oldHit < 0 && 10 * log10(s2 / floorE) > oldDb) oldHit = b;
      if (s2 < 2 * floorE) floorE = 0.99 * floorE + 0.01 * s2;
    }
  };
  printf("\nTrigger: in-band at %.1f dB vs the old whole-block trigger at %.0f dB (trials that fired within 2 blocks of the shot)\n", bandDb, oldDb);
  printf("%-34s %8s %8s %9s %9s %9s\n", "22LR 1067 fps, noise 8 counts", "in-band", "old", "quick chk", "reads ok", "all three");
  for (double amp : {3.0, 5.0, 8.0, 12.0, 20.0, 40.0}) {
    int nb = 0, no = 0, nq = 0, nr = 0, nall = 0;
    const int T = 20;
    for (int tr = 0; tr < T; tr++) {
      Shot s{1067 * 0.3048, -120, 0.10, 0.10, amp, 8, 0, 24.150e9, 0, 0};
      std::vector<uint16_t> I, Q;
      synth(s, fs, n, t0Sample, I, Q);
      rdsp::Params p; p.fs = (float)fs; p.lateralM = 0.10f; p.behindM = 0.10f; p.t0Sec = (float)(t0Sample / fs);
      p.vminMps = 600 * 0.3048f; p.vmaxMps = 1800 * 0.3048f;
      int bh, oh; float bm;
      trig(I, Q, p, 9, t0Sample / 1024 + 2, bh, oh, bm);
      bool b = bh >= t0Sample / 1024, o = oh >= t0Sample / 1024;
      bool q = proc.confirm(I.data(), Q.data(), n, trigSample, p);
      bool r = proc.analyze(I.data(), Q.data(), n, p).code == rdsp::OK;
      nb += b; no += o; nq += q; nr += r; nall += b && q && r;
    }
    char lab[40]; snprintf(lab, sizeof(lab), "  echo %.0f counts at 1 m", amp);
    printf("%-34s %5d/%d %5d/%d %6d/%d %6d/%d %6d/%d\n", lab, nb, T, no, T, nq, T, nr, T, nall, T);
  }
  // No bullet: how often each trigger fires on 160 ms of noise with interference (window 300-4500 fps)
  {
    struct NB { const char* name; double lineAmp, burstMs, white, low; };
    NB nbs[] = {{"noise only", 0, 0, 0, 0}, {"burst 3 ms", 0, 3, 40, 60}, {"burst 2 ms, strong", 0, 2, 80, 150},
                {"steady line 94 kHz (12 counts)", 12, 0, 0, 0}, {"steady line 94 kHz + burst", 12, 3, 40, 60}};
    printf("%-34s %8s %8s %12s\n", "no bullet, 160 ms captures", "in-band", "old", "in-band max");
    for (auto& b : nbs) {
      int nb2 = 0, no2 = 0;
      float worst = -99;
      for (int tr = 0; tr < 50; tr++) {
        gLineHz = 94300; gLineAmp = b.lineAmp; gBurstMs = b.burstMs; gBurstWhite = b.white; gBurstLow = b.low;
        Shot s{0, 0, 0.1, 0, 0, 8, 0, 24.150e9, 0, 0};
        std::vector<uint16_t> I, Q;
        synth(s, fs, n, t0Sample, I, Q);
        rdsp::Params p; p.fs = (float)fs; p.vminMps = 300 * 0.3048f; p.vmaxMps = 4500 * 0.3048f;
        int bh, oh; float bm;
        trig(I, Q, p, 9, 1000, bh, oh, bm);
        nb2 += bh >= 0; no2 += oh >= 0;
        if (bm > worst) worst = bm;
      }
      printf("  %-32s %5d/50 %5d/50 %9.1f dB\n", b.name, nb2, no2, worst);
    }
    gLineAmp = 0; gBurstMs = 0;
  }
  // Line rejection in analyze(): a steady line inside the window, stronger than the bullet's far echo
  {
    int okB = 0, lineB = 0;
    for (int tr = 0; tr < 20; tr++) {
      gLineHz = 94300; gLineAmp = 6;
      Shot s{2700 * 0.3048, -320, 0.12, 0.15, 250, 14, 1500, 24.150e9, 0, -2};
      std::vector<uint16_t> I, Q;
      synth(s, fs, n, t0Sample, I, Q);
      rdsp::Params p; p.fs = (float)fs; p.lateralM = 0.12f; p.behindM = 0.15f; p.t0Sec = (float)(t0Sample / fs);
      p.vminMps = 300 * 0.3048f; p.vmaxMps = 4500 * 0.3048f;
      rdsp::Result r = proc.analyze(I.data(), Q.data(), n, p);
      if (r.code == rdsp::OK && fabs(r.v0Mps / 0.3048 - 2700) < 10) okB++;
      if (r.code == rdsp::OK && fabs(r.v0Mps / 0.3048 - 2700) >= 10) lineB++;
    }
    printf("weak-echo bullet with a steady 94 kHz line in the window: read the bullet %d / 20, read the line %d / 20\n", okB, lineB);
    // a line that starts at the trigger and runs to the end (the phone connecting): must not read as a shot
    int falseL = 0;
    for (int tr = 0; tr < 20; tr++) {
      gLineAmp = 0;
      Shot s{0, 0, 0.1, 0, 0, 14, 0, 24.150e9, 0, 0};
      std::vector<uint16_t> I, Q;
      synth(s, fs, n, t0Sample, I, Q);
      std::normal_distribution<double> g(0.0, 1.0);
      double ph = 0;
      for (int i = t0Sample; i < n; i++) {   // 114 kHz line, 20 counts, with a slow wander
        ph += 2 * M_PI * (114000 + 30 * sin(i / fs * 40)) / fs;
        I[i] = (uint16_t)std::min(4095.0, I[i] + 20 * cos(ph)); Q[i] = (uint16_t)std::min(4095.0, Q[i] + 20 * sin(ph));
      }
      rdsp::Params p; p.fs = (float)fs; p.t0Sec = (float)(t0Sample / fs); p.vminMps = 300 * 0.3048f; p.vmaxMps = 4500 * 0.3048f;
      rdsp::Result r = proc.analyze(I.data(), Q.data(), n, p);
      if (r.code == rdsp::OK) falseL++;
    }
    printf("a line starting at the trigger and running to the end (phone connecting): read as a shot %d / 20\n", falseL);
    gLineAmp = 0;
  }
  return 0;
}
