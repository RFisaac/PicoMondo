# Molex EdgeLock (series 200890)

Board-edge wire-to-board connector used for J1-J6 and J9. The board edge carries contact pads and
cut-outs; a crimped wire housing clips over it.

| Folder | Contents |
|--------|----------|
| `docs/` | Molex product specification (2008900001PS), brochure, older product spec |
| `docs/drawings/` | Sales drawings `2008900nnn_sd.pdf` (sheet 2 is the PCB layout, contact side: the one that matters) |
| `docs/product-pages/` | Molex product-page printouts for 2008900102 / 104 / 106 / 108 |
| `3d/` | STEP models of the housings (Molex via TraceParts) |
| `kicad-vendor/` | Vendor KiCad libraries as downloaded, unpacked: `molex-kicadv6_*` (used for the project footprints; includes the board notches), `snapeda_*` (rounded notch corners, but pads have no mask opening), `other_*` (pads only) |
| `downloads/` | Original archives, unchanged |

Part numbers: `2008900106` = 6 circuits for a 1.6 mm board (J1-J4, J6, J9), `2008900104` = 4 circuits (J5).
`20089002nn` is the same housing for 1.2 mm boards. Terminal: Molex 2004490001 (series 200449).
The project footprints are generated from `molex-kicadv6_*` by `kicad/tools/make_edgelock_fp.py`.
