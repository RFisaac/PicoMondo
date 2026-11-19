# Archived designs

Neither of these is meant for new work.

## `v1-as-ordered/`

Frozen copy of the KiCad project matching the first JLCPCB order (October 2026). `README_AS_ORDERED.md` says where it came from and lists the hand-assembly gotchas. `jlc_order_files/` holds the exact gerbers, BOM and CPL that were submitted.

3D models were not included in this copy; the board opens and checks fine, the 3D view just has gaps.

`hand-assembly/` holds aids made afterwards for building the bare boards by hand:
- `picomondo_v1_IBOM_ONLY.kicad_pcb`: the as-ordered board plus a "fake board" drawn beside it, a model of the parts organiser (BOXALL96 lid and base) with every part assigned a bin. It exists only to generate the interactive BOM, which lives at [`docs/ibom/index.html`](../../docs/ibom/index.html). Don't use it for fabrication.
- `stencil_top_F_Paste.dxf`: F.Paste layer exported 2026-11-09 for laser-cutting a Mylar stencil. It was exported from the working project, so check it against the bare board before cutting (it may include pads for the later PSRAM footprint).

## `v0-full-scope/`

The first full design (February to October 2026): a 10-sheet schematic with USB-PD (STUSB4500), a TPS55288 5 A buck-boost, INA219/INA226 monitors, two switched outputs, three power inputs and Arduino/Pico sockets. The layout would not route and the scope was cut back to v1 in October 2026.

Worth keeping because the v2 candidates were already designed here:
- `DECISIONS.md`: design decisions and findings checked against Raspberry Pi documents (flash size limit, crystal load caps, VREG values, USB trace geometry). The verified findings still apply to v1.
- `docs/`: per-sheet design notes (buck-boost, USB-PD, power input, LDO thermal limits, outputs, I/O, PCB).
- `bom/`: JLCPCB part choices for every part on that board.
- `tools/`: the Python scripts that generated and placed the schematic and board (KiCad file manipulation, placement, BOM/CPL generation, datasheet fetching).

3D model folders were left out to save space; footprints and symbols are intact.
