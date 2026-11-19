"""Place each EdgeLock 100 ohm series resistor in line with its connector pin.

For every signal pad of the EdgeLock connectors (J1-J6, J9) the matching resistor is put straight inboard of the pad
(along the pad's length, away from the board edge), OFFSET mm from the pad centre, long axis along the pin, with the
connector-side resistor pad nearest the connector. Resistors listed in KEEP are left where they are.

Close KiCad's PCB editor first. Backs up the board, moves only these resistors (and takes them out of any group so
they box-select on their own). Run with KiCad's Python:
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools\\place_edgelock_resistors.py [--offset 6.5] [--keep R44]
"""
import argparse
import math
import shutil
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "picomondo.kicad_pcb"
PRO = ROOT / "picomondo.kicad_pro"
MM = 1e6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offset", type=float, default=6.5, help="mm from pad centre to resistor centre")
    ap.add_argument("--keep", nargs="*", default=["R44"], help="resistors to leave alone")
    args = ap.parse_args()

    shutil.copy2(PCB, PCB.with_suffix(".kicad_pcb.bak"))
    pro_bytes = PRO.read_bytes()
    board = pcbnew.LoadBoard(str(PCB))
    resistors = [fp for fp in board.GetFootprints() if fp.GetValue() == "100" and fp.GetReference().startswith("R")]
    moved = []
    for conn in sorted((fp for fp in board.GetFootprints() if "EdgeLock" in str(fp.GetFPID().GetLibItemName())),
                       key=lambda f: f.GetReference()):
        theta = math.radians(conn.GetOrientationDegrees())
        # footprint -Y (towards the board interior) in board coordinates
        ux, uy = math.sin(theta), -math.cos(theta)
        for pad in conn.Pads():
            net = pad.GetNetname()
            if not net.startswith("Net-("):
                continue
            r = next((fp for fp in resistors if any(p.GetNetname() == net for p in fp.Pads())), None)
            if r is None:
                print("no resistor for", conn.GetReference(), pad.GetNumber(), net)
                continue
            if r.GetReference() in args.keep:
                continue
            p = pad.GetPosition()
            r.SetPosition(pcbnew.VECTOR2I(int(p.x + ux * args.offset * MM), int(p.y + uy * args.offset * MM)))
            # long axis along the pin; the pad on the connector net must be the one nearest the connector
            for angle in (90, 270):
                r.SetOrientationDegrees(angle)
                near = next(q for q in r.Pads() if q.GetNetname() == net)
                far = next(q for q in r.Pads() if q.GetNetname() != net)
                d_near = (near.GetPosition().x - p.x) ** 2 + (near.GetPosition().y - p.y) ** 2
                d_far = (far.GetPosition().x - p.x) ** 2 + (far.GetPosition().y - p.y) ** 2
                if d_near < d_far:
                    break
            for g in board.Groups():
                if r in g.GetItems():
                    g.RemoveItem(r)
            moved.append((r.GetReference(), conn.GetReference(), pad.GetNumber()))
    pcbnew.SaveBoard(str(PCB), board)
    import time
    for _ in range(5):                                  # pcbnew rewrites the project file; keep yours
        try:
            PRO.write_bytes(pro_bytes)
            break
        except OSError:
            time.sleep(1)
    print(f"moved {len(moved)} resistors:", ", ".join(f"{r}->{c}.{n}" for r, c, n in moved))


if __name__ == "__main__":
    sys.exit(main())
