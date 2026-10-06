"""Remove the eight ADC indicator solder jumpers (JP1-JP8): the LED branch now connects straight to the GPIO net.

Why: the ADC LEDs are on by default and the branch is disconnected by cutting a narrow trace neck with a knife (made
while routing, see docs/io.md), so no jumper part is needed and the ADC columns match the digital ones.

Schematic (io_indicators.kicad_sch, edited as text so KiCad 10's own formatting is kept): deletes each JP symbol, its
two stubs and labels, and turns the resistor's LEDnn_J label into a global GPIOnn label. Board: deletes the footprints
and puts the resistor pads on the GPIO nets. Backups: *.bak next to each file.

Close KiCad first. Run with KiCad's Python from the kicad folder:
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools\\remove_led_jumpers.py
"""
import re
import shutil
import sys
import time
import uuid
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
SCH = ROOT / "io_indicators.kicad_sch"
PCB = ROOT / "picomondo.kicad_pcb"
PRO = ROOT / "picomondo.kicad_pro"
NUM = r"(-?\d+(?:\.\d+)?)"
AT = re.compile(r"\(at " + NUM + " " + NUM + " " + NUM + r"\)")
NOTE_SHIFT = 22.86       # the GPIO name text sat higher in the jumper cells; bring it level with the others


def children(text):
    """Spans (start, end) of the top-level items inside the outer (kicad_sch ...) form."""
    spans, depth, start, i, n = [], 0, None, 0, len(text)
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\":
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            depth += 1
            if depth == 2:
                start = i
        elif c == ")":
            if depth == 2:
                spans.append((start, i + 1))
            depth -= 1
        i += 1
    return spans


def kind(block):
    return re.match(r"\((\w+)", block).group(1)


def pos(block):
    m = AT.search(block)
    return float(m.group(1)), float(m.group(2))


def first_string(block):
    return re.search(r'"((?:[^"\\]|\\.)*)"', block).group(1)


def near(a, b, tol=0.02):
    return abs(a[0] - b[0]) < tol and abs(a[1] - b[1]) < tol


def dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def shift_block(block, dx, dy, new_text, old_text):
    block = block.replace(f'"{old_text}"', f'"{new_text}"', 1)
    block = AT.sub(lambda m: f"(at {float(m.group(1)) + dx:g} {float(m.group(2)) + dy:g} {m.group(3)})", block)
    return re.sub(r'\(uuid "[^"]+"\)', f'(uuid "{uuid.uuid4()}")', block, count=1)


def edit_schematic():
    text = SCH.read_text(encoding="utf-8")
    spans = children(text)
    blocks = [text[a:b] for a, b in spans]
    kinds = [kind(b) for b in blocks]
    delete, replace = set(), {}

    jumpers = [i for i, b in enumerate(blocks) if kinds[i] == "symbol"
               and '(lib_id "Jumper:SolderJumper_2_Open")' in b and re.search(r'"Reference" "JP[1-8]"', b)]
    if not jumpers:
        print("schematic: no jumpers left (already done)")
        return 0
    tmpl = next(i for i, b in enumerate(blocks) if kinds[i] == "global_label" and first_string(b) == "GPIO0")
    tmpl_at = pos(blocks[tmpl])
    local = [i for i, b in enumerate(blocks) if kinds[i] == "label" and re.fullmatch(r"LED\d+_J", first_string(b))]
    glob = [i for i, b in enumerate(blocks) if kinds[i] == "global_label" and re.fullmatch(r"GPIO4\d", first_string(b))]
    wires = [(i, [float(v) for v in re.findall(NUM, re.search(r"\(pts(.*?)\)\s*\)", b, re.S).group(1))])
             for i, b in enumerate(blocks) if kinds[i] == "wire"]

    for j in jumpers:
        jp = pos(blocks[j])
        delete.add(j)
        mine = sorted(local, key=lambda i: dist(pos(blocks[i]), jp))[:2]          # the two jumper-side labels' names
        name = first_string(blocks[mine[0]])
        pair = sorted((i for i in local if first_string(blocks[i]) == name), key=lambda i: dist(pos(blocks[i]), jp))
        jump_label, res_label = pair[0], pair[1]
        g = min(glob, key=lambda i: dist(pos(blocks[i]), jp))
        n = re.search(r"\d+", name).group()
        assert first_string(blocks[g]) == f"GPIO{n}", (name, first_string(blocks[g]))
        ends = [pos(blocks[jump_label]), pos(blocks[g])]
        for wi, pts in wires:
            a, b = (pts[0], pts[1]), (pts[2], pts[3])
            if any(near(a, e) or near(b, e) for e in ends):
                delete.add(wi)
        delete.update((jump_label, g, res_label))
        px, py = pos(blocks[res_label])
        replace[res_label] = shift_block(blocks[tmpl], px - tmpl_at[0], py - tmpl_at[1], f"GPIO{n}", "GPIO0")
        # the net name text above the cell
        for i, b in enumerate(blocks):
            if kinds[i] == "text" and first_string(b) == f"GPIO{n}":
                replace[i] = AT.sub(lambda m: f"(at {m.group(1)} {float(m.group(2)) + NOTE_SHIFT:g} {m.group(3)})", b, count=1)
    delete -= set(replace)
    shutil.copy2(SCH, SCH.with_suffix(".kicad_sch.bak"))
    out, last = [], 0
    for i, (a, b) in enumerate(spans):
        if i in delete:                      # drop the item and the whitespace before it
            last = b
            continue
        out.append(text[last:a])
        out.append(replace.get(i, blocks[i]))
        last = b
    out.append(text[last:])
    new = "".join(out)
    new = new.replace("LED is disconnected by an open solder jumper; bridge it to turn the LED on.",
                      "the LED is on by default; the board has a narrow trace neck to cut with a knife to disconnect it.")
    SCH.write_text(new, encoding="utf-8")
    return len(jumpers)


def edit_board():
    shutil.copy2(PCB, PCB.with_suffix(".kicad_pcb.bak"))
    pro_bytes = PRO.read_bytes()
    board = pcbnew.LoadBoard(str(PCB))
    removed = rewired = 0
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            m = re.search(r"LED(\d+)_J$", pad.GetNetname())
            if m:
                pad.SetNet(board.FindNet(f"GPIO{m.group(1)}"))
                rewired += 1
    doomed = [fp for fp in board.GetFootprints() if fp.GetValue() == "LED enable" and re.fullmatch(r"JP[1-8]", fp.GetReference())]
    for fp in doomed:
        for g in board.Groups():
            if fp in g.GetItems():
                g.RemoveItem(fp)
        board.Remove(fp)
        removed += 1
    pcbnew.SaveBoard(str(PCB), board)
    for _ in range(5):
        try:
            PRO.write_bytes(pro_bytes)
            break
        except OSError:
            time.sleep(1)
    return removed, rewired


if __name__ == "__main__":
    print("schematic: removed", edit_schematic(), "jumpers")
    print("board: removed %d footprints, rewired %d pads" % edit_board())
