# Protocol

CRDOP speaks **standard ARDOP** — same as ardopcf. Product name and launch presets differ; air and host layers do not.

## Stack

```
[Radio] ↔ [audio] ↔ crdopc (DSP, ARQ) ↔ TCP :8515 ctrl, :8516 data ↔ [host app]
```

## Over-the-air

From ardopcf: ARQ, bandwidth negotiation (`200MAX`–`2000MAX`), CRC, retransmission. CRDOP profiles only set **initial** `-H` defaults.

## Host TCP

| Port | Role |
|------|------|
| 8515 | Control |
| 8516 | Data |

CRC-16 **`0x8810`**. Commands terminated with `CR`.

Common commands: `INITIALIZE` · `PROTOCOLMODE ARQ` · `ARQBW` · `MYCALL` · `LISTEN` · `ARQCALL` · `EXTRADELAY` · `BUSYDET` · `DISCONNECT`

Full reference: [pflarue/ardop Host_Interface_Commands.md](https://github.com/pflarue/ardop/blob/master/docs/Host_Interface_Commands.md)

## CRDOP launch presets

| Profile | Default `-H` extras |
|---------|---------------------|
| `cb` | `500MAX`, `BUSYDET 1`, `EXTRADELAY 150`, `ARQTIMEOUT 30` |
| `dual` | `500MAX`, `BUSYDET 1`, `EXTRADELAY 200`, `ARQTIMEOUT 35` |
| `amateur` | `1000MAX`, `EXTRADELAY 80`, `ARQTIMEOUT 45` |

Runtime overrides via host TCP or `-H` on the command line always apply.
