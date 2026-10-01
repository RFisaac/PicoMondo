"""Add non-printing Arduino Uno R3 and Raspberry Pi Pico outlines to the "Arduino + Pico sockets" group.

The outlines are drawing-only graphics (never fabricated), so you can see what a shield or a Pico would cover:
  * Uno R3  -> layer Dwgs.User  (board outline, USB-B and DC jack bodies, four M3 holes)
  * Pico    -> layer Cmts.User  (board outline, USB micro, two mounting holes)
Both are anchored to the socket pads that are actually on the board, so they follow wherever the group was
moved or rotated. Safe to re-run: it removes its own earlier outlines first.

Close KiCad's PCB editor first. A backup of the board and project file is written next to them.
Run:  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools\\add_shield_outlines.py
"""
import math
import shutil
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "picomondo.kicad_pcb"
PRO = ROOT / "picomondo.kicad_pro"
MOD = Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints\Module.pretty")
GROUP = "Arduino + Pico sockets"
TAG = "shield-outline"
MM = 1e6
W = int(0.15 * MM)


def mm(v):
    return int(round(v * MM))


def pad_pos(board, value, number):
    for fp in board.GetFootprints():
        if fp.GetValue() == value:
            for p in fp.Pads():
                if p.GetNumber() == str(number):
                    return fp, p.GetPosition()
    sys.exit(f"socket '{value}' pad {number} not found")


def unit(a, b):
    dx, dy = b.x - a.x, b.y - a.y
    n = math.hypot(dx, dy)
    return dx / n, dy / n


class Frame:
    """Maps a footprint-frame point (mm) to board coordinates using two axis vectors."""

    def __init__(self, origin, ax, ay):
        self.o, self.ax, self.ay = origin, ax, ay

    def pt(self, x, y):
        return pcbnew.VECTOR2I(int(self.o.x + (self.ax[0] * x + self.ay[0] * y) * MM),
                               int(self.o.y + (self.ax[1] * x + self.ay[1] * y) * MM))


def line(board, grp, layer, a, b):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(a)
    s.SetEnd(b)
    s.SetLayer(layer)
    s.SetWidth(W)
    s.SetLocked(False)
    board.Add(s)
    grp.AddItem(s)
    return s


def circle(board, grp, layer, c, dia):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    s.SetCenter(c)
    s.SetEnd(pcbnew.VECTOR2I(c.x + mm(dia / 2), c.y))
    s.SetLayer(layer)
    s.SetWidth(W)
    board.Add(s)
    grp.AddItem(s)


def polyline(board, grp, layer, fr, pts, close=True):
    n = len(pts)
    for i in range(n if close else n - 1):
        line(board, grp, layer, fr.pt(*pts[i]), fr.pt(*pts[(i + 1) % n]))


def rounded_rect(x0, y0, x1, y1, r, steps=6):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(steps + 1):
            a = math.radians(a0 + 90 * i / steps)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def label(board, grp, layer, text, p, size=1.5):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetPosition(p)
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(0.15))
    board.Add(t)
    grp.AddItem(t)


def main():
    shutil.copy2(PCB, PCB.with_suffix(".kicad_pcb.bak"))
    pro_bytes = PRO.read_bytes()
    board = pcbnew.LoadBoard(str(PCB))
    grp = next((g for g in board.Groups() if g.GetName() == GROUP), None)
    if grp is None:
        sys.exit(f'group "{GROUP}" not found')

    # drop outlines from an earlier run
    for item in list(grp.GetItems()):
        if isinstance(item, (pcbnew.PCB_SHAPE, pcbnew.PCB_TEXT)) and item.GetLayer() in (
                pcbnew.Dwgs_User, pcbnew.Cmts_User):
            grp.RemoveItem(item)
            board.Remove(item)

    DW, CM = pcbnew.Dwgs_User, pcbnew.Cmts_User

    # --- Uno R3: frame origin = power header pad 1; x along the header, y toward the other rows
    _, p1 = pad_pos(board, "Arduino power", 1)
    _, p2 = pad_pos(board, "Arduino power", 2)
    _, d1 = pad_pos(board, "Arduino digital 0-7", 1)       # 48.26 mm across, at x = 35.56
    ax = unit(p1, p2)
    ay = unit(p1, d1)                                       # not perpendicular because of the x offset
    ay = (ay[0] - ax[0] * (ay[0] * ax[0] + ay[1] * ax[1]), ay[1] - ax[1] * (ay[0] * ax[0] + ay[1] * ax[1]))
    n = math.hypot(*ay)
    ay = (ay[0] / n, ay[1] / n)
    uno = Frame(p1, ax, ay)
    fpl = pcbnew.FootprintLoad(str(MOD), "Arduino_UNO_R3_WithMountingHoles")
    count = 0
    for g in fpl.GraphicalItems():
        if g.GetLayerName() == "F.Fab" and hasattr(g, "GetShapeStr") and g.GetShapeStr() == "Line":
            a, b = g.GetStart(), g.GetEnd()
            line(board, grp, DW, uno.pt(a.x / MM, a.y / MM), uno.pt(b.x / MM, b.y / MM))
            count += 1
    for p in fpl.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            c = p.GetPosition()
            circle(board, grp, DW, uno.pt(c.x / MM, c.y / MM), p.GetDrillSize().x / MM)
    label(board, grp, DW, "Arduino Uno R3 outline (not fabricated)", uno.pt(-20, 25), 1.5)

    # --- Pico: frame origin = left socket pad 1; y along the pins (pad 1 to 20), x toward the right socket
    _, q1 = pad_pos(board, "Pico left (pins 1-20)", 1)
    _, q2 = pad_pos(board, "Pico left (pins 1-20)", 2)
    _, q40 = pad_pos(board, "Pico right (pins 40-21)", 1)  # socket pin 1 is Pico pin 40, across from Pico pin 1
    pico = Frame(q1, unit(q1, q40), unit(q1, q2))
    # Pico board: 21 x 51 mm, pins 17.78 apart, pin 1 end is the USB end, 2 mm hole inset
    xs0, xs1, ys0, ys1 = -1.61, 19.39, -1.37, 49.63
    polyline(board, grp, CM, pico, rounded_rect(xs0, ys0, xs1, ys1, 2.0))
    for hx in (3.19, 14.59):
        circle(board, grp, CM, pico.pt(hx, 0.63), 2.1)
        circle(board, grp, CM, pico.pt(hx, 47.63), 2.1)
    polyline(board, grp, CM, pico, [(4.89, -2.6), (12.89, -2.6), (12.89, 3.9), (4.89, 3.9)])  # USB micro
    label(board, grp, CM, "Pico outline (not fabricated)", pico.pt(8.89, 24), 1.5)

    pcbnew.SaveBoard(str(PCB), board)
    PRO.write_bytes(pro_bytes)                              # pcbnew rewrites the project file; keep yours
    print(f"added {count} Uno lines + holes (Dwgs.User) and a Pico outline (Cmts.User) to '{GROUP}'")
    print("backup:", PCB.with_suffix(".kicad_pcb.bak").name)


if __name__ == "__main__":
    main()
