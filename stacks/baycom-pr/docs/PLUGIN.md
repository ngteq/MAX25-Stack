# HyBBX and external software

BayCom PR-Stack is a **modem and link layer** for BayCom-compatible hardware. It does **not** include a BBS, mailbox, or full-screen terminal UI.

The stack was developed **primarily for HyBBX** (attach via plugin). It fully supports **standard terminal AX.25 clients** for calling, being called, monitoring, and usual CB and amateur packet operations — see [CONNECTS.md](CONNECTS.md).

---

## What the stack provides

| Attachment | Path / name | Used by |
|------------|-------------|---------|
| KISS (single modem) | `/var/run/baycom-pr/kiss` | HyBBX plugin, picocom, custom clients |
| KISS (service dual) | `/var/run/baycom-pr/kiss-a`, `kiss-b` | HyBBX multi-port, automation |
| Kernel interface | `bcsf0` … `bcsf3` (ser12), `bcp0` … (par96) | Internal; apps use AX.25 port names |
| AX.25 port name | `ax25_port` in INI → `axports` | `listen`, `call`, HyBBX |
| Station ID | `callsign` in INI | Must match `axports` |

Lifecycle:

```bash
sudo baycom-pr-ctl preflight
sudo baycom-pr-ctl start    # up: driver + KISS bridge + PTY
sudo baycom-pr-ctl status   # verify
sudo baycom-pr-ctl stop     # clean shutdown
```

After crash or wrong IRQ: `sudo baycom-pr-ctl recover`.

---

## HyBBX plugin contract

HyBBX (external project) connects to a **running** stack. Expected integration points:

### Single modem (default)

| Setting | Typical value |
|---------|----------------|
| KISS device | `/var/run/baycom-pr/kiss` (PTY symlink) |
| AX.25 port | Value of `ax25_port` in INI (e.g. `cb0`, `radio`) |
| Callsign | Value of `callsign` in INI |
| Speed | 1200 bd (ser12/CB/HAM VHF) or 9600 (par96) |

INI example:

```ini
[modem.a]
kiss_link = /var/run/baycom-pr/kiss
ax25_port = radio
callsign = N0CALL-0
```

HyBBX should:

1. Wait until `baycom-pr-ctl status` shows kiss bridge **running**.
2. Open KISS on `kiss_link` **or** use kernel AX.25 via `ax25_port` (HyBBX design-dependent).
3. Not open raw `/dev/ttyS*` while `baycom_ser_fdx` is loaded.

### Service mode (dual modem)

For continuous operation with two radios — template `config/examples/baycom-pr.dual.ini`:

| Modem | KISS | AX.25 port | Iface |
|-------|------|------------|-------|
| a | `/var/run/baycom-pr/kiss-a` | `cb0` | `bcsf0` |
| b | `/var/run/baycom-pr/kiss-b` | `cb1` | `bcsf1` |

Requires unique IRQ per UART, staged start, and stable power — [GUIDE §11](GUIDE.md#11-service-mode-dual-modem).

HyBBX multi-port plugins map one logical channel per KISS path (or per `ax25_port`).

---

## Terminal clients (no HyBBX)

Any AX.25 tool that uses `/etc/ax25/axports` works when the stack is up (`baycom-pr-ctl axports apply` on start):

```bash
baycom-pr-ctl listen radio
baycom-pr-ctl call radio DEST
```

Optional raw inspection:

```bash
baycom-pr-ctl minicom a              # KISS, stack must be up
picocom -b 9600 /var/run/baycom-pr/kiss
```

Full examples: [CONNECTS.md](CONNECTS.md).

---

## Configuration files

| File | Role |
|------|------|
| `/etc/baycom/baycom-pr.ini` | Site profile — **callsign**, ports, devices |
| `/etc/baycom/modems.ini` | Hardware catalog (read-only for plugins) |
| `/etc/baycom/axports/axports` | AX.25 port table for `listen`/`call` |
| `/var/run/baycom-pr/active.env` | Last running profile (recover) |

Plugins should **read** INI or use documented paths — not hardcode `ttyS0`.

---

## Operational modes

| Mode | Modems | Typical use |
|------|--------|-------------|
| **Standard** | 1 | Operator, terminal connects, single HyBBX instance |
| **Service** | 2 | HyBBX/BBS/digipeater, 24/7, dual template |

Standard mode is the default for modem owners. Service mode is documented in [GUIDE §11](GUIDE.md#11-service-mode-dual-modem).

---

## What is not in this repository

- HyBBX application or plugin source
- BBS, mailbox, or chat UI

---

## See also

- [CONNECTS.md](CONNECTS.md) — `listen` / `call` examples
- [REFERENCE.md](REFERENCE.md) — INI schema
- [GETTING-STARTED.md](GETTING-STARTED.md) — first install
