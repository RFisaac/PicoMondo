"""Fit the parts that are still off the board into the free space on the board (top side).

For each sheet in turn (5V buck-boost, switched outputs, ...), the parts are placed one at a time, starting from the
IC and working outward along shared signal nets. Each part goes to the free spot nearest the parts it connects to
(their pads on the same nets; a sheet anchor point when nothing it connects to is placed yet), turned to the
rotation that puts its pads closest to those nets. Free space is a 0.25 mm grid of everything already on the board,
the board edge, mounting-hole keep-outs and a 0.5 mm margin around each part.

Not placed: test points (back side, for you), fiducials, and anything that finds no room (left off the board and
listed). Parts you have placed never move.

Close KiCad's PCB editor first. Backs up the board. Run with KiCad's Python from the kicad folder:
  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/place_rest.py [--dry-run]
"""
import argparse
import collections
import math
import re
import shutil
import sys
import time

import pcbnew

from arrange_offboard import SPECIAL
from make_pcb import read_netlist
from place_mcu import PCB, PRO

MM = 1e6
RES = 0.1                        # grid cell, mm
GX0, GY0, GX1, GY1 = 25.0, 25.0, 155.0, 125.0
BOARD = (30.0, 30.0, 150.0, 120.0)
EDGE_INSET = 0.8                 # keep parts this far from the board edge
MARGIN = 0.3                     # clear space kept around a part
EXIST_MARGIN = 0.1               # around parts that are already on the board
BIG_MARGIN = 0.0                 # big parts (inductor, bulk caps) get no extra margin so they can fit tight gaps
HOLE_KEEPOUT = 3.6               # half width of the square kept clear around each mounting hole
STAGE_X = 155.0
RAILS = re.compile(r"^(GND|AGND|\+.*|V_INPUT|VBUS)$|/(GND|AGND)$")
ANCHOR = {"5V buck-boost": (72.0, 92.0), "Switched outputs": (118.0, 106.0), "MCU core": (80.0, 75.0),
          "GPIO indicators": (90.0, 94.0), "Board support": (132.0, 56.0), "3V3 regulators": (70.0, 66.0)}
ORDER = ["5V buck-boost", "Switched outputs", "MCU core", "GPIO indicators", "Board support", "3V3 regulators"]
SKIP = re.compile(r"^(TP|FID)\d+$")
MCU_ZONE = (60.0, 66.0, 116.0, 84.0)     # between the Pico socket rows: kept for the MCU's own parts
BIG_AREA = 40.0                          # mm2: parts at least this big are placed right after their IC


class Grid:
    def __init__(self):
        self.nx = int((GX1 - GX0) / RES)
        self.ny = int((GY1 - GY0) / RES)
        self.rows = [bytearray(self.nx) for _ in range(self.ny)]
        bx0, by0, bx1, by1 = BOARD
        for j in range(self.ny):
            y = GY0 + j * RES
            for i in range(self.nx):
                x = GX0 + i * RES
                if not (bx0 + EDGE_INSET <= x <= bx1 - EDGE_INSET and by0 + EDGE_INSET <= y <= by1 - EDGE_INSET):
                    self.rows[j][i] = 1

    def cells(self, x0, y0, x1, y1):
        i0 = max(0, int(math.floor((x0 - GX0) / RES)))
        i1 = min(self.nx, int(math.ceil((x1 - GX0) / RES)))
        j0 = max(0, int(math.floor((y0 - GY0) / RES)))
        j1 = min(self.ny, int(math.ceil((y1 - GY0) / RES)))
        return i0, i1, j0, j1

    def mark(self, x0, y0, x1, y1):
        i0, i1, j0, j1 = self.cells(x0, y0, x1, y1)
        for j in range(j0, j1):
            self.rows[j][i0:i1] = b"\x01" * (i1 - i0)

    def free(self, x0, y0, x1, y1):
        if x0 < GX0 or y0 < GY0 or x1 > GX1 or y1 > GY1:
            return False
        i0, i1, j0, j1 = self.cells(x0, y0, x1, y1)
        for j in range(j0, j1):
            if self.rows[j].find(1, i0, i1) != -1:
                return False
        return True


