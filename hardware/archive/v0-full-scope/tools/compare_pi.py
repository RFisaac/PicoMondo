"""Compare the RP2350B pin connections in this project with the Raspberry Pi minimal design.

Usage: python compare_pi.py
Needs the Pi netlist XML exported to the temp dir first (done automatically).
"""
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import netlist  # noqa: E402

PI_SCH = (Path(__file__).resolve().parent.parent.parent / "resources" / "pi-reference" / "kicad" /
          "RP2350B Minimal Board" / "RP2350_80QFN_minimal.kicad_sch")

# Pi net name -> our net name
RENAME = {"SWD": "SWDIO", "Net-(U1-USB_DM)": "USB_DM_CHIP", "Net-(U1-USB_DP)": "USB_DP_CHIP"}


def pi_pins():
    out = Path(tempfile.gettempdir()) / "pi_net.xml"
    subprocess.run([netlist.KICAD_CLI, "sch", "export", "netlist", str(PI_SCH), "--format",
                    "kicadxml", "-o", str(out)], check=True, capture_output=True)
    t = ET.parse(out).getroot()
    pins = {}
    for n in t.find("nets"):
        for nd in n:
            if nd.get("ref") == "U1":
                pins[nd.get("pin")] = n.get("name")
    return pins


def norm(name):
    name = name.split("/")[-1]       # drop sheet path of local nets
    if name.startswith("GPIO") and "_ADC" in name:
        name = name.split("_")[0]
    return RENAME.get(name, name)


def main():
    pi = {p: norm(n) for p, n in pi_pins().items()}
    _, _, mine_pins = netlist.load()
    mine = {p: norm(n) for p, n in mine_pins["U1"].items()}
    bad = 0
    for p in sorted(pi, key=int):
        if p == "81":
            continue
        a, b = pi[p], mine.get(p)
        if b is None or a != b:
            print(f"pin {p:>2}: Pi={a!r}  ours={b!r}")
            bad += 1
    print("mismatches:", bad, "of", len(pi) - 1, "compared pins (pin 81 = exposed pad GND not compared)")


if __name__ == "__main__":
    main()
