// Range Book BLIPR (Ballistic Launch Inspection Portable Radar) - Teensy 4.1 firmware
// Samples the radar's I and Q channels, detects shots, measures muzzle velocity,
// saves raw captures to the SD card and reports each shot to the ESP32-C3
// (which handles Bluetooth, the OLED and the battery gauge).
//
// Board settings (Arduino IDE): Tools > Board > Teensy 4.1,
// USB Type: "Serial + MTP Disk (Experimental)" (lets the SD card show up as a drive on the computer;
// plain "Serial" also works, without the drive), CPU Speed: 600 MHz.
// Open Serial Monitor at any speed and type "help".
//
// Wiring: radar I amplifier -> A0 (pin 14), Q amplifier -> A1 (pin 15).
//         Serial8: pin 35 (TX8) -> 1 kOhm -> ESP32 GPIO20, pin 34 (RX8) <- 1 kOhm <- ESP32 GPIO21,
//         GND to GND. (Board v1.1 and later. Firmware before 0.2.2 used Serial1, pins 0 and 1.)
//         Bench test signal (only when the amplifier is NOT connected):
//         pin 2 -> 1 kOhm -> A0, and pin 2 -> 1 kOhm -> A1.
//
// Copyright (c) 2026 Sean O'Neill. AGPL-3.0-or-later (same as Range Book).

#include <ADC.h>
#include <AnalogBufferDMA.h>
#include <DMAChannel.h>
#include <SD.h>
#include <EEPROM.h>
#include <algorithm>
#if defined(MTP_INTERFACE)
#include <MTP_Teensy.h>
#define HAVE_DRIVE 1
#else
#define HAVE_DRIVE 0
#endif
#include "radar_dsp.h"

#define FW_VERSION "0.2.5"

// ---------------- pins and sizes ----------------
static const int PIN_I = A0;      // pin 14
static const int PIN_Q = A1;      // pin 15
static const int PIN_SIM = 2;     // bench test signal output
static const int PIN_LED = 13;
#define LINK Serial8
static const uint32_t LINK_BAUD = 460800;
static bool driveMode = false;   // "drive" command: shot detection paused while the computer reads the SD card

static const int BLOCK = 1024;            // samples per DMA buffer
static const int NBLK = 80;               // blocks kept in the ring (per channel)
static const int PRE_BLK = 12;            // blocks kept before the trigger
static const int POST_BLK = 66;           // blocks recorded after the trigger
static const int CAP_BLK = PRE_BLK + POST_BLK;  // must be < NBLK
// Quick check after a trigger (rdsp::Processor::confirm): CONF_PRE blocks before the trigger block as the reference,
// CONF_POST blocks from the trigger block on. Bursts that aren't a bullet are dropped after ~18 ms instead of
// keeping BLIPR busy for ~0.5 s with a full capture.
static const int CONF_PRE = 8;
static const int CONF_POST = rdsp::CONFIRM_FIRST + rdsp::CONFIRM_FRAMES + 1;
static const int CONF_BLK = CONF_PRE + CONF_POST;

DMAMEM static volatile uint16_t __attribute__((aligned(32))) dmaI1[BLOCK];
DMAMEM static volatile uint16_t __attribute__((aligned(32))) dmaI2[BLOCK];
DMAMEM static volatile uint16_t __attribute__((aligned(32))) dmaQ1[BLOCK];
DMAMEM static volatile uint16_t __attribute__((aligned(32))) dmaQ2[BLOCK];
DMAMEM static uint16_t ringI[NBLK * BLOCK];
DMAMEM static uint16_t ringQ[NBLK * BLOCK];
DMAMEM static uint16_t confI[CONF_BLK * BLOCK];
DMAMEM static uint16_t confQ[CONF_BLK * BLOCK];

ADC* adc = new ADC();
AnalogBufferDMA abI(dmaI1, BLOCK, dmaI2, BLOCK);
AnalogBufferDMA abQ(dmaQ1, BLOCK, dmaQ2, BLOCK);
rdsp::Processor dsp;
static rdsp::Peak peakLog[rdsp::MAX_FRAMES];

// ---------------- settings (kept in EEPROM) ----------------
struct Settings {
  uint32_t magic;
  uint16_t version;
  float vminFps, vmaxFps;    // velocity window
  float lateralM, behindM;   // radar position relative to the muzzle
  float calPpm;              // velocity calibration
  float f0Hz;                // radar frequency
  float snrDb;               // peak threshold
  float trigDb;              // trigger: energy above noise floor
  uint32_t fsReq;            // requested sample rate
  uint8_t saveRaw;           // save every capture to SD
  uint8_t armed;             // listening for shots
  float bandDb;              // in-band trigger: a line this far above its usual level (dB); 0 = old whole-block trigger (version 2 on)
};
static const uint32_t SET_MAGIC = 0x52434831;  // "RCH1"
static Settings cfg;

