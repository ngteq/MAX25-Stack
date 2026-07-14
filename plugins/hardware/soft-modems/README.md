# Hardware: Soft Modems

Sound-card software modems — **MAX25-SoftModem (CRDOP)** is the in-house standard. **CRDOP** = stack acronym for **MAX25-SoftModem** (device id `soft-crdop`).

| Device | Stack | HyBBX plugin | Protocol | v1 |
|--------|-------|--------------|----------|-----|
| `soft-crdop` | `stacks/crdop` | `crdop` | MAX25-native M25/KISS host | **active** |

## CRDOP (standard)

**CRDOP (MAX25-SoftModem)** — MAX25-Stack standard (`stacks/crdop/`). Built by default (`MAX25_BUILD_CRDOP=ON`). Native M25 host protocol on TCP :8515/:8516.

**ARDOP-plugin** — optional separate registry for third-party ARDOP host software — see [plugins/external/ardop/README.md](../../external/ardop/README.md). Not coupled to CRDOP.

## Start (operator)

```bash
./scripts/max25-ctl start --hardware soft-modems --device soft-crdop
```

Then attach HyBBX with `share/hybbx/crdop-host.ini.example`.

CRDOP is acoustically AX.25-compatible at 1200 baud+; host path uses native MAX25 SoftModem TCP (M25/KISS).
