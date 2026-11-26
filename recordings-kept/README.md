# Recordings worth keeping

Raw BLIPR captures (see firmware/README.md for the format) kept in git as test cases for `firmware/test/replay`.

- `2026-11-26_22lr_cci_sv/` (s01041-s01045): the first real echoes. .22LR CCI Standard Velocity, Sean's rifle, Nov 26, Teensy 0.2.7 (window 900-1200, quick check off). The echo lasts ~6-8 ms (~2 m), 15-24 dB; the in-band trigger fires 2-4 ms after the muzzle. Teensy 0.2.8 reads 4 of 5: 992, 1029, 1029, 1042 fps. Reference (Athlon Rangecraft, same gun and ammo, Nov 21, 29 shots): avg 1017, SD 15.2, 980-1041.
