<!-- AUTO-SYNC 2026-07-15 — vault: projects/max25-stack/2026-07-13-master-documentation.md -->
<!-- Re-sync: /home/akb/Code/0-RESEARCHES/tools/vault-sync-slave-docs.sh -->

# MAX25-Stack — Master operator guide

**Shipped guide** — canonical edits in research vault `projects/max25-stack/2026-07-13-master-documentation.md`; run sync script after change.

## Summary

Single linear guide: MAX25 layer model, `max25d`, devices (TNC, BayCom, CRDOP), M25/1 protocol, TNC recovery, FreeBSD split, HyBBX boundary. Shipped docs in `docs/` and `stacks/tncs/docs/` remain **frozen reference**.

---

## 1. What MAX25 is

**Main AX.25 Stack (MAX25)** — standalone packet-radio stack with HyBBX-compatible plugin boundaries. Owns RF prep (boot-wait, KISS entry, BayCom kernel lifecycle, CRDOP audio). HyBBX consumes prepared devices via transport plugins.

```
max25-terminal / max25-client  (F10 menu, M25/1)
         │
max25d — Main + Secondaries (:7325 M25/1)
         │
HyBBX (external) — packet_radio | baycom | crdop
         │
Hardware — tnc2c | baycom-ser12 | soft-crdop
```

Frozen: `docs/ARCHITECTURE.md`, `docs/README.md`.

---

## 2. Host layout — Main + Secondaries

| Role | Count | Function |
|------|-------|----------|
| **Main** | 1× | Stack hub, HyBBX attach point, M25/1 `:7325` |
| **Secondary** | 0–5+ | Additional `max25d` instances — one RF backend each |

**Linux rules (when netdev ships):**

| Item | Name |
|------|------|
| TUN interface | **`max25d0`** only |
| BayCom kernel netdev | **`bcsf0`** unchanged |

**Example split:** FreeBSD Main (CRDOP/TCP/IP hub) + Linux Secondary (TNC/BayCom). Not mandatory — single Linux host is the primary v1 layout.

Vault matrix: [2026-07-13-max25-freebsd-tnc-baycom-full-feature-matrix.md](2026-07-13-max25-freebsd-tnc-baycom-full-feature-matrix.md).

---

## 3. Install and site configuration

```bash
git clone <repo> MAX25-Stack && cd MAX25-Stack
./scripts/build.sh
sudo cmake --install build --prefix /usr/local   # or user prefix
```

| File | Purpose |
|------|---------|
| `~/.config/max25/max25d.ini` | Devices, TCP, auth, serial watch |
| `share/max25/max25d.ini.example` | Template |
| `share/hybbx/*-host.ini.example` | HyBBX attach fragments |

```ini
[devices]
tnc2c = serial:/dev/ttyUSB0
; soft-crdop = crdop:default
```

Frozen runbook: `docs/MAX25-OPERATOR-RUNBOOK.md`, `docs/LINUX-HOST-SETUP.md`.

---

## 4. Start stack — by device type

### TNC (tnc2c, pktnc2)

```bash
max25-ctl start --hardware tncs --device tnc2c
# or: stacks/tncs/tnc2c-boot-wait.sh
```

Boot-wait: DTR+RTS high during power-on (Landolt TNC2C). Software recovery ladder before power cycle.

### BayCom (kernel SER12)

```bash
sudo cp share/baycom/baycom-pr.pccom-ttyS0-only.ini.example /etc/baycom/baycom-pr.ini
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini setup
max25-ctl start --hardware modems --device baycom-ser12
```

v1: `sudo` for kernel module. v2 target: rootless daily operation.

### CRDOP (soft modem)

```bash
max25-ctl start --hardware soft-modems --device soft-crdop
# TCP 8515 (control) / 8516 (data)
```

Vault dev master: [2026-07-13-crdop-development-master.md](2026-07-13-crdop-development-master.md).

Verify: `max25-ctl status` · `ss -ltn | grep 7325`.

---

## 5. M25/1 and operator terminal

| Item | Value |
|------|-------|
| Protocol | M25/1 text commands on TCP `:7325` |
| Client | `max25-terminal` — `SET DEVICE`, `CONNECT`, `SEND` |
| Codec | In-tree `ax25_codec.py` — no kernel AX.25 required |

Frozen: `docs/MAX25-TERMINAL.md`, `include/max25/protocol.md`.

---

## 6. TNC recovery (software-first)

Power cycle is **rescue fallback** only when DTR was low at cold boot or hardware hang.

| Situation | First action |
|-----------|--------------|
| Echo-only (`INFO` → `INFO`) | `tnc2c-host-reset.sh` or max25d serial watch |
| After prep `error-host` | Auto boot-wait escalate (if enabled) |
| Cold boot, no `cmd:` | `tnc2c-boot-wait.sh` with DTR before power-on |

**Software ladder** (TheFirmware TF 2.7): KISS return → JHOST 0 → ESC V → ESC QRES → ESC `@K` → MYCALL.

| Layer | Responsibility |
|-------|----------------|
| `max25d` / boot-wait | DTR, recovery, `kiss on`, serial watch |
| HyBBX `packet_radio` | Attach only — `kiss_entry=none` |

Vault SSoT: [2026-07-13-thefirmware-native-recovery-sequence.md](2026-07-13-thefirmware-native-recovery-sequence.md) · [hardware/tnc2c/2026-07-13-kiss-host-without-power-cycle.md](../../hardware/tnc2c/2026-07-13-kiss-host-without-power-cycle.md).

max25d INI defaults: `serial_watch=yes`, `stack_recover_only=yes`, `serial_bootwait_escalate=yes`.

