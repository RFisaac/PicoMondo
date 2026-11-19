# PicoMondo working project

Open `picomondo_reduced.kicad_pro` in KiCad 10.

This is the live design: v1 as ordered, plus changes made since. Anything here may be half-finished. To build or debug the boards that were actually made, use `../archive/v1-as-ordered/` instead.

## Changes since the v1 order

- **PSRAM (in progress, paused):** U16 APS6404L-3SQR (SOIC-8) and C71 100 nF added on the MCU sheet (2026-11-03) as an optional second QSPI memory. The schematic symbol is a W25Q128JVS borrowed for its pinout. It is placed on the board but not finished or checked.

## Sheets

| Sheet | Contents |
|---|---|
| `mcu_core` | RP2350B, VREG, crystal, flash, PSRAM, BOOTSEL/RESET, SWD |
| `barrel_input` | Barrel jack, PTC fuse, TVS, LM74502 reverse/overvoltage cut-off |
| `power_5v` | LMR33630B buck and the USB/barrel diode OR |
| `power_3v3` | AP2112K-3.3 LDO |
| `usb_c` | USB-C receptacle, CC resistors, ESD |
| `switched_output` | High-side P-FET output, INA226 monitor, fuse, flyback |
| `edgelock` | EdgeLock connectors, header holes, 100 Ω series resistors |
| `io_indicators` | Per-GPIO indicator LED ring |
| `neopixel` | NeoPixel buffer and connector, Qwiic |
| `board_support` | microSD, status/user/power LEDs, I2C pull-ups, test points |

## Libraries

- `lib/picomondo.pretty`: custom footprints (EdgeLock with 1.0 mm notches, header-hole and heavy-hole variants, RP2350 QFN-80 with thermal vias, polarity-marked VREG inductor, small-pad 0402).
- `lib/lcsc/`: parts converted from LCSC/EasyEDA with `easyeda2kicad`, with 3D models.
- `lib/MCU_RaspberryPi_RP2350.kicad_sym`: Raspberry Pi's RP2350 symbol.
- `JLCImport.*`: the JST-XH NeoPixel connector. One 3D model (`XY-SM04B-SRSS-TB.wrl`, the Qwiic connector) points at a global `${KICAD10_3RD_PARTY}` library and only shows if you have it installed.

## Fabrication

JLCPCB output is made with the Fabrication Toolkit plugin (settings in `fabrication-toolkit-options.json`). Generated `production/`, `jlcpcb/` and `bom/` folders are git-ignored here; the files that were actually ordered are in `../archive/v1-as-ordered/jlc_order_files/`.
