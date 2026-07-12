# Parallel port modems (par96 / picpar)

**BayCom PR-Stack v0.5.0** · Catalog: [MODEMS.md](MODEMS.md) · Config: [CONFIGURATION.md](CONFIGURATION.md)

G3RUH **9600 baud** packet modems on the PC **parallel port** (LPT) via the Linux kernel driver **`baycom_par`**.

## Supported hardware

| Catalog ID | Product | Driver mode | DCD |
|------------|---------|-------------|-----|
| `baycom-par96` | BayCom par96 DIY | `par96` | Software (softdcd) |
| `baycom-picpar` | DF9IC picpar / par97 | `picpar` | Hardware (if wired) |
| `baypac-bp96a` | Tigertronics BayPac BP-96A | `par96` | Software |

Kernel interface names: **`bcp0` … `bcp3`** (one per loaded port).

## Kernel requirements

| Requirement | Detail |
|-------------|--------|
| `CONFIG_PARPORT` | Parallel port subsystem |
| `CONFIG_BAYCOM_PAR` | `baycom_par` module |
| `parport_pc` | Usually auto-loaded; stack runs `modprobe parport_pc` if needed |

Check:

```bash
grep -E 'CONFIG_PARPORT|CONFIG_BAYCOM_PAR' /boot/config-$(uname -r)
modinfo baycom_par
```

## LPT I/O addresses

| Port | Typical iobase | BIOS label |
|------|----------------|------------|
| LPT1 | `0x378` | Parallel port 1 |
| LPT2 | `0x278` | Parallel port 2 |
| LPT3 | `0x3bc` | Some onboard ports |

Verify in `/proc/ioports` after BIOS enable. **No `irq=` in site INI** — the parport subsystem assigns IRQ per port.

## Wiring overview

par96/picpar use a **shift-register** on the parallel port (not the same as LPT-wired ser12 modems). Pinout class: `par96-shift` in [modems.ini](../config/modems.ini).

- PTT, TX/RX data, and clocking via LPT data/control lines
- **picpar**: connect hardware DCD from the radio when possible
- **par96**: kernel uses **software DCD** (`options=softdcd` or mode `par96`)

Reference: [kernel baycom.rst](https://docs.kernel.org/networking/device_drivers/hamradio/baycom.html)

## Site configuration

Template: [config/examples/baycom-pr.par96.ini](../config/examples/baycom-pr.par96.ini)

Minimal **par96 on LPT1 (0x378)**:

```ini
[modem.a]
catalog = baycom-par96
label = Par96 LPT1
iobase = 0x378
mode = par96
iface = bcp0
kiss_link = /var/run/baycom-pr/kiss
ax25_port = radio
callsign = N0CALL-0
txdelay = 20
options = softdcd
```

**No `serial=` or `irq=`** — unlike kernel-ser12.

picpar variant: [config/examples/baycom-pr.picpar.ini](../config/examples/baycom-pr.picpar.ini) (`mode = picpar`).

## Operator workflow

```bash
# 1. Validate offline (no hardware required for parse/validate)
python3 tools/baycom_validate_config.py config/examples/baycom-pr.par96.ini

# 2. Install profile
sudo cp config/examples/baycom-pr.par96.ini /etc/baycom/baycom-pr.ini

# 3. Preflight (checks parport, iobase in /proc/ioports)
sudo baycom-pr-ctl preflight

# 4. Start stack
sudo baycom-pr-ctl start

# 5. Verify without RF
sudo baycom-pr-ctl status
sudo baycom-pr-ctl check
```

Expected: `baycom_par: loaded`, `bcp0: UP`, KISS at `/var/run/baycom-pr/kiss`.

Manual modprobe (debug only):

```bash
sudo modprobe parport_pc
sudo modprobe baycom_par mode=par96 iobase=0x378
ip link set bcp0 up
```

Dual LPT modems: distinct `iobase` per `[modem.*]`; staged probe runs by default (same as dual ser12).

## Mixed profiles (ser12 + par96)

One profile may combine **kernel-ser12** and **kernel-par96** modems. `baycom-pr-ctl` loads **`baycom_ser_fdx`** and **`baycom_par`** in separate `modprobe` calls — they cannot share one module invocation.

Example: `[modem.a]` ser12 on `bcsf0` + `[modem.b]` par96 on `bcp0`.

## KISS bridge

Same as ser12: `baycom_kissbridge` connects `bcp*` → `kiss_link` PTY when `kiss_bridge = yes`.

Attach clients:

```bash
socat -x /var/run/baycom-pr/kiss,raw,echo=0 -
baycom-pr-ctl listen radio
```

There is **no raw UART serial path** for par96.

## Troubleshooting

| Symptom | Check |
|---------|--------|
| `baycom_par` fails to load | `dmesg`; `CONFIG_BAYCOM_PAR`; LPT enabled in BIOS |
| iobase not in `/proc/ioports` | Wrong address; port disabled; USB-only “LPT” adapter |
| `bcp0` missing | `modprobe baycom_par`; `ip link set bcp0 up` |
| Duplicate iobase error | Two modems on same LPT address |
| Poor RX / no decode | par96 soft DCD — try picpar + hardware DCD |

Recover:

```bash
sudo baycom-pr-ctl recover
sudo baycom-pr-ctl preflight && sudo baycom-pr-ctl start
```

## Related docs

- [HARDWARE.md](HARDWARE.md) — connection paths
- [MODEMS.md](MODEMS.md) — catalog matrix
- [STABILITY.md](STABILITY.md) — preflight / recover (ser12 IRQ rules do not apply to parport)
