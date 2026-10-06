"""Run KiCad DRC on the PCB and print a compact summary.

Usage: python drc_report.py [--type TYPE] [--refill]
  default: counts per violation type with a few examples, plus the unconnected-pad count
  --type TYPE: list every violation of that type with coordinates (mm)
  --refill: refill zones before checking
"""
import collections
import json
import subprocess
import sys
import tempfile
from pathlib import Path

KICAD_CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
PCB = Path(__file__).resolve().parent.parent / "picomondo.kicad_pcb"


def run(refill=False):
    out = Path(tempfile.gettempdir()) / "picomondo_drc.json"
    cmd = [KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "--all-track-errors",
           "--schematic-parity", "--output", str(out)]
    if refill:
        cmd.append("--refill-zones")
    r = subprocess.run(cmd + [str(PCB)], capture_output=True, text=True)
    if not out.exists():
        sys.exit("DRC produced no report:\n" + r.stdout + r.stderr)
    return json.loads(out.read_text(encoding="utf-8"))


def main():
    want = sys.argv[sys.argv.index("--type") + 1] if "--type" in sys.argv else None
    d = run("--refill" in sys.argv)
    groups = {"violations": d.get("violations", []), "unconnected": d.get("unconnected_items", []),
              "schematic parity": d.get("schematic_parity", [])}
    counts = collections.Counter()
    examples = collections.defaultdict(list)
    for kind, items in groups.items():
        for v in items:
            key = (v.get("severity", "-"), v.get("type", kind))
            counts[key] += 1
            where = "; ".join(f"{i['description']} @({i['pos']['x']:.2f},{i['pos']['y']:.2f})"
                              for i in v.get("items", [])[:2])
            examples[v.get("type", kind)].append(f"{v.get('description','')}: {where}")
    if want:
        print(*examples.get(want, []), sep="\n")
        return
    for (sev, typ), n in sorted(counts.items()):
        print(f"{sev:8} {typ:28} {n}")
        for line in examples[typ][:2]:
            print("          ", line[:200])
    if not counts:
        print("DRC clean")


if __name__ == "__main__":
    main()
