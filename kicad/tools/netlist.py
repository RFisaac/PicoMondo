"""Export the project netlist with kicad-cli and print it per part or per net.

Usage:
  python netlist.py                 # summary: net count, parts
  python netlist.py --ref U1        # every pin of a part with its net
  python netlist.py --net +3V3      # every pin on a net
  python netlist.py --nets          # list net names with pin counts
"""
import collections
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

KICAD_CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
ROOT = Path(__file__).resolve().parent.parent / "picomondo.kicad_sch"


def load():
    out = Path(tempfile.gettempdir()) / "picomondo_net.xml"
    subprocess.run([KICAD_CLI, "sch", "export", "netlist", str(ROOT), "--format", "kicadxml",
                    "-o", str(out)], check=True, capture_output=True)
    t = ET.parse(out).getroot()
    values = {c.get("ref"): c.findtext("value") or "" for c in t.find("components")}
    nets = collections.OrderedDict()
    pins = collections.defaultdict(dict)
    for n in t.find("nets"):
        name = n.get("name")
        nets[name] = [(nd.get("ref"), nd.get("pin"), nd.get("pinfunction") or "") for nd in n]
        for nd in n:
            pins[nd.get("ref")][nd.get("pin")] = name
    return values, nets, pins


def main():
    values, nets, pins = load()
    a = sys.argv
    if "--ref" in a:
        ref = a[a.index("--ref") + 1]
        for p, net in sorted(pins[ref].items(), key=lambda kv: (len(kv[0]), kv[0])):
            print(f"{ref}.{p:>3} -> {net}")
    elif "--net" in a:
        want = a[a.index("--net") + 1]
        # local nets are named /<sheet>/<net>; accept the short name too
        for net, members in nets.items():
            if net == want or net.endswith("/" + want):
                for ref, pin, fn in members:
                    print(f"{net}: {ref}.{pin} {fn} ({values.get(ref,'')})")
    elif "--nets" in a:
        for name, members in nets.items():
            print(f"{len(members):3} {name}")
    else:
        print(len(values), "parts,", len(nets), "nets")


if __name__ == "__main__":
    main()
