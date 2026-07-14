# FreeBSD and *BSD port plan

**`max25d` on FreeBSD 15.1+** is **DEV-Level 1** (*ca.*, with Linux/KLinux) — modular TCP/IP hub + **minimal CRDOP/OSS**. CRDOP expansion is **DEV-Level 4**.

Platform order: **[PLATFORMS.md](PLATFORMS.md)** · [V2.0.0-SCOPE.md](V2.0.0-SCOPE.md#dev-levels-roadmap-stack-wide) · *BSD chain: **FreeBSD → OpenBSD → NetBSD** (sequential, no skipping).

---

## FreeBSD AX.25 — SoftModem (CRDOP) only

On FreeBSD, packet radio through MAX25 is **initially pure SoftModem** — **CRDOP** (`soft-crdop`) over the **FreeBSD/OSS** audio path.

| Topic | FreeBSD | Linux/KLinux |
|-------|---------|--------------|
| **AX.25 RF path (first BSD wave)** | **CRDOP only** | TNC · BayCom · CRDOP |
| **Audio API** | **OSS** (native FreeBSD sound) | **ALSA** (`libasound`) |
| **Do not use** | Linux/ALSA on FreeBSD | OSS shim pretending to be production path on Linux |

Same acoustic AX.25 goals as Linux CRDOP; different host audio stack. Implementation notes: `stacks/crdop/` (OSS backend when ported).

---

## FreeBSD as primary TCP/IP host (example deployment)

In a **multi-host** layout, FreeBSD is the natural home for the **Modular TCP/IP Servers Service Main** — full M25/1 entry, CRDOP/OSS softmodem, and optional local CRDOP Secondary on the same machine.

| Host | Role | Responsibility |
|------|------|----------------|
| **FreeBSD** | **Main** | Central `max25d` hub (`modular_tcp.role = main`) · CRDOP RF via OSS |
| **Linux** | **Secondary** | TNC · kernel BayCom (`bcsf0`) · KISS PTY — extends RF, does not replace FreeBSD Main |

Linux hosts in this pattern do **not** carry the primary TCP/IP / CRDOP path; they register as Secondaries in the FreeBSD Main INI. No site-specific IPs or callsigns in docs — configure `[modular_tcp.secondaries]` with your reachable `host:port` peers.

Cross-host topology: [MODULAR-TCPIP-SERVER.md](MODULAR-TCPIP-SERVER.md) · [ARCHITECTURE.md](ARCHITECTURE.md#example-deployment--freebsd-primary-linux-secondary).

---

## FreeBSD — initial scope (light port)

No large MAX25-Stack port up front. Ship a **working server** with what is **easy to port**:

| In scope (first) | Out of scope (initially) |
|------------------|---------------------------|
| `max25d` **server** (Main/Secondary hub) | Kernel **BayCom** (`baycom_ser_fdx`, `bcsf0`) |
| **CRDOP** / `soft-crdop` via **OSS** | TNC boot-wait / serial KISS stack |
| M25/1 `:7325` · `max25-terminal` | Linux/ALSA audio on BSD |
| | OpenBSD / NetBSD (later) |

---

## *BSD family order (mandatory)

| Step | OS | Prerequisite |
|------|-----|--------------|
| **1** | **FreeBSD 15.1+** | Linux/KLinux tier complete — CRDOP/OSS working |
| **2** | **OpenBSD** | FreeBSD server + CRDOP working |
| **3** | **NetBSD** | OpenBSD covered |

Do not parallelize OpenBSD and NetBSD with an unfinished FreeBSD port.

---

## AX.25 on *BSD (background)

Native Linux AX.25 (`AF_AX25`, kernel netdev) is **not** assumed on FreeBSD. MAX25 does **not** depend on vendored `libax25` for `max25d` core — in-tree `ax25_codec.py` / M25/1 + **CRDOP** suffice for the first BSD server.

HyBBX attach on a FreeBSD MAX25 host: after CRDOP/`max25d` prep — same external contract as Linux ([HYBBX.md](HYBBX.md)).

---

## Today

Build on FreeBSD:

```bash
./scripts/install-freebsd.sh
# or: ./scripts/build-freebsd.sh && sudo cmake --install build --prefix /usr/local
```

Templates: `share/max25/max25d.freebsd.ini.example`, `share/max25/max25d.main.ini.example`, `share/max25/max25d.secondary-linux.ini.example`, `stacks/crdop/share/crdop.freebsd.ini.example`.

**Split deploy:** Main + CRDOP on FreeBSD; point `[modular_tcp.secondaries]` at Linux Secondary hosts for TNC/BayCom. Template: `share/max25/max25d.main.ini.example`.

Until first on-air test on BSD: use **MAX25 Terminal** against a **Linux/KLinux** `max25d` with full device set, or against FreeBSD Main once CRDOP/OSS is up.
