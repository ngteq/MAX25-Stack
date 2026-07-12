# Packet connects — incoming and outgoing

How to **call**, **be called**, **monitor**, and use **broadcast-style** traffic on CB and Amateur packet with BayCom PR-Stack.

The stack exposes **AX.25 port names** (`ax25_port` in INI). Standard Linux tools use those names — not `bcsf0` directly.

**Station ID:** set `callsign` in `/etc/baycom/baycom-pr.ini` once; the same value must appear in `/etc/baycom/axports/axports`.

Works with **HyBBX** (plugin) or **any terminal AX.25 client** (`listen`, `call`, etc.).

---

## Before you connect (checklist)

```bash
sudo baycom-pr-ctl status    # baycom_ser_fdx loaded, bcsf0 UP, kiss bridge running
```

1. `callsign` in INI matches your legal ID (CB or amateur).
2. Axports synced: `sudo baycom-pr-ctl axports check` (auto on `start` / `setup`).
3. Radio on, antenna connected, appropriate licence / band plan.

`start` writes `/etc/baycom/axports/axports` and symlinks `/etc/ax25/axports`. User lines outside the managed block are preserved.

**CB single example** (`config/examples/baycom-pr.cb.ini`):

```ini
ax25_port = cb0
callsign = CB0CALL-0
```

`/etc/baycom/axports/axports`:

```
cb0       CB0CALL-0   1200   255     2       CB / bcsf0
```

**HAM single example** (`config/examples/baycom-pr.ham.ini`):

```ini
ax25_port = radio
callsign = N0CALL-0
```

```
radio     N0CALL-0   1200   255     2       HAM / bcsf0
```

Snippet templates: `config/axports/single.snippet`, `config/axports/dual.snippet`.

---

## Outgoing — you call someone

Syntax: `call <port> <destination>`

Destination is the remote AX.25 address (CB or amateur format per band practice).

### Example 1 — CB call

```bash
# Stack running, axports ready, port cb0
call cb0 CB1TEST-0
```

### Example 2 — CB call with digipeater path

```bash
call cb0 CB1TEST-0 via DB0CB-0
```

(Path depends on your network — adjust digi callsigns.)

### Example 3 — Amateur VHF/UHF connect

```bash
call radio DL1ABC
```

### Example 4 — Amateur with SSID

```bash
call radio DL1ABC-7
```

### Example 5 — Hang up / end session

End the `call` session with its built-in quit command (often **Ctrl+C** or client-specific escape — see your ax25-tools version). Then:

```bash
sudo baycom-pr-ctl status   # confirm stack still up
```

---

## Incoming — you are called / you wait

Syntax: `listen -a -c <port>` — accept connects on that port.

### Example 6 — CB: wait for incoming connects

```bash
listen -a -c cb0
```

Remote stations can connect to your `callsign` on port `cb0`.

### Example 7 — HAM: wait for incoming connects

```bash
listen -a -c radio
```

### Example 8 — Monitor channel (no connect — watch traffic)

Decode UI frames without accepting connects (useful for beacons, broadcast bulletins, channel observation):

```bash
listen -a -v cb0
```

```bash
listen -a -v radio
```

(`-v` verbose — exact flags may vary by ax25-tools build; `-a` attaches to port.)

### Example 9 — Background listener (service / script)

Run in `screen` or `tmux` for continuous incoming capability:

```bash
screen -S packet
listen -a -c radio
# detach: Ctrl+A then D
```

Pair with HyBBX or other BBS software in [service mode](GUIDE.md#11-service-mode-dual-modem) for automated handling.

---

## Broadcast and bulletin-style traffic

Packet **broadcast** on CB and amateur bands is usually **UI frames** (beacons, APRS-style, bulletin boards) — not a separate stack command.

| Activity | Typical approach |
|----------|------------------|
| Hear all traffic on channel | `listen -a -v <port>` |
| Beacon / periodic ID | External app, HyBBX, or `call` to a BBS mailbox |
| CQ-style operation | Monitor with `listen`, then `call` when you see a station |
| BBS bulletins | Connect to BBS callsign via `call` (e.g. `call radio BBS-0`) |

The stack delivers the RF link; **applications** (terminal client or HyBBX) send and receive frames.

### Example 10 — CB: monitor then call a station you heard

Terminal 1:

```bash
listen -a -v cb0
```

When you see `CB1TEST-0`, terminal 2:

```bash
call cb0 CB1TEST-0
```

### Example 11 — HAM: connect to a packet BBS

```bash
call radio DB0LUE-1
```

(Replace with a valid BBS address on your band.)

---

## Service mode — two ports (HyBBX / dual radio)

Only when running **continuous service** with two modems — see [GUIDE §11](GUIDE.md#11-service-mode-dual-modem).

| Modem | INI `ax25_port` | Incoming | Outgoing |
|-------|-----------------|----------|----------|
| A | `cb0` | `listen -a -c cb0` | `call cb0 DEST` |
| B | `cb1` | `listen -a -c cb1` | `call cb1 DEST` |

KISS: `/var/run/baycom-pr/kiss-a` and `kiss-b` for external apps.

---

## HyBBX vs terminal clients

| | HyBBX (plugin) | Terminal (`listen` / `call`) |
|--|----------------|------------------------------|
| Attach | KISS PTY + optional AX.25 port | `ax25_port` name |
| Station ID | `callsign` from INI | same in `axports` |
| Incoming | HyBBX handles | `listen -a -c <port>` |
| Outgoing | HyBBX handles | `call <port> <dest>` |
| Dual | Service profile | One `listen`/`call` per port |

Details: [PLUGIN.md](PLUGIN.md).

---

## Troubleshooting

| Symptom | Check |
|---------|--------|
| `call`: port not found | `cat /etc/ax25/axports` — symlink from `/etc/baycom/axports/axports` |
| No connects, stack idle | `sudo baycom-pr-ctl status` — `bcsf0` UP? kiss bridge running? |
| Wrong station ID on air | INI `callsign` must match `axports` column 2 |
| `I/O error` / no RF | Radio power, PTT cable, `baycom-pr-ctl check` |
| USB TNC | `kiss-serial` backend — KISS path in `status`; AX.25 may need different client setup |

Freeze / IRQ: [GUIDE §6](GUIDE.md#6-freeze-prevention).

---

## See also

- [GETTING-STARTED.md](GETTING-STARTED.md) — install paths CB / HAM / USB
- [GLOSSARY.md](GLOSSARY.md) — terms
- [REFERENCE.md](REFERENCE.md) — INI and paths
