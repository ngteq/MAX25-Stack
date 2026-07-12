# HyBBX Integration

**MainAX25-Stack (MAX25-Stack)** is the **standalone RF/link layer**. HyBBX (external repo) consumes it via built-in transport plugins.

## Plugin mapping

| MainAX25 | HyBBX plugin | CMake flag | INI `[networks]` |
|-------|--------------|------------|------------------|
| `hardware/tncs` | `packet_radio` | default ON | `ax25 = yes` |
| `hardware/modems` | `baycom` | `-DHYBBX_PLUGIN_BAYCOM=ON` | `baycom = yes` |
| `hardware/soft-modems` | `crdop` | `-DHYBBX_PLUGIN_CRDOP=ON` | `crdop = yes` |

HyBBX source: `https://github.com/ngteq/hyBBX/` (not vendored in MainAX25).

**AX.25 / KISS / TNC technical facts** for MAX25 (not HyBBX product docs): [PACKET-RADIO.md](PACKET-RADIO.md).

## Contract: packet_radio (TNCs)

### Preparation (MainAX25)

```bash
./scripts/max25-ctl start --hardware tncs --device tnc2c
./stacks/tncs/tnc2c-integration-test.sh
```

### HyBBX INI

Merge `share/hybbx/tnc2c-edge.ini.example` into Secondary `hybbx.ini`:

```ini
[transport.packet_radio1]
tnc = tnc2c
protocol = kiss
device = /dev/ttyS4
baud = 19200
serial_line = 8n1
rts_dtr = yes
```

Profiles: HyBBX [TNCS.md](https://github.com/ngteq/hyBBX/blob/main/docs/TNCS.md) — `tnc2c`, `tnc2`, `pk232`, …

### Rules

- HyBBX opens serial **after** boot-wait succeeds
- Do not run minicom and HyBBX on same port
- `kiss on` at HyBBX start — TNC must be in host mode

## Contract: baycom (Modems)

### Preparation (MainAX25)

```bash
sudo stacks/baycom-pr/scripts/baycom-pr-ctl preflight
sudo stacks/baycom-pr/scripts/baycom-pr-ctl start
sudo stacks/baycom-pr/scripts/baycom-pr-ctl status   # KISS running
```

### HyBBX INI

Merge `share/hybbx/baycom-ser12-edge.ini.example`:

```ini
[networks]
baycom = yes

[transport.baycom1]
backend = kernel
mode = ser12*
interface = bcsf0
```

Or KISS path: open `/var/run/baycom-pr/kiss` (stack-managed PTY).

Full contract: `stacks/baycom-pr/docs/PLUGIN.md`

### Rules

- Stack must be running before HyBBX `baycom` plugin starts
- Never open raw `/dev/ttyS*` while `baycom_ser_fdx` loaded
- Root/capabilities for kernel autoload if used

## Operating mode: hybbx-edge

Recommended flow for Secondary nodes:

1. Select device plugin (`plugins/devices/<id>/plugin.yaml`)
2. Run device `scripts.boot_wait` or `runtime.ctl start`
3. Apply matching `share/hybbx/*-edge.ini.example`
4. Build HyBBX with required plugin enabled
5. Start HyBBX Secondary → HBX link to Main

## Dual radio (service)

- BayCom: `stacks/baycom-pr/config/examples/baycom-pr.dual.ini`
- TNC mix: `share/hybbx/service-dual.ini.example`
- Unique `link_id` per `[transport.*N]` on Main registry

## What HyBBX does not provide

- TNC boot/DTR sequencing
- Kernel BayCom module load
- KISS PTY creation
- AX.25 `axports` sync

Those remain MainAX25 (MAX25) / merged stack responsibilities.

## Contract: crdop (Soft modems)

### Preparation (MainAX25)

```bash
./scripts/build.sh
./scripts/max25-ctl start --hardware soft-modems --device soft-crdop
```

`crdopc` listens on TCP **8515** (control) / **8516** (data). Start modem **before** HyBBX.

### HyBBX INI

Merge `share/hybbx/crdop-edge.ini.example`:

```ini
[networks]
crdop = yes

[transport.crdop1]
modem_host = 127.0.0.1
modem_port = 8515
mycall = CB-0
listen = yes
```

HyBBX doc: external `hyBBX/docs/CRDOP.md`. CRDOP is **ARDOP**, not AX.25 — parallel to packet-radio transports.

### Rules

- One `crdopc` instance per sound-card radio path
- HyBBX connects via TCP; no serial port exclusivity
- CB profile defaults (`500MAX`, half-duplex) from `stacks/crdop/share/crdop.ini.example`
