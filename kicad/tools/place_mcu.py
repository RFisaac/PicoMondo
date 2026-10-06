"""Place the RP2350B and the passives that belong right next to it.

U1 goes between the two Pico socket rows, shifted left of the board centre and turned so the side with the regulator,
USB and QSPI pins faces left (towards the power input and USB-C). Every part is placed from the real pad positions:

  * one 100 nF at each +3V3 supply pin (pins 59/60 and 68/69 share one) and at each +1V1 pin
  * the on-chip regulator parts (L1, C1, C2, C5, C6, R1) at pins 61-65
  * the crystal group (Y1, C17, C18, R2) near pins 30/31
  * the flash U2 with its 100 nF and the CS link R3, and the USB series resistors R10, R11

Each part starts at its pin and slides sideways, then outward, until its courtyard clears everything already on the
board. Not placed: the SWD header, BOOT/RESET switches, pull-ups, the DNP second flash and its parts.

Close KiCad's PCB editor first. Backs up the board. Run with KiCad's Python from the kicad folder:
  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/place_mcu.py [--x 80 --y 75 --angle 90]
"""
import argparse
import math
import shutil
import sys
import time
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "picomondo.kicad_pcb"
PRO = ROOT / "picomondo.kicad_pro"
MM = 1e6
GAP = 0.12            # mm kept between courtyards


def v(x, y):
    return pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))


def pad(fp, number):
    return next(p for p in fp.Pads() if p.GetNumber() == str(number))


def box(fp, margin=GAP):
    b = fp.GetBoundingBox(False)
    b.Inflate(int(margin * MM))
    return b


