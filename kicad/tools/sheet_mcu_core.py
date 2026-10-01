"""MCU core sheet: RP2350B + on-chip regulator, decoupling, crystal, QSPI flash, boot/reset, USB
series resistors and SWD header.

Circuit values and connections follow the Raspberry Pi "RP2350B Minimal Board" reference
(Hardware design with RP2350, Appendix B), except:
  * flash is a W25Q128JVS (16 MB), as in the reference; a second memory footprint is kept (DNP)
  * the NCP1117 supply and micro-USB connector are not here (power and USB live on other sheets)
"""
from cells import (C, FP_C0402, FP_C0402_SMALL, FP_C0805, FP_R0402, L, R, cap, res)

FP_L2016 = "picomondo:L_pol_2016"
FP_QFN80 = "picomondo:RP2350-QFN-80-1EP_10x10_P0.4mm_EP3.4x3.4mm_ThermalVias"
FP_SOIC8 = "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm"
FP_SW = "Button_Switch_SMD:SW_Push_1P1T_NO_Vertical_Wuerth_434133025816"
FP_SWD = "Connector_JST:JST_SH_SM03B-SRSS-TB_1x03-1MP_P1.00mm_Horizontal"


def build(s, refs):
    # ------------------------------------------------------------------ the MCU
    u1 = s.add("MCU_RaspberryPi_RP2350:RP2350_80QFN", refs.next("U"), "RP2350B", FP_QFN80,
               254.0, 190.5, extra={"MPN": "RP2350B"})

    # Right edge: GPIOs (global labels, used on the IO sheets) and USB data pins.
    for n in range(48):
        pin = {0: 77, 1: 78, 2: 79, 3: 80, 4: 1, 5: 2, 6: 3, 7: 4, 8: 6, 9: 7, 10: 8, 11: 9,
               12: 11, 13: 12, 14: 13, 15: 14, 16: 16, 17: 17, 18: 18, 19: 19, 20: 20, 21: 21,
               22: 22, 23: 23, 24: 25, 25: 26, 26: 27, 27: 28, 28: 36, 29: 37, 30: 38, 31: 39,
               32: 40, 33: 42, 34: 43, 35: 44, 36: 45, 37: 46, 38: 47, 39: 48, 40: 49, 41: 52,
               42: 53, 43: 54, 44: 55, 45: 56, 46: 57, 47: 58}[n]
        s.attach(u1.pin(pin), f"GPIO{n}", length=10.16, glob=True)
    s.attach(u1.pin(66), "USB_DM_CHIP", length=10.16)
    s.attach(u1.pin(67), "USB_DP_CHIP", length=10.16)

    # Left edge: regulator, QSPI, clock, reset, SWD.
    for num, net in {61: "VREG_AVDD", 63: "VREG_LX", 64: "+3V3", 65: "+1V1", 62: "GND",
                     70: "QSPI_SD3", 71: "QSPI_SCLK", 72: "QSPI_SD0", 73: "QSPI_SD2",
                     74: "QSPI_SD1", 75: "QSPI_SS", 30: "XIN", 31: "XOUT",
                     33: "SWCLK", 34: "SWDIO"}.items():
        s.attach(u1.pin(num), net, length=10.16)
    s.attach(u1.pin(35), "RUN", length=10.16, glob=True)

    # Top edge: core and I/O supply pins joined on two rails.
    s.bus([u1.pin(n) for n in (10, 32, 51)], "+1V1")
    s.bus([u1.pin(n) for n in (5, 15, 24, 29, 41, 50, 60, 76, 59, 68, 69)], "+3V3")
    # Bottom: exposed pad (thermal pad, needs ground vias on the PCB)
    s.attach(u1.pin(81), "GND")

    # ------------------------------------------------------------------ on-chip regulator
    x0, y0 = 50.8, 63.5
    s.note("ON-CHIP REGULATOR (copy the Pi reference layout exactly)\n"
           "L1: Abracon AOTA-B201610S3R3-101-T, polarity dot toward VREG_LX.\n"
           "Keep L1, C6, C7, R3, C9 within 10 mm of U1; VREG_LX short and wide, no vias.\n"
           "R3 must be close to U1.", x0 - 12.7, y0 - 17.78)
    l1 = s.add(L, refs.next("L"), "3.3u", FP_L2016, x0, y0, rot=180,
               extra={"MPN": "AOTA-B201610S3R3-101-T"})
    s.attach(l1.pin(2), "+1V1", length=0)
    s.attach(l1.pin(1), "VREG_LX", length=5.08)
    xs = x0 + 25.4
    for val, fp in (("4.7u", FP_C0402_SMALL), ("4.7u", FP_C0402_SMALL), ("100n", FP_C0402),
                    ("100n", FP_C0402)):
        cap(s, refs, xs, y0, val, fp, "+1V1", "GND")
        xs += 15.24
    cap(s, refs, xs, y0, "4.7u", FP_C0402_SMALL, "+3V3", "GND")   # VREG_VIN bulk
    xs += 20.32
    r3 = s.add(R, refs.next("R"), "33", FP_R0402, xs, y0)
    c9 = s.add(C, refs.next("C"), "4.7u", FP_C0402_SMALL, xs, y0 + 7.62)
    s.attach(r3.pin(1), "+3V3", length=0)
    s.attach(c9.pin(2), "GND", length=0)
    node = r3.pin(2).pos          # R3 pin 2 and C9 pin 1 meet here
    end = (node[0] + 10.16, node[1])
    s.wire(node, end)
    s.label("VREG_AVDD", end, 0)
    s.flag_net(node, direction=180)   # VREG_AVDD is a filtered supply node (ERC: driven)

    # ------------------------------------------------------------------ decoupling
    s.note("DECOUPLING: one 100 nF per supply pin, within 5 mm of the pin; pins 68 and 69 share one.\n"
           "4.7 uF on the +1V1 rail sits on the opposite side of the chip from the regulator.",
           x0 - 12.7, 94.0)
    for i in range(9):
        cap(s, refs, x0 + 12.7 * i, 106.68, "100n", FP_C0402, "+3V3", "GND")
    cap(s, refs, x0 + 12.7 * 9, 106.68, "10u", FP_C0805, "+3V3", "GND")
    s.flag("+1V1", (x0 + 12.7 * 11, 106.68 + 15.24))
    s.flag("GND", (x0 + 12.7 * 13, 106.68 + 15.24))

    # ------------------------------------------------------------------ crystal
    x, y = 63.5, 190.5
    s.note("12 MHz CRYSTAL: Abracon ABM8-272-T3 (10 pF load) with 15 pF caps and 1k series resistor.\n"
           "Traces short; ground under the crystal; keep other signals out.", x - 12.7, y - 17.78)
    y1 = s.add("Device:Crystal_GND24", refs.next("Y"), "ABM8-272-T3",
               "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", x, y,
               extra={"MPN": "ABM8-272-T3"})
    s.attach(y1.pin(2), "GND", length=0)          # pins 2 and 4 are the same point in the symbol
    c3 = s.add(C, refs.next("C"), "15p", FP_C0402, x - 3.81, y + 10.16)
    s.wire(y1.pin(1).pos, c3.pin(1).pos)
    s.attach(c3.pin(2), "GND", length=0)
    s.attach(y1.pin(1), "XIN", length=5.08)
    s.junction(y1.pin(1).pos)
    r2 = s.add(R, refs.next("R"), "1k", FP_R0402, x + 16.51, y, rot=90)
    nodeb = (x + 8.89, y)
    s.wire(y1.pin(3).pos, nodeb)
    s.wire(nodeb, r2.pin(1).pos)
    s.junction(nodeb)
    c4 = s.add(C, refs.next("C"), "15p", FP_C0402, x + 8.89, y + 10.16)
    s.wire(nodeb, c4.pin(1).pos)
    s.attach(c4.pin(2), "GND", length=0)
    s.attach(r2.pin(2), "XOUT", length=5.08)

    # ------------------------------------------------------------------ flash + boot
    x, y = 63.5, 279.4
    s.note("QSPI FLASH: W25Q128JVS, 16 MB (RP2350 addresses at most 16 MB per chip select).\n"
           "Keep QSPI traces short; place R1, R6, R9, R10 close to the flash.", x - 12.7, y - 30.48)
    u2 = s.add("Memory_Flash:W25Q128JVS", refs.next("U"), "W25Q128JVS", FP_SOIC8, x, y,
               extra={"MPN": "W25Q128JVS"})
    for num, net in {1: "FLASH_SS", 2: "QSPI_SD1", 3: "QSPI_SD2", 4: "GND", 5: "QSPI_SD0",
                     6: "QSPI_SCLK", 7: "QSPI_SD3", 8: "+3V3"}.items():
        s.attach(u2.pin(num), net)
    cap(s, refs, x + 38.1, y - 12.7, "100n", FP_C0402, "+3V3", "GND")
    res(s, refs, x + 53.34, y - 12.7, "0", "QSPI_SS", "FLASH_SS")                  # primary CS link
    res(s, refs, x + 68.58, y - 12.7, "10k", "+3V3", "FLASH_SS", dnp=True)         # optional pull-up
    res(s, refs, x + 83.82, y - 12.7, "0", "GPIO0", "FLASH_SS", dnp=True)          # CS on GPIO0 option

    # Optional second memory (flash or PSRAM) on chip select 1 = GPIO0. Not fitted by default.
    u3 = s.add("Memory_Flash:W25Q128JVS", refs.next("U"), "DNP second memory", FP_SOIC8,
               x + 63.5, y + 25.4, dnp=True)
    for num, net in {1: "FLASH2_SS", 2: "QSPI_SD1", 3: "QSPI_SD2", 4: "GND", 5: "QSPI_SD0",
                     6: "QSPI_SCLK", 7: "QSPI_SD3", 8: "+3V3"}.items():
        s.attach(u3.pin(num), net)
    s.note("Optional second memory (not fitted): populate with R-link GPIO0->FLASH2_SS, its pull-up and decoupling.\n"
           "Uses GPIO0 as chip select, so GPIO0 is then unavailable on the EdgeLock/Arduino connectors.",
           x + 25.4, y + 57.0)
    res(s, refs, x + 106.68, y + 25.4, "0", "GPIO0", "FLASH2_SS", dnp=True)
    res(s, refs, x + 121.92, y + 25.4, "10k", "+3V3", "FLASH2_SS", dnp=True)
    cap(s, refs, x + 137.16, y + 25.4, "100n", FP_C0402, "+3V3", "GND", dnp=True)

    # BOOTSEL: pulling QSPI_SS low through 1k at reset starts the USB bootloader.
    bx, by = 63.5, 355.6
    s.note("BOOTSEL: hold while resetting to enter the USB bootloader (QSPI_SS pulled low via 1k).\n"
           "RESET: pulls RUN low.", bx - 12.7, by - 17.78)
    res(s, refs, bx, by, "1k", "QSPI_SS", "USB_BOOT_N")
    sw1 = s.add("Switch:SW_Push", refs.next("SW"), "BOOTSEL", FP_SW, bx + 38.1, by + 12.7,
                extra={"MPN": "B3FS-4005P"})
    s.attach(sw1.pin(1), "USB_BOOT_N", length=5.08)
    s.attach(sw1.pin(2), "GND", length=5.08)
    sw2 = s.add("Switch:SW_Push", refs.next("SW"), "RESET", FP_SW, bx + 91.44, by,
                extra={"MPN": "B3FS-4005P"})
    s.attach(sw2.pin(1), "RUN", length=5.08, glob=True)
    s.attach(sw2.pin(2), "RESET_N", length=5.08)
    res(s, refs, bx + 121.92, by, "1k", "RESET_N", "GND")

    # ------------------------------------------------------------------ USB series resistors
    ux, uy = 355.6, 177.8
    s.note("USB: 27 ohm series resistors close to U1; 90 ohm differential pair, solid ground below.\n"
           "USB_D+ / USB_D- are global nets used by the USB-C connector sheet.", ux - 12.7, uy - 17.78)
    for off, chip, conn in ((0, "USB_DP_CHIP", "USB_D+"), (12.7, "USB_DM_CHIP", "USB_D-")):
        rr = s.add(R, refs.next("R"), "27", FP_R0402, ux, uy + off, rot=90)
        s.attach(rr.pin(1), chip, length=5.08)
        s.attach(rr.pin(2), conn, length=5.08, glob=True)

    # ------------------------------------------------------------------ SWD header
    jx, jy = 355.6, 254.0
    j4 = s.add("Connector_Generic_MountingPin:Conn_01x03_MountingPin", refs.fixed("J", 10), "SWD",
               FP_SWD, jx, jy, extra={"MPN": "SM03B-SRSS-TB"})
    s.attach(j4.pin(1), "SWCLK", length=5.08)
    s.attach(j4.pin(2), "GND", length=5.08)
    s.attach(j4.pin(3), "SWDIO", length=5.08)
    s.attach(j4.pin("MP"), "GND", length=0)
