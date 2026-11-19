"""Bring the saved board in line with bom/parts.csv without touching placement or routing.

  * swaps the BOOTSEL / RESET switch footprints to the TS-1187A footprint (position, rotation, references, paths and
    nets carried over; pad 1 and pad 2 keep their nets);
  * writes the LCSC and MPN fields onto every footprint whose (Value, Footprint) is in the table.

Close KiCad's PCB editor first. A backup picomondo.kicad_pcb.bak is written. Run with KiCad's Python:
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools\\sync_board_parts.py
(Running Update PCB from Schematic in KiCad afterwards does the same job; this just saves a step.)
"""
import csv
import shutil
import sys
import time
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "picomondo.kicad_pcb"
PRO = ROOT / "picomondo.kicad_pro"
PRETTY = ROOT / "lib" / "picomondo.pretty"
OLD_SW = "SW_Push_1P1T_NO_Vertical_Wuerth_434133025816"
NEW_SW = "SW_SMD_TS-1187A_5.1x5.1"


def set_hidden(fp, key, value):
    fp.SetField(key, value)
    fp.GetField(key).SetVisible(False)


def swap_switch(board, old):
    new = pcbnew.FootprintLoad(str(PRETTY), NEW_SW)
    new.SetFPID(pcbnew.LIB_ID("picomondo", NEW_SW))
    new.SetPosition(old.GetPosition())
    new.SetOrientation(old.GetOrientation())
    if old.GetLayer() != new.GetLayer():
        new.Flip(old.GetPosition(), False)
    new.SetReference(old.GetReference())
    new.SetValue(old.GetValue())
    new.SetPath(old.GetPath())
    new.Reference().SetVisible(old.Reference().IsVisible())
    new.Value().SetVisible(old.Value().IsVisible())
    nets = {}
    for pad in old.Pads():
        nets.setdefault(pad.GetNumber(), pad.GetNet())
    for pad in new.Pads():
        if pad.GetNumber() in nets:
            pad.SetNet(nets[pad.GetNumber()])
    for field in old.GetFields():
        if field.GetName() not in ("Reference", "Value", "Footprint", "Datasheet", "Description"):
            set_hidden(new, field.GetName(), field.GetText())
    board.Remove(old)
    board.Add(new)
    return new


def main():
    shutil.copy2(PCB, PCB.with_suffix(".kicad_pcb.bak"))
    pro_bytes = PRO.read_bytes()
    table = {(r["Value"], r["Footprint"]): r for r in csv.DictReader(open(ROOT / "bom" / "parts.csv", encoding="utf-8"))}
    board = pcbnew.LoadBoard(str(PCB))
    swapped = fields = 0
    for fp in list(board.GetFootprints()):
        if str(fp.GetFPID().GetLibItemName()) == OLD_SW:
            fp = swap_switch(board, fp)
            swapped += 1
        row = table.get((fp.GetValue(), f"{fp.GetFPID().GetLibNickname()}:{fp.GetFPID().GetLibItemName()}"))
        if row:
            for key in ("LCSC", "MPN"):
                if row[key]:
                    set_hidden(fp, key, row[key])
                    fields += 1
    pcbnew.SaveBoard(str(PCB), board)
    for attempt in range(5):                              # the file can be briefly busy right after a save
        try:
            PRO.write_bytes(pro_bytes)
            break
        except OSError:
            time.sleep(1)
    print(f"swapped {swapped} switches, wrote {fields} fields")


if __name__ == "__main__":
    sys.exit(main())
