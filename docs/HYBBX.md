# HyBBX integration

MAX25 is the **standalone RF/link layer**. [HyBBX](https://github.com/ngteq/hyBBX) (external) consumes it via transport plugins after MAX25 prep.

AX.25 / KISS / TNC technical facts: [PACKET-RADIO.md](PACKET-RADIO.md). HyBBX operator docs: HyBBX `docs/TNCS.md`, `docs/BAYCOM.md`, `docs/CRDOP.md`.

## Plugin mapping

| MAX25 hardware | HyBBX plugin | INI `[networks]` |
|----------------|--------------|------------------|
| `hardware/tncs` | `packet_radio` | `ax25 = yes` |
| `hardware/modems` | `baycom` | `baycom = yes` |
| `hardware/soft-modems` | `crdop` | `crdop = yes` |

## Order rule

**MAX25 stack before HyBBX transport plugin.** One process per serial port — never userspace serial owner + HyBBX + boot-wait concurrently.

## TNC (`packet_radio`)

**MAX25 prep:**

```bash
./scripts/max25-ctl start --hardware tncs --device tnc2c
# or: stacks/tncs/tnc2c-boot-wait.sh
```

**HyBBX INI:** merge `share/hybbx/tnc2c-host.ini.example` into Secondary `hybbx.ini`. Key fields: `tnc=tnc2c`, `protocol=kiss`, `device`, `baud`, `serial_line`, `rts_dtr`, **`kiss_entry=none`** (MAX25 owns KISS entry), `persist=255` on CB.

Recovery without power cycle: `stacks/tncs/docs/TNC-RECOVERY.md`.

## BayCom (`baycom`)

**MAX25 prep (single PC-COM on ttyS0 — canonical v1 path):**

```bash
sudo cp share/baycom/baycom-pr.pccom-ttyS0-only.ini.example /etc/baycom/baycom-pr.ini
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini setup
./scripts/max25-ctl start --hardware modems --device baycom-ser12
# or: max25d with auto_start=yes and [device.baycom-ser12] baycom_ini=
```

**HyBBX INI:** merge `share/hybbx/baycom-ser12-host.ini.example` — `backend=kernel`, `mode=ser12*`, `interface=bcsf0`. Or KISS PTY at `/var/run/baycom-pr/kiss`.

Full BayCom contract: [BAYCOM.md](BAYCOM.md) · `stacks/baycom-pr/docs/PLUGIN.md`.

## CRDOP — CB/AR Digital Open Protocol (`crdop`)

**CRDOP** = **CB/AR Digital Open Protocol** (CB = Citizens Band, AR = Amateur Radio).

**MAX25 prep:**

```bash
./scripts/build.sh
./scripts/max25-ctl start --hardware soft-modems --device soft-crdop
```

`crdop` launcher listens on TCP **8515** (control) / **8516** (data). Native MAX25-SoftModem M25/KISS host — acoustically AX.25-compatible. MAX25 starts and bridges via `CrdopTcpBackend`; it does not ship ARDOP. Optional third-party ARDOP attach: `ardop_compat=true`.

**HyBBX INI:** merge `share/hybbx/crdop-host.ini.example` — `modem_host`, `modem_port=8515`.

## HyBBX host workflow

1. Run MAX25 device prep (boot-wait, `baycom-pr-ctl start`, or `crdopc`)
2. Merge matching `share/hybbx/*-host.ini.example`
3. Build HyBBX with required plugin enabled
4. Start HyBBX Secondary → HBX link to Main

Operating mode plugin: `plugins/betriebsform/hybbx-host/`.

## Dual radio (service)

- BayCom: `stacks/baycom-pr/config/examples/baycom-pr.dual.ini`
- max25d: `share/max25/max25d.dual-baycom.ini.example` (`baycom-a` + `baycom-b`)
- HyBBX: `share/hybbx/service-dual.ini.example` — `[transport.baycom1]` + `[transport.baycom2]`
- Start: `max25-ctl start --hardware modems --device baycom-ser12 --baycom-profile dual`
- Unique `link_id` per transport on Main

## What HyBBX does not provide

| MAX25 owns | HyBBX does not |
|------------|----------------|
| TNC boot/DTR sequencing | — |
| Kernel BayCom module load | — |
| KISS PTY creation | — |
| `axports` sync | — |

## See also

- [LINUX-HOST-SETUP.md](LINUX-HOST-SETUP.md) — host install
- [V1.0.0-SCOPE.md](V1.0.0-SCOPE.md) — active devices
- `share/hybbx/*.ini.example`
