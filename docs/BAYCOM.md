# BayCom (kernel modems)

**MAX25** operator guide for kernel-driven SER12 and PAR96 modems (PC-COM, BayPac, LPT 9600). Stack implementation: [`stacks/baycom-pr/`](../stacks/baycom-pr/). Kernel deep dives: [`stacks/baycom-pr/docs/`](../stacks/baycom-pr/docs/INDEX.md) — do not duplicate here.

[README](../README.md) · [PACKET-RADIO.md](PACKET-RADIO.md) · [HYBBX.md](HYBBX.md) · [LINUX-EDGE-SETUP.md](LINUX-EDGE-SETUP.md)

---

## Role in MAX25

```
Radio ←→ UART (8250/16550)
           ↓
    baycom-pr-ctl start          (kernel module, KISS PTY)
           ↓
    /var/run/baycom-pr/kiss      (KISS PTY)
           ↓
    max25d BayComKissBackend     (M25/1 routing)
           ↓
    max25-terminal  ·  HyBBX baycom plugin
```

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| Hardware prep | `baycom-pr-ctl` | Load kernel module, release UART, KISS PTY, AX.25 netdev |
| Device plugin | `baycom-ser12`, `baycom-par96`, `baycom-kiss` | Discovery metadata, HyBBX contract |
| Daemon | `max25d` `BayComKissBackend` | Attach KISS PTY, M25/1 routing |
| BBS (optional) | HyBBX `baycom` plugin | Kernel netdev or KISS after prep |

**One owner per UART** — never run a userspace serial client, HyBBX `packet_radio`, and `baycom_ser_fdx` on the same `/dev/tty*` concurrently.

---

## Operating modes (single default, dual opt-in)

| Mode | Who | INI |
|------|-----|-----|
| **Single (default)** | One modem; AX25SRV and most sites | `share/baycom/baycom-pr.pccom-ttyS0-only.ini.example` → `/etc/baycom/baycom-pr.ini` |
| **Dual (service)** | Two kernel-ser12 modems worldwide (HyBBX, digipeater, 24/7) | `stacks/baycom-pr/config/examples/baycom-pr.dual.ini` — unique IRQ per UART |

**AX25SRV** has one PC-COM on `/dev/ttyS0` only — no second BayCom UART. Dual BayCom is **opt-in** for operators with two modems; it is not the default install path.

Without override, `max25-ctl` and `install-max25.sh` use the **single** template. Dual `/etc/baycom/baycom-pr.ini` is skipped unless you pass `--baycom-ini` or `--baycom-profile dual`.

---

## BayCom vs TNCs

| Aspect | TNC (`tnc2c`) | BayCom (`baycom-ser12`) |
|--------|---------------|-------------------------|
| Site config | `*serial.env` | `baycom-pr.ini` |
| Stack start | boot-wait (no root) | `baycom-pr-ctl` (**root**) |
| max25d link | direct serial KISS | KISS PTY from kernel |
| Client YAML | `share/clients/tnc2c.yaml` | `share/clients/baycom-ser12.yaml` (reference) |
| Terminal flow | `SET DEVICE` → `CONNECT` → `SEND` | **identical** |

Unified five-step workflow: [PLUGINS-DEVICE-MODEL.md](PLUGINS-DEVICE-MODEL.md).

| Use BayCom when | Use TNC (`hardware/tncs`) when |
|-----------------|--------------------------------|
| Bit-banged UART modem (PC-COM, AE8000 internal, BayPac SER12) | Dedicated TNC firmware (TNC2C, PK-TNC2, PK-232) |
| Real 8250/16550 UART (`/dev/ttyS*`) | USB/async serial KISS (`/dev/ttyUSB*`) |
| Linux kernel `baycom_ser_fdx` path | Boot-wait + command-mode KISS entry |

| Do **not** use kernel BayCom for | Alternative |
|----------------------------------|-------------|
| Async USB serial | `baycom-kiss` device or `hardware/tncs` |
| LPT without `CONFIG_BAYCOM_PAR` | `baycom-par96` only when kernel built with parport |

---

## Canonical start path (single PC-COM)

**Default for v1 and AX25SRV:** one kernel-ser12 modem on `/dev/ttyS0`. There is **no second PC-COM** on this station — `/dev/ttyS5` is PK-TNC2 (HyBBX). Dual-modem BayCom is **service-mode only** on other hosts.