static void setDefaults() {
  cfg.magic = SET_MAGIC;
  cfg.version = 2;
  cfg.vminFps = 600;   // Sean shoots 600-3500 fps (Nov 12)
  cfg.vmaxFps = 3500;
  cfg.lateralM = 0.10f;
  cfg.behindM = 0.10f;
  cfg.calPpm = 0;
  cfg.f0Hz = 24.150e9f;        // K-LC5 typical (24.050-24.250 GHz); set cal once against a reference chronograph
  cfg.snrDb = 12;
  cfg.trigDb = 9;
  cfg.fsReq = 600000;
  cfg.saveRaw = 1;
  cfg.armed = 1;
  cfg.bandDb = 15;
}
static void saveSettings() { EEPROM.put(0, cfg); }
static void loadSettings() {
  EEPROM.get(0, cfg);
  if (cfg.magic == SET_MAGIC && cfg.version == 1) {   // settings from 0.2.4 and before: keep them, add the new one
    cfg.version = 2;
    cfg.bandDb = 15;
    saveSettings();
  }
  if (cfg.magic != SET_MAGIC || cfg.version != 2) { setDefaults(); saveSettings(); }
  if (!(cfg.bandDb >= 0 && cfg.bandDb <= 60)) { cfg.bandDb = 15; saveSettings(); }
}

// ---------------- state ----------------
static float fsActual = 0;           // the rate the ADC timer really runs at
static uint32_t cntI = 0, cntQ = 0;  // blocks written to the ring
static uint32_t lastIntI = 0, lastIntQ = 0;
static uint32_t overruns = 0;
static uint32_t evalBlk = 0;         // next block index to check for a trigger
static float dcI = 2048, dcQ = 2048; // running DC levels
static float floorE = 0;             // noise floor (energy per block, both channels)
static uint32_t floorN = 0;
static float lastBlkDb = 0;          // last block energy over floor (dB) for "live"
static float bandAvg[rdsp::NFFT / 2]; // in-band trigger: each frequency bin's usual level
static float lastBandDb = 0, lastBandHz = 0;  // last in-band reading (for "live")
static uint32_t bandUsMax = 0;       // longest in-band check (us), shown by "stat"
static float fadeDb = 6.0f;          // "set fade=": steady-line test in the analysis (dB); 0 turns it off. Not saved.
static bool simAtTrig = false;       // the capture was set off by the bench "sim" tone (it doesn't fade like an echo)
static volatile bool simOn = false;  // the bench "sim" tone is playing
enum State { LISTEN, CONFIRM, CAPTURE };
static State state = LISTEN;
static uint32_t trigBlk = 0;         // block where the shot started
static int trigIdx = 0;              // sample within that block
static uint32_t armedAtBlk = 0;
static uint32_t holdoffUntil = 0;
static uint32_t rejects = 0;         // triggers the quick check dropped
static float qcDb = 11.0f;           // "set qc=": the quick check's line threshold (dB); 0 turns it off. Not saved: 11 after a restart.
static rdsp::Confirm lastConf;       // the quick check of the capture being recorded
static uint32_t shotNo = 0;
static uint32_t fileNo = 0;
static bool sdOk = false;
static bool manualRec = false;       // "rec" command: capture now
static bool liveMode = false;
static uint32_t bootId = 0;

// ---------------- link to the ESP32 ----------------
// Lines look like "@S,....*5A\n" (to ESP) and "!command*3F\n" (from ESP).
// The checksum (XOR of the characters between the first char and '*') lets
// both sides ignore noise, such as the ESP32's boot messages.
static uint8_t xorSum(const char* s, size_t n) { uint8_t c = 0; for (size_t i = 0; i < n; i++) c ^= (uint8_t)s[i]; return c; }
static void linkSend(const char* body) {
  char buf[200];
  uint8_t c = xorSum(body, strlen(body));
  snprintf(buf, sizeof(buf), "@%s*%02X\n", body, c);
  LINK.write(buf, strlen(buf));
}

// ---------------- sampling ----------------
static void startSampling() {
  pinMode(PIN_I, INPUT_DISABLE);
  pinMode(PIN_Q, INPUT_DISABLE);
  ADC_Module* mods[2] = {adc->adc0, adc->adc1};
  for (ADC_Module* m : mods) {
    m->setAveraging(1);
    m->setResolution(12);
    m->setConversionSpeed(ADC_CONVERSION_SPEED::VERY_HIGH_SPEED);
    m->setSamplingSpeed(ADC_SAMPLING_SPEED::VERY_HIGH_SPEED);
  }
  abI.init(adc, ADC_0);
  abQ.init(adc, ADC_1);
  adc->adc0->startSingleRead(PIN_I);
  adc->adc1->startSingleRead(PIN_Q);
  adc->adc0->startTimer(cfg.fsReq);
  adc->adc1->startTimer(cfg.fsReq);
  fsActual = (float)adc->adc0->getTimerFrequency();
  if (fsActual < 1000) fsActual = (float)cfg.fsReq;
}

// Copy any finished DMA buffer into the ring. Returns true if anything was copied.
static bool pump(AnalogBufferDMA& ab, uint16_t* ring, uint32_t& cnt, uint32_t& lastInt) {
  if (!ab.interrupted()) return false;
  uint32_t ic = ab.interruptCount();
  if (lastInt && ic - lastInt > 1) overruns += ic - lastInt - 1;
  lastInt = ic;
  volatile uint16_t* src = ab.bufferLastISRFilled();
  arm_dcache_delete((void*)src, BLOCK * 2);
  if (state != CAPTURE || cnt < trigBlk + POST_BLK) {   // freeze the ring once the capture is complete
    uint16_t* dst = ring + (cnt % NBLK) * BLOCK;
    memcpy(dst, (const void*)src, BLOCK * 2);
    cnt++;
  }
  ab.clearInterrupt();
  return true;
}

static float blockEnergy(const uint16_t* b, float& dc) {
  double s = 0, s2 = 0;
  for (int i = 0; i < BLOCK; i++) { s += b[i]; }
  float mean = (float)(s / BLOCK);
  for (int i = 0; i < BLOCK; i++) { float d = b[i] - mean; s2 += d * d; }
  dc = 0.98f * dc + 0.02f * mean;
  return (float)s2;
}

