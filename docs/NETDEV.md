# MAX25 virtual network device (`max25d`)

**Status: planned (near term)** — TUN/TAP sidecar bridges Linux TCP/IP to `max25d` M25/1 and the active RF device. Research: private vault `projects/max25-stack/2026-07-13-max25-tcpip-virtual-netdev-hbx-analysis.md` (not in this repo).

Goal: **Linux host ↔ MAX25-Stack ↔ TCP/IP clients** — one registered device, IPv4 and IPv6 in userspace, RF via the same `max25d` backend as `max25-terminal`.

```
TCP/IP apps ──► TUN max25d ──► max25-tun (planned) ──► max25d M25/1 ──► modem/TNC
```

M25/1 text clients (`max25-terminal`, third-party GUI on `:7325`) remain independent of the TUN path.

---

## Interface name

| Item | Default |
|------|---------|
| **Kernel name** | `max25d` |
| **Visible in** | `ip link show`, `ifconfig max25d` |
| **Type** | TUN (IP packets); TAP optional later |

```bash
ip -br link show max25d
# max25d@NONE: <NOARP,UP,LOWER_UP> … tun
```

---

## Standard addresses (defaults)

These are the **factory defaults** when `[netdev]` is enabled. Override in `max25d.ini` or add more addresses (see below).

| Stack | Default | CIDR | Legacy netmask |
|-------|---------|------|----------------|
| **IPv4** | `127.0.0.25` | `127.0.0.25/8` | `255.0.0.0` |
| **IPv6** | `::25` | `::25/128` | host route |

**Rationale:** loopback-class IPv4 `.25` and IPv6 `::25` — memorable, distinct from `127.0.0.1`, aligned with MAX25 naming.

### Operator setup (after `max25-tun` ships)

```bash
# Defaults from max25d.ini — or run max25-ctl netdev up
ip link set max25d up
ip addr add 127.0.0.25/8 dev max25d
ip -6 addr add ::25/128 dev max25d
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
; Enable TUN bridge (planned — max25-tun sidecar)
enabled = no

; Interface name (ip link / ifconfig)
interface = max25d

; tun | tap (default tun — IP frames)
mode = tun

; Primary addresses (override defaults)
ipv4 = 127.0.0.25/8
ipv6 = ::25/128

; Optional legacy netmask display (ipv4 only; derived from prefix if omitted)
; ipv4_netmask = 255.0.0.0

; Additional addresses on the same interface (comma-separated CIDRs)
; extra_ipv4 = 10.73.25.1/24, 192.168.25.1/32
; extra_ipv6 = fd25::1/64, 2001:db8:25::1/128

; M25/1 attach for the bridge process
m25_unix = /run/max25/modem.sock
; m25_host = 127.0.0.1
; m25_port = 7325

; Encapsulation: ax25-ui (default) | raw-ax25 (later)
encap = ax25-ui
```

| Key | Default | Meaning |
|-----|---------|---------|
| `enabled` | `no` | Start TUN bridge with stack |
| `interface` | `max25d` | TUN device name |
| `ipv4` | `127.0.0.25/8` | Primary IPv4 (prefix or address + `ipv4_netmask`) |
| `ipv6` | `::25/128` | Primary IPv6 |
| `extra_ipv4` | *(empty)* | More IPv4 CIDRs on `max25d` |
| `extra_ipv6` | *(empty)* | More IPv6 CIDRs on `max25d` |
| `encap` | `ax25-ui` | How IP payloads map to RF |

**Single device:** the bridge uses the same `[devices]` default / `SET DEVICE` as M25/1 sessions — one RF path at a time unless multi-device policy is extended later.

---

## Relationship to other paths

| Path | Role |
|------|------|
| **M25/1 `:7325`** | Text/GUI clients — always available |
| **TUN `max25d`** | IP packets ↔ AX.25 UI (planned) |
| **BayCom `bcsf0`** | Kernel AX.25 netdev — parallel on BayCom hosts only |
| **HyBBX HBX `:7323`** | HyBBX sessions — external consumer |

Do not run `kissattach` on the same serial port as `max25d` TNC backends.

---

## Related

- [DEVELOPMENT.md](DEVELOPMENT.md) — third-party GUI welcome on M25/1
- [PACKET-RADIO.md](PACKET-RADIO.md) — AX.25 / KISS
- [HYBBX.md](HYBBX.md) — attach boundary
- [MAX25-CLIENT.md](MAX25-CLIENT.md) — M25/1 client contract
- `include/max25/protocol.md` — wire protocol
