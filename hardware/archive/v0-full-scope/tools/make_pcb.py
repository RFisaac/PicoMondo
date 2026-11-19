"""Create picomondo.kicad_pcb from the schematic netlist (once).

Run with KiCad's own Python (it provides the pcbnew module):
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" make_pcb.py [--force]

What it does
  * 4-layer JLCPCB-style stackup (JLC04161H-3313, 1.6 mm, ENIG), 120 x 90 mm board with 3 mm corners
  * imports every schematic part as a footprint with its nets and schematic path, loaded by KiCad itself so
    text, layers and properties are exactly as in the library; because the schematic path is set, KiCad's own
    "Update PCB from Schematic" (F8) later updates these footprints instead of duplicating them
  * places the parts whose position is fixed by the mechanics: the seven EdgeLock edge connectors (their Edge.Cuts
    notches are joined into the outline), four M3 holes, and the Arduino Uno R3 and Pico sockets on their exact
    hole patterns (grouped, so the set can be moved together)
  * lays every other part out in tidy rows beside the board, grouped by schematic sheet
  * adds a GND plane on In1.Cu

It refuses to overwrite an existing board unless --force is given: once you have placed parts in KiCad, the
.kicad_pcb file is the source of truth.
"""
import math
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "picomondo.kicad_pcb"
KICAD_CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
KICAD_FP = Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints")
TMP = Path(tempfile.gettempdir())

BX0, BY0, BW, BH, R = 30.0, 30.0, 120.0, 90.0, 3.0      # board rectangle on the sheet (mm)
BX1, BY1 = BX0 + BW, BY0 + BH
EDGE_Y = 1.805799                                        # EdgeLock board-edge line is at local y = -1.8058

mm = pcbnew.FromMM


