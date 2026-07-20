# BayCom/based — host freeze warning (RX / TX)

**MAX25-Stack** · **BayCom/based** SER12 class (PC-COM / TCM3105)

**Status:** BayCom/based is **not usable** in the shipped product (default build OFF). This page documents freeze risk if an operator enables the experimental opt-in (`-DMAX25_BUILD_MAX25_BCPR=ON`).

> **Warning:** On some hosts (especially interactive desktops), **RX and TX** with BayCom/based PC-COM-class hardware can **hard-freeze** or soft-hang the machine — historically observed with kernel `baycom_ser_fdx`. Treat SQ-open / strong RF / USB HID hubs as risk.

## Freeze classes

| Class | Typical trigger | Radio needed? |
|-------|-----------------|---------------|
| **TX / calibrate (legacy kernel)** | `baycom_test calibrate N`, HDLC calibrate ioctl | **No** — observed with radio **off** |
| **RX / RF EMI** | Peer packet TX / strong RF near the PC; USB HID dropout (`EMI?` in `dmesg`) | Over-air RF; can freeze **even if** no modem driver is loaded |
| Soft hang | High UART IRQ bitbang load; brief input/USB stall | Often radio off |

Kernel `baycom_ser_fdx` / `baycom-pr` was **removed** from this tree (2026-07-18). Do **not** reintroduce calibrate against `bcsf*` on interactive desktops.

## Forbidden / high risk on interactive desktops

| Do not | Why |
|--------|-----|
| Load `baycom_ser_fdx` / run calibrate helpers | Instant hard freeze observed on interactive hosts |
| Hot-plug radio/mic cables while any path owns the UART | Freeze risk |
| Leave stack up unattended next to live RF | EMI class |

## Safer practice (experimental opt-in only)

| Do | Notes |
|----|--------|
| Prefer **not** enabling BayCom/based | Product status: **not usable** — [BAYCOM.md](BAYCOM.md) |
| Prefer a **dedicated / minimal** host if experimenting | Not a daily desktop with USB HID on a hub |
| Unplug AF / power radio off when not testing | Reduces EMI class |
| Move keyboard/mouse to motherboard USB ports | Avoid front/shared hubs near RF |

## Related

| Topic | Path |
|-------|------|
| BayCom/based status | [BAYCOM.md](BAYCOM.md) |
| Unified TX/RX release test | [TX-RX-TEST.md](TX-RX-TEST.md) · `scripts/tx-rx-test.sh` |
