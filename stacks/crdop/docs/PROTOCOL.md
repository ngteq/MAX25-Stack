# Protocol

Normative wire: **[HOST-PROTOCOL-SPEC.md](HOST-PROTOCOL-SPEC.md)** (frozen v1.0.0).

CRDOP (**MAX25-SoftModem**) uses the **native MAX25 M25/KISS host protocol** on TCP :8515 (control) / :8516 (data).

## Stack (default)

```
[Radio] ↔ [audio/ALSA] ↔ audio-dummyd / native modem ↔ TCP :8515 ctrl, :8516 data ↔ max25d
```

## Over-the-air

AX.25-compatible AFSK tones (1200 baud primary, up to 19200 baud design range). See [SOFTMODEM.md](SOFTMODEM.md).

## Host TCP (native M25)

| Port | Role |
|------|------|
| 8515 | Control (line-oriented ASCII, `\n` terminated) |
| 8516 | Data (AX.25 UI body without HDLC/FCS) |

Common commands: `INITIALIZE` · `PROTOCOLMODE KISS` · `MYCALL` · `LISTEN` · `STATUS` · `PING`

Implementation reference: `stacks/crdop/lib/m25_host_protocol.py`

## CRDOP launch presets

| Profile | Role |
|---------|------|
| `cb` | Default — CB / 500MAX class |
| `dual` | CB ↔ amateur turnaround |
| `amateur` | Amateur bandwidth class |

Runtime overrides via host TCP or `crdop.ini` always apply.
