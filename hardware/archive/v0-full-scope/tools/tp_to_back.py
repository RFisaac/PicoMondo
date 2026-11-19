"""Move every test point (TP1...) to the back of the board, keeping its x/y position.

Test points on the bottom side give a pogo-pin test fixture one face to probe, and keep the top free for parts.
Their pads become B.Cu / B.Mask. Re-running does nothing for points already on the back.

Close KiCad's PCB editor first. Backs up the board. Run with KiCad's Python from the kicad folder:
  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/tp_to_back.py
"""
import re
import shutil
import sys
import time
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "picomondo.kicad_pcb"
PRO = ROOT / "picomondo.kicad_pro"


def main():
    shutil.copy2(PCB, PCB.with_suffix(".kicad_pcb.bak"))
    pro_bytes = PRO.read_bytes()
    board = pcbnew.LoadBoard(str(PCB))
    moved = []
    for fp in board.GetFootprints():
        if re.fullmatch(r"TP\d+", fp.GetReference()) and fp.GetLayer() == pcbnew.F_Cu:
            fp.Flip(fp.GetPosition(), False)
            moved.append(fp.GetReference())
    pcbnew.SaveBoard(str(PCB), board)
    for _ in range(5):
        try:
            PRO.write_bytes(pro_bytes)
            break
        except OSError:
            time.sleep(1)
    print(f"flipped {len(moved)} test points to B.Cu")


if __name__ == "__main__":
    sys.exit(main())
