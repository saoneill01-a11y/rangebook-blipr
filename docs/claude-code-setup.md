# Working on BLIPR with Claude Code on your laptop

Claude Code runs on your own computer, so it can do what a chat in the browser can't: build the firmware,
flash both boards over USB, talk to them over the serial port, log a shooting session, pull the raw
recordings off the SD card, replay them through the velocity code, change the filtering and flash again.
This repo has a `CLAUDE.md` at the top, which Claude Code reads every time it starts here, so it knows the
project, the tools in this folder and the rules.

## 1. Install (once)

**Claude Code.** Open a terminal (Mac: Terminal; Windows: PowerShell) and run:

- Mac: `curl -fsSL https://claude.ai/install.sh | bash`
- Windows (PowerShell): `irm https://claude.ai/install.ps1 | iex`
  (also install [Git for Windows](https://git-scm.com/downloads/win))

Open a new terminal and check it with `claude --version`. It asks you to sign in the first time you run it.
The Claude desktop app's **Code** tab works too, if you'd rather not use a terminal.
Instructions current as of October 2026; see https://code.claude.com/docs/en/overview if they've changed.

**Git and GitHub.** You need `git` and to be signed in to GitHub, because the repo is private. The easiest
way is the GitHub CLI: install it from https://cli.github.com, then run `gh auth login`.

**Python 3** (Mac: already there, or `brew install python`; Windows: python.org or the Microsoft Store).

Everything else (the Arduino command-line tools, the Teensy and ESP32 board packages, the libraries,
pyserial, numpy) Claude Code installs for you in step 3.

## 2. Get the project

```
gh repo clone saoneill01-a11y/rangebook-blipr
cd rangebook-blipr
claude
```

## 3. First session: let Claude Code set up the tools

Plug in the Teensy and the ESP32 (USB data cables, not charge-only ones) and say something like:

> Set up the build tools from CLAUDE.md, build both firmwares, and check you can see both boards.

It will install `arduino-cli`, the Teensy and ESP32 board packages and the libraries, build both sketches,
and list the serial ports. It records anything it learned about your laptop (port names, the exact
Teensy USB-type option) in CLAUDE.md under "This computer", so the next session starts ready.

**The very first flash** may need a button:
- **Teensy:** if the upload waits, press the little white button on the Teensy once.
- **ESP32-C3 SuperMini:** if it won't connect, hold **BOOT**, tap **RESET**, let go of BOOT, then upload
  again. After the first time, uploads are hands-off (and Range Book can update the ESP32 over Bluetooth).

## 4. A shooting session at home

1. Put BLIPR where it'll sit, with the Teensy's USB cable to the laptop. Keep the laptop and cable
   behind the firing line, out of the muzzle blast.
2. Ask Claude Code to start logging, for example:
   > Start a logged session: 6.5 CM 140 ELD-M, BLIPR 30 cm behind and 12 cm right of the muzzle.
   It runs `python tools/blipr_log.py --note "..."`, which arms the Teensy (plugging into a computer
   pauses shots for USB drive mode; the logger turns that off), turns on saving the raw recordings,
   and prints every shot with a running average, SD and extreme spread. Everything goes into
   `sessions/<date_time>/`.
3. Shoot a string. If you have another chronograph, read its numbers to Claude Code as you go.
4. Between strings, ask it to look: it can send commands to the Teensy without stopping the logger,
   pull the recordings, replay them, and change and reflash the firmware.

## 5. Working on the noise and the filtering

The Teensy saves the raw radar signal of every shot to the SD card (`set save=1`). Those recordings
are what to tune from, because the same shots can be run through every version of the code.

```
python tools/pull_shots.py /Volumes/SDCARD          # copy new recordings into recordings/<today>/
firmware/test/replay recordings/2026-10-25/*.bin    # run them through the current velocity code
```

To get the recordings: take the micro SD card out of the Teensy and use a card reader (simplest), or
use USB drive mode (the SD card shows up as "BLIPR SD": Windows shows it in File Explorer; a Mac needs an
MTP app such as OpenMTP to copy the `shots` folder out first).

`replay` prints each shot's recorded velocity next to what the current code gets, and can write every
frame's peak (`--peaks`) for plotting. A filtering change should keep every good shot within a fraction of
an fps of its old value (or move it toward the reference chronograph) and pick up shots the old code
missed, before it goes on the board. `tools/make_test_recordings.py` makes fake recordings for testing
without the hardware, and `firmware/test/sim_test.cpp` checks the math on simulated shots.

## 6. Sharing results

Recordings and session logs stay on your laptop (`recordings/` and `sessions/` aren't saved to git;
a shot is about 300 KB). Commit any that are worth keeping into `recordings-kept/` with a note, and
push, so a later session (or a chat on claude.ai) can see them.
