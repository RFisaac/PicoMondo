"""Place the SWD header (J10) and the BOOTSEL / RESET buttons (SW1, SW2) on the right side of the board.

They go in the free strip to the right of the Arduino shield outline (so they stay reachable with a shield fitted), in line
with the chip's RUN / SWD pins. J10 is turned so its mating face points at the right board edge. Each part is moved to
the nearest free spot to its target. The 1 k resistors R8 / R9 are left for later.

Close KiCad's PCB editor first. Backs up the board. Run with KiCad's Python from the kicad folder:
  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/place_swd_switches.py
"""
import shutil
import sys
import time

import pcbnew

from place_mcu import PCB, PRO, Placer

TARGETS = {          # ref: (x, y, orientation)
    "SW2": (128.0, 66.0, 0),         # RESET
    "SW1": (128.0, 78.0, 0),         # BOOTSEL
    "J10": (145.0, 72.0, 270),       # SWD: mating face towards the right edge
}


def main():
    shutil.copy2(PCB, PCB.with_suffix(".kicad_pcb.bak"))
    pro_bytes = PRO.read_bytes()
    board = pcbnew.LoadBoard(str(PCB))
    pl = Placer(board, board.FindFootprintByReference("U1"))
    pl.pending = set(TARGETS)
    for g in board.Groups():
        for r in TARGETS:
            if board.FindFootprintByReference(r) in g.GetItems():
                g.RemoveItem(board.FindFootprintByReference(r))
    for ref, (x, y, a) in TARGETS.items():
        pl.put_near(board.FindFootprintByReference(ref), x, y, angle=a, show_ref=True)
        p = board.FindFootprintByReference(ref).GetPosition()
        print(ref, round(p.x / 1e6, 1), round(p.y / 1e6, 1))
    pcbnew.SaveBoard(str(PCB), board)
    for _ in range(5):
        try:
            PRO.write_bytes(pro_bytes)
            break
        except OSError:
            time.sleep(1)


if __name__ == "__main__":
    sys.exit(main())