// Find the first sample in a block that clearly stands out (-1: none does).
static int onsetIndex(uint32_t blk) {
  const uint16_t* bi = ringI + (blk % NBLK) * BLOCK;
  const uint16_t* bq = ringQ + (blk % NBLK) * BLOCK;
  float sigma = sqrtf(floorE / (2.0f * BLOCK));
  float lim = 5.0f * sigma + 3.0f;
  for (int i = 0; i < BLOCK; i++)
    if (fabsf(bi[i] - dcI) > lim || fabsf(bq[i] - dcQ) > lim) return i;
  return -1;
}

static rdsp::Params currentParams();

// Check each newly completed block (both channels) for a shot.
// 0.2.5 on (bandDb > 0): the in-band trigger. The last two blocks get an FFT and each frequency inside the velocity
// window is compared with its own usual level and its neighbours' (rdsp::Processor::bandScan): a bullet is a new
// narrow line there. Bluetooth bursts (broadband, mostly low-pitched) and steady lines (the ESP32, the phone link)
// don't stand out that way. bandDb = 0 goes back to the old trigger: the whole block's energy over the noise floor.
static void checkTrigger() {
  uint32_t ready = std::min(cntI, cntQ);
  static int k0 = 0, k1 = 0;
  static float lastFs = 0, lastVmin = 0, lastVmax = 0;
  if (fsActual != lastFs || cfg.vminFps != lastVmin || cfg.vmaxFps != lastVmax) {   // window changed: new bins
    rdsp::Processor::bandBins(currentParams(), k0, k1);
    lastFs = fsActual; lastVmin = cfg.vminFps; lastVmax = cfg.vmaxFps;
  }
  const bool band = cfg.bandDb > 0;
  while (evalBlk < ready) {
    uint32_t b = evalBlk++;
    if (state != LISTEN) continue;
    float e = blockEnergy(ringI + (b % NBLK) * BLOCK, dcI) + blockEnergy(ringQ + (b % NBLK) * BLOCK, dcQ);
    float bdb = -99;
    if (band && b >= 1 && ready - b < NBLK - 4) {   // (skip blocks the ring has already overwritten)
      int kb = 0;
      uint32_t tb = micros();
      bdb = dsp.bandScan(ringI + ((b - 1) % NBLK) * BLOCK, ringQ + ((b - 1) % NBLK) * BLOCK, ringI + (b % NBLK) * BLOCK,
                         ringQ + (b % NBLK) * BLOCK, dcI, dcQ, k0, k1, bandAvg, floorN < 200 ? 0.125f : 1.0f / 64, &kb);
      tb = micros() - tb;
      if (tb > bandUsMax) bandUsMax = tb;
      lastBandDb = bdb;
      lastBandHz = kb * fsActual / rdsp::NFFT;
    }
    if (floorN < 200) {           // learn the quiet level after power-up
      floorE = floorN ? 0.95f * floorE + 0.05f * e : e;
      floorN++;
      continue;
    }
    lastBlkDb = 10.0f * log10f(e / (floorE + 1e-9f) + 1e-9f);
    bool ready2 = (b >= armedAtBlk + PRE_BLK + 1) && millis() >= holdoffUntil;
    bool hit = band ? bdb > cfg.bandDb : lastBlkDb > cfg.trigDb;
    if (ready2 && (manualRec || (cfg.armed && !driveMode && hit))) {
      state = manualRec ? CAPTURE : CONFIRM;
      lastConf = rdsp::Confirm();
      lastConf.hits = 99;   // a manual recording isn't checked
      simAtTrig = simOn;
      trigBlk = b;
      trigIdx = 0;
      if (!manualRec) {
        // the shot starts where the first sample stands out (the muzzle blast, or the echo itself); the in-band
        // trigger looks at two blocks, so it may have started in the earlier one
        int o = band ? onsetIndex(b - 1) : -1;
        if (o >= 0) { trigBlk = b - 1; trigIdx = o; }
        else { o = onsetIndex(b); trigIdx = o >= 0 ? o : 0; }
      }
      digitalWriteFast(PIN_LED, HIGH);
      return;
    }
    // follow slow changes in the background noise, but not shots
    if (lastBlkDb < 3.0f) floorE = 0.99f * floorE + 0.01f * e;
  }
}

// ---------------- bench test signal ----------------
// Plays a decelerating Doppler tone on PIN_SIM, as a bullet at simV0 fps would give
// with the current radar position settings.
static IntervalTimer simTimer;
static volatile uint32_t simStartUs = 0;
static float simV0 = 2800, simAcc = -300;
static void simTick() {
  if (!simOn) return;
  float t = (micros() - simStartUs) * 1e-6f;
  if (t > 0.060f) { analogWrite(PIN_SIM, 0); simOn = false; return; }
  float v = simV0 * 0.3048f + simAcc * t;
  float s = simV0 * 0.3048f * t + 0.5f * simAcc * t * t;
  float X = s + cfg.behindM;
  float c = X > 0 ? X / sqrtf(X * X + cfg.lateralM * cfg.lateralM) : 0;
  float hw = rdsp::Processor::halfWavelength(rdsp::Params{});  // uncalibrated 24.150 GHz
  float f = v * c / hw;
  if (f < 2000) f = 2000;
  analogWriteFrequency(PIN_SIM, f);
  analogWrite(PIN_SIM, 128);
}

