"""Run KiCad ERC on the project and print a compact summary.

Usage: python erc_report.py [--all] [--type TYPE]
  default: counts per type, plus the first few examples of each
  --type TYPE: list every violation of that type with coordinates (mm)
KiCad's JSON report scales coordinates by 1/100; they are converted back here.
"""
import collections
import json
import subprocess
import sys
import tempfile
from pathlib import Path

KICAD_CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
ROOT = Path(__file__).resolve().parent.parent / "picomondo.kicad_sch"


def run():
    out = Path(tempfile.gettempdir()) / "picomondo_erc.json"
    subprocess.run([KICAD_CLI, "sch", "erc", str(ROOT), "--format", "json", "--severity-all",
                    "-o", str(out)], check=True, capture_output=True)
    return json.loads(out.read_text(encoding="utf-8"))


def main():
    want = sys.argv[sys.argv.index("--type") + 1] if "--type" in sys.argv else None
    d = run()
    counts = collections.Counter()
    examples = collections.defaultdict(list)
    for sheet in d["sheets"]:
        for v in sheet["violations"]:
            counts[(v["severity"], v["type"])] += 1
            desc = "; ".join(f"{i['description']} @({i['pos']['x']*100:.2f},{i['pos']['y']*100:.2f})"
                             for i in v["items"][:2])
            examples[v["type"]].append(f"{sheet['path']} {v['description']}: {desc}")
    if want:
        for line in examples.get(want, []):
            print(line)
        return
    for (sev, typ), n in sorted(counts.items()):
        print(f"{sev:8} {typ:28} {n}")
        for line in examples[typ][:3]:
            print("          ", line[:200])
    if not counts:
        print("ERC clean")


if __name__ == "__main__":
    main()