def vec(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


HEADER = '''(kicad_pcb (version 20221018) (generator pcbnew)
  (general (thickness 1.6) (legacy_teardrops no))
  (paper "A2")
  (layers
    (0 "F.Cu" signal) (1 "In1.Cu" signal) (2 "In2.Cu" signal) (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive") (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user) (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user) (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings") (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1") (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user) (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user) (49 "F.Fab" user)
    (50 "User.1" user) (51 "User.2" user) (52 "User.3" user) (53 "User.4" user)
  )
  (setup
    (stackup
      (layer "F.SilkS" (type "Top Silk Screen"))
      (layer "F.Paste" (type "Top Solder Paste"))
      (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
      (layer "F.Cu" (type "copper") (thickness 0.035))
      (layer "dielectric 1" (type "prepreg") (thickness 0.0994) (material "3313") (epsilon_r 4.05) (loss_tangent 0.02))
      (layer "In1.Cu" (type "copper") (thickness 0.0152))
      (layer "dielectric 2" (type "core") (thickness 1.265) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
      (layer "In2.Cu" (type "copper") (thickness 0.0152))
      (layer "dielectric 3" (type "prepreg") (thickness 0.0994) (material "3313") (epsilon_r 4.05) (loss_tangent 0.02))
      (layer "B.Cu" (type "copper") (thickness 0.035))
      (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
      (layer "B.Paste" (type "Bottom Solder Paste"))
      (layer "B.SilkS" (type "Bottom Silk Screen"))
      (copper_finish "ENIG")
      (dielectric_constraints no)
    )
    (pad_to_mask_clearance 0)
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff) (plot_on_all_layers_selection 0x0000000_00000000)
      (disableapertmacros false) (usegerberextensions false) (usegerberattributes true)
      (usegerberadvancedattributes true) (creategerberjobfile true) (dashed_line_dash_ratio 12.0)
      (dashed_line_gap_ratio 3.0) (svgprecision 4) (plotframeref false) (viasonmask false) (mode 1)
      (useauxorigin false) (hpglpennumber 1) (hpglpenspeed 20) (hpglpendiameter 15.0) (dxfpolygonmode true)
      (dxfimperialunits true) (dxfusepcbnewfont true) (psnegative false) (psa4output false)
      (plotreference true) (plotvalue true) (plotinvisibletext false) (sketchpadsonfab false)
      (subtractmaskfromsilk false) (outputformat 1) (mirror false) (drillshape 1) (scaleselection 1)
      (outputdirectory "gerbers/")
    )
  )
  (net 0 "")
)
'''


# --------------------------------------------------------------------------- netlist
def read_netlist():
    xml = TMP / "picomondo_net.xml"
    subprocess.run([KICAD_CLI, "sch", "export", "netlist", str(PROJECT / "picomondo.kicad_sch"), "--format",
                    "kicadxml", "-o", str(xml)], check=True, capture_output=True)
    root = ET.parse(xml).getroot()
    comps = {}
    for c in root.find("components"):
        sp = c.find("sheetpath")
        comps[c.get("ref")] = dict(
            ref=c.get("ref"), value=c.findtext("value") or "", footprint=c.findtext("footprint") or "",
            fields={f.get("name"): (f.text or "") for f in c.find("fields")},
            sheet=sp.get("names").strip("/") if sp is not None else "",
            dnp=any(p.get("name") == "dnp" for p in c.findall("property")),
            path=(sp.get("tstamps") if sp is not None else "/") + (c.findtext("tstamps") or ""))
    nets, pin_net = {}, {}
    for n in root.find("nets"):
        name = n.get("name")
        nets[int(n.get("code"))] = name
        for nd in n:
            pin_net.setdefault(nd.get("ref"), {})[nd.get("pin")] = name
    return comps, nets, pin_net


def fp_dir(nick):
    if nick == "picomondo":
        return PROJECT / "lib" / "picomondo.pretty"
    if nick == "lcsc":
        return PROJECT / "lib" / "lcsc" / "lcsc.pretty"
    return KICAD_FP / f"{nick}.pretty"


# --------------------------------------------------------------------------- helpers
def new_fp(board, c, pin_net):
    nick, name = c["footprint"].split(":")
    fp = pcbnew.FootprintLoad(str(fp_dir(nick)), name)
    if fp is None:
        raise RuntimeError(f"cannot load {c['footprint']}")
    fp.SetFPID(pcbnew.LIB_ID(nick, name))
    fp.SetReference(c["ref"])
    fp.SetValue(c["value"])
    fp.SetPath(pcbnew.KIID_PATH(c["path"]))
    fp.SetDNP(c["dnp"])
    for k, v in c["fields"].items():                     # MPN, LCSC and similar schematic fields, hidden
        if k not in ("Footprint", "Datasheet", "Description") and v:
            fp.SetField(k, v)
            fp.GetField(k).SetVisible(False)
    nets = pin_net.get(c["ref"], {})
    for pad in fp.Pads():
        netname = nets.get(pad.GetNumber())
        if netname is not None:
            pad.SetNet(board.FindNet(netname))
    return fp


def place(fp, x, y, angle=0.0):
    fp.SetPosition(vec(x, y))
    fp.SetOrientationDegrees(angle)


def segment(board, a, b):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(vec(*a))
    s.SetEnd(vec(*b))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(mm(0.1))
    board.Add(s)


def arc(board, c, start, end):
    a0 = math.atan2(start[1] - c[1], start[0] - c[0])
    a1 = math.atan2(end[1] - c[1], end[0] - c[0])
    da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    am = a0 + da / 2
    mid = (c[0] + R * math.cos(am), c[1] + R * math.sin(am))
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetArcGeometry(vec(*start), vec(*mid), vec(*end))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(mm(0.1))
    board.Add(s)


def edge_ends(fp, edge_y):
    """x range of the footprint's Edge.Cuts line ends that lie on the board edge (board coordinates, mm)."""
    xs = []
    for g in fp.GraphicalItems():
        if g.GetLayer() == pcbnew.Edge_Cuts and g.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            for p in (g.GetStart(), g.GetEnd()):
                if abs(pcbnew.ToMM(p.y) - edge_y) < 0.01:
                    xs.append(pcbnew.ToMM(p.x))
    return min(xs), max(xs)


def build_outline(board, top_ends, bottom_ends):
    arc(board, (BX0 + R, BY0 + R), (BX0, BY0 + R), (BX0 + R, BY0))
    arc(board, (BX1 - R, BY0 + R), (BX1 - R, BY0), (BX1, BY0 + R))
    arc(board, (BX1 - R, BY1 - R), (BX1, BY1 - R), (BX1 - R, BY1))
    arc(board, (BX0 + R, BY1 - R), (BX0 + R, BY1), (BX0, BY1 - R))
    segment(board, (BX0, BY0 + R), (BX0, BY1 - R))
    segment(board, (BX1, BY0 + R), (BX1, BY1 - R))
    for y, ends in ((BY0, top_ends), (BY1, bottom_ends)):
        x = BX0 + R
        for lx, rx in sorted(ends):
            segment(board, (x, y), (lx, y))
            x = rx
        segment(board, (x, y), (BX1 - R, y))


def extent(fp):
    bb = fp.GetBoundingBox(False)
    return (pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight()),
            pcbnew.ToMM(bb.GetCenter().x - fp.GetPosition().x), pcbnew.ToMM(bb.GetCenter().y - fp.GetPosition().y))


def heading(board, text, x, y):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetPosition(vec(x, y))
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(mm(2.0), mm(2.0)))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    board.Add(t)