// ---------------- SD card ----------------
static void sdInit() {
  sdOk = SD.begin(BUILTIN_SDCARD);
  if (!sdOk) return;
  if (!SD.exists("/shots")) SD.mkdir("/shots");
  char name[40];
  for (fileNo = 1; fileNo < 100000; fileNo++) {
    snprintf(name, sizeof(name), "/shots/s%05lu.bin", (unsigned long)fileNo);
    if (!SD.exists(name)) break;
  }
}

static void saveCapture(const uint16_t* I, const uint16_t* Q, int n, const rdsp::Params& p,
                        const rdsp::Result& r, float t0) {
  if (!sdOk) return;
  char name[40];
  snprintf(name, sizeof(name), "/shots/s%05lu.bin", (unsigned long)fileNo);
  File f = SD.open(name, FILE_WRITE);
  if (!f) { sdOk = false; return; }
  // 512-byte text header (JSON), then n I samples, then n Q samples (uint16, little-endian)
  char hdr[512];
  memset(hdr, ' ', sizeof(hdr));
  int len = snprintf(hdr, sizeof(hdr),
    "{\"fmt\":\"rchrono1\",\"fw\":\"" FW_VERSION "\",\"boot\":\"%08lx\",\"shot\":%lu,\"fs\":%.1f,\"n\":%d,"
    "\"t0\":%.6f,\"pre\":%d,\"f0\":%.0f,\"cal\":%.1f,\"lat\":%.3f,\"behind\":%.3f,\"vmin\":%.1f,\"vmax\":%.1f,"
    "\"snr\":%.1f,\"trig\":%.1f,\"code\":%d,\"v0\":%.2f,\"acc\":%.1f,\"pts\":%d,\"rms\":%.3f,\"ovr\":%lu,\"ms\":%lu,\"unix\":%lu}",
    (unsigned long)bootId, (unsigned long)shotNo, p.fs, n, t0, PRE_BLK * BLOCK, (double)p.f0, p.calPpm, p.lateralM,
    p.behindM, p.vminMps, p.vmaxMps, p.snrMinDb, cfg.trigDb, r.code, r.v0Mps, r.accel, r.npts, r.rmsMps,
    (unsigned long)overruns, (unsigned long)millis(), (unsigned long)rtc_get());
  if (len < 511) hdr[len] = ' ';
  hdr[510] = '\r'; hdr[511] = '\n';
  f.write(hdr, sizeof(hdr));
  f.write((const uint8_t*)I, n * 2);
  f.write((const uint8_t*)Q, n * 2);
  f.close();
  fileNo++;
  // one line per capture in a CSV you can open in a spreadsheet
  File log = SD.open("/shots/log.csv", FILE_WRITE);
  if (log) {
    if (log.size() == 0) log.println("file,boot,shot,unix_utc,ms,code,fps,mps,accel,points,span_ms,snr_db,rms_mps,d0_m,d1_m");
    log.printf("s%05lu.bin,%08lx,%lu,%lu,%lu,%d,%.1f,%.2f,%.1f,%d,%.1f,%.1f,%.3f,%.2f,%.2f\n", (unsigned long)(fileNo - 1),
               (unsigned long)bootId, (unsigned long)shotNo, (unsigned long)rtc_get(), (unsigned long)millis(), r.code, r.v0Mps / 0.3048f,
               r.v0Mps, r.accel, r.npts, r.spanMs, r.snrDb, r.rmsMps, r.d0, r.d1);
    log.close();
  }
}

// ---------------- after a capture ----------------
static const char* codeText(int c) {
  switch (c) {
    case rdsp::OK: return "ok";
    case rdsp::NO_SIGNAL: return "no signal";
    case rdsp::TOO_FEW: return "weak";
    case rdsp::TOO_SHORT: return "short";
    case rdsp::NOISY: return "noisy";
    case rdsp::OUT_OF_RANGE: return "out of range";
    case rdsp::STEADY_LINE: return "interference";
  }
  return "?";
}

static rdsp::Params currentParams() {
  rdsp::Params p;
  p.fs = fsActual;
  p.f0 = cfg.f0Hz;
  p.calPpm = cfg.calPpm;
  p.vminMps = cfg.vminFps * 0.3048f;
  p.vmaxMps = cfg.vmaxFps * 0.3048f;
  p.snrMinDb = cfg.snrDb;
  p.lateralM = cfg.lateralM;
  p.behindM = cfg.behindM;
  p.fadeMinDb = fadeDb;
  return p;
}

// Empties the ADC buffers into the rings (used while the quick check runs, so no block is lost).
static void pumpOnly() {
  pump(abI, ringI, cntI, lastIntI);
  pump(abQ, ringQ, cntQ, lastIntQ);
}

static void quickCheck() {
  uint32_t first = trigBlk - CONF_PRE;
  for (int k = 0; k < CONF_BLK; k++) {
    size_t from = (size_t)((first + k) % NBLK) * BLOCK;
    memcpy(confI + k * BLOCK, ringI + from, BLOCK * 2);
    memcpy(confQ + k * BLOCK, ringQ + from, BLOCK * 2);
  }
  rdsp::Params p = currentParams();
  p.confirmDb = qcDb;
  bool pass = dsp.confirm(confI, confQ, CONF_BLK * BLOCK, CONF_PRE * BLOCK, p, &lastConf);
  if (qcDb <= 0) { pass = true; lastConf.hits = 99; }   // quick check off: record every trigger
  if (pass) {
    state = CAPTURE;   // looks like a bullet: record the rest
    return;
  }
  rejects++;
  if (liveMode) Serial.printf("  (trigger dropped: best line %.1f dB at %.0f Hz, %d frames)\n", lastConf.bestDb, lastConf.f, lastConf.hits);
  state = LISTEN;
  evalBlk = trigBlk + 3;   // carry on just past the burst
  digitalWriteFast(PIN_LED, LOW);
}

