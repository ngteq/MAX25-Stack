# Automation and operator UX

**v0.5.x → v0.6.0** · [QUICKSTART.md](QUICKSTART.md) · [STABILITY.md](STABILITY.md)

Guided workflow for minimal manual configuration.

## Recommended first run

```bash
sudo make install
sudo baycom-pr-ctl probe      # scan UART / USB / LPT
sudo baycom-pr-ctl setup      # auto-fill missing iobase/irq/serial in INI
sudo baycom-pr-ctl doctor     # validate + preflight + runtime hints
sudo baycom-pr-ctl start
sudo baycom-pr-ctl selftest
```

## Commands

| Command | Purpose |
|---------|---------|
| `probe` | List hardware: ttyS* (setserial), ttyUSB/ACM, parport, loaded modules |
| `setup` | Write missing INI fields from probe (backup → `.bak`) |
| `doctor` | Full health: deps, modules, validate, preflight, KISS links |
| `preflight` | Safety gate before `start` (IRQ/UART conflicts) |
| `recover` | Post-crash cleanup |

## Minimal INI (ser12)

Only **`serial`** and **`catalog`** are required — `iobase`/`irq` come from `setserial` or `setup`:

```ini
[modem.a]
catalog = albrecht-pc-com
serial = /dev/ttyS0
iface = bcsf0
kiss_link = /var/run/baycom-pr/kiss
callsign = N0CALL-0
txdelay = 35
```

## System protection layers

1. **validate** — schema, duplicates, unsupported catalog
2. **preflight** — setserial match, lsof, duplicate IRQ, parport ioports
3. **staged probe** — dual modem: one port at a time
4. **IRQ watchdog** — auto-stop on storm after start
5. **recover** — unload drivers, restore UARTs

See [UX-AUTOMATION-ANALYSIS.md](UX-AUTOMATION-ANALYSIS.md) for the full gap analysis.
