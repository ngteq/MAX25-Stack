# MAX25-Stack-v1.0.0 — hardware acceptance protocol

**Purpose:** Manual smoke tests per **active** v1 device after offline CI is green. Not run in CI (no RF/UART in build farm).

**Offline gates first:** `./scripts/release-check.sh` — see [RELEASE-READINESS.md](../RELEASE-READINESS.md).

---

## Active devices (v1.0.0)

| Device | Backend | Minimum smoke |
|--------|---------|---------------|
| `tnc2c` | serial KISS | UART open, boot-wait or reset script, KISS frame echo |
| `baycom-ser12` | kernel BayCom | `baycom_test`, PTT/RX path |
| `soft-crdop` | crdop-tcp | TCP :8515 connect + Phase 0 bench (RF optional) |

---

## Generic procedure (all devices)

1. Build and install: `./scripts/build.sh` · `cmake --install` to test prefix.
2. Edit site `max25d.ini` — `[devices]` + `[device.*]` (placeholders only in docs: `/dev/ttyUSB0`).
3. `max25-ctl start --hardware <family> --device <id>`.
4. `max25-terminal` → `SET DEVICE <id>` → `CONNECT` → `SEND` test UI frame.
5. Log: backend `open`, no `error-*` status, RX display line if loopback/reflector available.

---

## tnc2c

| Step | Action | Pass |
|------|--------|------|
| 1 | Free serial port (`fuser` / stop conflicting daemons) | Port exclusive |
| 2 | `stacks/tncs/tnc2c-host-reset.sh --kiss` or max25d boot-wait | TNC responds |
| 3 | `max25d` with `tnc2c` device | `status: open` |
| 4 | Send UI via terminal | `[AX25 UI …]` or KISS loopback |

Recovery: [`tnc_serial_recovery.py`](../stacks/tncs/tnc_serial_recovery.py) — [stacks/tncs/docs/TNC-RECOVERY.md](../stacks/tncs/docs/TNC-RECOVERY.md).

---

## baycom-ser12

| Step | Action | Pass |
|------|--------|------|
| 1 | Kernel module loaded, `baycom_test` | Module OK |
| 2 | `max25d` device `baycom-ser12` | PTY/KISS bridge up |
| 3 | PTT keyed, short TX | No kernel oops; TXDELAY sane |

See [BAYCOM.md](BAYCOM.md), `share/baycom/` INI examples.

---

## soft-crdop (CRDOP)

| Step | Action | Pass |
|------|--------|------|
| 1 | `crdopc` or `audio-dummyd` on :8515/:8516 | TCP OK |
| 2 | `max25d` `soft-crdop` device | `CrdopTcpBackend` open |
| 3 | Phase 0 bench | [ACOUSTIC-TEST-PROTOCOL.md](../stacks/crdop/docs/ACOUSTIC-TEST-PROTOCOL.md) T0–T6 |
| 4 | *(optional)* Line/acoustic to FM rig | AX.25 UI decoded on-air |

**v1.0.0 tag:** Steps 1–3 sufficient offline. Step 4 = post-tag operator acceptance.

---

## Sign-off template

| Field | Value |
|-------|-------|
| Date | |
| MAX25 version | `1.0.0` |
| Host | |
| Device tested | |
| Result | PASS / FAIL |
| Notes | |

Store results in operator log (not committed to repo unless anonymized).

---

## Out of scope v1.0.0

`pktnc2`, `baycom-par96`, `baycom-kiss` — scaffold only; no acceptance required.
