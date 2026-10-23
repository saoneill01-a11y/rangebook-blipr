// Replay BLIPR raw recordings (s00001.bin ... from the SD card's /shots folder) through the same velocity
// code the Teensy runs (radar_dsp.cpp), so a change to the signal processing can be checked against every
// real shot before it goes on the board.
//
// Build (from firmware/test):
//   g++ -O2 -std=c++17 -I../BliprTeensy replay.cpp ../BliprTeensy/radar_dsp.cpp -o replay
// Use:
//   ./replay ../../recordings/2026-10-25/*.bin            one line per shot, then a summary
//   ./replay --csv out.csv files...                       also write the results to a CSV
//   ./replay --peaks peaks.csv s00012.bin                 every frame's strongest peak (for plotting)
//   ./replay --set snr=10 --set lat=0.12 files...         override a setting from the file header
//     keys: fs f0 cal lat behind vmin vmax (fps) snr t0 mindist
//
// File format (written by saveCapture() in BliprTeensy.ino): a 512-byte text header holding one JSON
// object, then n I samples, then n Q samples, each uint16 little-endian (12-bit ADC counts).
#include "radar_dsp.h"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

static bool num(const std::string& h, const char* key, double& out) {
  std::string k = std::string("\"") + key + "\":";
  size_t p = h.find(k);
  if (p == std::string::npos) return false;
  out = atof(h.c_str() + p + k.size());
  return true;
}
static std::string str(const std::string& h, const char* key) {
  std::string k = std::string("\"") + key + "\":\"";
  size_t p = h.find(k);
  if (p == std::string::npos) return "";
  size_t e = h.find('"', p + k.size());
  return h.substr(p + k.size(), e - p - k.size());
}

