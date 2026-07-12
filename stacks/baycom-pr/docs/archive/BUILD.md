# Build and install

## Requirements

| Tool | Purpose |
|------|---------|
| GCC, GNU make | Build C tools |
| Linux kernel UAPI | ioctl structs (uses installed headers) |
| `libutil` | PTY in `baycom_kissbridge`, `baycom_kiss_serial` |
| Python 3.6+ | INI loader and validator (stdlib only) |
| `setserial` | UART release before `modprobe` |

Kernel modules at runtime: `ax25`, `baycom_ser_fdx` (pulls `hdlcdrv`).

## Build

```bash
make all          # from repo root
make -C tools all # equivalent
```

| Binary | Source |
|--------|--------|
| `baycom_test` | `tools/baycom_test.c` |
| `baycom_sethdlc` | `tools/baycom_sethdlc.c` |
| `baycom_kissbridge` | `tools/baycom_kissbridge.c` |
| `baycom_kiss_serial` | `tools/baycom_kiss_serial.c` |

## Install (prefix `/usr/local`)

```bash
make install
# or: sudo bash scripts/install-root.sh
```

Installs:

| Path | Content |
|------|---------|
| `/usr/local/sbin/baycom_*` | Binaries + Python tools |
| `/usr/local/sbin/baycom-pr-ctl` | Control script |
| `/usr/local/sbin/pccom_*` | Legacy symlinks → `baycom_*` |
| `/etc/baycom/baycom-pr.ini` | Site profile |
| `/etc/baycom/modems.ini` | Catalog |
| `/etc/baycom/axports/*.snippet` | AX.25 examples |
| `/etc/baycom/legacy/pccom.env*` | Legacy env (deprecated) |

Full path reference: [CONFIGURATION.md](CONFIGURATION.md).

## Validate config (no root)

```bash
make test-config
python3 tools/baycom_validate_config.py config/baycom-pr.ini
```

## Offline test suite

```bash
make test    # scripts/test-all.sh
```

## Clean

```bash
make clean
```
