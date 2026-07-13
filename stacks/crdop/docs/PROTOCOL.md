# Protocol

CRDOP (**CB/AR Digital Open Protocol** — MAX25-SoftModem) uses the **native MAX25 M25/KISS host protocol** on TCP :8515 (control) / :8516 (data).

**ARDOP wire format** is optional third-party compat only (`ardop_compat=true`) — never shipped by MAX25.

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

## Optional ARDOP wire compat (external only)

When `ardop_compat=true` on `soft-crdop` or in `crdop.ini` `[compat]`, operators may attach a **third-party ARDOP** host on the same ports. Commands use `\r` termination and ARDOP FEC/ARQ modes.

MAX25 does **not** ship ARDOP sources or binaries. See [plugins/external/ardop/plugin.yaml](../../plugins/external/ardop/plugin.yaml).

Full ARDOP reference: [pflarue/ardop Host_Interface_Commands.md](https://github.com/pflarue/ardop/blob/master/docs/Host_Interface_Commands.md)

## CRDOP launch presets (native)

| Profile | Role |
|---------|------|
| `cb` | Default — CB / 500MAX class |
| `dual` | CB ↔ amateur turnaround |
| `amateur` | Amateur bandwidth class |

Runtime overrides via host TCP or `crdop.ini` always apply.
