"""Lay out the parts that are still off the board as tidy sub-circuit clusters.

Parts staged to the right of the board (x > 155) are grouped by schematic sheet, then by connectivity: parts joined by
signal nets (ground, supply rails, GPIO nets and nets with many pins do not count) form one sub-circuit, laid out as a
compact block with its biggest part first and the parts directly connected to it next. Parts that only touch rails
(bypass caps, test points) go into an "other" block per sheet, sorted by value. Each sheet gets a heading and each
cluster a small label (layer Cmts.User, which is not fabricated; old silkscreen headings are removed).

Only parts at x > 155 move. Nothing on or near the board is touched. Safe to re-run.

Close KiCad's PCB editor first. Backs up the board. Run with KiCad's Python from the kicad folder:
  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/arrange_offboard.py
"""
import collections
import math
import re
import shutil
import sys
import time

import pcbnew

from make_pcb import read_netlist
from place_mcu import PCB, PRO

MM = 1e6
STAGE_X = 155.0
X0, Y0 = 175.0, 30.0           # top left of the staging area
BLOCK_W = 95.0                 # width of one sheet block
ROW_W = 330.0                  # blocks wrap to a new row beyond this
PAD = 1.4                      # clear space around each part
MARK = "["                     # headings start with this so a re-run can find and remove them
ORDER = ["5V buck-boost", "USB-C PD", "Switched outputs", "Board support", "3V3 regulators", "MCU core",
         "GPIO indicators", "Power input", "Arduino and Pico headers"]
SPECIAL = re.compile(r"^(GND|AGND|V_INPUT|VBUS|RUN|USB_D[+-]|GPIO\d+)$|^\+|^/?.*/(GND|AGND)$")


def vec(x, y):
    return pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))


def size(fp):
    b = fp.GetBoundingBox(False)
    return b.GetWidth() / MM + PAD, b.GetHeight() / MM + PAD


def put(fp, x, y):
    """Move fp so its box has top-left corner (x, y)."""
    b = fp.GetBoundingBox(False)
    p = fp.GetPosition()
    cx, cy = (b.GetLeft() + b.GetRight()) / 2 / MM, (b.GetTop() + b.GetBottom()) / 2 / MM
    w, h = size(fp)
    fp.SetPosition(vec(x + w / 2 - (cx - p.x / MM), y + h / 2 - (cy - p.y / MM)))


