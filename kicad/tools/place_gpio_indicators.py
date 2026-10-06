"""Put each GPIO indicator (470 ohm + white LED, plus the solder jumper on the ADC pins) at its EdgeLock pin.

Continues the column made by place_edgelock_resistors.py (the 100 ohm resistor is 6.5 mm from the pad centre). Distances are
along the pin, away from the board edge:

  every pin:    pad ... 100 ohm (6.5) ... 470 ohm (9.0)
  (a pin whose LED branch still has a solder jumper gets it at 9.3 and its 470 ohm at 12.0; the ADC jumpers were removed)

The LED is not in the column: it sits beside the 470 ohm, 2 mm to the side, in an L. Within a pair of pins the one on the
left has its LED shifted left and the one on the right shifted right. Where four signal pins are side by side (J5, J6)
the two outer pins do the same and the two inner pins have no free side, so their LED goes straight below the 470 ohm.
Each part is turned so the pad on the net nearest the connector faces the connector. Reference text on the new parts is
hidden (it collides at a 2 mm pitch). GPIO32 and GPIO33 have no EdgeLock pin and are left where they are.

Close KiCad's PCB editor first. Backs up the board, and takes the parts out of any group.
  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/place_gpio_indicators.py
"""
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
JUMPER_AT, R_ADC_AT, R_AT = 9.3, 12.0, 9.0
SIDE = 2.0            # mm from the 470 ohm to its LED, sideways
LED_DROP = 0.4        # LED centre this far past the 470 ohm centre, so its anode pad meets the resistor's inner pad
INLINE_DROP = 2.4     # LED centre this far past the 470 ohm centre when it sits straight below it


def nets(fp):
    return {p.GetNetname() for p in fp.Pads()}


def other_net(fp, net):
    return next((p.GetNetname() for p in fp.Pads() if p.GetNetname() != net), None)


def place(board, fp, pad_pos, u, dist, outer_net, side=0.0):
    """Centre fp `dist` mm inboard of pad_pos, long axis along the pin, outer_net's pad towards the connector."""
    fp.SetPosition(pcbnew.VECTOR2I(int(pad_pos.x + (u[0] * dist + side) * MM), int(pad_pos.y + u[1] * dist * MM)))
    for angle in (90, 270):
        fp.SetOrientationDegrees(angle)
        near = next(p for p in fp.Pads() if p.GetNetname() == outer_net)
        far = next(p for p in fp.Pads() if p.GetNetname() != outer_net)
        dn = (near.GetPosition().x - pad_pos.x) ** 2 + (near.GetPosition().y - pad_pos.y) ** 2
        df = (far.GetPosition().x - pad_pos.x) ** 2 + (far.GetPosition().y - pad_pos.y) ** 2
        if dn < df:
            break
    fp.Reference().SetVisible(False)
    for g in board.Groups():
        if fp in g.GetItems():
            g.RemoveItem(fp)


def main():
    shutil.copy2(PCB, PCB.with_suffix(".kicad_pcb.bak"))
    pro_bytes = PRO.read_bytes()
    board = pcbnew.LoadBoard(str(PCB))
    fps = list(board.GetFootprints())
    r100 = [f for f in fps if f.GetValue() == "100" and f.GetReference().startswith("R")]
    r470 = [f for f in fps if f.GetValue() == "470" and f.GetReference().startswith("R")]
    jumpers = [f for f in fps if f.GetValue() == "LED enable"]
    leds = [f for f in fps if f.GetReference().startswith("D") and f.GetValue() in ("white", "power", "user")]
    done, skipped = [], []
    mine = set()          # parts this script is placing (and the 100 ohm resistors), ignored by the overlap check
    mine.update(f.GetReference() for f in r100)
    for conn in sorted((f for f in fps if "EdgeLock" in str(f.GetFPID().GetLibItemName())), key=lambda f: f.GetReference()):
        theta = math.radians(conn.GetOrientationDegrees())
        u = (math.sin(theta), -math.cos(theta))              # board interior, in board coordinates
        assert abs(u[0]) < 1e-6, "columns are assumed to run along Y"
        pads = sorted((p for p in conn.Pads() if p.GetNetname().startswith("Net-(")), key=lambda p: p.GetPosition().x)
        # runs of signal pads at the 2 mm pitch; role of each: 'left' / 'right' (LED beside the 470) or 'below'
        runs, run = [], []
        for p in pads:
            if run and p.GetPosition().x - run[-1].GetPosition().x > 2.5 * MM:
                runs.append(run)
                run = []
            run.append(p)
        runs.append(run)
        role = {}
        for run in runs:
            for i, p in enumerate(run):
                if len(run) == 1:
                    role[p.GetNumber()] = "right"
                elif i == 0:
                    role[p.GetNumber()] = "left"
                elif i == len(run) - 1:
                    role[p.GetNumber()] = "right"
                else:
                    role[p.GetNumber()] = "below"
        for pad in pads:
            conn_net = pad.GetNetname()
            r = next((f for f in r100 if conn_net in nets(f)), None)
            gpio = other_net(r, conn_net)
            jp = next((f for f in jumpers if gpio in nets(f)), None)
            top = other_net(jp, gpio) if jp else gpio        # net at the 470 ohm's outer pad
            res = next((f for f in r470 if top in nets(f)), None)
            led = None
            if res is not None:
                lnet = other_net(res, top)
                led = next((f for f in leds if lnet in nets(f)), None)
            if res is None or led is None:
                skipped.append(f"{conn.GetReference()}.{pad.GetNumber()} ({gpio})")
                continue
            p = pad.GetPosition()
            r_at = R_ADC_AT if jp else R_AT
            if jp:
                place(board, jp, p, u, JUMPER_AT, gpio)
            place(board, res, p, u, r_at, top)
            mine.update({jp.GetReference() if jp else "", res.GetReference(), led.GetReference(), r.GetReference()})
            if role[pad.GetNumber()] != "below":
                place(board, led, p, u, r_at + LED_DROP, lnet, side=SIDE if role[pad.GetNumber()] == "right" else -SIDE)
                spot = led.GetBoundingBox(False)
                spot.Inflate(int(0.3 * MM))
                blocker = next((f for f in fps if f.GetReference() not in mine and f is not conn
                                and spot.Intersects(f.GetBoundingBox(False))), None)
                if blocker is not None:
                    print(f"{led.GetReference()} would overlap {blocker.GetReference()}: placed below its 470 ohm instead")
                    role[pad.GetNumber()] = "below"
            if role[pad.GetNumber()] == "below":
                place(board, led, p, u, r_at + INLINE_DROP, lnet)
            done.append(f"{conn.GetReference()}.{pad.GetNumber()}:{gpio}")
    pcbnew.SaveBoard(str(PCB), board)
    for _ in range(5):                                       # pcbnew rewrites the project file; keep yours
        try:
            PRO.write_bytes(pro_bytes)
            break
        except OSError:
            time.sleep(1)
    print(f"placed {len(done)} columns; skipped: {skipped or 'none'}")


if __name__ == "__main__":
    sys.exit(main())