### 1. Build and install

```bash
./scripts/build.sh
sudo ./scripts/install-max25.sh          # or: sudo make -C stacks/baycom-pr install
```

### 2. Site BayCom INI (once per site, root)

Copy the shipped single-modem template — adjust callsign, verify UART:

```bash
sudo cp share/baycom/baycom-pr.pccom-ttyS0-only.ini.example /etc/baycom/baycom-pr.ini
/sbin/setserial -g /dev/ttyS0    # must match iobase/irq in INI
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini setup      # first time: probe iobase/irq
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini preflight
```

KISS PTY after start: `/var/run/baycom-pr/kiss` · netdev: `bcsf0`

### 3. Start via MAX25 (every boot)

**Option A — umbrella ctl (manual or scripting):**

```bash
./scripts/max25-ctl start --hardware modems --device baycom-ser12
```

**Default INI:** `max25-ctl` resolves the **single-modem** template (`share/baycom/baycom-pr.pccom-ttyS0-only.ini.example`, or the installed copy under `/usr/local/share/max25/baycom/`). It **skips** a dual-modem `/etc/baycom/baycom-pr.ini` unless you pass `--baycom-ini PATH` or `--baycom-profile dual`. Override with site `local/baycom-pr.ini`.

**Option B — max25d supervisor (recommended for production):**

```ini
[devices]
baycom-ser12 = baycom:a

[device.baycom-ser12]
kiss_link = /var/run/baycom-pr/kiss
modem = a
baycom_ini = /etc/baycom/baycom-pr.ini

[stack]
auto_start = yes
```

```bash
sudo cp share/max25/max25d.ini.edge.example /etc/max25/max25d.ini
# Uncomment BayCom [devices] block; set hardware=modems device=baycom-ser12
sudo max25d -c /etc/max25/max25d.ini
max25-terminal -U /run/max25/modem.sock
```

`max25d` passes `baycom_ini` to `max25-ctl` → `baycom-pr-ctl -c` on auto_start.

Set `auto_start = no` only when an external site wrapper runs `baycom-pr-ctl` before `max25d`.

### 4. Shutdown / recovery

```bash
sudo baycom-pr-ctl stop
# after crash:
sudo baycom-pr-ctl recover
sudo stacks/baycom-pr/scripts/check-freeze.sh
sudo baycom-pr-ctl preflight && sudo baycom-pr-ctl start
```

---

## Configuration files

| Location | Purpose |
|----------|---------|
| `share/baycom/` | Shipped MAX25 examples (single PC-COM on ttyS0) |
| `local/` | Site overrides — **gitignored**, not committed |
| `/etc/baycom/baycom-pr.ini` | Installed system INI (from example or `make install`) |
| `/etc/baycom/modems.ini` | Modem catalog (`albrecht-pc-com`, …) |
| `stacks/baycom-pr/config/examples/` | CB, HAM, dual, LPT profiles — link only |
| `share/max25/max25d*.ini.example` | Daemon multi-device templates (incl. `max25d.dual-baycom.ini.example`) |
| `share/hybbx/baycom-ser12-edge.ini.example` | HyBBX merge snippet |

**Workflow:** edit under `local/` or `/etc/`, never commit site callsigns or IRQ values. Verify live UART:

```bash
/sbin/setserial -g /dev/ttyS0
```

Minimal `[modem.a]` block:

```ini
catalog = albrecht-pc-com
serial = /dev/ttyS0
iface = bcsf0
kiss_link = /var/run/baycom-pr/kiss
callsign = YOURCALL-0
txdelay = 35
iobase = 0x3f8
irq = 4
```

---

## Commands

| Tool | Command | Notes |
|------|---------|-------|
| `max25-ctl` | `start --hardware modems --device baycom-ser12` | Single-modem default (root) |
| `max25-ctl` | `start … --baycom-ini PATH` or `--baycom-profile dual` | Explicit dual INI |
| `max25-ctl` | `stop` / `status` | BayCom teardown / health |
| `baycom-pr-ctl` | `probe` · `setup` · `preflight` · `start` · `check` · `status` · `stop` · `recover` · `doctor` | Always root for module load |
| `max25d` | `sudo max25d -c /etc/max25/max25d.ini` | Attach after KISS PTY exists |
| `max25-terminal` | `-U /run/max25/modem.sock` or TCP `:7325` | `SET DEVICE baycom-ser12` (or `baycom-a` / `baycom-b` in dual) |
| Client profile | `share/clients/baycom-ser12.yaml` | Operator reference — connection + config pointers |
| `baycom_test` | `-i bcsf0 -s /dev/ttyS0 quick` | Per-modem test (driver loaded) |