class Placer:
    def __init__(self, board, u1):
        self.board, self.u1 = board, u1
        self.placed = set()
        c = u1.GetPosition()
        self.c = (c.x / MM, c.y / MM)

    def obstacles(self, fp):
        around = self.u1.GetBoundingBox(False)
        around.Inflate(int(40 * MM))
        return [f for f in self.board.GetFootprints()
                if f is not fp and around.Intersects(f.GetBoundingBox(False))
                and f.GetReference() not in self.pending]

    def free(self, fp):
        b = box(fp)
        return not any(b.Intersects(o.GetBoundingBox(False)) for o in self.obstacles(fp))

    def normal(self, pin_pad):
        p = pin_pad.GetPosition()
        dx, dy = p.x / MM - self.c[0], p.y / MM - self.c[1]
        return (math.copysign(1, dx), 0.0) if abs(dx) > abs(dy) else (0.0, math.copysign(1, dy))

    def orient(self, fp, net, axis_angle):
        """Of the two ways round at `axis_angle`, the one that puts the pad on `net` nearest the pin."""
        pc = self.cur_pad.GetPosition()
        best = None
        for a in (axis_angle, axis_angle + 180):
            fp.SetOrientationDegrees(a)
            pads = list(fp.Pads())
            inner = next((p for p in pads if p.GetNetname() == net), pads[0])
            d = (inner.GetPosition().x - pc.x) ** 2 + (inner.GetPosition().y - pc.y) ** 2
            if best is None or d < best[0] - 1:
                best = (d, a)
        fp.SetOrientationDegrees(best[1])

    def put_at_pin(self, fp, pins, extra_out=0.0, shift=0.0):
        """Slide the part from its pin until it is free; returns distance from the pin pad.

        Tries the part standing out from the chip and lying along the chip edge, keeps the closer fit."""
        pins = pins if isinstance(pins, (list, tuple)) else [pins]
        pads = [pad(self.u1, n) for n in pins]
        px = sum(p.GetPosition().x for p in pads) / len(pads) / MM
        py = sum(p.GetPosition().y for p in pads) / len(pads) / MM
        self.cur_pad = pads[0]
        n = self.normal(pads[0])
        t = (-n[1], n[0])
        net = pads[0].GetNetname()
        along_normal = 0 if n[0] else 90
        best = None
        for axis in (along_normal, along_normal + 90):
            self.orient(fp, net, axis)
            bb = fp.GetBoundingBox(False)
            hl = (bb.GetWidth() if n[0] else bb.GetHeight()) / MM / 2
            base_out = 5.575 + hl - 4.9 + extra_out + GAP    # U1 courtyard is +-5.575, pad centres at 4.9
            angle = fp.GetOrientationDegrees()
            steps = sorted(((e, s) for e in [i * 0.3 for i in range(0, 14)]
                            for s in [shift + k * 0.4 for k in range(-14, 15)]),
                           key=lambda es: abs(es[1] - shift) + 1.6 * es[0])
            for e, s in steps:
                fp.SetPosition(v(px + n[0] * (base_out + e) + t[0] * s, py + n[1] * (base_out + e) + t[1] * s))
                if self.free(fp):
                    cost = abs(s - shift) + 1.6 * e
                    if best is None or cost < best[0]:
                        best = (cost, angle, fp.GetPosition())
                    break
        if best is None:
            raise RuntimeError(f"no room for {fp.GetReference()} at pin {pins}")
        fp.SetOrientationDegrees(best[1])
        fp.SetPosition(best[2])
        fp.Reference().SetVisible(False)
        self.pending.discard(fp.GetReference())
        return math.hypot(fp.GetPosition().x / MM - px, fp.GetPosition().y / MM - py)

    def put_near(self, fp, x, y, angle=0, show_ref=False):
        fp.SetOrientationDegrees(angle)
        steps = sorted(((dx, dy) for dx in [i * 0.5 for i in range(-14, 15)] for dy in [i * 0.5 for i in range(-14, 15)]),
                       key=lambda d: d[0] ** 2 + d[1] ** 2)
        for dx, dy in steps:
            fp.SetPosition(v(x + dx, y + dy))
            if self.free(fp):
                fp.Reference().SetVisible(show_ref)
                self.pending.discard(fp.GetReference())
                return
        raise RuntimeError(f"no room for {fp.GetReference()}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--x", type=float, default=80.0)
    ap.add_argument("--y", type=float, default=75.0)
    ap.add_argument("--angle", type=float, default=90.0)
    args = ap.parse_args()

    shutil.copy2(PCB, PCB.with_suffix(".kicad_pcb.bak"))
    pro_bytes = PRO.read_bytes()
    board = pcbnew.LoadBoard(str(PCB))
    fp = lambda r: board.FindFootprintByReference(r)           # noqa: E731
    u1 = fp("U1")
    u1.SetOrientationDegrees(args.angle)
    u1.SetPosition(v(args.x, args.y))
    u1.Reference().SetVisible(True)

    mine = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11", "C12", "C13", "C14", "C15", "C16",
            "C17", "C18", "C19", "R1", "R2", "R3", "R10", "R11", "L1", "Y1", "U2"]
    pl = Placer(board, u1)
    pl.pending = set(mine)                      # staged parts do not block each other
    for g in board.Groups():
        for r in mine:
            if fp(r) in g.GetItems():
                g.RemoveItem(fp(r))
    report = []

    def pin_part(ref, pins, **kw):
        d = pl.put_at_pin(fp(ref), pins, **kw)
        report.append((ref, fp(ref).GetValue(), pins, round(d, 1)))

    # regulator corner (pins 61-65)
    pin_part("C6", 61)
    pin_part("R1", 61, extra_out=2.2)
    pin_part("C5", 64)
    pin_part("C1", 65)
    pin_part("L1", 63, extra_out=1.6)
    # decoupling: one 100 nF per supply pin / group of pins
    groups = [[5], [15], [24], [29], [41], [50], [59, 60], [68, 69], [76]]
    for ref, pins in zip(("C7", "C8", "C9", "C10", "C11", "C12", "C13", "C14", "C15"), groups):
        pin_part(ref, pins)
    pin_part("C3", 10)
    pin_part("C4", 51)
    pin_part("C2", 32)
    pin_part("C16", 76, extra_out=2.0)
    # USB series resistors at pins 66 / 67
    pin_part("R11", 66, extra_out=1.6)       # D-
    pin_part("R10", 67, extra_out=1.6)       # D+
    # crystal near pins 30/31
    pin_part("R2", 31, extra_out=1.2)
    c30 = pad(u1, 30).GetPosition()
    n = pl.normal(pad(u1, 30))
    yx, yy = c30.x / MM + n[0] * 8.5, c30.y / MM + n[1] * 8.5
    pl.put_near(fp("Y1"), yx, yy, angle=0, show_ref=True)
    yc = fp("Y1").GetPosition()
    pl.put_near(fp("C17"), yc.x / MM, yc.y / MM + 3.0, angle=90)
    pl.put_near(fp("C18"), yc.x / MM, yc.y / MM - 3.0, angle=90)
    # flash on the left, facing the QSPI pins, with its decoupling and CS link
    q = pad(u1, 72).GetPosition()
    pl.put_near(fp("U2"), q.x / MM - 12.5, q.y / MM, angle=0, show_ref=True)
    f2 = fp("U2").GetPosition()
    pl.put_near(fp("C19"), f2.x / MM, f2.y / MM + 5.5, angle=0)
    pl.put_near(fp("R3"), (q.x / MM + f2.x / MM) / 2, q.y / MM + 4.0, angle=90)

    pcbnew.SaveBoard(str(PCB), board)
    for _ in range(5):
        try:
            PRO.write_bytes(pro_bytes)
            break
        except OSError:
            time.sleep(1)
    for r in report:
        print(*r)


if __name__ == "__main__":
    sys.exit(main())
