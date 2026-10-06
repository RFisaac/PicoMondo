"""Shared footprints and small circuit cells (capacitor / resistor between two nets)."""
from kihelp import POWER_SYMBOLS

C, R, L = "Device:C", "Device:R", "Device:L"

FP_C0402 = "Capacitor_SMD:C_0402_1005Metric"
FP_C0402_SMALL = "picomondo:C_0402_1005Metric_small_pads"
FP_C0603 = "Capacitor_SMD:C_0603_1608Metric"
FP_C0805 = "Capacitor_SMD:C_0805_2012Metric"
FP_C1206 = "Capacitor_SMD:C_1206_3216Metric"
FP_R0402 = "Resistor_SMD:R_0402_1005Metric"
FP_R0603 = "Resistor_SMD:R_0603_1608Metric"
FP_R2512 = "Resistor_SMD:R_2512_6332Metric"


def _len(net):
    return 0 if net in POWER_SYMBOLS else 5.08


def cap(s, refs, x, y, value, fp, top, bot, dnp=False, extra=None):
    """Vertical capacitor from net `top` to net `bot`."""
    p = s.add(C, refs.next("C"), value, fp, x, y, dnp=dnp, extra=extra)
    s.attach(p.pin(1), top, length=_len(top))
    s.attach(p.pin(2), bot, length=_len(bot))
    return p


def res(s, refs, x, y, value, top, bot, rot=0, dnp=False, fp=FP_R0402, extra=None):
    """Resistor between two nets: vertical (rot 0, pin 1 on top) or horizontal (rot 90, pin 1 left)."""
    p = s.add(R, refs.next("R"), value, fp, x, y, rot=rot, dnp=dnp, extra=extra)
    s.attach(p.pin(1), top, length=_len(top))
    s.attach(p.pin(2), bot, length=_len(bot))
    return p
