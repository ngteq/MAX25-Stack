# TNC2C reference (example profile)

Example profile for a Landolt TNC2C with **19200 8N1** host link and **2400** radio AFSK. Adjust for your hardware.

## Serial (host)

| Parameter | Example |
|-----------|---------|
| Device | `/dev/ttyUSB0` |
| Baud | 19200 |
| Format | 8N1 |
| RTS/DTR | Required for boot-wait |

## Radio (typical CB packet)

| Parameter | Example |
|-----------|---------|
| Modem | TCM3105 |
| Radio baud | 2400 |
| Band | CB |
| Duplex | Half |

## Config file

`stacks/tncs/tnc2c-serial.env` — copy and edit device/baud for your station.

## Tool matrix

| Tool | Use |
|------|-----|
| `tnc2c-boot-wait.sh` | Host mode after power-on |
| `tnc2c-host-reset.sh` | Recovery without power cycle |
| `tnc2c-autotest.sh` | Quick 19200-8N1 probe |
| `tnc2c-health.sh` | Full check, no TX |
| `tnc2c-integration-test.sh` | Post boot-wait HyBBX gate |
| `tnc2c-listen.sh` | Passive monitor |
| `tnc2c-probe` | Port scan utility |

## HyBBX INI snippet

Use `share/hybbx/tnc2c-host.ini.example` — set `device`, `mycall`, and RF fields for your station.

HyBBX TNC profiles: [hyBBX docs/TNCS.md](https://github.com/ngteq/hyBBX/blob/main/docs/TNCS.md)