int main(int argc, char** argv) {
  std::vector<std::string> files;
  std::vector<std::pair<std::string, double>> overrides;
  const char* csvPath = nullptr;
  const char* peaksPath = nullptr;
  for (int i = 1; i < argc; i++) {
    if (!strcmp(argv[i], "--csv") && i + 1 < argc) csvPath = argv[++i];
    else if (!strcmp(argv[i], "--peaks") && i + 1 < argc) peaksPath = argv[++i];
    else if (!strcmp(argv[i], "--set") && i + 1 < argc) {
      std::string kv = argv[++i];
      size_t eq = kv.find('=');
      if (eq == std::string::npos) { fprintf(stderr, "--set wants key=value\n"); return 2; }
      overrides.push_back({kv.substr(0, eq), atof(kv.c_str() + eq + 1)});
    } else files.push_back(argv[i]);
  }
  if (files.empty()) {
    fprintf(stderr, "usage: replay [--csv out.csv] [--peaks peaks.csv] [--set key=value ...] s00001.bin ...\n");
    return 2;
  }
  static rdsp::Processor proc;
  proc.begin();
  FILE* csv = csvPath ? fopen(csvPath, "w") : nullptr;
  if (csv) fprintf(csv, "file,shot,fw,rec_code,rec_fps,code,fps,diff_fps,points,span_ms,snr_db,rms_mps,accel,d0_m,d1_m\n");
  FILE* pk = peaksPath ? fopen(peaksPath, "w") : nullptr;
  if (pk) fprintf(pk, "file,t_ms,f_hz,mps,snr_db,used\n");

  printf("%-12s %5s %9s %9s %7s %4s %7s %6s %6s %8s %s\n", "file", "shot", "recorded", "replay", "diff", "pts", "span_ms",
         "snr", "rms", "accel", "result");
  int ok = 0, total = 0;
  double sum = 0, sum2 = 0, lo = 1e9, hi = -1e9;
  for (auto& path : files) {
    FILE* f = fopen(path.c_str(), "rb");
    if (!f) { fprintf(stderr, "%s: can't open\n", path.c_str()); continue; }
    char hdr[513] = {0};
    if (fread(hdr, 1, 512, f) != 512) { fprintf(stderr, "%s: too short\n", path.c_str()); fclose(f); continue; }
    std::string h(hdr);
    if (h.find("\"fmt\":\"rchrono1\"") == std::string::npos) { fprintf(stderr, "%s: not a BLIPR recording\n", path.c_str()); fclose(f); continue; }
    double n = 0, fs = 600000, f0 = 24.150e9, cal = 0, lat = 0.1, behind = 0, vmin = 120, vmax = 1600, snr = 12, t0 = 0;
    double recCode = -1, recV0 = 0, shot = 0;
    num(h, "n", n); num(h, "fs", fs); num(h, "f0", f0); num(h, "cal", cal); num(h, "lat", lat); num(h, "behind", behind);
    num(h, "vmin", vmin); num(h, "vmax", vmax); num(h, "snr", snr); num(h, "t0", t0);
    num(h, "code", recCode); num(h, "v0", recV0); num(h, "shot", shot);
    int N = (int)n;
    std::vector<uint16_t> I(N), Q(N);
    size_t got = fread(I.data(), 2, N, f);
    got += fread(Q.data(), 2, N, f);
    fclose(f);
    if ((int)got != 2 * N) { fprintf(stderr, "%s: data cut short (%zu of %d samples)\n", path.c_str(), got, 2 * N); continue; }

    rdsp::Params p;
    p.fs = (float)fs; p.f0 = (float)f0; p.calPpm = (float)cal; p.lateralM = (float)lat; p.behindM = (float)behind;
    p.vminMps = (float)vmin; p.vmaxMps = (float)vmax; p.snrMinDb = (float)snr; p.t0Sec = (float)t0;
    for (auto& o : overrides) {
      const std::string& k = o.first; double v = o.second;
      if (k == "fs") p.fs = v; else if (k == "f0") p.f0 = v; else if (k == "cal") p.calPpm = v;
      else if (k == "lat") p.lateralM = v; else if (k == "behind") p.behindM = v;
      else if (k == "vmin") p.vminMps = v * 0.3048; else if (k == "vmax") p.vmaxMps = v * 0.3048;
      else if (k == "snr") p.snrMinDb = v; else if (k == "t0") p.t0Sec = v; else if (k == "mindist") p.minDistM = v;
      else { fprintf(stderr, "unknown setting %s\n", k.c_str()); return 2; }
    }
    static rdsp::Peak peaks[rdsp::MAX_FRAMES];
    int np = 0;
    rdsp::Result r = proc.analyze(I.data(), Q.data(), N, p, peaks, &np);
    double fps = r.v0Mps / 0.3048, recFps = recV0 / 0.3048;
    const char* base = strrchr(path.c_str(), '/');
    base = base ? base + 1 : path.c_str();
    static const char* codes[] = {"ok", "no signal", "weak", "short", "noisy", "out of range"};
    const char* res = (r.code >= 0 && r.code <= 5) ? codes[r.code] : "?";
    printf("%-12s %5.0f %9.1f %9.1f %7.1f %4d %7.1f %6.1f %6.2f %8.0f %s%s\n", base, shot, recFps, fps,
           (r.code == 0 && recCode == 0) ? fps - recFps : 0.0, r.npts, r.spanMs, r.snrDb, r.rmsMps, r.accel, res,
           (recCode >= 0 && (int)recCode != r.code) ? "  (board said something else)" : "");
    if (csv) fprintf(csv, "%s,%.0f,%s,%.0f,%.2f,%d,%.2f,%.2f,%d,%.2f,%.2f,%.3f,%.1f,%.3f,%.3f\n", base, shot, str(h, "fw").c_str(),
                     recCode, recFps, r.code, fps, (r.code == 0 && recCode == 0) ? fps - recFps : 0.0, r.npts, r.spanMs, r.snrDb,
                     r.rmsMps, r.accel, r.d0, r.d1);
    if (pk) {
      float hw = rdsp::Processor::halfWavelength(p);
      for (int i = 0; i < np; i++)
        fprintf(pk, "%s,%.3f,%.1f,%.2f,%.1f,%d\n", base, peaks[i].t * 1000, peaks[i].f, peaks[i].f * hw, peaks[i].snrDb, peaks[i].used ? 1 : 0);
    }
    total++;
    if (r.code == rdsp::OK) { ok++; sum += fps; sum2 += fps * fps; lo = fps < lo ? fps : lo; hi = fps > hi ? fps : hi; }
  }
  if (ok) {
    double avg = sum / ok, sd = ok > 1 ? sqrt((sum2 - ok * avg * avg) / (ok - 1)) : 0;
    printf("\n%d of %d read. Average %.1f fps, SD %.1f, ES %.1f (low %.1f, high %.1f)\n", ok, total, avg, sd, hi - lo, lo, hi);
  } else printf("\n0 of %d read.\n", total);
  if (csv) fclose(csv);
  if (pk) fclose(pk);
  return 0;
}
