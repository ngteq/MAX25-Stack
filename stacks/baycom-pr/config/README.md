# Configuration

Templates install to **`/etc/baycom/`**.

| Source | Install target |
|--------|----------------|
| `baycom-pr.ini` | `/etc/baycom/baycom-pr.ini` (single default) |
| `modems.ini` | `/etc/baycom/modems.ini` |
| `examples/*.ini` | `/etc/baycom/examples/` |
| `axports/*.snippet` | `/etc/baycom/axports/` |
| `minicom/*` | `/etc/baycom/minicom/` |

## Examples

| File | Use |
|------|-----|
| `baycom-pr.ini` | Single modem |
| `examples/baycom-pr.cb.ini` | CB 27 MHz |
| `examples/baycom-pr.ham.ini` | Amateur HAM |
| `examples/baycom-pr.dual.ini` | Service mode — two modems (HyBBX / 24/7) |
| `examples/baycom-pr.par96.ini` | LPT 9600 |
| `examples/baycom-pr.picpar.ini` | LPT picpar |

Site INI references catalog IDs from `modems.ini` via `catalog = <id>`.

Docs: [docs/GETTING-STARTED.md](../docs/GETTING-STARTED.md) · [docs/REFERENCE.md](../docs/REFERENCE.md)
