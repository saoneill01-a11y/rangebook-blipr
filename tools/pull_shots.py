#!/usr/bin/env python3
"""Copy BLIPR's raw shot recordings off its SD card into recordings/<date>/.

The Teensy saves every shot (with 'set save=1') as /shots/s00001.bin ... plus /shots/log.csv. Get at them either way:
  - SD card reader (simplest, works everywhere): take the card out of the Teensy and put it in the computer.
  - USB drive mode: plug the Teensy in; it shows up as "BLIPR SD". Windows shows it in File Explorer;
    a Mac needs an MTP app (OpenMTP or Android File Transfer) to copy the shots folder out first.
Then:
    python tools/pull_shots.py /Volumes/SDCARD            (Mac, card reader)
    python tools/pull_shots.py E:\\                         (Windows, card reader)
    python tools/pull_shots.py ~/Downloads/shots           (a shots folder you copied out)
    python tools/pull_shots.py SRC --into recordings/2026-10-25_ladder
Only files it hasn't copied before are copied (same name and size = already there).
"""
import argparse, datetime, os, shutil, sys


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help="the SD card (or a folder holding the shots folder, or the shots folder itself)")
    ap.add_argument("--into", help="destination folder (default: recordings/<today>)")
    a = ap.parse_args()
    src = os.path.expanduser(a.src)
    if os.path.isdir(os.path.join(src, "shots")):
        src = os.path.join(src, "shots")
    if not os.path.isdir(src):
        sys.exit(f"{src} isn't a folder")
    files = sorted(f for f in os.listdir(src) if f.endswith(".bin") or f == "log.csv")
    if not files:
        sys.exit(f"no recordings (s*.bin) in {src}")
    dest = a.into or os.path.join("recordings", datetime.date.today().isoformat())
    os.makedirs(dest, exist_ok=True)
    copied = 0
    for f in files:
        s, d = os.path.join(src, f), os.path.join(dest, f)
        if f != "log.csv" and os.path.exists(d) and os.path.getsize(d) == os.path.getsize(s):
            continue
        shutil.copy2(s, d)
        copied += f != "log.csv"
    nbin = sum(f.endswith(".bin") for f in files)
    print(f"{copied} new recordings copied to {dest} ({nbin} on the card). Replay them with:")
    print(f"    firmware/test/replay {dest}/*.bin")


if __name__ == "__main__":
    main()