def box_mm(fp):
    """Courtyard box when the footprint has one, else everything it draws (without text)."""
    c = fp.GetCourtyard(pcbnew.F_CrtYd)
    b = c.BBox() if c.OutlineCount() else fp.GetBoundingBox(False)
    return b.GetLeft() / MM, b.GetTop() / MM, b.GetRight() / MM, b.GetBottom() / MM


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    comps, _, pin_net = read_netlist()
    shutil.copy2(PCB, PCB.with_suffix(".kicad_pcb.bak"))
    pro_bytes = PRO.read_bytes()
    board = pcbnew.LoadBoard(str(PCB))
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    todo = [r for r, f in fps.items() if f.GetPosition().x / MM > STAGE_X and r in comps and not SKIP.match(r)]
    grid = Grid()
    placed = {}                                # ref -> footprint, for every part on the board
    for r, f in fps.items():
        p = f.GetPosition()
        if r in todo or not (GX0 < p.x / MM < GX1 and GY0 < p.y / MM < GY1):
            continue
        if f.GetLayer() == pcbnew.B_Cu and r.startswith("TP"):
            continue
        x0, y0, x1, y1 = box_mm(f)
        grid.mark(x0 - EXIST_MARGIN, y0 - EXIST_MARGIN, x1 + EXIST_MARGIN, y1 + EXIST_MARGIN)
        placed[r] = f
        if r.startswith("H") and r[1:].isdigit():
            grid.mark(p.x / MM - HOLE_KEEPOUT, p.y / MM - HOLE_KEEPOUT, p.x / MM + HOLE_KEEPOUT, p.y / MM + HOLE_KEEPOUT)

    def pad_points(net):
        pts = []
        for r, f in placed.items():
            for pad in f.Pads():
                if pad.GetNetname() == net:
                    pts.append((pad.GetPosition().x / MM, pad.GetPosition().y / MM))
        return pts

    by_sheet = collections.defaultdict(list)
    for r in todo:
        by_sheet[comps[r]["sheet"]].append(r)
    results, failed = [], []
    for sheet in ORDER + [s for s in by_sheet if s not in ORDER]:
        refs = by_sheet.get(sheet, [])
        if not refs:
            continue
        anchor = ANCHOR.get(sheet, (90.0, 75.0))
        zone_marked = []
        if sheet != "MCU core":
            zx0, zy0, zx1, zy1 = MCU_ZONE
            i0, i1, j0, j1 = grid.cells(zx0, zy0, zx1, zy1)
            for j in range(j0, j1):
                zone_marked.append((j, i0, i1, bytes(grid.rows[j][i0:i1])))
            grid.mark(zx0, zy0, zx1, zy1)
        # signal-net neighbours inside the sheet, for the placement order
        nets = collections.defaultdict(set)
        for r in refs:
            for n in set(pin_net.get(r, {}).values()):
                if n and not SPECIAL.search(n) and not RAILS.search(n):
                    nets[n].add(r)
        order, seen = [], set()
        pending = sorted(refs, key=lambda r: -len(list(fps[r].Pads())))
        for start in pending:
            if start in seen:
                continue
            queue = [start]
            seen.add(start)
            while queue:
                cur = queue.pop(0)
                order.append(cur)
                for n, members in nets.items():
                    if cur in members and 1 < len(members) <= 12:
                        for m in sorted(members, key=lambda r: -len(list(fps[r].Pads()))):
                            if m not in seen:
                                seen.add(m)
                                queue.append(m)
        def area(r):
            f = fps[r]
            f.SetOrientationDegrees(0)
            x0, y0, x1, y1 = box_mm(f)
            return (x1 - x0) * (y1 - y0)
        if order:
            big = sorted((r for r in order[1:] if area(r) >= BIG_AREA), key=lambda r: (comps[r]["dnp"], -area(r)))
            order = order[:1] + big + [r for r in order[1:] if r not in big]
        for r in order:
            fp = fps[r]
            net_of = {pad.GetNumber(): pad.GetNetname() for pad in fp.Pads()}
            wants = {}                                     # net -> (weight, points)
            for n in set(net_of.values()):
                if not n or n == "GND" or n.endswith("/GND") or n.endswith("/AGND"):
                    continue
                pts = pad_points(n)
                if pts:
                    pts.sort(key=lambda q: (q[0] - anchor[0]) ** 2 + (q[1] - anchor[1]) ** 2)
                    sig = not RAILS.search(n) and not SPECIAL.search(n)
                    wants[n] = (3.0 if sig else 0.6, pts[:60])
            sig_pts = [p for w, pts in wants.values() if w > 1 for p in pts[:1]]
            tgt = (sum(p[0] for p in sig_pts) / len(sig_pts), sum(p[1] for p in sig_pts) / len(sig_pts)) if sig_pts else anchor
            best = None
            shapes = {}
            for ang in (0, 90, 180, 270):
                fp.SetOrientationDegrees(ang)
                fp.SetPosition(pcbnew.VECTOR2I(0, 0))
                x0, y0, x1, y1 = box_mm(fp)
                m = BIG_MARGIN if (x1 - x0) * (y1 - y0) >= BIG_AREA else MARGIN
                shapes[ang] = (x0 - m, y0 - m, x1 + m, y1 + m)
            radius, found_at = 0.0, None
            while radius <= 60.0:
                n_steps = int(radius / 0.5)
                ring = {(dx, dy) for dx in range(-n_steps, n_steps + 1) for dy in (-n_steps, n_steps)} | \
                       {(dx, dy) for dy in range(-n_steps, n_steps + 1) for dx in (-n_steps, n_steps)}
                for dx, dy in ring:
                    cx, cy = tgt[0] + dx * 0.5, tgt[1] + dy * 0.5
                    for ang, (bx0, by0, bx1, by1) in shapes.items():
                        ccx, ccy = cx, cy
                        if not grid.free(cx + bx0, cy + by0, cx + bx1, cy + by1):
                            if (bx1 - bx0) * (by1 - by0) < BIG_AREA:
                                continue
                            # a big part gets nudged by tenths of a millimetre to slip into a tight gap
                            nudged = None
                            for d in (0.1, -0.1, 0.2, -0.2, 0.3, -0.3, 0.4, -0.4, 0.5, -0.5):
                                for ddx, ddy in ((0, d), (d, 0)):
                                    if grid.free(cx + ddx + bx0, cy + ddy + by0, cx + ddx + bx1, cy + ddy + by1):
                                        nudged = (cx + ddx, cy + ddy)
                                        break
                                if nudged:
                                    break
                            if nudged is None:
                                continue
                            ccx, ccy = nudged
                        fp.SetOrientationDegrees(ang)
                        fp.SetPosition(pcbnew.VECTOR2I(int(ccx * MM), int(ccy * MM)))
                        cost = 0.0
                        for pad in fp.Pads():
                            wt = wants.get(pad.GetNetname())
                            if wt:
                                px, py = pad.GetPosition().x / MM, pad.GetPosition().y / MM
                                cost += wt[0] * min(math.hypot(px - q[0], py - q[1]) for q in wt[1])
                        cost += 0.15 * math.hypot(ccx - tgt[0], ccy - tgt[1])
                        if best is None or cost < best[0]:
                            best = (cost, ccx, ccy, ang)
                if best is not None and found_at is None:
                    found_at = radius
                if found_at is not None and radius >= found_at + 1.5:
                    break
                radius += 0.5
            if best is None:
                failed.append(r)
                continue
            _, cx, cy, ang = best
            fp.SetOrientationDegrees(ang)
            fp.SetPosition(pcbnew.VECTOR2I(int(cx * MM), int(cy * MM)))
            fp.Reference().SetVisible(False)
            bx0, by0, bx1, by1 = box_mm(fp)
            m = BIG_MARGIN if (bx1 - bx0) * (by1 - by0) >= BIG_AREA else MARGIN
            grid.mark(bx0 - m, by0 - m, bx1 + m, by1 + m)
            placed[r] = fp
            results.append((sheet, r, comps[r]["value"], round(cx, 1), round(cy, 1), ang))
        for j, i0, i1, saved in zone_marked:          # give the MCU zone back
            grid.rows[j][i0:i1] = saved
    # (zone cells are released per sheet below)
    # big parts keep their reference text visible
    for r, f in placed.items():
        if r in todo and (r[0] in "UQLJYF" or len(list(f.Pads())) > 4):
            f.Reference().SetVisible(True)
    if not args.dry_run:
        for g in board.Groups():
            for r in todo:
                if fps[r] in g.GetItems():
                    g.RemoveItem(fps[r])
        pcbnew.SaveBoard(str(PCB), board)
        for _ in range(5):
            try:
                PRO.write_bytes(pro_bytes)
                break
            except OSError:
                time.sleep(1)
    per = collections.Counter(s for s, *_ in results)
    for s in per:
        print(f"{s:20} placed {per[s]}")
    print("could not fit:", failed or "none")


if __name__ == "__main__":
    sys.exit(main())
