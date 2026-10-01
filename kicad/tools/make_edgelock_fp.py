"""Create the EdgeLock board-edge footprints from Molex's own KiCad footprints.

Source: resources/edgelock/kicad-vendor/molex-kicadv6_*/ (CONN_2008900206_nn_MOL). They match Molex's
sales drawing 2008900206 (PCB layout, contact side): pads 1.10 x 6.2 mm at 2.0 mm pitch, 0.9 mm
from the board edge, outer slots 7.1 mm deep, narrow slots 4.2 mm deep, 2.8 x 3.05 mm latch window.

Changes made here:
  * pads carry F.Cu and F.Mask only: they are bare (ENIG) contact fingers, so no solder paste;
  * the footprint is marked board-only (no BOM line, no pick-and-place row): the mating housing is bought
    separately;
  * renamed EdgeLock_<n>ckt_Molex2008900<1nn>.
The footprint's Edge.Cuts lines are the board-edge notches: place it on the board edge and connect the
board outline to its end points.

Run from kicad/tools:  python make_edgelock_fp.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT.parent / "resources" / "edgelock" / "kicad-vendor"
DST = ROOT / "lib" / "picomondo.pretty"

CIRCUITS = {2: "02", 4: "04", 6: "06", 8: "08"}

# STEP models are centred on the footprint origin with Y up; KiCad wants Z up
ROTATE = (-90, 0, 0)


def convert(n, nn):
    src = next((SRC / f"molex-kicadv6_{nn}ckt" / "KiCADv6" / "footprints.pretty").glob("*.kicad_mod"))
    text = src.read_text(encoding="utf-8")
    name = f"EdgeLock_{n}ckt_Molex20089001{nn}"
    text = re.sub(r'^\(footprint "[^"]+"', f'(footprint "{name}"', text, count=1)
    # pads: contact fingers only (copper + mask)
    text = text.replace('(layers "F.Cu" "F.Paste" "F.Mask")', '(layers "F.Cu" "F.Mask")')
    # board-only part
    text = re.sub(r"\(attr smd\)", "(attr smd board_only exclude_from_pos_files exclude_from_bom)", text, count=1)
    descr = (f'(descr "Molex Edge Lock 2008900{1}{nn} ({n}-circuit, 1.6 mm board) board-edge contact pads and board cut-outs. '
             f'Source: Molex sales drawing 2008900206 sheet 2; place on the board edge, connect the outline to the Edge.Cuts end points.")')
    text = text.replace(f'(tags "20089001{nn} ")', f'{descr}\n  (tags "molex edgelock 20089001{nn} edge connector")')
    model = ('  (model "${KIPRJMOD}/lib/3dmodels/edgelock/20089001%s.stp"\n'
             '    (offset (xyz 0 0 0))\n    (scale (xyz 1 1 1))\n'
             '    (rotate (xyz %s %s %s))\n  )\n' % (nn, ROTATE[0], ROTATE[1], ROTATE[2]))
    text = text.rstrip()
    assert text.endswith(")")
    text = text[:-1].rstrip() + "\n" + model + ")\n"
    src_text = text
    Path(DST / f"{name}.kicad_mod").write_text(src_text, encoding="utf-8")
    return name, len(re.findall(r"\(pad ", src_text))


if __name__ == "__main__":
    for n, nn in CIRCUITS.items():
        name, pads = convert(n, nn)
        print(f"{name}: {pads} pads")
