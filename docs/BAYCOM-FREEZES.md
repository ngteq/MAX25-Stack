# BayCom / PC-COM — host freeze warning (RX / TX)

**MAX25-Stack** · kernel path `baycom_ser_fdx` (SER12) · PC-COM and other BayCom-compatible modems

> **Warning:** On some hosts (especially interactive desktops), **RX and TX** with a BayCom-compatible PC-COM modem can **hard-freeze** or soft-hang the machine. Read this before `baycom-pr-ctl start` or any PTT/calibrate test.

## Freeze classes

| Class | Typical trigger | Radio needed? |
|-------|-----------------|---------------|
| **TX / calibrate** | `baycom_test calibrate N`, HDLC calibrate ioctl, heavy SER12 TX | **No** — observed with radio **off** |
| **RX / RF EMI** | Peer packet TX / strong RF near the PC; USB HID dropout (`EMI?` in `dmesg`) | Over-air RF; can freeze **even if** `baycom_ser_fdx` is **unloaded** |
| Soft hang | Driver loaded, ~100–200 IRQ/s idle bitbang; brief input/USB stall | Often radio off |

The Linux `baycom_ser_fdx` driver bit-bangs the UART under interrupt load (`local_irq_enable` inside the hard IRQ path). Wrong IRQ / UART conflict can also lock the host — see [GUIDE.md §6](../stacks/baycom-pr/docs/GUIDE.md#6-after-a-freeze-or-crash) and [STABILITY.md](../stacks/baycom-pr/docs/archive/STABILITY.md).

## Forbidden / high risk on interactive desktops

| Do not | Why |
|--------|-----|
| `baycom_test calibrate …` | Keys PTT + calibration pattern — **instant hard freeze** observed |
| `sethdlc -c …` / `BAYCOM_SELFTEST_FULL=yes` PTT | Same calibrate path |
| Raw `modprobe baycom_ser_fdx iobase=… irq=…` | Bypass preflight → wrong IRQ / 8250 conflict |
| Hot-plug radio/mic cables while driver owns the UART | Freeze risk |
| Leave stack up unattended next to live RF | EMI + driver load |

## Safer practice

| Do | Notes |
|----|--------|
| `baycom-pr-ctl preflight` then `start` | Never skip preflight |
| Prefer a **dedicated / minimal** host for durable PC-COM | Not a daily desktop with USB HID on a hub |
| Unplug AF / power radio off when not testing | Reduces EMI class |
| Move keyboard/mouse to motherboard USB ports | Avoid front/shared hubs near RF |
| After any freeze: `baycom-pr-ctl recover` | Then doctor / preflight before start |

## Direction

Planned follow-on: **userspace** SER12/PC-COM solution **with or without** `baycom_ser_fdx` — still TBD. See [BAYCOM.md § Direction](BAYCOM.md#direction-userspace).

## Related

| Doc | Role |
|-----|------|
| [BAYCOM.md](BAYCOM.md) | Device / start matrix · userspace direction |
| [stacks/baycom-pr/docs/GUIDE.md](../stacks/baycom-pr/docs/GUIDE.md) | Operator bring-up + freeze recovery |
| [stacks/baycom-pr/docs/kernel/BAYCOM-DRIVER-ANALYSIS.md](../stacks/baycom-pr/docs/kernel/BAYCOM-DRIVER-ANALYSIS.md) | Driver IRQ path |
| [stacks/baycom-pr/docs/archive/STABILITY.md](../stacks/baycom-pr/docs/archive/STABILITY.md) | Stack safeguards |
