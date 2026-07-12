# Terminal client examples

Copy, edit paths, `chmod +x`, run as root when opening `/var/run/baycom-pr/*` or UARTs.

| Script | Client | Mode |
|--------|--------|------|
| [minicom-kiss-a.example.sh](minicom-kiss-a.example.sh) | minicom | KISS, modem a |
| [picocom-kiss-a.example.sh](picocom-kiss-a.example.sh) | picocom | KISS, modem a |
| [picocom-serial-a.example.sh](picocom-serial-a.example.sh) | picocom | Raw UART, stack stopped |
| [socat-kiss-tap-a.example.sh](socat-kiss-tap-a.example.sh) | socat | KISS hex tap |
| [socat-kiss-tcp-a.example.sh](socat-kiss-tcp-a.example.sh) | socat | KISS → TCP :8001 |

Full guide: [docs/GUIDE.md § Terminals](../../docs/GUIDE.md#8-terminals).

## Variables (edit per site)

```bash
KISS=/var/run/baycom-pr/kiss          # single (default)
KISS_A=/var/run/baycom-pr/kiss-a      # dual profile
SERIAL_A=/dev/ttyS0
```

From INI: `python3 tools/baycom_ini_load.py /etc/baycom/baycom-pr.ini`
