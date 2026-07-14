# MAX25 virtual network device (`max25d0`)

**Status: DEV-Level 1** (*ca.*) — TUN/TAP sidecar bridges Linux TCP/IP to `max25d` M25/1 and the active RF device. Research: private vault `projects/max25-stack/2026-07-13-max25-tcpip-virtual-netdev-hbx-analysis.md` (not in this repo).

Goal: **Linux host ↔ MAX25-Stack ↔ TCP/IP clients** — IPv4 and IPv6 on TUN **`max25d0`**, same RF backend as the owning `max25d` instance.

> **Host layout:** one **Main** `max25d` plus optional **Secondaries** on a single server — see [ARCHITECTURE.md](ARCHITECTURE.md#host-layout--main--secondaries).

```
TCP/IP apps ──► TUN max25d0 ──► max25-tun (planned) ──► max25d M25/1 ──► modem/TNC
```

M25/1 text clients (`max25-terminal`, third-party GUI on `:7325`) remain independent of the TUN path.

**Naming:** the **daemon** is `max25d`; the **Linux kernel interface** when up is always **`max25d0`** (`ip link`, `ifconfig`) — no other name.

---

## Interface name (fixed)

| Item | Value |
|------|--------|
| **Kernel name** | **`max25d0`** — not `max25d`, not configurable |
| **Visible in** | `ip link show`, `ifconfig max25d0` |
| **Type** | TUN (IP packets); TAP optional later |

```bash
ip -br link show max25d0
# max25d0@NONE: <NOARP,UP,LOWER_UP> … tun
```

---

## Standard addresses (defaults)

Factory defaults when `[netdev]` is enabled. Override addresses in `max25d.ini`; interface name stays **`max25d0`**.

| Stack | Default | CIDR | Legacy netmask |
|-------|---------|------|----------------|
| **IPv4** | `127.0.0.25` | `127.0.0.25/8` | `255.0.0.0` |
| **IPv6** | `::25` | `::25/128` | host route |

### Operator setup (after `max25-tun` ships)

```bash
ip link set max25d0 up
ip addr add 127.0.0.25/8 dev max25d0
ip -6 addr add ::25/128 dev max25d0
```

Ping test (local, when bridge is active):

```bash
ping -c1 127.0.0.25
ping -6 -c1 ::25
```

---

## Configuration — `[netdev]` in `max25d.ini`

See `share/max25/max25d.ini.example` and `share/max25/max25d.netdev.ini.example`.

```ini
[netdev]
enabled = no
; interface is always max25d0 — do not change
mode = tun
ipv4 = 127.0.0.25/8
ipv6 = ::25/128
; extra_ipv4 = 10.73.25.1/24
; extra_ipv6 = fd25::1/64
encap = ax25-ui
m25_unix = /run/max25/modem.sock
```

| Key | Default | Meaning |
|-----|---------|---------|
| `enabled` | `no` | Start TUN bridge with stack |
| `interface` | **`max25d0`** | Fixed Linux netdev name |
| `ipv4` / `ipv6` | see above | Primary addresses on `max25d0` |
| `extra_ipv4` / `extra_ipv6` | *(empty)* | More CIDRs on `max25d0` |
| `encap` | `ax25-ui` | How IP payloads map to RF |

---

## BayCom kernel netdev (unchanged)

On BayCom kernel-ser12 hosts, **`bcsf0`** stays as-is. TUN **`max25d0`** is an additional IP path via KISS PTY — not a substitute for `bcsf0`.

| Interface | Type | Role |
|-----------|------|------|
| **`bcsf0`** … `bcsf3` | `ARPHRD_AX25` (hdlcdrv) | BayCom kernel modem |
| **`max25d0`** | TUN (IP) | Planned TCP/IP bridge → M25/1 |
| **KISS PTY** | `/var/run/baycom-pr/kiss` | Kernel modem ↔ `max25d` M25/1 |

**Later:** kernel patch may be proposed — not current scope.

---

## Relationship to other paths

| Path | Role |
|------|------|
| **M25/1 `:7325`** | Text/GUI clients |
| **TUN `max25d0`** | IP packets ↔ AX.25 UI (planned) |
| **BayCom KISS PTY** | `bcsf0` ↔ `max25d` M25/1 |
| **HyBBX HBX `:7323`** | HyBBX sessions — external |

Do not run `kissattach` on the same serial port as a `max25d` TNC backend.

---

## Related

- [ARCHITECTURE.md](ARCHITECTURE.md) — Main + Secondaries layout
- [PLATFORMS.md](PLATFORMS.md) — FreeBSD server + CRDOP; *BSD order
- [PACKET-RADIO.md](PACKET-RADIO.md) · [HYBBX.md](HYBBX.md) · [MAX25-CLIENT.md](MAX25-CLIENT.md)
