# Modular TCP/IP Servers Service

**Public name** for the MAX25 multi-instance topology: a **central Main** server plus **optional Secondaries** for load distribution and clearer structure.

**DEV-Level 1 focus:** this service model is the **current implementation priority** — ahead of DEV-Level 3 (WebSocket) and DEV-Level 4 (CRDOP expansion). See [V2.0.0-SCOPE.md](V2.0.0-SCOPE.md#dev-levels-roadmap-stack-wide).

> Operator-specific host layouts (hardware, uplinks, site naming) are **not** documented here — only the service model and configuration contract.

---

## Roles

| Role | `modular_tcp.role` | Responsibility |
|------|-------------------|----------------|
| **Main** | `main` | Central M25/1 entry — routes client sessions to Secondaries |
| **Secondary** | `secondary` | Owns RF path (e.g. CRDOP on FreeBSD/OSS, TNC/BayCom on Linux) |
| **Standalone** | `standalone` (default) | Single `max25d` — no router |

Typical layout on **one** server host:

```
Operators / TCP clients
        │
        ▼
  Main max25d :7325  (modular TCP/IP Servers Service)
        │
        ├── Secondary-1 :7326  (CRDOP / device A)
        ├── Secondary-2 :7327  (CRDOP / device B)
        └── … (5+ optional)
```

### Cross-host topology (example)

**Recommended split** when CRDOP and TCP/IP integration live on FreeBSD and hardware TNCs/BayCom stay on Linux:

```
Operators / TCP clients
        │
        ▼
  FreeBSD — Main max25d :7325
        │
        ├── FreeBSD — Secondary :7326  (CRDOP/OSS, local or same host)
        ├── Linux   — Secondary :7327  (TNC / BayCom / bcsf0)
        └── Linux   — Secondary :7328  (optional extra radio)
```

| Placement | Typical role |
|-----------|--------------|
| **FreeBSD** | **Main** — central M25/1 router; often also a local CRDOP Secondary |
| **Linux** | **Secondary only** — serial TNC, kernel BayCom, KISS PTY; not the primary CRDOP/TCP path |

Main `[modular_tcp.secondaries]` entries use `host:port` — `127.0.0.1` for co-located Secondaries, or a reachable LAN address for remote Linux hosts. See [ARCHITECTURE.md](ARCHITECTURE.md#example-deployment--freebsd-primary-linux-secondary).

---

## Configuration

### Main — `share/max25/max25d.main.ini.example`

```ini
[modular_tcp]
enabled = yes
role = main
service_name = modular-tcp-server

[modular_tcp.secondaries]
secondary-1 = 127.0.0.1:7326
secondary-2 = 127.0.0.1:7327

[network]
tcp_port = 7325

[stack]
auto_start = no
```

Main forwards M25/1 TCP sessions to Secondaries (round-robin across configured peers). In a FreeBSD-primary split, list local CRDOP Secondaries (`127.0.0.1:port`) and remote Linux hardware Secondaries (`host:port`) in `[modular_tcp.secondaries]`.

### Secondary (FreeBSD CRDOP) — `share/max25/max25d.freebsd.ini.example`

```ini
[modular_tcp]
enabled = yes
role = secondary
instance_id = secondary-1

[network]
tcp_port = 7326

[devices]
default = soft-crdop
soft-crdop = crdop:default
```

### Secondary (Linux hardware) — `share/max25/max25d.secondary-linux.ini.example`

```ini
[modular_tcp]
enabled = yes
role = secondary
instance_id = secondary-linux-1

[network]
tcp_port = 7327

[devices]
default = baycom-ser12
baycom-ser12 = baycom:default
```

Linux Secondaries register with a remote FreeBSD Main — set `tcp_host` / firewall so the Main can reach each Secondary port.

---

## Platform notes

| Platform | Main (typical) | Secondary RF |
|----------|----------------|--------------|
| **FreeBSD** | **yes** (primary TCP/IP hub in split deploy) | **CRDOP/OSS only** (initial port) |
| **Linux/KLinux** | yes (single-host sites) | TNC, BayCom, CRDOP/ALSA — **Secondary only** in FreeBSD-primary split |

Implementation: `stacks/daemon/modular_tcp_server.py`

---

## See also

- [ARCHITECTURE.md](ARCHITECTURE.md) — Host layout — Main + Secondaries
- [FREEBSD-AX25.md](FREEBSD-AX25.md) — FreeBSD CRDOP/OSS port
- [PLATFORMS.md](PLATFORMS.md) — port order