M25/1: `SET DEVICE baycom-ser12`, `RX device=baycom-ser12 …`. Dual: `baycom-a` / `baycom-b` — see [§ Dual modem](#dual-modem-service-mode). Full station: `share/max25/max25d.full-station.ini.example`.

---

## RX / TX / PTT (max25d)

Kernel BayCom does **not** expose a separate M25/1 PTT command. PTT is handled inside `baycom_ser_fdx` / `baycom_par` when the KISS bridge accepts a DATA frame for transmit.

| Direction | Path | max25d role |
|-----------|------|-------------|
| **TX** | `SEND` → M25/1 → `BayComKissBackend.transmit` → KISS DATA on `/var/run/baycom-pr/kiss` → `baycom_kissbridge` → kernel netdev → UART RTS (PTT) → RF | Build AX.25 UI frame, write KISS; requires `CONNECT` |
| **RX** | RF → kernel → KISS bridge → PTY → `BayComKissBackend._rx_loop` → `RX device=baycom-ser12 …` broadcast | Poll PTY continuously; no `CONNECT` required for monitor |
| **PTT** | Kernel driver | Verify with `baycom_test calibrate` (see below); **not** in max25d or HyBBX |

**Operator flow (max25-terminal):**

```text
SET DEVICE baycom-ser12
CONNECT                    # opens KISS PTY, marks session ready for TX
SEND hello                 # → KISS → RF (PTT automatic)
                           # ← RX device=baycom-ser12 [AX25 UI …] on receive
DISCONNECT
```

**HyBBX boundary:** HyBBX `baycom` plugin attaches to kernel netdev (`bcsf0`) or the same KISS PTY **after** `baycom-pr-ctl start`. It does not drive PTT separately on the kernel path. MAX25 owns modem prep and KISS attach; HyBBX owns BBS/session logic.

**PTT verification (hardware, root):**

```bash
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini start
sudo baycom_test -i bcsf0 -s /dev/ttyS0 calibrate 2   # expect during_ptt=1
sudo baycom_test -i bcsf0 -s /dev/ttyS0 quick          # IRQ delta > 0
```

For end-to-end TX via max25d: stack up → `max25d` with `baycom-ser12` → terminal `CONNECT` + `SEND` → monitor RF or second station.

`max25d` retries KISS PTY attach when the link appears after `baycom-pr-ctl start` (no manual restart needed if the PTY was briefly missing).

---

## Dual modem (service mode)

**Worldwide / general use:** two independent kernel-ser12 modems on **different UARTs** with **unique IRQs** is fully supported, documented, and tested. Use this for service mode (24/7), two radios, or HyBBX dual-transport sites — **not** on AX25SRV while TNCs own `ttyS4`/`ttyS5`.

### 1. BayCom INI (dual profile)

Template: `stacks/baycom-pr/config/examples/baycom-pr.dual.ini`

```bash
sudo cp stacks/baycom-pr/config/examples/baycom-pr.dual.ini /etc/baycom/baycom-pr.ini
sudo /sbin/setserial -g /dev/ttyS0 /dev/ttyS5    # verify iobase/irq match INI
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini setup
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini preflight
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini start
```

After start:

| Modem | UART | netdev | KISS PTY |
|-------|------|--------|----------|
| `modem.a` | `/dev/ttyS0` | `bcsf0` | `/var/run/baycom-pr/kiss-a` |
| `modem.b` | `/dev/ttyS5` | `bcsf1` | `/var/run/baycom-pr/kiss-b` |

Staged start and IRQ safeguards: [`stacks/baycom-pr/docs/GUIDE.md`](../stacks/baycom-pr/docs/GUIDE.md) §11.

### 2. Start via max25-ctl (explicit dual INI)

`max25-ctl` **skips** a dual-modem `/etc/baycom/baycom-pr.ini` by default (AX25SRV-safe). Pass `--baycom-ini` when you intend dual:

```bash
./scripts/max25-ctl start --hardware modems --device baycom-ser12 \
  --baycom-ini /etc/baycom/baycom-pr.ini
# or from checkout:
./scripts/max25-ctl start --hardware modems --device baycom-ser12 \
  --baycom-ini stacks/baycom-pr/config/examples/baycom-pr.dual.ini
```

Aliases `baycom-a` / `baycom-b` map to the same kernel stack start as `baycom-ser12`. Or use `--baycom-profile dual` to resolve the shipped dual template without a path.

### 3. max25d multi-device (two M25/1 device ids)

Template: `share/max25/max25d.dual-baycom.ini.example`

```ini
[devices]
default = baycom-a
baycom-a = baycom:a
baycom-b = baycom:b

[device.baycom-a]
kiss_link = /var/run/baycom-pr/kiss-a
modem = a
baycom_ini = /etc/baycom/baycom-pr.ini

[device.baycom-b]
kiss_link = /var/run/baycom-pr/kiss-b
modem = b
baycom_ini = /etc/baycom/baycom-pr.ini
```

`max25d` starts **one** `baycom-pr-ctl` for both devices (shared `baycom_ini`), attaches each backend to its KISS PTY, and routes RX/TX per device id.

| M25/1 command | Effect |
|---------------|--------|
| `GET DEVICES` | Lists `baycom-a`, `baycom-b` with `backend=baycom-kiss` |
| `SET DEVICE baycom-a` | Select radio A (kiss-a / bcsf0) |
| `SET DEVICE baycom-b` | Select radio B (kiss-b / bcsf1) |
| `RX device=baycom-a …` | RX from modem A only |
| `RX device=baycom-b …` | RX from modem B only |
| `CONNECT` + `SEND` | TX on **selected** device |

**max25-terminal:** connect to the daemon socket, then `SET DEVICE baycom-b` before `CONNECT` / `SEND` to operate the second radio.

### 4. HyBBX dual transport

Merge `share/hybbx/service-dual.ini.example` — two `[transport.baycomN]` sections (`bcsf0` + `bcsf1`), unique `link_id` per radio. Prerequisite: dual `baycom-pr.ini` running. See [HYBBX.md](HYBBX.md) § Dual radio.

---

## AX25SRV layout and freeze prevention

Kernel-ser12 bit-bangs UART lines under interrupt load. **Wrong IRQ or UART conflicts can hard-freeze the host.**

### Port assignment

| Port | Role on AX25SRV |
|------|-----------------|
| `/dev/ttyS0` | PC-COM (BayCom kernel-ser12) |
| `/dev/ttyS4` | TNC2C (`packet_radio`, boot-wait) |
| `/dev/ttyS5` | PK-TNC2 (`packet_radio`, boot-wait) |

**Never** run default dual BayCom (`ttyS0` + `ttyS5`) while TNCs own `ttyS4`/`ttyS5`. Use the single-modem INI:

```bash
sudo cp share/baycom/baycom-pr.pccom-ttyS0-only.ini.example /etc/baycom/baycom-pr.ini
./scripts/max25-ctl start --hardware modems --device baycom-ser12
```

### Freeze prevention checklist

| Step | Action |
|------|--------|
| 1 | `setserial -g` — INI `iobase`/`irq` must match live values |
| 2 | `baycom-pr-ctl preflight` — zero errors before `start` |
| 3 | Single modem first — stable hours/days before dual (service mode only) |
| 4 | Unique IRQ per UART — no duplicate IRQ on dual layouts |
| 5 | No userspace serial owner on raw UART while driver loaded |
| 6 | `baycom-pr-ctl stop` before reboot/shutdown |
| 7 | After crash: `recover` → `check-freeze.sh` → fix INI → single start |

| Safeguard | Tool |
|-----------|------|
| Config validation | `baycom_validate_config.py` |
| Preflight | `baycom_preflight.py` |
| Staged dual start | Per-UART probe before combined load |
| IRQ watch | Auto-stop ~80k IRQ/s (`BAYCOM_MAX_IRQ_PER_SEC`) |

Full analysis: [`stacks/baycom-pr/docs/archive/STABILITY.md`](../stacks/baycom-pr/docs/archive/STABILITY.md).

### Cold start with TNCs + HyBBX

1. TNC boot-wait on `ttyS4`/`ttyS5` — **not** on BayCom UART
2. `baycom-pr-ctl preflight` → `start` (single modem)
3. `max25d` with `baycom-ser12 = baycom:a`
4. HyBBX — merge snippet, `baycom=yes` after step 3

---

## USB-RS232 and power

Kernel-ser12 (`baycom_ser_fdx`) requires a **real 8250/16550 UART** — not `ttyUSB*`.

For **USB KISS** paths (`baycom-kiss`, `kiss-serial-usb`): use a **self-powered USB hub with PSU** when the modem/TNC is port-powered. Cheap adapters often lack line drive → garbled KISS, missing PTT, disconnects. Profile: `share/clients/kiss-serial-usb.yaml`.

---

## Device plugins

| Plugin id | Hardware | Backend | KISS path |
|-----------|----------|---------|-----------|
| `baycom-ser12` | PC-COM, BayPac UART | kernel `baycom_ser_fdx` | `/var/run/baycom-pr/kiss` |
| `baycom-par96` | LPT 9600 | kernel `baycom_par` | same pattern |
| `baycom-kiss` | USB async KISS | none (serial KISS) | `/dev/ttyUSB*` |

Registry: `plugins/manifest.yaml` · `./scripts/discover-plugins.sh`

---

## HyBBX

Merge `share/hybbx/baycom-ser12-edge.ini.example` into Secondary `hybbx.ini` — `backend=kernel`, `mode=ser12*`, `interface=bcsf0`, or KISS PTY. Details: [HYBBX.md](HYBBX.md) · [`stacks/baycom-pr/docs/PLUGIN.md`](../stacks/baycom-pr/docs/PLUGIN.md).

---

## Diagnostics

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| `must run as root` | Non-root shell | Use root for `baycom-pr-ctl` |
| `network interface missing` | Driver not loaded | `start`; `lsmod \| grep baycom` |
| IRQ delta 0 in `baycom_test quick` | Wrong IRQ / no RF | `setserial -g`, fix INI, `preflight` |
| Host freeze on start | Wrong IRQ (e.g. ttyS5 ≠ APIC 30) | Reboot, `recover`, single modem, fix INI |
| KISS attach fails | Stack not running | `status`; check `/var/run/baycom-pr/kiss` |
| Garbled RF | Wrong catalog / txdelay | Match `modems.ini` catalog entry |
| USB KISS flaky / no PTT | Under-powered USB | Active powered hub; see above |

```bash
sudo baycom-pr-ctl doctor
sudo baycom-pr-ctl status
watch -n1 'grep -E "ttyS|baycom" /proc/interrupts'
```

---

## Implementation status

| Item | Status |
|------|--------|
| `baycom-pr-ctl` lifecycle | **Mature** |
| Freeze safeguards | **Implemented** |
| `max25-ctl` → `baycom-pr-ctl -c` | **Wired** — single-modem INI by default; `--baycom-ini` / `--baycom-profile dual` for opt-in |
| `max25d` dual `baycom:a` + `baycom:b` | **Wired** — shared stack start, per-modem KISS PTY, SET DEVICE |
| `max25d` `BayComKissBackend` + `auto_start` | **Wired** — passes `baycom_ini` to stack start; KISS PTY RX/TX poll |
| M25/1 SEND → KISS → kernel PTT | **Wired** — no separate PTT command |
| KISS PTY RX → `RX device=…` | **Wired** — background `_rx_loop` |
| HyBBX `baycom` contract | **Documented** |
| Dual kernel-ser12 24/7 | **Service mode** — not used on AX25SRV (single PC-COM only) |

---

## See also

| Document | Content |
|----------|---------|
| [`stacks/baycom-pr/README.md`](../stacks/baycom-pr/README.md) | Stack overview |
| [`stacks/baycom-pr/docs/GUIDE.md`](../stacks/baycom-pr/docs/GUIDE.md) | Extended operator guide |
| [`stacks/baycom-pr/docs/PLUGIN.md`](../stacks/baycom-pr/docs/PLUGIN.md) | HyBBX integration contract |
| [`stacks/baycom-pr/docs/archive/STABILITY.md`](../stacks/baycom-pr/docs/archive/STABILITY.md) | Full freeze checklist |
| [PACKET-RADIO.md](PACKET-RADIO.md) | AX.25 / multi-device overview |
| [V1.0.0-SCOPE.md](V1.0.0-SCOPE.md) | v1 release scope |
