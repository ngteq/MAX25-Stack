# ARDOP-plugin

Optional **MAX25-Stack plugin** for ARDOP host wire mode on `soft-crdop`.

## When to use

| Mode | Use |
|------|-----|
| **CRDOP (default)** | Native MAX25-SoftModem — M25/KISS on :8515/:8516 |
| **ARDOP-plugin** | ARDOP host wire — set `ardop_compat=true` |

## Configuration

```ini
[device.soft-crdop]
ardop_compat = yes
host = 127.0.0.1
port = 8515
```

CRDOP INI (`crdop.ini`):

```ini
[compat]
ardop_compat = yes
```

## Metadata

[plugin.yaml](plugin.yaml) · [../README.md](../README.md)
