"""Place the USB-C PD support parts around the USB-C receptacle (J13) and the STUSB4500 (U10).

Each part goes next to the pad it serves, found from its nets:
  * the ESD / TVS parts and the USB data protection (D9, D10, U9) and the VBUS capacitor C49 at J13;
  * everything else (decoupling, address and reset resistors, VBUS sense / discharge, alert pull-up) at the U10 pin
    on the same net.
A part starts about 3 mm outward from its anchor pad and moves to the nearest spot where its courtyard is free.
J13 and U10 stay where you put them, and so does everything else on the board.

Close KiCad's PCB editor first. Backs up the board. Run with KiCad's Python from the kicad folder:
  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/place_usb_pd.py
"""
import math
import shutil
import sys
import time

import pcbnew

from place_mcu import PCB, PRO, Placer

MM = 1e6
AT_J13 = ("D9", "D10", "U9", "C49")
AT_U10 = ("C46", "C47", "C48", "R38", "R39", "R40", "R41", "R42", "R43")
IGNORE = ("GND", "+3V3", "+3V3_AUX")


def pads_by_net(fp):
    out = {}
    for p in fp.Pads():
        out.setdefault(p.GetNetname(), []).append(p)
    return out


def main():
    shutil.copy2(PCB, PCB.with_suffix(".kicad_pcb.bak"))
    pro_bytes = PRO.read_bytes()
    board = pcbnew.LoadBoard(str(PCB))
    ref = board.FindFootprintByReference
    j13, u10 = ref("J13"), ref("U10")
    pl = Placer(board, u10)
    pl.pending = set(AT_J13 + AT_U10)
    for g in board.Groups():
        for r in pl.pending:
            if ref(r) in g.GetItems():
                g.RemoveItem(ref(r))
    centre = {id(j13): j13.GetPosition(), id(u10): u10.GetPosition()}
    nets = {id(j13): pads_by_net(j13), id(u10): pads_by_net(u10)}
    report = []
    for r in AT_J13 + AT_U10:
        fp = ref(r)
        ic = j13 if r in AT_J13 else u10
        # first net of the part that appears on that IC (not a plain rail), else any net on the other IC
        cand = None
        for ic_try in (ic, u10 if ic is j13 else j13):
            for p in fp.Pads():
                n = p.GetNetname()
                if n in nets[id(ic_try)] and n not in IGNORE:
                    cand, ic = nets[id(ic_try)][n], ic_try
                    break
            if cand:
                break
        if not cand:
            cand = [pl.u1.Pads().__iter__().__next__()]
        cp = centre[id(ic)]
        # the anchor pad nearest the middle of the pads on that net, ties to the one nearest U10
        anchor = min(cand, key=lambda p: (p.GetPosition().x - u10.GetPosition().x) ** 2
                     + (p.GetPosition().y - u10.GetPosition().y) ** 2)
        ap = anchor.GetPosition()
        dx, dy = ap.x - cp.x, ap.y - cp.y
        n = math.hypot(dx, dy) or 1.0
        if ic is j13:                       # receptacle sits on the left edge: parts go east of it
            tx, ty = ap.x / MM + 3.0, ap.y / MM
        else:
            tx, ty = ap.x / MM + dx / n * 3.0, ap.y / MM + dy / n * 3.0
        pl.put_near(fp, tx, ty, angle=0, show_ref=True)
        p = fp.GetPosition()
        report.append((r, fp.GetValue(), "at", ic.GetReference(), anchor.GetNumber(),
                       round(math.hypot(p.x - ap.x, p.y - ap.y) / MM, 1), "mm"))
    pcbnew.SaveBoard(str(PCB), board)
    for _ in range(5):
        try:
            PRO.write_bytes(pro_bytes)
            break
        except OSError:
            time.sleep(1)
    for row in report:
        print(*row)


if __name__ == "__main__":
    sys.exit(main())