# --------------------------------------------------------------------------- main
def main():
    if OUT.exists() and "--force" not in sys.argv:
        sys.exit(f"{OUT.name} already exists: it may hold your placement. Use --force to overwrite.")
    comps, net_names, pin_net = read_netlist()

    blank = TMP / "picomondo_blank.kicad_pcb"
    blank.write_text(HEADER, encoding="utf-8")
    board = pcbnew.LoadBoard(str(blank))
    for name in net_names.values():
        board.Add(pcbnew.NETINFO_ITEM(board, name))

    fps, missing = {}, []
    for ref, c in sorted(comps.items()):
        try:
            fps[ref] = new_fp(board, c, pin_net)
        except Exception as e:                        # noqa: BLE001
            missing.append(f"{ref} ({c['footprint']}): {e}")
    if missing:
        print("footprints not loaded:", *missing, sep="\n  ")

    by_value = {c["value"]: ref for ref, c in comps.items()}
    placed = set()

    # --- EdgeLock edge connectors: J1-J4 on the top edge (rotated 180), J9, J6, J5 on the bottom edge
    top = [("J1", 20.2), ("J2", 46.8), ("J3", 73.4), ("J4", 100.0)]
    bottom = [("J9", 20.2), ("J6", 46.8), ("J5", 72.0)]
    top_ends, bottom_ends = [], []
    for row, angle, y, edge_y, store in ((top, 180, BY0 - EDGE_Y, BY0, top_ends),
                                         (bottom, 0, BY1 + EDGE_Y, BY1, bottom_ends)):
        for ref, dx in row:
            fp = fps[ref]
            place(fp, BX0 + dx, y, angle)
            board.Add(fp)
            store.append(edge_ends(fp, edge_y))
            placed.add(ref)
    build_outline(board, top_ends, bottom_ends)

    # --- mounting holes, 4 mm in from each corner
    holes = sorted(r for r, c in comps.items() if c["footprint"].endswith("MountingHole_3.2mm_M3"))
    for ref, (hx, hy) in zip(holes, ((BX0 + 4, BY0 + 4), (BX1 - 4, BY0 + 4), (BX0 + 4, BY1 - 4), (BX1 - 4, BY1 - 4))):
        place(fps[ref], hx, hy)
        fps[ref].Reference().SetVisible(False)           # keep text off the board edge
        board.Add(fps[ref])
        placed.add(ref)

    # --- Arduino Uno R3 and Pico sockets on their exact patterns, centred on the board
    ox, oy = BX0 + BW / 2 - 13.2, BY0 + BH / 2 - 24.13       # Uno pad 1 position
    sockets = [("Arduino power", ox, oy, 90),
               ("Arduino analog", ox + 22.86, oy, 90),
               ("Arduino digital 0-7", ox + 35.56, oy + 48.26, 270),
               ("Arduino digital 8-13", ox + 13.72, oy + 48.26, 270)]
    pico_x, pico_yc = ox + 13.2 - 24.13, oy + 24.13
    sockets += [("Pico left (pins 1-20)", pico_x, pico_yc + 8.89, 90),
                ("Pico right (pins 40-21)", pico_x, pico_yc - 8.89, 90)]
    group = pcbnew.PCB_GROUP(board)
    group.SetName("Arduino + Pico sockets")
    for val, x, y, a in sockets:
        ref = by_value[val]
        place(fps[ref], x, y, a)
        board.Add(fps[ref])
        group.AddItem(fps[ref])
        placed.add(ref)
    board.Add(group)

    # --- stage the rest in rows to the right of the board, grouped by sheet
    sheets = {}
    for ref in sorted(fps):
        if ref not in placed:
            sheets.setdefault(comps[ref]["sheet"], []).append(ref)
    sx0, sy = BX1 + 25.0, BY0
    max_w = 330.0
    for sheet in sorted(sheets):
        heading(board, sheet.upper(), sx0, sy - 3.0)
        x, y, row_h = sx0, sy, 0.0
        for ref in sheets[sheet]:
            fp = fps[ref]
            board.Add(fp)
            w, h, cx, cy = extent(fp)
            w, h = w + 2.5, h + 2.5
            if x + w > sx0 + max_w:
                x, y, row_h = sx0, y + row_h, 0.0
            place(fp, x + w / 2 - cx, y + h / 2 - cy)
            x += w
            row_h = max(row_h, h)
        sy = y + row_h + 8.0

    # --- GND plane on In1.Cu
    z = pcbnew.ZONE(board)
    z.SetLayer(pcbnew.In1_Cu)
    z.SetNet(board.FindNet("GND"))
    z.SetZoneName("GND plane")
    ol = z.Outline()
    ol.NewOutline()
    for px, py in ((BX0 + 0.5, BY0 + 0.5), (BX1 - 0.5, BY0 + 0.5), (BX1 - 0.5, BY1 - 0.5), (BX0 + 0.5, BY1 - 0.5)):
        ol.Append(mm(px), mm(py))
    z.SetMinThickness(mm(0.2))
    z.SetIsFilled(False)
    board.Add(z)

    pcbnew.SaveBoard(str(OUT), board)
    # saving through pcbnew rewrites picomondo.kicad_pro with KiCad's defaults: put our rules and net classes back
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import project_settings
    project_settings.apply()
    print(f"wrote {OUT.name}: {len(fps)} footprints, {len(net_names)} nets")


if __name__ == "__main__":
    main()
