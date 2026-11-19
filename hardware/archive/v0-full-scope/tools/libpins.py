"""Print the pins (number, name, type, position) of symbols in a .kicad_sym library.

Usage: python libpins.py LIBFILE [NAME_SUBSTRING]
       LIBFILE may be a path or a standard library name such as Device or Regulator_Linear.
"""
import sys
from pathlib import Path

from kiutils.symbol import SymbolLib

STD = Path(r"C:\Program Files\KiCad\10.0\share\kicad\symbols")


def main():
    lib_arg = sys.argv[1]
    path = Path(lib_arg)
    if not path.exists():
        path = STD / f"{lib_arg}.kicad_sym"
    flt = sys.argv[2].lower() if len(sys.argv) > 2 else ""
    for s in SymbolLib.from_file(str(path)).symbols:
        if flt and flt not in s.entryName.lower():
            continue
        fp = next((p.value for p in s.properties if p.key == "Footprint"), "")
        lcsc = next((p.value for p in s.properties if p.key == "LCSC Part"), "")
        print(f"== {s.entryName}  footprint={fp}  lcsc={lcsc}  extends={s.extends}")
        pins = [p for u in s.units for p in u.pins] + list(s.pins)
        for p in sorted(pins, key=lambda p: (len(str(p.number)), str(p.number))):
            print(f"   pin {str(p.number):>3} {p.name:14} {p.electricalType:13} "
                  f"at ({p.position.X},{p.position.Y},{p.position.angle})")


if __name__ == "__main__":
    main()
