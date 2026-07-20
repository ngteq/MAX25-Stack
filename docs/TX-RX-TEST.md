# TX / RX release test · MAX25-Stack

**RX before TX (§0.20):** live `--tx` requires Soft-DCD/noise (`dcd-bc*` / `rx-activity-bc*`) or TNC RX CONNECT in the same run. Override only `--force-tx` (against policy).
**Root (§0.21):** start via `scripts/run-max25d.sh` (auto sudo/su).


Unified operator and CI test for **TX** and **RX** on both device classes:

| Class | Public mark | Internal / code |
|-------|-------------|-----------------|
| Modem (SER12 / PC-COM) | **BayCom/based** | **bcpr** |
| Classic TNC | TNC / KISS serial | `tnc2c`, `pktnc2`, … |

Entry: `scripts/tx-rx-test.sh`. Offline **L0** ships in release gates (`ctest`, `max25_test`, `release-check.sh`). Live / TX levels are **manual** (operator-gated).

## Levels

| Level | Name | Default | Scope |
|-------|------|---------|-------|
| **L0** | Offline | **always** | Host CONNECT/SEND loopback · KISS encode/decode · TNC recovery units · bcpr HDLC/dry-run smoke |
| **L1** | Soft preflight | `--level 1` | bcpr preflight soft · TNC profile present |
| **L2/L3** | Live RX | `--live` | Modem: timed `max25-bcprd` attach + listen (nofreeze). TNC: unix `CONNECT` + STATUS |
| **L4** | Capped TX | `--live --tx` | Modem: ~3s KISS UI (default `--tx-seconds 3`, ≈376B info) + MCR proof. TNC: one `SEND` on live socket |

Defaults: **NO TX**. Live seconds capped (default 15, max 60). No calibrate. No kernel `baycom_ser_fdx`.

L4 modem notes:

| Item | Contract |
|------|----------|
| Payload | Default ~3s PTT (proven AX25WRK1 inject: info **376B** → ~3005 ms MCR) — not a 23-byte stub |
| `--tx-seconds N` | Target key window (1–12); longer than ~3s uses multiple bursts (`BCPR_MAXFLEN` cap) |
| Host proof | Script requires UART **MCR** key (`0x0e`/`0x0f`); `PASS:` without MCR = fail |
| Live stack | Reuses running `max25-bcprd` + `kiss_link` when present (no second attach / no blanket `pkill`) |
| KISS peer | Smoke keeps the KISS slave open during TX (standalone attach); closing after write → POLLHUP → no MCR |
| RF evidence | Wattmeter needle + radio TX/PTT LED during the key window — not automated |

## Operator RF evidence (optional · not automated)

On a live host with radio + in-line wattmeter (e.g. AX25WRK1), during `--live --tx` (~3s default):

| Check | Pass |
|-------|------|
| External power meter | Needle deflection during TX burst |
| Radio TX / PTT LED | Lit for the TX window (~3s) |
| Script line | `MCR_keyed=…ms` and `PASS: L4 TX MCR keyed` |

Host write-only `PASS:` without MCR is insufficient. SQ closed / no speaker audio does **not** disprove TX. Not in CI.

## Offline (CI / release)

```bash
cd /path/to/MAX25-Stack

# Operator entry (L0)
./scripts/tx-rx-test.sh

# Or via CMake
cmake -B build -DCMAKE_BUILD_TYPE=Release -DMAX25_BUNDLE_AX25=OFF -DMAX25_BUILD_MAX25_BCPR=ON
cmake --build build -j"$(nproc)"
cmake --build build --target max25_tx_rx_test
# also: ctest -R max25_tx_rx_offline --output-on-failure
# umbrella: cmake --build build --target max25_test
# release:  bash scripts/release-check.sh
```

Pass criterion: all `PASS:` / `OK:` lines; exit 0.

## Live — BayCom/based (bcpr / PC-COM)

Requires root + live INI (`dry_run=no`, real IRQ/serial). Prefer dedicated host. See [BAYCOM.md](BAYCOM.md) · [BAYCOM-FREEZES.md](BAYCOM-FREEZES.md).

```bash
# Soft L1 + short live RX (radio may be OFF)
sudo ./scripts/tx-rx-test.sh --device modem --live --seconds 15 \
  -c /etc/max25/max25-bcpr.ini

# Capped TX (~3s PTT — watch wattmeter / TX LED; MCR required for PASS)
sudo ./scripts/tx-rx-test.sh --device modem --live --tx --tx-seconds 3 \
  -c /etc/max25/max25-bcpr.ini

# Longer attach window (optional)
sudo ./scripts/tx-rx-test.sh --device modem --live --tx --seconds 20 --tx-seconds 3 \
  -c /etc/max25/max25-bcpr.ini
```

Equivalent max25-bcpr-only path: `stacks/max25-bcpr/tools/max25-bcpr-ctl smoke [--live] [--tx] [--tx-seconds N]`.

Prefer a running max25d/max25-bcprd stack (script reuses `kiss_link`). Fresh timed `max25-bcprd` only when none is running.

max25d path (after stack up): `max25-terminal -U /run/max25/modem.sock` (with `default = max25e0`, no `-d` required) → `CONNECT` → `SEND …` — host TX keys UART MCR on SER12. Prefer PATH/`build*/bin` (stale `stacks/terminal/max25-terminal` may lack `-d`). For ~3s visible PTT use KISS inject ≥~376B info (unix `SEND` is capped by max25d `MAX_PAYLOAD=256` ≈2.2s).

## Live — classic TNC

Start **max25d** with a TNC device (`tnc2c` / `pktnc2`) so `/run/max25/modem.sock` (or `/tmp/max25/modem.sock`) exists.

```bash
# RX readiness (CONNECT + STATUS) — no SEND
./scripts/tx-rx-test.sh --device tnc --live

# One capped SEND (keys radio if PTT wired)
./scripts/tx-rx-test.sh --device tnc --live --tx
```

Override socket: `MAX25_SOCK=/run/max25/modem.sock`.

## Both classes

```bash
./scripts/tx-rx-test.sh --device all          # L0 offline
sudo ./scripts/tx-rx-test.sh --device all --live -c /etc/max25/max25-bcpr.ini
```

TNC live still needs a running max25d socket; modem live needs bcpr INI.

## What is in release / CI

| Gate | Runs |
|------|------|
| `scripts/tx-rx-test.sh` (L0) | Offline TX/RX for TNC + bcpr |
| CTest `max25_tx_rx_offline` | Same |
| Target `max25_tx_rx_test` | Same |
| `max25_test` | Depends on `max25_tx_rx_test` |
| `scripts/release-check.sh` | Invokes L0 tx-rx-test |
| GitHub CI | `max25_test` + `release-check.sh` |

**Not** in CI: `--live` / `--tx` (hardware / RF).

## Related

| Doc | Role |
|-----|------|
| [BAYCOM.md](BAYCOM.md) | BayCom/based bring-up |
| [BAYCOM-FREEZES.md](BAYCOM-FREEZES.md) | Freeze warning |
| [HARDWARE-ACCEPTANCE.md](HARDWARE-ACCEPTANCE.md) | Manual RF matrix |
| [`stacks/max25-bcpr/README.md`](../stacks/max25-bcpr/README.md) | bcpr smoke L0–L4 |
| [`stacks/tncs/docs/TNC-RECOVERY.md`](../stacks/tncs/docs/TNC-RECOVERY.md) | TNC recovery |
