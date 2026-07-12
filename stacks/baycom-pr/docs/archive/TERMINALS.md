# Terminal clients

**v0.5.0** · [INDEX](INDEX.md) · [MANUAL](MANUAL.md) · [Examples](../config/examples/terminals/)

BayCom PR-Stack exposes stable attachment points (`kiss_link`, `serial`, `ax25_port`). This document covers the **three most common terminal-style clients** on Linux for inspection, KISS attach, and scripting.

| Client | Best for | Stack state |
|--------|----------|-------------|
| [minicom](#minicom) | Interactive sessions, menus, logging | KISS or serial |
| [picocom](#picocom) | Lightweight serial/KISS terminal | KISS or serial |
| [socat](#socat) | Hex dumps, logging, TCP/PTY bridges | KISS (stack running) |

> **Not PicoTerm:** [PicoTerm](https://github.com/RC2014Z80/picoterm) is VGA firmware for RP2040 retro hardware — unrelated to this stack. On Linux, use **picocom** for a minimal serial terminal.

## Golden rules

1. **kernel-ser12:** Do **not** open `/dev/ttyS*` with any terminal while `baycom_ser_fdx` owns the UART. Use `kiss_link` or stop the stack first.
2. **kiss-serial:** Open the modem's `kiss_link` PTY, not the USB device directly (unless debugging USB with stack stopped).
3. **AX.25 apps** (`listen`, `call`) use `ax25_port` names — not covered here; see [MANUAL — AX.25](MANUAL.md#ax25).

Paths below assume the **default single-modem** profile ([config/baycom-pr.ini](../config/baycom-pr.ini)):

| Modem | Serial | KISS link | AX.25 port |
|-------|--------|-----------|------------|
| **a** | `/dev/ttyS0` | `/var/run/baycom-pr/kiss` | `radio` |

**Dual-modem** sites use `kiss-a` / `kiss-b` and `cb0` / `cb1` — see [config/examples/baycom-pr.dual.ini](../config/examples/baycom-pr.dual.ini).

Adjust for your `/etc/baycom/baycom-pr.ini`.

---

## minicom

Full-featured terminal. **Integrated** in `baycom-pr-ctl` with installable profiles.

### Install

Install **minicom** from your Linux system packages (or build from source).

Profiles: `/etc/baycom/minicom/minirc.baycom-kiss`, `minirc.baycom-serial` (from `make install`).

### KISS (stack running)

```bash
sudo baycom-pr-ctl start
sudo baycom-pr-ctl minicom a              # default single profile
minicom baycom-kiss -D /var/run/baycom-pr/kiss -b 9600
```

Baud on the KISS PTY is nominal; framing is byte-oriented KISS.

### Raw serial (stack **stopped**)

```bash
sudo baycom-pr-ctl stop
sudo baycom-pr-ctl minicom a --serial
```

Manual (modem A, 1200 baud ser12):

```bash
minicom baycom-serial -D /dev/ttyS0 -b 1200
```

### Exit

`Ctrl-A`, then `X` (confirm).

### Example script

[config/examples/terminals/minicom-kiss-a.example.sh](../config/examples/terminals/minicom-kiss-a.example.sh)

---

## picocom

Minimal dumb terminal — fast, few dependencies. Ideal on embedded hosts and SSH sessions.

### Install

Install **picocom** from your Linux system packages (or build from source).

### KISS (stack running)

```bash
sudo baycom-pr-ctl start
picocom -b 9600 -r -l /var/run/baycom-pr/kiss
```

### Raw serial (stack **stopped**)

```bash
sudo baycom-pr-ctl stop
picocom -b 1200 -r -l /dev/ttyS0
```

Use catalog `baud` from [MODEM-SETUP.md](MODEM-SETUP.md) (typically **1200** for ser12).

### USB KISS modem (kiss-serial backend)

Stack running; attach to PTY, not `ttyUSB0`:

```bash
picocom -b 9600 -r -l /var/run/baycom-pr/kiss-usb
```

### Exit

`Ctrl-A`, then `Ctrl-X`.

### Example scripts

- [picocom-kiss-a.example.sh](../config/examples/terminals/picocom-kiss-a.example.sh)
- [picocom-serial-a.example.sh](../config/examples/terminals/picocom-serial-a.example.sh)

---

## socat

Stream relay — hex dumps, logging, feeding another program, or exposing KISS on TCP for a remote client.

### Install

Install **socat** from your Linux system packages (or build from source).

### KISS hex tap (interactive)

Stack running:

```bash
sudo baycom-pr-ctl start
socat -x OPEN:/var/run/baycom-pr/kiss,raw,echo=0 STDIO
```

`-x` prints hex+ASCII (useful for KISS frame inspection). `Ctrl-C` to exit.

### KISS → log file

```bash
socat OPEN:/var/run/baycom-pr/kiss,raw,echo=0 \
  OPEN:/tmp/kiss.log,creat,append
```

### KISS → TCP (one client)

Expose local KISS to a network client (firewall accordingly):

```bash
socat TCP-LISTEN:8001,reuseaddr,fork \
  OPEN:/var/run/baycom-pr/kiss,raw,echo=0
```

Remote: `socat STDIO TCP:radio-host:8001` or point your KISS app at the host:port if supported.

### Pair with picocom

One terminal for TX typing, one for hex monitor — **only one consumer** should own KISS unless you use a fan-out setup; for debug, prefer socat alone or minicom alone.

### Example scripts

- [socat-kiss-tap-a.example.sh](../config/examples/terminals/socat-kiss-tap-a.example.sh)
- [socat-kiss-tcp-a.example.sh](../config/examples/terminals/socat-kiss-tcp-a.example.sh)

---

## Quick comparison

| Task | minicom | picocom | socat |
|------|---------|---------|-------|
| KISS interactive | `baycom-pr-ctl minicom a` | `picocom -b 9600 -r -l kiss` | — |
| Raw UART inspect | `--serial` | `picocom -b 1200 -r -l ttyS0` | — |
| Hex / debug KISS | limited | limited | `socat -x …` |
| TCP bridge | — | — | `TCP-LISTEN:…` |
| INI profiles | yes (`minirc.*`) | CLI flags | scripts |

## Related

- [QUICKSTART — Attach clients](QUICKSTART.md#4-attach-clients)
- [MANUAL — External clients](MANUAL.md#external-clients)
- [TESTING.md](TESTING.md) — run `selftest` before attaching clients
