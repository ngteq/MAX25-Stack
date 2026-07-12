# UX, automation, and system protection — analysis

**Date:** 2026-07-08 · **Target release:** v0.6.0 (after hardware validation)

## Executive summary (DE)

Der Stack war technisch solide (preflight, recover, staged start), aber **zu viel manuelle INI-Arbeit** (`iobase`, `irq`, Katalog-Wahl). v0.6.0 fokussiert **Probe → Setup → Doctor → Start** als Standardpfad und **minimale INI** (nur `serial` + `catalog` für ser12).

---

## Inventory (before v0.6.0 UX work)

| Layer | Tool | Status |
|-------|------|--------|
| Config validate | `baycom_validate_config.py` | Schema, duplicates |
| Pre-start safety | `baycom_preflight.py` | IRQ/UART/lsof/parport |
| Post-start IRQ watch | `baycom-pr-ctl start` | Auto-stop on storm |
| Staged dual probe | `baycom-pr-ctl` | ser12 + par96 |
| Crash cleanup | `recover` | Unload + UART restore |
| Freeze report | `check-freeze.sh` | journal/dmesg |
| Self-test | `baycom-pr-selftest.sh` | End-to-end offline |

**Gaps identified:** no hardware scan, no auto INI fill, no unified health command, default INI required manual iobase/irq, install-root started blindly.

---

## Pain points (operators)

1. **Must know setserial output** before first start
2. **Dual PC-COM:** IRQ 30 vs IRQ 3 confusion — easy host freeze
3. **No discovery** of USB KISS vs ser12 path
4. **Error messages** scattered across validate/preflight/start
5. **install-root.sh** started without preflight

---

## Implemented (v0.6.0 prep)

| Feature | Command / file |
|---------|----------------|
| Hardware probe | `baycom-pr-ctl probe` → `tools/baycom_probe.py` |
| Auto INI fill | `baycom-pr-ctl setup` (backup `.bak`) |
| Unified health | `baycom-pr-ctl doctor` → `tools/baycom_doctor.py` |
| Minimal default INI | `config/baycom-pr.ini` — optional iobase/irq |
| Safe install | `install-root.sh` — setup + preflight before start |
| Operator guide | `docs/AUTOMATION.md` |

---

## Prioritized backlog

### P0 (done in tree)

- [x] `probe` / `setup` / `doctor`
- [x] Minimal ser12 INI
- [x] Preflight gate on install-root

### P1 (next)

- [ ] `doctor --json` for scripting/monitoring
- [ ] udev rule template: USB KISS hotplug → `kiss-serial` bridge restart
- [ ] Optional systemd unit + `ExecStartPre=preflight`
- [ ] AX.25 axports auto-merge helper (today: manual snippet copy)

### P2 (later)

- [ ] Interactive TUI wizard (`baycom-pr-ctl wizard`)
- [ ] Kernel IRQ-rate patch (see `kernel/BAYCOM-DRIVER-ANALYSIS.md`)
- [ ] Telemetry export (Prometheus/node_exporter textfile)

---

## Auto vs manual

| Auto-detectable | Must stay manual |
|-----------------|------------------|
| UART iobase/irq via setserial | Callsign, txdelay tuning |
| USB device path (if single) | Radio wiring, squelch |
| LPT iobase in /proc/ioports | AX.25 routing policy |
| Kernel module presence | On-air RF test |
| Duplicate IRQ/iobase conflicts | Dual-modem ordering when unstable |

---

## Recommended operator flow

```
install → probe → setup → doctor → preflight → start → selftest
```

After freeze: `recover → check-freeze.sh → doctor → start`
