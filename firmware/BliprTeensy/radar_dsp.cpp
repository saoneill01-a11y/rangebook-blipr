// Radar chronograph signal processing. See radar_dsp.h for the overview.
#include "radar_dsp.h"
#include <math.h>
#include <string.h>
#include <algorithm>

namespace rdsp {

static constexpr float kPi = 3.14159265358979f;
static constexpr double kC = 299792458.0;  // speed of light, m/s

float Processor::halfWavelength(const Params& p) {
  // metres of travel per Hz of Doppler, with the user's calibration applied
  return (float)(kC / (2.0 * (double)p.f0) * (1.0 + (double)p.calPpm * 1e-6));
}

void Processor::begin() {
  for (int i = 0; i < NFFT; i++) win_[i] = 0.5f - 0.5f * cosf(2 * kPi * i / NFFT);  // Hann
  for (int i = 0; i < NFFT / 2; i++) {
    cos_[i] = cosf(2 * kPi * i / NFFT);
    sin_[i] = -sinf(2 * kPi * i / NFFT);
  }
  int bits = 0;
  while ((1 << bits) < NFFT) bits++;
  for (int i = 0; i < NFFT; i++) {
    int r = 0;
    for (int b = 0; b < bits; b++)
      if (i & (1 << b)) r |= 1 << (bits - 1 - b);
    rev_[i] = (uint16_t)r;
  }
}

// In-place radix-2 complex FFT.
void Processor::fft(float* re, float* im) {
  for (int i = 0; i < NFFT; i++) {
    int j = rev_[i];
    if (j > i) {
      float t = re[i]; re[i] = re[j]; re[j] = t;
      t = im[i]; im[i] = im[j]; im[j] = t;
    }
  }
  for (int len = 2; len <= NFFT; len <<= 1) {
    int half = len >> 1;
    int step = NFFT / len;
    for (int i = 0; i < NFFT; i += len) {
      for (int k = 0; k < half; k++) {
        float wr = cos_[k * step], wi = sin_[k * step];
        int a = i + k, b = a + half;
        float xr = re[b] * wr - im[b] * wi;
        float xi = re[b] * wi + im[b] * wr;
        re[b] = re[a] - xr; im[b] = im[a] - xi;
        re[a] += xr;        im[a] += xi;
      }
    }
  }
}

float Processor::peakHz(const uint16_t* I, const uint16_t* Q, float dcI, float dcQ, float fs, float fminHz) {
  for (int i = 0; i < NFFT; i++) {
    re_[i] = ((float)I[i] - dcI) * win_[i];
    im_[i] = ((float)Q[i] - dcQ) * win_[i];
  }
  fft(re_, im_);
  int k0 = (int)(fminHz / fs * NFFT);
  if (k0 < 1) k0 = 1;
  int best = k0;
  float bp = 0;
  for (int k = k0; k < NFFT / 2; k++) {
    int m = NFFT - k;
    float pw = re_[k] * re_[k] + im_[k] * im_[k] + re_[m] * re_[m] + im_[m] * im_[m];
    if (pw > bp) { bp = pw; best = k; }
  }
  return best * fs / NFFT;
}

// Least-squares line y = a + b*x, optionally weighted. Returns false if degenerate.
static bool fitLine(const float* x, const float* y, const float* w, int n, float& a, float& b) {
  double sw = 0, sx = 0, sy = 0, sxx = 0, sxy = 0;
  for (int i = 0; i < n; i++) {
    double wi = w ? w[i] : 1.0;
    sw += wi; sx += wi * x[i]; sy += wi * y[i];
    sxx += wi * x[i] * x[i]; sxy += wi * x[i] * y[i];
  }
  double den = sw * sxx - sx * sx;
  if (sw <= 0 || fabs(den) < 1e-30) return false;
  b = (float)((sw * sxy - sx * sy) / den);
  a = (float)((sy - b * sx) / sw);
  return true;
}

Result Processor::analyze(const uint16_t* I, const uint16_t* Q, int n, const Params& p,
                          Peak* peaksOut, int* npeaksOut) {
  Result r;
  const float hw = halfWavelength(p);  // m/s per Hz
  // DC level of each channel (the amplifier idles at mid-scale)
  double si = 0, sq = 0;
  for (int i = 0; i < n; i++) { si += I[i]; sq += Q[i]; }
  const float mi = (float)(si / n), mq = (float)(sq / n);

  int kmin = (int)floorf(p.vminMps / hw / p.fs * NFFT);
  int kmax = (int)ceilf(p.vmaxMps / hw / p.fs * NFFT);
  if (kmin < 3) kmin = 3;
  if (kmax > NFFT / 2 - 3) kmax = NFFT / 2 - 3;
  if (kmax <= kmin + 4) { r.code = NO_SIGNAL; return r; }

  // ---- 1-3: frame peaks ----
  int nf = 0;
  for (int start = 0; start + NFFT <= n && nf < MAX_FRAMES; start += HOP) {
    for (int i = 0; i < NFFT; i++) {
      re_[i] = ((float)I[start + i] - mi) * win_[i];
      im_[i] = ((float)Q[start + i] - mq) * win_[i];
    }
    fft(re_, im_);
    // Packing I as real and Q as imaginary lets one FFT serve both channels.
    // Their combined power at bin k is (|Z[k]|^2 + |Z[N-k]|^2) / 2, which is the
    // same whichever way the bullet's I/Q phase turns, so wiring order doesn't matter.
    for (int k = kmin - 1; k <= kmax + 1; k++) {
      int m = NFFT - k;
      pw_[k] = 0.5f * (re_[k] * re_[k] + im_[k] * im_[k] + re_[m] * re_[m] + im_[m] * im_[m]);
    }
    int cnt = kmax - kmin + 1, best = kmin;
    for (int k = kmin; k <= kmax; k++) {
      tmp_[k - kmin] = pw_[k];
      if (pw_[k] > pw_[best]) best = k;
    }
    std::nth_element(tmp_, tmp_ + cnt / 2, tmp_ + cnt);
    float med = tmp_[cnt / 2];
    Peak& pk = peaks_[nf];
    pk.t = (start + NFFT * 0.5f) / p.fs;
    pk.used = false;
    if (med <= 0 || pw_[best] <= 0) { pk.f = 0; pk.snrDb = 0; nf++; continue; }
    pk.snrDb = 10.0f * log10f(pw_[best] / med);
    // Sub-bin position from a parabola through the log power of the peak and its neighbours
    float a = logf(pw_[best - 1] + 1e-12f), b = logf(pw_[best] + 1e-12f), c = logf(pw_[best + 1] + 1e-12f);
    float den = a - 2 * b + c, d = 0;
    if (den < 0) d = 0.5f * (a - c) / den;
    if (d > 0.5f) d = 0.5f;
    if (d < -0.5f) d = -0.5f;
    pk.f = (best + d) * p.fs / NFFT;
    nf++;
  }
  r.nframes = nf;

  // ---- 4: link peaks into a track ----
  // Try the strongest few peaks as starting points. From each, walk forwards and
  // backwards, accepting a frame's peak if it is close to where the track was heading
  // (short gaps allowed). Keep the longest track. Trying several starts matters: the
  // strongest peak is often right at the muzzle, where blast and the changing angle
  // make the frequency jump about.
  const float binHz = p.fs / NFFT;
  const float dt = HOP / p.fs;
  const int maxGap = 6;               // frames
  const float maxRate = 2500.0f / hw; // Hz per second (2500 m/s^2 covers drag plus the angle effect)
  static bool cur[MAX_FRAMES], best[MAX_FRAMES];
  int bestCount = 0;
  float bestScore = -1;
  int tried = 0;
  static bool triedSeed[MAX_FRAMES];
  for (int i = 0; i < nf; i++) triedSeed[i] = false;
  while (tried < 8) {
    int seed = -1;
    for (int i = 0; i < nf; i++)
      if (!triedSeed[i] && peaks_[i].snrDb >= p.snrMinDb && peaks_[i].t >= p.t0Sec &&
          (seed < 0 || peaks_[i].snrDb > peaks_[seed].snrDb))
        seed = i;
    if (seed < 0) break;
    triedSeed[seed] = true;
    tried++;
    for (int i = 0; i < nf; i++) cur[i] = false;
    cur[seed] = true;
    int count = 1;
    float score = peaks_[seed].snrDb;
    for (int dir = -1; dir <= 1; dir += 2) {
      int last = seed, gap = 0, nInDir = 0;
      float slope = 0;  // Hz per frame, learned as the track grows
      for (int i = seed + dir; i >= 0 && i < nf; i += dir) {
        int steps = (i - last) * dir;
        float pred = peaks_[last].f + slope * (float)(i - last);
        float tol = 2.0f * binHz + maxRate * dt * steps * 0.5f + (nInDir < 2 ? 2.0f * binHz : 0.0f);
        if (peaks_[i].snrDb >= p.snrMinDb - 3.0f && fabsf(peaks_[i].f - pred) <= tol &&
            peaks_[i].t >= p.t0Sec) {
          float newSlope = (peaks_[i].f - peaks_[last].f) / (float)(i - last);
          slope = (nInDir == 0) ? newSlope * 0.5f : 0.7f * slope + 0.3f * newSlope;
          cur[i] = true;
          count++;
          score += peaks_[i].snrDb;
          last = i; gap = 0; nInDir++;
        } else if (++gap > maxGap) {
          break;
        }
      }
    }
    if (count > bestCount || (count == bestCount && score > bestScore)) {
      bestCount = count; bestScore = score;
      for (int i = 0; i < nf; i++) best[i] = cur[i];
    }
    // A seed already inside the best track would only find the same track again
    for (int i = 0; i < nf; i++) if (cur[i]) triedSeed[i] = true;
  }
  if (bestCount == 0) {
    if (peaksOut) { memcpy(peaksOut, peaks_, sizeof(Peak) * nf); *npeaksOut = nf; }
    r.code = NO_SIGNAL;
    return r;
  }
  for (int i = 0; i < nf; i++) peaks_[i].used = best[i];

  // ---- 5-6: speeds, angle correction, fit back to the muzzle ----
  static float tt[MAX_FRAMES], vr[MAX_FRAMES], ww[MAX_FRAMES], snr[MAX_FRAMES];
  int m = 0;
  for (int i = 0; i < nf; i++) {
    if (!peaks_[i].used) continue;
    tt[m] = peaks_[i].t - p.t0Sec;  // time since the bullet left the muzzle
    vr[m] = peaks_[i].f * hw;       // speed toward/away from the radar
    snr[m] = peaks_[i].snrDb;
    float lin = powf(10.0f, peaks_[i].snrDb / 10.0f);
    ww[m] = lin > 1000.0f ? 1000.0f : lin;  // trust strong points more, within reason
    m++;
  }
  if (peaksOut) { memcpy(peaksOut, peaks_, sizeof(Peak) * nf); *npeaksOut = nf; }
  if (m < 3) { r.code = TOO_FEW; r.npts = m; return r; }

  float v0 = 0, acc = 0;
  if (!fitLine(tt, vr, ww, m, v0, acc)) { r.code = TOO_FEW; return r; }
  static float tx[MAX_FRAMES], vy[MAX_FRAMES], wy[MAX_FRAMES], dist[MAX_FRAMES];
  int k = 0;
  // Each frame's frequency is an average over its window (NFFT / fs: 3.4 ms at 600 kS/s). Close to the muzzle
  // the echo gets much weaker within one window (it falls off as 1/R^2) and the angle
  // changes, so the average leans toward the start of the window. Using the current
  // fit, work out what the frame should have measured and scale the reading by
  // (true speed at the frame centre) / (expected averaged reading).
  const float winSec = NFFT / p.fs;
  auto corrFactor = [&](float tc, float sMid) -> float {
    const int J = 16;
    double num = 0, den = 0;
    for (int j = 0; j < J; j++) {
      float u = (j + 0.5f) / J;                       // 0..1 across the window
      float tj = tc + (u - 0.5f) * winSec;
      if (tj <= 0) continue;
      float sj = v0 * tj + 0.5f * acc * tj * tj;
      float X = sj + p.behindM;
      float R2 = X * X + p.lateralM * p.lateralM;
      if (X <= 0.02f) continue;
      float hann = 0.5f - 0.5f * cosf(2 * 3.14159265f * u);
      float w = hann * hann / (R2 * R2);              // echo power ~ 1/R^4
      float c = X / sqrtf(R2);
      num += w * (v0 + acc * tj) * c;
      den += w;
    }
    if (den <= 0) return 1.0f;
    float measured = (float)(num / den);
    float truth = v0 + acc * tc;
    (void)sMid;
    return measured > 1.0f ? truth / measured : 1.0f;
  };
  for (int iter = 0; iter < 8; iter++) {
    k = 0;
    for (int i = 0; i < m; i++) {
      float s = v0 * tt[i] + 0.5f * acc * tt[i] * tt[i];  // bullet's distance from the muzzle
      float X = s + p.behindM;                          // ... measured from the radar along the bore
      if (s < p.minDistM || X <= 0.05f) continue;
      float plain = sqrtf(X * X + p.lateralM * p.lateralM) / X;  // 1 / cos(angle)
      float f = plain;
      if (iter > 0) {
        f = corrFactor(tt[i], s);
        // Very close to the radar the model behind the window correction is shaky
        // (beam shape, blast). Leave those points out rather than trust a big correction.
        if (fabsf(f / plain - 1.0f) > 0.01f) continue;
      }
      tx[k] = tt[i]; vy[k] = vr[i] * f; wy[k] = ww[i]; dist[k] = s; k++;
    }
    if (k < 3) break;
    float nv0, nacc;
    if (!fitLine(tx, vy, wy, k, nv0, nacc)) break;
    bool done = fabsf(nv0 - v0) < 0.001f && fabsf(nacc - acc) < 0.01f;
    v0 = nv0; acc = nacc;
    if (done) break;
  }
  r.npts = k;
  if (k < 6) { r.code = TOO_FEW; return r; }

  // Throw out the worst outliers (more than 3x the typical scatter) and refit once
  {
    double s2 = 0;
    for (int i = 0; i < k; i++) { float e = vy[i] - (v0 + acc * tx[i]); s2 += e * e; }
    float rms = (float)sqrt(s2 / k);
    int k2 = 0;
    for (int i = 0; i < k; i++) {
      float e = vy[i] - (v0 + acc * tx[i]);
      if (fabsf(e) <= 3.0f * rms + 0.3f) { tx[k2] = tx[i]; vy[k2] = vy[i]; wy[k2] = wy[i]; dist[k2] = dist[i]; k2++; }
    }
    if (k2 >= 6 && k2 < k) { k = k2; fitLine(tx, vy, wy, k, v0, acc); }
  }

  double s2 = 0;
  for (int i = 0; i < k; i++) { float e = vy[i] - (v0 + acc * tx[i]); s2 += e * e; }
  for (int i = 0; i < m; i++) tmp_[i] = snr[i];
  std::nth_element(tmp_, tmp_ + m / 2, tmp_ + m);

  r.v0Mps = v0;
  r.accel = acc;
  r.npts = k;
  r.spanMs = (tx[k - 1] - tx[0]) * 1000.0f;
  r.snrDb = tmp_[m / 2];
  r.rmsMps = (float)sqrt(s2 / k);
  r.d0 = dist[0];
  r.d1 = dist[k - 1];
  r.vFirstMps = v0 + acc * tx[0];

  // A real bullet is tracked for at least a couple of metres, and drag only ever
  // slows it down. Blast and clutter tracks tend to be short or to speed up.
  if (r.spanMs < 3.0f || r.d1 < 2.0f) r.code = TOO_SHORT;
  else if (r.rmsMps > 1.5f || acc > 150.0f) r.code = NOISY;
  else if (v0 < p.vminMps || v0 > p.vmaxMps) r.code = OUT_OF_RANGE;
  else r.code = OK;
  return r;
}

}  // namespace rdsp
