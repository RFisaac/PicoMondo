"""Footprint for the 5.1 x 5.1 mm 4-pad tactile switch XKB TS-1187A-B-A-B (LCSC C318884, JLCPCB basic part).

Pad geometry is EasyEDA's (pads 1.0 x 0.75 mm at x +-3.0, y +-1.85). Two of the four pads are joined inside the
switch along one side and the other two along the opposite side; the datasheet does not say which way round, so
the schematic pins go to the diagonal pads (always opposite contacts) and the other two pads are left unconnected.

  pad 1 = top left, pad 2 = bottom right (the switch contacts); pad 3, 4 = mechanical only

Run:  python make_sw_fp.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "lib" / "picomondo.pretty" / "SW_SMD_TS-1187A_5.1x5.1.kicad_mod"

SILK = [((-1.28, -2.55), (1.28, -2.55)), ((-1.28, 2.55), (1.28, 2.55)),
        ((-2.55, -1.17), (-2.55, 1.17)), ((2.55, -1.17), (2.55, 1.17)),
        ((-1.28, -2.55), (-2.17, -1.66)), ((1.28, -2.55), (2.17, -1.66)),
        ((-1.28, 2.55), (-2.17, 1.66)), ((1.28, 2.55), (2.17, 1.66))]


def build():
    lines = ['(footprint "SW_SMD_TS-1187A_5.1x5.1"',
             '  (version 20241229) (generator "pcbnew") (layer "F.Cu")',
             '  (descr "XKB TS-1187A-B-A-B 5.1x5.1x1.5 mm tactile switch (LCSC C318884). Pads 1 and 2 are the diagonal contacts.")',
             '  (tags "tactile switch smd 5.1mm")', '  (attr smd)']
    for name, y, layer in (("Reference", -4.0, "F.SilkS"), ("Value", 4.0, "F.Fab")):
        text = "REF**" if name == "Reference" else "SW_SMD_TS-1187A_5.1x5.1"
        lines.append(f'  (property "{name}" "{text}" (at 0 {y}) (layer "{layer}")'
                     f' (effects (font (size 1 1) (thickness 0.15))))')
    lines.append('  (fp_text user "${REFERENCE}" (at 0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))')
    for a, b in SILK:
        lines.append(f'  (fp_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width 0.15) (type solid)) (layer "F.SilkS"))')
    lines.append('  (fp_rect (start -3.7 -3.0) (end 3.7 3.0) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))')
    lines.append('  (fp_rect (start -2.55 -2.55) (end 2.55 2.55) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))')
    for num, x, y in (("1", -3.0, -1.85), ("2", 3.0, 1.85), ("3", 3.0, -1.85), ("4", -3.0, 1.85)):
        lines.append(f'  (pad "{num}" smd rect (at {x} {y}) (size 1.0 0.75) (layers "F.Cu" "F.Mask" "F.Paste"))')
    lines.append('  (model "${KIPRJMOD}/lib/lcsc/lcsc.3dshapes/SW-SMD_4P-L5.1-W5.1-P3.70-LS6.5-TL_H1.5.step"'
                 ' (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
    lines.append(")")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print("wrote", OUT.name)
