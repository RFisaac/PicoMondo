"""Write LCSC part numbers and MPNs from bom/parts.csv into the schematic symbols.

parts.csv is keyed by (Value, Footprint). Every symbol whose pair matches gets hidden "LCSC" and "MPN" fields
(empty cells are left alone). FOOTPRINT_CHANGES swaps footprints first, so a part can change package here.

Does not touch placement or wiring. Close KiCad's schematic editor first, then run:  python apply_parts.py
After that, in the PCB editor use Tools > Update PCB from Schematic (F8) to copy the fields and any footprint change
to the board. (make_sw_fp.py creates the new switch footprint; swap_footprints.py can do the board side for you while
KiCad is closed.)
"""
import copy
import csv
import sys
from pathlib import Path

from kiutils.items.common import Effects, Font, Position, Property
from kiutils.schematic import Schematic

ROOT = Path(__file__).resolve().parent.parent
PARTS = ROOT / "bom" / "parts.csv"

FOOTPRINT_CHANGES = {
    "Button_Switch_SMD:SW_Push_1P1T_NO_Vertical_Wuerth_434133025816": "picomondo:SW_SMD_TS-1187A_5.1x5.1",
}


def prop(sym, key):
    return next((p for p in sym.properties if p.key == key), None)


def set_field(sym, key, value):
    p = prop(sym, key)
    if p is not None:
        p.value = value
        return
    ref = prop(sym, "Reference")
    nid = max((q.id or 0) for q in sym.properties) + 1
    pos = Position(ref.position.X, ref.position.Y, 0) if ref and ref.position else Position(0, 0, 0)
    sym.properties.append(Property(key=key, value=value, id=nid, position=pos,
                                   effects=Effects(font=Font(height=1.27, width=1.27), hide=True)))


def main():
    table = {(r["Value"], r["Footprint"]): r for r in csv.DictReader(open(PARTS, encoding="utf-8"))}
    changed = missing = 0
    for path in sorted(ROOT.glob("*.kicad_sch")):
        sch = Schematic.from_file(str(path))
        dirty = False
        for sym in sch.schematicSymbols:
            ref, val, fp = prop(sym, "Reference"), prop(sym, "Value"), prop(sym, "Footprint")
            if not (ref and val and fp) or ref.value.startswith("#"):
                continue
            if fp.value in FOOTPRINT_CHANGES:
                fp.value = FOOTPRINT_CHANGES[fp.value]
                dirty = True
            row = table.get((val.value, fp.value))
            if row is None:
                missing += 1
                print("no row for", ref.value, val.value, fp.value)
                continue
            for key in ("LCSC", "MPN"):
                if row[key] and (prop(sym, key) is None or prop(sym, key).value != row[key]):
                    set_field(sym, key, row[key])
                    dirty = True
                    changed += 1
        if dirty:
            sch.to_file(str(path))
            print("updated", path.name)
    print(f"{changed} fields written, {missing} symbols without a row")


if __name__ == "__main__":
    sys.exit(main())
