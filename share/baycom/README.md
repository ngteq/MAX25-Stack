# BayCom configuration examples (MAX25)

Shipped **single-modem** templates for kernel BayCom (SER12). Site-specific copies go to `/etc/baycom/` or `local/baycom-pr.ini` (gitignored).

## Canonical single PC-COM (v1 default)

| File | Use |
|------|-----|
| [`baycom-pr.pccom-ttyS0-only.ini.example`](baycom-pr.pccom-ttyS0-only.ini.example) | **One modem** on `/dev/ttyS0` — production default |

Install:

```bash
sudo cp share/baycom/baycom-pr.pccom-ttyS0-only.ini.example /etc/baycom/baycom-pr.ini
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini setup
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini preflight
```

Start via MAX25:

```bash
./scripts/max25-ctl start --hardware modems --device baycom-ser12
```

Or let `max25d` auto-start (set `[device.baycom-ser12] baycom_ini = /etc/baycom/baycom-pr.ini`).

## Example multi-device host layout (single PC-COM)

Typical onboard-UART assignment when BayCom and two TNCs share one host:

| Port | Example role |
|------|----------------|
| `/dev/ttyS0` | PC-COM (BayCom kernel-ser12) — **only BayCom UART** |
| `/dev/ttyS4` | TNC2C (`packet_radio`, boot-wait) |
| `/dev/ttyS5` | PK-TNC2 (`packet_radio`, HyBBX) — **not BayCom** |

Dual-modem BayCom (`ttyS0` + `ttyS5`) is **service-mode only** (`stacks/baycom-pr/config/examples/baycom-pr.dual.ini`) — do not use when `ttyS5` is already assigned to a TNC.

## Dual modem (service mode, opt-in)

For two kernel-ser12 modems on **two free UARTs**:

```bash
sudo cp stacks/baycom-pr/config/examples/baycom-pr.dual.ini /etc/baycom/baycom-pr.ini
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini setup
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini preflight
./scripts/max25-ctl start --hardware modems --device baycom-ser12 --baycom-profile dual
```

HyBBX: `share/hybbx/service-dual.ini.example` · stack guide: `stacks/baycom-pr/docs/GUIDE.md` §11.

## Other stack profiles

CB, HAM, LPT — see `stacks/baycom-pr/config/examples/` (link from [docs/BAYCOM.md](../../docs/BAYCOM.md)).

## Installed paths (after `install-max25.sh`)

| Path | Content |
|------|---------|
| `/etc/baycom/baycom-pr.ini` | Site config (operator copy) |
| `/etc/baycom/baycom-pr.ini.example` | Shipped single-modem template |
| `/etc/baycom/modems.ini` | Hardware catalog |
| `/usr/local/share/max25/baycom/` | Same examples as this directory |

## See also

- [docs/BAYCOM.md](../../docs/BAYCOM.md)
- [local/README.md](../../local/README.md) — operator `local/` workflow
