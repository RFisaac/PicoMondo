"""Search KiCad's standard symbol and footprint libraries by name.

Usage: python symfind.py PATTERN [PATTERN ...]     (case-insensitive substring match)
       python symfind.py -f PATTERN                (search footprints instead)
Prints  Library:Symbol  and the default footprint for symbols.
"""
import re
import sys
from pathlib import Path

BASE = Path(r"C:\Program Files\KiCad\10.0\share\kicad")


def symbols(pats):
    for f in sorted((BASE / "symbols").glob("*.kicad_sym")):
        text = f.read_text(encoding="utf-8", errors="ignore")
        # top-level symbols are indented two spaces; unit sub-symbols end in _N_N
        for m in re.finditer(r'^\t\(symbol "([^"]+)"', text, re.M):
            name = m.group(1)
            if re.search(r"_\d+_\d+$", name):
                continue
            if all(p.lower() in name.lower() for p in pats):
                seg = text[m.end():m.end() + 1500]
                fp = re.search(r'\(property "Footprint" "([^"]*)"', seg)
                print(f"{f.stem}:{name}   fp={fp.group(1) if fp else ''}")


def footprints(pats):
    for d in sorted((BASE / "footprints").glob("*.pretty")):
        for f in d.glob("*.kicad_mod"):
            if all(p.lower() in f.stem.lower() for p in pats):
                print(f"{d.stem}:{f.stem}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "-f":
        footprints(args[1:])
    else:
        symbols(args)