static void processCapture() {
  // Rotate both rings so the capture starts at index 0 and is contiguous.
  uint32_t first = trigBlk - PRE_BLK;
  size_t shift = (size_t)(first % NBLK) * BLOCK;
  std::rotate(ringI, ringI + shift, ringI + NBLK * BLOCK);
  std::rotate(ringQ, ringQ + shift, ringQ + NBLK * BLOCK);
  const int n = CAP_BLK * BLOCK;
  rdsp::Params p = currentParams();
  p.t0Sec = (PRE_BLK * BLOCK + trigIdx) / fsActual;
  if (simAtTrig) p.fadeMinDb = 0;   // the bench tone keeps the same strength all the way: don't call it interference
  uint32_t t1 = micros();
  int np = 0;
  rdsp::Result r = dsp.analyze(ringI, ringQ, n, p, peakLog, &np);
  uint32_t tProc = micros() - t1;
  shotNo++;
  bool wasManual = manualRec;
  manualRec = false;

  char body[180];
  float fps = r.v0Mps / 0.3048f;
  snprintf(body, sizeof(body), "S,%lu,%.1f,%.2f,%.0f,%d,%.1f,%.2f,%.1f,%.1f,%d,%s",
           (unsigned long)shotNo, fps, r.v0Mps, r.accel, r.npts, r.snrDb, r.rmsMps, r.d0, r.d1,
           r.code, wasManual ? "rec" : codeText(r.code));
  // A capture that only just passed the quick check and then didn't measure is almost certainly not a shot: keep it
  // off the phone (it's still printed and saved here).
  bool quiet = !wasManual && r.code != rdsp::OK && (lastConf.hits < 3 || r.code == rdsp::STEADY_LINE);
  if (!wasManual && !quiet) linkSend(body);
  Serial.printf("\n%s #%lu: %s%s", wasManual ? "Recording" : "Shot", (unsigned long)shotNo, codeText(r.code), quiet ? " (not sent)" : "");
  if (r.code == rdsp::OK) Serial.printf("  %.1f fps (%.2f m/s)", fps, r.v0Mps);
  Serial.printf("\n  points %d, span %.1f ms, SNR %.1f dB, scatter %.2f m/s, accel %.0f m/s^2, tracked %.1f-%.1f m, %lu ms to process\n",
                r.npts, r.spanMs, r.snrDb, r.rmsMps, r.accel, r.d0, r.d1, (unsigned long)(tProc / 1000));
  if (!wasManual) Serial.printf("  quick check: line %.1f dB at %.0f Hz in %d frames\n", lastConf.bestDb, lastConf.f, lastConf.hits);
  if (cfg.saveRaw || wasManual) {
    uint32_t t2 = millis();
    saveCapture(ringI, ringQ, n, p, r, p.t0Sec);
    Serial.printf("  saved as s%05lu.bin (%lu ms)%s\n", (unsigned long)(fileNo - 1),
                  (unsigned long)(millis() - t2), sdOk ? "" : "  ** SD card problem **");
  }
  // Start listening again: the ring has to refill before the next trigger.
  cntQ = cntI = std::max(cntI, cntQ);
  evalBlk = cntI;
  armedAtBlk = cntI;
  abI.clearInterrupt();
  abQ.clearInterrupt();
  lastIntI = lastIntQ = 0;
  holdoffUntil = millis() + 250;
  state = LISTEN;
  digitalWriteFast(PIN_LED, LOW);
}

// ---------------- commands (USB serial and the ESP32) ----------------
static void sendConfig(Print& out, bool toLink) {
  char body[190];
  snprintf(body, sizeof(body),
           "C,vmin=%.0f,vmax=%.0f,lat=%.3f,behind=%.3f,cal=%.0f,f0=%.0f,snr=%.1f,trig=%.1f,fs=%lu,save=%d,arm=%d,band=%.1f",
           cfg.vminFps, cfg.vmaxFps, cfg.lateralM, cfg.behindM, cfg.calPpm, (double)cfg.f0Hz, cfg.snrDb, cfg.trigDb,
           (unsigned long)cfg.fsReq, cfg.saveRaw, cfg.armed, cfg.bandDb);
  if (toLink) linkSend(body);
  else out.printf("%s\n", body + 2);
}

static void sendStatus(bool toLink) {
  char body[160];
  snprintf(body, sizeof(body), "T,%d,%lu,%.0f,%.1f,%lu,%d,%s,%08lx,%d",
           cfg.armed && !driveMode, (unsigned long)shotNo, fsActual, 10.0f * log10f(floorE / (2.0f * BLOCK) + 1e-9f),
           (unsigned long)overruns, sdOk ? 1 : 0, FW_VERSION, (unsigned long)bootId, state == LISTEN ? 1 : 0);
  if (toLink) linkSend(body);
  else Serial.printf("armed %d%s, shots %lu, dropped triggers %lu, sample rate %.0f Hz, noise %.1f dB(counts^2), overruns %lu, SD %s, fw %s, "
                     "trigger %s (check %lu of %lu us per block)\n",
                     cfg.armed, driveMode ? " (paused: USB drive mode)" : "", (unsigned long)shotNo, (unsigned long)rejects, fsActual,
                     10.0f * log10f(floorE / (2.0f * BLOCK) + 1e-9f), (unsigned long)overruns, sdOk ? "ok" : "missing", FW_VERSION,
                     cfg.bandDb > 0 ? "in-band" : "whole block", (unsigned long)bandUsMax, (unsigned long)(BLOCK * 1e6f / fsActual));
}

