# PicoMondo v1: archived as ordered

This is a frozen copy of the KiCad project matching the first JLCPCB order
(5 assembled boards, ordered late October 2026). Open it for building and
troubleshooting those boards. Don't develop new work here.

## Where it came from
- KiCad project files: the KiCad auto-backup `picomondo_reduced-2026-10-28_152341.zip`.
- `jlc_order_files/`: the gerbers (generated 2026-10-26 14:07), BOM and CPL from `jlcpcb/production_files/`.
- The PCB is byte-identical to the board file saved at 2026-10-26 14:06. It didn't change until 2026-11-03.
  Every placed part in the CPL lands at the same position as on this board, apart from the usual
  JLC rotation/offset corrections on connectors.
- There's no PSRAM (U16/C71). It was added on 2026-11-03, after this order.

## Notes for hand assembly
The order arrived as bare PCBs (no JLC assembly), so every part is hand-soldered.
- R5 (0 Ω, GPIO0 to FLASH_SS): **don't fit it.** On this board it ties GPIO0 to the main flash chip-select.
  R4 (10k pull-up on FLASH_SS) is optional.
- D21, D22, R82 and R83 (the I2C activity LEDs): optional. They load the I2C lines. If you fit them and the bus
  is flaky, remove R82/R83 or use 10k or larger.
- J13 (barrel jack) is through-hole and was always meant to be fitted by hand.
- The original 3D models for JLCImport parts aren't included. That only affects 3D view.
