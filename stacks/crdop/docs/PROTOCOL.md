# Protocol

Normative wire: **[HOST-PROTOCOL-SPEC.md](HOST-PROTOCOL-SPEC.md)** (frozen v1.0.0).

CRDOP (**MAX25-SoftModem** — MAX25-SoftModem) uses the **native MAX25 M25/KISS host protocol** on TCP :8515 (control) / :8516 (data).

**ARDOP-plugin** is an optional MAX25-Stack plugin for ARDOP wire mode (`ardop_compat=true`).

## Stack (default)

```
[Radio] ↔ [audio/ALSA] ↔ audio-dummyd / native modem ↔ TCP :8515 ctrl, :8516 data ↔ max25d
```

## Over-the-air

AX.25-compatible AFSK tones (1200 baud primary, up to 19200 baud design range). See [SOFTMODEM.md](SOFTMODEM.md).

## Host TCP (native M25 — default)

| Port | Role |
|------|------|
| 8515 | Control (line-oriented ASCII, `\n` terminated) |
| 8516 | Data (AX.25 UI body without HDLC/FCS) |

Common commands: `INITIALIZE` · `PROTOCOLMODE KISS` · `MYCALL` · `LISTEN` · `STATUS` · `PING`

Implementation reference: `stacks/crdop/lib/m25_host_protocol.py`

## ARDOP-plugin wire mode

When `ardop_compat=true` on `soft-crdop` or in `crdop.ini` `[compat]`, **ARDOP-plugin** mode uses ARDOP host commands on the same ports (`\r` termination, FEC/ARQ modes).

Registry: [plugins/external/ardop/README.md](../../../plugins/external/ardop/README.md)

ARDOP reference: [pflarue/ardop Host_Interface_Commands.md](https://github.com/pflarue/ardop/blob/master/docs/Host_Interface_Commands.md)

## CRDOP launch presets (native)

| Profile | Role |
|---------|------|
| `cb` | Default — CB / 500MAX class |
| `dual` | CB ↔ amateur turnaround |
| `amateur` | Amateur bandwidth class |

Runtime overrides via host TCP or `crdop.ini` always apply.
