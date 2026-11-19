"""Compare two-terminal passives (R, C, L) between this project and the Pi minimal design.

Anonymous nets (nodes between two parts) are treated as '~'; the check is a multiset comparison
of (value, net, net). Differences are printed.
"""
import collections
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import netlist  # noqa: E402
from compare_pi import PI_SCH, norm  # noqa: E402

KNOWN = {"GND", "+3V3", "+1V1", "VREG_AVDD", "VREG_LX", "XIN", "XOUT", "QSPI_SS", "RUN", "USB_D+",
         "USB_D-", "USB_DP_CHIP", "USB_DM_CHIP", "FLASH_SS", "GPIO0", "FLASH2_SS"}


def parts(root_sch, tag):
    out = Path(tempfile.gettempdir()) / f"{tag}.xml"
    subprocess.run([netlist.KICAD_CLI, "sch", "export", "netlist", str(root_sch), "--format",
                    "kicadxml", "-o", str(out)], check=True, capture_output=True)
    t = ET.parse(out).getroot()
    val = {c.get("ref"): c.findtext("value") or "" for c in t.find("components")}
    pins = collections.defaultdict(dict)
    for n in t.find("nets"):
        for nd in n:
            pins[nd.get("ref")][nd.get("pin")] = n.get("name")
    res = collections.Counter()
    for ref, p in pins.items():
        if ref[0] in "RCL" and ref[1].isdigit() and len(p) == 2 and ref[0] != "#":
            v = val[ref]
            if v in ("DNF", "DNP second memory") or v.startswith("DNP"):
                continue
            nets = sorted(n if (n := norm(x)) in KNOWN else "~" for x in p.values())
            res[(v, tuple(nets))] += 1
    return res


def main():
    pi = parts(PI_SCH, "pi_p")
    me = parts(netlist.ROOT, "me_p")
    # ignore parts that live outside the MCU core in the Pi design (input supply, headers)
    skip = {("10u", ("+3V3", "GND")), ("10u", ("GND", "~")), ("10u", ("GND", "~"))}
    for k in sorted(set(pi) | set(me), key=str):
        a, b = pi.get(k, 0), me.get(k, 0)
        mark = "" if a == b else "   <-- differs"
        print(f"{k[0]:6} {str(k[1]):28} Pi={a} ours={b}{mark}")


if __name__ == "__main__":
    main()
