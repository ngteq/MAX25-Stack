# Terminal clients

Attach to a running BayCom PR-Stack for KISS debug or AX.25 sessions.

| Client | Use | Mode |
|--------|-----|------|
| [max25-terminal](#max25-terminal) | Official operator UI (M25/1) | TCP to `max25d` |
| [listen / call](#listen--call) | AX.25 monitor and connects | kernel AX.25 port |
| [socat](#socat) | KISS hex tap or TCP bridge | KISS PTY |

**One consumer per path:** do not open raw `/dev/ttyS*` while `baycom_ser_fdx` owns the UART. Use KISS PTY or AX.25 port names.

---

## max25-terminal

Official MAX25 client — text UI + F10 menu over M25/1.

```bash
max25-terminal --host 127.0.0.1 --port 7325
```

See [docs/MAX25-TERMINAL.md](../../../docs/MAX25-TERMINAL.md).

---

## listen / call

When the stack is up and `axports` are applied:

```bash
sudo baycom-pr-ctl listen radio
sudo baycom-pr-ctl call radio DEST
```

Or use `listen` / `call` directly with the port name from `/etc/ax25/axports`.

---

## socat

Lightweight KISS inspection or TCP fan-out. Examples in [config/examples/terminals/](../config/examples/terminals/).

### KISS hex tap (modem a)

```bash
KISS=/var/run/baycom-pr/kiss
socat -x "${KISS},raw,echo=0" -
```

Stack must be running; KISS bridge must be up.

### KISS → TCP (modem a)

```bash
socat TCP-LISTEN:8001,reuseaddr,fork "${KISS},raw,echo=0"
```

Remote clients connect to `host:8001` for raw KISS frames.

Scripts:

- [socat-kiss-tap-a.example.sh](../config/examples/terminals/socat-kiss-tap-a.example.sh)
- [socat-kiss-tcp-a.example.sh](../config/examples/terminals/socat-kiss-tcp-a.example.sh)

---

## Quick reference

| Task | Tool | Example |
|------|------|---------|
| Operator UI | max25-terminal | M25/1 TCP |
| AX.25 monitor | listen | `baycom-pr-ctl listen radio` |
| AX.25 connect | call | `baycom-pr-ctl call radio DEST` |
| KISS hex debug | socat | `socat -x kiss,raw,echo=0 -` |
| KISS TCP bridge | socat | see example scripts |