def text(board, s, x, y, h, layer):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(vec(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(int(h * MM), int(h * MM)))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    board.Add(t)


def shelf(items, width, x0, y0):
    """Pack (fp, w, h) left to right in rows no wider than `width`; returns (used width, used height)."""
    x = y = rowh = used = 0.0
    for fp, w, h in items:
        if x > 0 and x + w > width:
            x, y, rowh = 0.0, y + rowh, 0.0
        put(fp, x0 + x, y0 + y)
        x += w
        used = max(used, x)
        rowh = max(rowh, h)
    return used, y + rowh


def clusters_of(refs, pin_net, fps):
    """Union the parts of one sheet that share a signal net. Returns (clusters, loose parts)."""
    nets = collections.defaultdict(set)
    for r in refs:
        for n in set(pin_net.get(r, {}).values()):
            if n and not SPECIAL.search(n):
                nets[n].add(r)
    parent = {r: r for r in refs}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for n, members in nets.items():
        if 1 < len(members) <= 8:
            m = sorted(members)
            for other in m[1:]:
                parent[find(other)] = find(m[0])
    groups = collections.defaultdict(list)
    for r in refs:
        groups[find(r)].append(r)
    big = [g for g in groups.values() if len(g) > 1]
    loose = [g[0] for g in groups.values() if len(g) == 1]
    return big, loose, nets


def order_cluster(refs, nets, fps):
    """Part with the most pads first (the IC), then breadth first along shared signal nets."""
    anchor = max(refs, key=lambda r: (len(list(fps[r].Pads())), size(fps[r])[0] * size(fps[r])[1]))
    seen, out, queue = {anchor}, [anchor], [anchor]
    while queue:
        cur = queue.pop(0)
        for n, members in nets.items():
            if cur in members:
                for m in sorted(members):
                    if m in refs and m not in seen:
                        seen.add(m)
                        out.append(m)
                        queue.append(m)
    out += [r for r in refs if r not in seen]
    return out


def main():
    comps, _, pin_net = read_netlist()
    shutil.copy2(PCB, PCB.with_suffix(".kicad_pcb.bak"))
    pro_bytes = PRO.read_bytes()
    board = pcbnew.LoadBoard(str(PCB))
    # drop the old headings (silkscreen ones from make_pcb, and ours from a previous run)
    old_headings = []
    for d in list(board.GetDrawings()):
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetPosition().x / MM > STAGE_X - 30:
            s = d.GetText()
            if s.startswith(MARK) or (d.GetLayer() == pcbnew.F_SilkS and s.isupper()):
                old_headings.append(d)          # removed after placing: removing earlier upsets the footprint list

    fps = {f.GetReference(): f for f in board.GetFootprints()}
    sheet_of = {r: comps[r]["sheet"] for r in fps if r in comps}
    staged = [r for r, f in fps.items() if f.GetPosition().x / MM > STAGE_X and r in comps]
    on_board = collections.Counter(sheet_of[r] for r, f in fps.items()
                                   if r in sheet_of and f.GetPosition().x / MM <= STAGE_X
                                   and "EdgeLock" not in str(f.GetFPID().GetLibItemName()))

    by_sheet = collections.defaultdict(list)
    for r in staged:
        by_sheet[sheet_of[r]].append(r)
    sheets = sorted(by_sheet, key=lambda s: (ORDER.index(s) if s in ORDER else len(ORDER), s))

    x, y, rowh = X0, Y0, 0.0
    summary = []
    for s in sheets:
        refs = by_sheet[s]
        big, loose, nets = clusters_of(refs, pin_net, fps)
        big.sort(key=lambda g: -len(g))
        title = s.upper() + ("  (still to place)" if on_board[s] else "")
        if x > X0 and x + BLOCK_W > X0 + ROW_W:
            x, y, rowh = X0, y + rowh + 6.0, 0.0
        bx, by = x, y
        text(board, MARK + title + "]", bx, by, 2.0, pcbnew.Cmts_User)
        cy = by + 5.0
        cx, crow = bx, 0.0
        blocks = [(f"{order_cluster(g, nets, fps)[0]} {fps[order_cluster(g, nets, fps)[0]].GetValue()} circuit",
                   order_cluster(g, nets, fps)) for g in big]
        if loose:
            blocks.append(("other: bypass, pull-ups, test points", sorted(loose, key=lambda r: (comps[r]["value"], r))))
        for label, order in blocks:
            items = [(fps[r], *size(fps[r])) for r in order]
            area = sum(w * h for _, w, h in items)
            width = min(BLOCK_W, max(0.85 * len(label), math.sqrt(area) * 1.5, max(w for _, w, _ in items)))
            if cx > bx and cx + width > bx + BLOCK_W:
                cx, cy, crow = bx, cy + crow + 4.0, 0.0
            text(board, MARK + label + "]", cx, cy, 1.2, pcbnew.Cmts_User)
            used, h = shelf(items, width, cx, cy + 2.4)
            cx += max(used, 0.85 * len(label)) + 4.0
            crow = max(crow, h + 2.4)
        x_next, bottom = bx + BLOCK_W + 8.0, cy + crow
        summary.append((s, len(refs), len(big), len(loose)))
        x, rowh = x_next, max(rowh, bottom - by)
        y = by
    for d in old_headings:
        board.Remove(d)
    pcbnew.SaveBoard(str(PCB), board)
    for _ in range(5):
        try:
            PRO.write_bytes(pro_bytes)
            break
        except OSError:
            time.sleep(1)
    for s, n, c, l in summary:
        print(f"{s:28} {n:3} parts, {c} clusters, {l} loose")


if __name__ == "__main__":
    sys.exit(main())