Known failure mode (power-cycle still required): [2026-07-13-max25d-tnc-recovery-power-cycle-root-cause.md](2026-07-13-max25d-tnc-recovery-power-cycle-root-cause.md).

Frozen: `MAX25-Stack/stacks/tncs/docs/TNC-RECOVERY.md`.

---

## 7. BayCom ↔ max25d

```
Radio ← UART ← baycom-pr-ctl (kernel) ← KISS PTY ← max25d BayComKissBackend ← M25/1 / HyBBX
```

| Use BayCom when | Use TNC when |
|-----------------|--------------|
| PC-COM / SER12 on real 8250 UART | TNC2C, PK-TNC2, USB serial KISS |
| Linux `baycom_ser_fdx` path | Boot-wait + firmware KISS |

Alias compatibility: [2026-07-13-baycom-max25d-alias-compatibility.md](2026-07-13-baycom-max25d-alias-compatibility.md).

Frozen: `docs/BAYCOM.md`.

---

## 8. CRDOP

MAX25-SoftModem (`soft-crdop`) — acoustic AX.25 over soundcard. FreeBSD uses OSS; Linux uses ALSA.

| Host | CRDOP role |
|------|------------|
| Linux | RF backend in `max25d` |
| FreeBSD | Primary softmodem path (no kernel BayCom/TNC in stack defaults) |

Frozen: `docs/CRDOP.md`, `stacks/crdop/docs/`.

---

## 9. FreeBSD and platform split

| Component | Linux | FreeBSD |
|-----------|-------|---------|
| `max25d` + RF (TNC/BayCom) | ✅ | ❌ (daemon Linux-first in v1) |
| `max25-terminal` | ✅ | ✅ (remote to Linux `:7325`) |
| CRDOP standalone / OSS | ALSA | OSS (DEV-Level 1 port) |
| Kernel BayCom `bcsf0` | ✅ | ❌ |

No native FreeBSD kernel AX.25 — userspace KISS/M25/1 only. Vault: [2026-07-13-max25-freebsd-tnc-baycom-full-feature-matrix.md](2026-07-13-max25-freebsd-tnc-baycom-full-feature-matrix.md).

Frozen: `docs/FREEBSD-AX25.md`, `docs/PLATFORMS.md`.

---

## 10. HyBBX boundary

**MAX25 before HyBBX.** One serial owner per port.

| MAX25 owns | HyBBX owns |
|------------|------------|
| Boot-wait, MYCALL, `kiss on`, BayCom kernel, CRDOPC | `[max25] check`, KISS attach, AX.25 UI, HBX, broadcast |

```bash
max25-ctl start --hardware tncs --device tnc2c   # 1
ss -ltn | grep 7325                               # 2
hybbxd -c hybbx.ini                               # 3 — kiss_entry=none
```

Vault: [../integration/2026-07-12-max25-hybbx-boundary-final.md](../integration/2026-07-12-max25-hybbx-boundary-final.md).

Frozen: `docs/HYBBX.md`, `docs/PACKET-RADIO.md`.

---

## 11. Virtual netdev (planned)

TUN **`max25d0`** — IPv4 `127.0.0.25/8`, IPv6 `::25/128`. DEV-Level 1 scaffold; `[netdev] enabled=no` default.

Vault analysis: [2026-07-13-max25-tcpip-virtual-netdev-hbx-analysis.md](2026-07-13-max25-tcpip-virtual-netdev-hbx-analysis.md).

Frozen: `docs/NETDEV.md`.

---

## 12. Troubleshooting

| Symptom | Check |
|---------|-------|
| Serial busy | One owner — stop minicom; max25d **or** HyBBX |
| TNC silent / echo-only | Recovery ladder; DTR at boot |
| max25d unreachable | HyBBX skips local TNC when `[max25] check=yes` |
| BayCom no KISS PTY | `baycom-pr-ctl status`; module loaded |
| CRDOP TCP fail | Ports 8515/8516; `crdopc` running |

Release audit: [2026-07-12-max25-v1.0.0-release-audit.md](2026-07-12-max25-v1.0.0-release-audit.md).

---

## Related

| Topic | Path |
|-------|------|
| FreeBSD + feature matrix SSoT | [2026-07-13-max25-freebsd-tnc-baycom-full-feature-matrix.md](2026-07-13-max25-freebsd-tnc-baycom-full-feature-matrix.md) |
| TF native recovery SSoT | [2026-07-13-thefirmware-native-recovery-sequence.md](2026-07-13-thefirmware-native-recovery-sequence.md) |
| max25d power-cycle root cause | [2026-07-13-max25d-tnc-recovery-power-cycle-root-cause.md](2026-07-13-max25d-tnc-recovery-power-cycle-root-cause.md) |
| CRDOP development | [2026-07-13-crdop-development-master.md](2026-07-13-crdop-development-master.md) |
| HyBBX integration guide | [../hybbx/2026-07-13-master-documentation.md](../hybbx/2026-07-13-master-documentation.md) |
| Dual-TNC operator flow | [../integration/2026-07-13-master-operator-guide.md](../integration/2026-07-13-master-operator-guide.md) |
| TNC2multi integration | [2026-07-14-tnc2multi-max25-integration.md](2026-07-14-tnc2multi-max25-integration.md) |
| Linux kernel AX.25 ecosystem gap | [reference/2026-07-13-linux-kernel-ax25-ecosystem-gap.md](../../reference/2026-07-13-linux-kernel-ax25-ecosystem-gap.md) |
| Frozen product docs | `docs/`, `stacks/tncs/docs/` |