static bool setKey(const char* k, float v) {
  // refuse values outside sensible ranges (a typo shouldn't wreck the settings)
  auto in = [&](float lo, float hi) { return v == v && v >= lo && v <= hi; };
  // 5,500 fps is about 270 kHz of Doppler: kept clear of the 300 kHz limit of the default 600 kS/s sampling
  if (!strcmp(k, "vmin")) { if (!in(100, 5500)) return false; }
  else if (!strcmp(k, "vmax")) { if (!in(100, 5500)) return false; }
  else if (!strcmp(k, "lat")) { if (!in(0.0f, 2.0f)) return false; }
  else if (!strcmp(k, "behind")) { if (!in(-2.0f, 2.0f)) return false; }
  else if (!strcmp(k, "cal")) { if (!in(-50000, 50000)) return false; }
  else if (!strcmp(k, "f0")) { if (!in(23.9e9f, 24.4e9f)) return false; }
  else if (!strcmp(k, "snr") || !strcmp(k, "trig") || !strcmp(k, "qc") || !strcmp(k, "band") || !strcmp(k, "fade")) { if (!in(0, 60)) return false; }
  else if (!strcmp(k, "fs")) { if (!in(100000, 1000000)) return false; }
  if (!strcmp(k, "vmin")) cfg.vminFps = v;
  else if (!strcmp(k, "vmax")) cfg.vmaxFps = v;
  else if (!strcmp(k, "lat")) cfg.lateralM = v;
  else if (!strcmp(k, "behind")) cfg.behindM = v;
  else if (!strcmp(k, "cal")) cfg.calPpm = v;
  else if (!strcmp(k, "f0")) cfg.f0Hz = v;
  else if (!strcmp(k, "snr")) cfg.snrDb = v;
  else if (!strcmp(k, "trig")) cfg.trigDb = v;
  else if (!strcmp(k, "qc")) qcDb = v;
  else if (!strcmp(k, "band")) cfg.bandDb = v;
  else if (!strcmp(k, "fade")) fadeDb = v;
  else if (!strcmp(k, "save")) cfg.saveRaw = v != 0;
  else if (!strcmp(k, "arm")) cfg.armed = v != 0;
  else if (!strcmp(k, "fs")) cfg.fsReq = (uint32_t)v;
  else return false;
  return true;
}

static void printHelp() {
  Serial.println(
    "\nCommands:\n"
    "  stat              status (sample rate, noise, SD card)\n"
    "  get               show settings\n"
    "  set key=value ... change settings, e.g. set vmin=1500 vmax=3500\n"
    "                    keys: vmin vmax (fps), lat behind (m), cal (ppm), snr trig (dB),\n"
    "                          save (0/1), arm (0/1), fs (Hz, needs restart), f0 (Hz),\n"
    "                          band (in-band trigger dB, 0 = old trigger), qc fade (dB, 0 = off; not saved)\n"
    "  arm / disarm      listen for shots, or not\n"
    "  live              toggle a twice-a-second readout of the radar signal\n"
    "  rec               record 100 ms right now and save it\n"
    "  sim [fps]         play a fake bullet on pin 2 (bench test; amplifier NOT connected)\n"
    "  test              send a made-up shot to the ESP32 (checks the Bluetooth path)\n"
    "  time [seconds]    show or set the clock (the app sets it when it connects)\n"
    "  defaults          restore default settings\n"
    "  drive [off]       USB drive mode (turns on by itself when plugged into a computer): pause\n"
    "                    shots and refresh the SD card's file list; 'drive off' or 'arm' resumes\n"
    "  reboot            restart the Teensy\n");
}

