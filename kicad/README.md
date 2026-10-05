# PicoMondo KiCad project

Open `picomondo.kicad_pro` in KiCad 10. See [DECISIONS.md](DECISIONS.md) for what has been decided.
Reference designs and source material are in `../resources/`.

## Status

| Sheet | File | State |
|-------|------|-------|
| MCU core (RP2350B, regulator, crystal, flash, boot/reset, USB resistors, SWD) | `mcu_core.kicad_sch` | Done; all 80 MCU pin connections match the Pi minimal design |
| 5 V buck-boost (TPS55288) | `power_buck.kicad_sch` | Done, ERC clean (docs/power_buck_boost.md) |
| Power input (diode-OR, fuse, TVS, connectors) | `power_input.kicad_sch` | Done (docs/power_input.md) |
| 3.3 V regulators (AP2112K x2) | `power_ldo.kicad_sch` | Done (docs/power_ldo.md) |
| Switched outputs J7 / J8 / +5V_SW | `power_outputs.kicad_sch` | Done (docs/power_outputs.md) |
| USB-C + PD controller (STUSB4500) | `usb_pd.kicad_sch` | Done (docs/usb_pd.md) |
| EdgeLock connectors J1-J6, J9 | `io_edgelock.kicad_sch` | Done; real Molex footprints incl. board-edge notches (docs/io.md) |
| GPIO indicator LEDs | `io_indicators.kicad_sch` | Done |
| Arduino and Pico sockets | `io_headers.kicad_sch` | Done |
| microSD, WS2812, LEDs, pull-ups, test points, mounting | `io_misc.kicad_sch` | Done |
| PCB | `picomondo.kicad_pcb` | Created: outline, EdgeLock edge connectors, mounting holes, Arduino/Pico sockets placed; all parts imported, rest staged for you to place and route (docs/pcb.md) |

## How the schematic is built

Every part is placed explicitly and every connection is a pin stub ending in a net label or power
symbol, so net names (not wire routing) define the connections. GPIO, `RUN`, `USB_D+/-` and power
nets are global and join across sheets; other labels are local to their sheet.

`tools/` holds the generator and checkers:

| Script | Purpose |
|--------|---------|
| `build.py` | Creates the initial project files. **Overwrites** the schematics: do not run after editing in KiCad. |
| `kihelp.py`, `sheet_*.py` | Helper library and per-sheet definitions |
| `erc_report.py` | Runs KiCad ERC and prints a summary |
| `netlist.py` | Exports the netlist; `--ref U1`, `--net +3V3`, `--nets` |
| `compare_pi.py`, `compare_passives.py` | Check the MCU core against the Raspberry Pi reference |
| `make_pcb.py` | Creates the PCB once (needs KiCad's Python); see docs/pcb.md |
| `drc_report.py`, `project_settings.py` | PCB DRC summary; design rules and net classes |
| `add_shield_outlines.py` | Non-printing Uno and Pico outlines in the socket group |
| `apply_parts.py`, `sync_board_parts.py`, `bom.py` | LCSC numbers from `bom/parts.csv` into schematic and board; JLCPCB BOM, CPL and stock report |
| `fetch_datasheets.py`, `make_edgelock_fp.py`, `fix_lcsc_footprints.py`, `symfind.py`, `libpins.py` | Library and datasheet helpers |

Once a sheet has been edited in KiCad, that file is the source of truth. New sheets can be added
with the generator; edits to existing sheets should be made in KiCad or with kiutils
read-modify-write.

## Known ERC output

- `isolated_pin_label` on `GPIOn`: expected until the IO sheets exist.
- `lib_symbol_mismatch` on the crystal and flash: embedded copies differ cosmetically from the library.
