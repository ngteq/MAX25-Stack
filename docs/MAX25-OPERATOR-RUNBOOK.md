# MAX25-Stack operator runbook — v1.0.0

**Product:** MAX25-Stack-v1.0.0 · One path from build to on-air (or bench).

---

## 1. Host preparation

| Step | Action |
|------|--------|
| OS | Linux with ALSA, serial permissions (`dialout`) |
| Optional | `ax25-apps` for BayCom `listen`/`call` |
| Docs | [LINUX-HOST-SETUP.md](LINUX-HOST-SETUP.md) |

```bash
git clone <repo> MAX25-Stack && cd MAX25-Stack
./scripts/build.sh
sudo cmake --install build --prefix /usr/local   # or user prefix
```

---

## 2. Site configuration

| File | Purpose |
|------|---------|
| `~/.config/max25/max25d.ini` | Devices, TCP, auth |
| `share/max25/max25d.ini.example` | Template |
| `share/hybbx/*.ini.example` | HyBBX attach (optional) |

```ini
[devices]
tnc2c = serial:/dev/ttyUSB0
; soft-crdop = crdop:default
```

Copy examples from `share/max25/`, `share/crdop/`, `share/baycom/`.

---

## 3. Start stack (standalone)

```bash
# TNC
max25-ctl start --hardware tncs --device tnc2c

# BayCom kernel modem
max25-ctl start --hardware modems --device baycom-ser12

# CRDOP soft modem
max25-ctl start --hardware soft-modems --device soft-crdop
# or launcher: crdop   # starts audio-dummyd / native path
```

Verify: `max25-ctl status` · logs · `discover-plugins.sh --json`

---

## 4. Operator terminal

```bash
max25-terminal
# SET DEVICE tnc2c
# CONNECT
# SEND <callsign> <text>
```

Protocol: M25/1 — [MAX25-TERMINAL.md](MAX25-TERMINAL.md), [include/max25/protocol.md](../include/max25/protocol.md).

---

## 5. HyBBX attach (optional)

MAX25 must run **first** (boot-wait, KISS PTY, serial ownership).

1. Start `max25d` with desired devices.
2. Merge `share/hybbx/crdop-host.ini.example` or TNC examples.
3. Start HyBBX with `kiss_entry=none`, `[max25] check=yes`.

Boundary: [HYBBX.md](HYBBX.md) · vault `max25-hybbx-boundary-final.md`.

---

## 6. CRDOP bench (no RF)

```bash
python3 stacks/crdop/tools/max25-signal-sniffer.py --loopback
python3 stacks/crdop/tools/audio-dummyd.py --ctrl-port 8515 --data-port 8516
```

Full matrix: [stacks/crdop/docs/ACOUSTIC-TEST-PROTOCOL.md](../stacks/crdop/docs/ACOUSTIC-TEST-PROTOCOL.md).

---

## 7. Verification

```bash
./scripts/release-check.sh    # offline CI
```

Hardware: [HARDWARE-ACCEPTANCE.md](HARDWARE-ACCEPTANCE.md).

---

## 8. Troubleshooting

| Issue | Doc |
|-------|-----|
| Serial busy | Stop minicom; one owner — max25d **or** HyBBX |
| TNC silent | `tnc2c-host-reset.sh`, recovery ladder |
| CRDOP TCP fail | Ports 8515/8516; `crdopc` running |
| No AX.25 parse | [AX25-NATIVE-CODEC.md](AX25-NATIVE-CODEC.md) |

---

## Document map

| Role | Entry |
|------|-------|
| All CRDOP | [stacks/crdop/docs/INDEX.md](../stacks/crdop/docs/INDEX.md) |
| Devices | [PLUGINS-DEVICE-MODEL.md](PLUGINS-DEVICE-MODEL.md) |
| v1 scope | [V1.0.0-SCOPE.md](V1.0.0-SCOPE.md) |
| AI agents | [AGENTS.md](../AGENTS.md) |