static void handleCommand(char* line, bool fromLink) {
  while (*line == ' ') line++;
  char* cmd = strtok(line, " ");
  if (!cmd) return;
  for (char* c = cmd; *c; c++) *c = tolower(*c);
  if (!strcmp(cmd, "help") || !strcmp(cmd, "?")) printHelp();
  else if (!strcmp(cmd, "stat")) sendStatus(fromLink);
  else if (!strcmp(cmd, "get")) sendConfig(Serial, fromLink);
  else if (!strcmp(cmd, "set")) {
    bool any = false, fsChanged = false;
    const float oldMin = cfg.vminFps, oldMax = cfg.vmaxFps;
    for (char* kv = strtok(nullptr, " ,"); kv; kv = strtok(nullptr, " ,")) {
      char* eq = strchr(kv, '=');
      if (!eq) continue;
      *eq = 0;
      for (char* c = kv; *c; c++) *c = tolower(*c);
      if (setKey(kv, atof(eq + 1))) { any = true; if (!strcmp(kv, "fs")) fsChanged = true; }
      else if (!fromLink) Serial.printf("unknown setting or value out of range: %s\n", kv);
    }
    if (cfg.vminFps >= cfg.vmaxFps) {   // an empty velocity window would reject every shot
      cfg.vminFps = oldMin; cfg.vmaxFps = oldMax;
      if (!fromLink) Serial.println("vmin must be below vmax: velocity window not changed");
    }
    if (any) { saveSettings(); sendConfig(Serial, fromLink); if (!fromLink) sendConfig(Serial, true); }
    if (fsChanged && !fromLink) Serial.println("New sample rate takes effect after 'reboot'.");
  }
  else if (!strcmp(cmd, "arm")) { cfg.armed = 1; driveMode = false; saveSettings(); sendStatus(true); if (!fromLink) Serial.println("armed"); }
  else if (!strcmp(cmd, "disarm")) { cfg.armed = 0; saveSettings(); sendStatus(true); if (!fromLink) Serial.println("disarmed"); }
  else if (!strcmp(cmd, "live")) { liveMode = !liveMode; }
  else if (!strcmp(cmd, "rec")) { manualRec = true; if (!fromLink) Serial.println("recording..."); }
  else if (!strcmp(cmd, "sim")) {
    driveMode = false;  // bench test over USB: listen for the fake shot
    char* a = strtok(nullptr, " ");
    simV0 = a ? atof(a) : 2800;
    if (simV0 < 300 || simV0 > 4500) simV0 = 2800;
    simAcc = -0.35f * simV0 * 0.3048f;   // roughly what drag does near the muzzle (about -300 m/s^2 at 2800 fps)
    if (!fromLink) Serial.printf("fake shot at %.0f fps on pin 2 (expect about %.0f fps)\n", simV0, simV0);
    simStartUs = micros();
    simOn = true;
  }
  else if (!strcmp(cmd, "test")) {
    shotNo++;
    float fps = 2700 + random(-150, 150) / 10.0f;
    char body[120];
    snprintf(body, sizeof(body), "S,%lu,%.1f,%.2f,-320,40,18.0,0.30,0.6,18.0,0,test", (unsigned long)shotNo, fps, fps * 0.3048f);
    linkSend(body);
    if (!fromLink) Serial.printf("sent test shot #%lu: %.1f fps\n", (unsigned long)shotNo, fps);
  }
  else if (!strcmp(cmd, "time")) {
    // "time 1760958000": seconds since 1970 (UTC), sent by the app when it connects
    char* a = strtok(nullptr, " ");
    unsigned long t = a ? strtoul(a, nullptr, 10) : 0;
    if (t > 1600000000UL) { rtc_set(t); if (!fromLink) Serial.printf("clock set: %lu\n", t); }
    else if (!fromLink) Serial.printf("clock: %lu (seconds since 1970, UTC)\n", rtc_get());
  }
  else if (!strcmp(cmd, "defaults")) { setDefaults(); saveSettings(); sendConfig(Serial, fromLink); }
  else if (!strcmp(cmd, "drive")) {
    char* a = strtok(nullptr, " ");
    bool off = a && (!strcasecmp(a, "off") || !strcmp(a, "0"));
#if HAVE_DRIVE
    if (!sdOk && !off) { if (!fromLink) Serial.println("No SD card found, so there is nothing to show."); }
    else {
      driveMode = !off;
      if (driveMode) MTP.reset();  // makes the computer re-read the file list
      sendStatus(true);
      if (!fromLink) Serial.println(driveMode ? "USB drive mode: shots paused. Open \"Teensy\" on the computer. Type 'drive off' when done."
                                              : "USB drive mode off, listening for shots again.");
    }
#else
    if (!fromLink) Serial.println("Drive mode isn't in this build. In Arduino set Tools > USB Type to \"Serial + MTP Disk (Experimental)\" and upload again.");
#endif
  }
  else if (!strcmp(cmd, "reboot")) { Serial.flush(); delay(50); SCB_AIRCR = 0x05FA0004; }
  else if (!fromLink) Serial.printf("unknown command: %s (type help)\n", cmd);
}

static char usbLine[200]; static size_t usbLen = 0;
static char lnkLine[200]; static size_t lnkLen = 0;

static void readUsb() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\r' || c == '\n') {
      if (usbLen) { usbLine[usbLen] = 0; handleCommand(usbLine, false); usbLen = 0; }
    } else if (usbLen < sizeof(usbLine) - 1) usbLine[usbLen++] = c;
  }
}

static void readLink() {
  while (LINK.available()) {
    char c = LINK.read();
    if (c == '!') { lnkLen = 0; lnkLine[lnkLen++] = c; continue; }
    if (c == '\n') {
      lnkLine[lnkLen] = 0;
      char* star = strrchr(lnkLine, '*');
      if (lnkLen > 3 && lnkLine[0] == '!' && star) {
        uint8_t want = (uint8_t)strtoul(star + 1, nullptr, 16);
        *star = 0;
        if (xorSum(lnkLine + 1, strlen(lnkLine + 1)) == want) handleCommand(lnkLine + 1, true);
      }
      lnkLen = 0;
    } else if (lnkLen > 0 && lnkLen < sizeof(lnkLine) - 1) lnkLine[lnkLen++] = c;
  }
}

