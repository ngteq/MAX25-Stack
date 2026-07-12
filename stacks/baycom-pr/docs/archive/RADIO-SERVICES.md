# CB and Amateur packet radio (compact)

**BayCom PR-Stack** treats **CB packet** and **Amateur (HAM) packet** equally — same stack, same ser12/KISS drivers, different typical defaults only.

| | **CB (27 MHz packet)** | **Amateur (HAM)** |
|--|------------------------|-------------------|
| Speed | 1200 bd Bell 202 (AX.25 class) | 1200 bd (VHF/UHF) · 9600 bd G3RUH (par96) |
| Typical modem | Albrecht PC-COM / 4500, generic CB ser12 | BayCom ser12 DIY, PC-COM, BayPac |
| Catalog ID | `albrecht-pc-com-4500`, `cb-ser12-generic`, `albrecht-pc-com` | `baycom-ser12`, `albrecht-pc-com`, `baypac-bp2` |
| `txdelay` start | **30–35** (350 ms AE8000 class) | **20–35** (verify on air) |
| Example INI | `config/examples/baycom-pr.cb.ini` | `config/examples/baycom-pr.ham.ini` |
| AX.25 port name | `cb0` (your choice) | `radio` (your choice) |

**9600 bd parallel (G3RUH):** Amateur-oriented; same `baycom_par` path — [PARPORT.md](PARPORT.md).

## Single modem (default — start here)

```bash
sudo cp config/examples/baycom-pr.cb.ini /etc/baycom/baycom-pr.ini   # CB
# or
sudo cp config/examples/baycom-pr.ham.ini /etc/baycom/baycom-pr.ini  # HAM

sudo baycom-pr-ctl probe && sudo baycom-pr-ctl setup
sudo baycom-pr-ctl doctor && sudo baycom-pr-ctl start
```

Minimal INI block (both services):

```ini
[modem.a]
catalog = albrecht-pc-com          ; CB or HAM — same hardware class
serial = /dev/ttyS0
iface = bcsf0
kiss_link = /var/run/baycom-pr/kiss
callsign = YOURCALL-0              ; CB: often numeric suffix allowed locally
txdelay = 35                       ; CB: 30–35 · HAM: 20–35
ax25_port = cb0                    ; or radio
```

## Dual modem (optional — after single is stable)

One profile for **two radios** (CB+CB, HAM+HAM, or mixed — stack does not care):

```bash
sudo cp config/examples/baycom-pr.dual.ini /etc/baycom/baycom-pr.ini
sudo baycom-pr-ctl probe && sudo baycom-pr-ctl setup
sudo /sbin/setserial -g /dev/ttyS0 /dev/ttyS5    # must match INI
sudo baycom-pr-ctl preflight                     # zero errors required
sudo baycom-pr-ctl start                         # staged probe (freeze-safe)
```

See [STABILITY.md](STABILITY.md) — wrong IRQ on 2nd UART is the main freeze cause.

## USB KISS (CB or HAM TNC)

No `iobase`/`irq` — use `kiss-serial-usb`:

```ini
[modem.a]
catalog = kiss-serial-usb
serial = /dev/ttyUSB0
kiss_baud = 9600
```

## Operator time budget

| Step | Time |
|------|------|
| `make install` | once |
| `probe` + `setup` | ~1 min |
| `doctor` + `start` | ~1 min |
| Dual upgrade | +5 min if IRQ verified |

Full automation path: [AUTOMATION.md](AUTOMATION.md).

## Related

- [MODEMS.md](MODEMS.md) — catalog matrix
- [QUICKSTART.md](QUICKSTART.md) — install
- [STABILITY.md](STABILITY.md) — freeze prevention