// ---------------- live readout ----------------
static uint16_t liveI[rdsp::NFFT], liveQ[rdsp::NFFT];
static void liveReport() {
  // Levels and the strongest frequency above 500 Hz in the latest 2048 samples
  uint32_t last = std::min(cntI, cntQ);
  if (last < 3) return;
  uint32_t b0 = last - 2;
  for (int k = 0; k < 2; k++) {
    memcpy(liveI + k * BLOCK, ringI + ((b0 + k) % NBLK) * BLOCK, BLOCK * 2);
    memcpy(liveQ + k * BLOCK, ringQ + ((b0 + k) % NBLK) * BLOCK, BLOCK * 2);
  }
  double si = 0, sq = 0, pi = 0, pq = 0;
  int clip = 0;
  for (int i = 0; i < rdsp::NFFT; i++) { si += liveI[i]; sq += liveQ[i]; }
  float mi = si / rdsp::NFFT, mq = sq / rdsp::NFFT;
  for (int i = 0; i < rdsp::NFFT; i++) {
    float a = liveI[i] - mi, b = liveQ[i] - mq;
    pi += a * a; pq += b * b;
    if (liveI[i] > 4090 || liveI[i] < 5 || liveQ[i] > 4090 || liveQ[i] < 5) clip++;
  }
  float f = dsp.peakHz(liveI, liveQ, mi, mq, fsActual, 500);
  float hw = rdsp::Processor::halfWavelength(currentParams());
  Serial.printf("I: dc %4.0f rms %6.1f | Q: dc %4.0f rms %6.1f | clipped %4d | strongest %7.0f Hz = %6.1f m/s = %6.0f fps | block %+5.1f dB | in-band %+5.1f dB at %.0f fps\n",
                mi, sqrt(pi / rdsp::NFFT), mq, sqrt(pq / rdsp::NFFT), clip, f, f * hw, f * hw / 0.3048f, lastBlkDb,
                lastBandDb, lastBandHz * hw / 0.3048f);
}

// ---------------- setup / loop ----------------
void setup() {
  pinMode(PIN_LED, OUTPUT);
  Serial.begin(115200);
  LINK.begin(LINK_BAUD);
  static uint8_t rxMem[1024], txMem[1024];
  LINK.addMemoryForRead(rxMem, sizeof(rxMem));
  LINK.addMemoryForWrite(txMem, sizeof(txMem));
  loadSettings();
  // a different id at every power-up, so the app knows shot numbers have restarted: a counter kept in
  // EEPROM (well away from the settings), mixed with the clock in case the counter is ever reset
  {
    uint32_t boots = 0;
    EEPROM.get(2000, boots);
    boots++;
    EEPROM.put(2000, boots);
    bootId = (boots * 2654435761UL) ^ (uint32_t)rtc_get() ^ ARM_DWT_CYCCNT;
  }
  analogWriteResolution(8);
  pinMode(PIN_SIM, OUTPUT);
  digitalWriteFast(PIN_SIM, LOW);
  simTimer.begin(simTick, 250);  // update the test tone 4000 times a second
  dsp.begin();
  dsp.idle = pumpOnly;
  sdInit();
#if HAVE_DRIVE
  MTP.begin();
  if (sdOk) MTP.addFilesystem(SD, "BLIPR SD");
#endif
  startSampling();
  uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 1500) {}
  Serial.printf("\nRange Book BLIPR, Teensy firmware %s\n", FW_VERSION);
  Serial.printf("Sample rate %.0f Hz (asked for %lu). SD card %s. Type 'help' for commands.\n",
                fsActual, (unsigned long)cfg.fsReq, sdOk ? "found" : "NOT found");
  sendConfig(Serial, true);
  sendStatus(true);
}

void loop() {
  bool any = pump(abI, ringI, cntI, lastIntI);
  any |= pump(abQ, ringQ, cntQ, lastIntQ);
  if (any) checkTrigger();
  if (state == CONFIRM && cntI >= trigBlk + CONF_POST && cntQ >= trigBlk + CONF_POST) quickCheck();
  if (state == CAPTURE && cntI >= trigBlk + POST_BLK && cntQ >= trigBlk + POST_BLK) processCapture();

  readUsb();
  readLink();
#if HAVE_DRIVE
  if (state == LISTEN) MTP.loop();  // never while a shot is being recorded
  // Automatic drive mode: plugged into a computer (USB set up for 1 s) -> pause shots so the SD card can be
  // copied; unplugged for 3 s -> listen for shots again. A USB charger or power bank never sets up USB, so it
  // doesn't count. "drive off" or "arm" while plugged in resumes shots until the next time it's plugged in.
  {
    static bool usbOn = false;
    static uint32_t since = 0;
    bool u = usb_configuration != 0;
    if (u == usbOn) since = 0;
    else if (!since) since = millis();
    else if (millis() - since > (u ? 1000u : 3000u)) {
      usbOn = u; since = 0;
      if (driveMode != u) {
        driveMode = u;
        sendStatus(true);
        if (u) Serial.println("\nPlugged into a computer: USB drive mode, shots paused. The SD card is \"BLIPR SD\".\n"
                              "Type 'arm' (or 'drive off') to listen for shots while plugged in.");
      }
    }
  }
#endif

  static uint32_t lastStat = 0, lastLive = 0, rateCheck = 0, rateCnt0 = 0;
  uint32_t now = millis();
  if (now - lastStat >= 2000) { lastStat = now; sendStatus(true); }
  if (liveMode && now - lastLive >= 500 && state == LISTEN) { lastLive = now; liveReport(); }
  // Measure the real sample rate once, 3 s after start (should match the timer setting)
  if (rateCheck == 0 && now > 2000) { rateCheck = now; rateCnt0 = cntI + overruns; }
  else if (rateCheck && rateCheck != 1 && now - rateCheck >= 1000) {
    float measured = (cntI + overruns - rateCnt0) * (float)BLOCK * 1000.0f / (now - rateCheck);
    if (fabsf(measured / fsActual - 1) > 0.01f)
      Serial.printf("NOTE: measured sample rate %.0f Hz, timer says %.0f Hz\n", measured, fsActual);
    rateCheck = 1;
  }
}
