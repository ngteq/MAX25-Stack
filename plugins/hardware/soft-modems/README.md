# Hardware: Soft Modems

Sound-card software modems — **MAX25-SoftModem (CRDOP — MAX25-SoftModem)** is the in-house standard. **CRDOP** = stack acronym for **MAX25-SoftModem** (device id `soft-crdop`).

| Device | Stack | HyBBX plugin | Protocol | v1 |
|--------|-------|--------------|----------|-----|
| `soft-crdop` | `stacks/crdop` | `crdop` | MAX25-native M25/KISS host | **active** |

## CRDOP vs ARDOP-plugin

- **CRDOP (MAX25-SoftModem)** — MAX25-Stack standard (`stacks/crdop/`). Built by default (`MAX25_BUILD_CRDOP=ON`). Native M25 host protocol on TCP :8515/:8516.
- **ARDOP-plugin** — optional MAX25-Stack plugin for ARDOP wire mode — `ardop_compat=true` — see [plugins/external/ardop/README.md](../../external/ardop/README.md).

## Start (operator)

```bash
./scripts/max25-ctl start --hardware soft-modems --device soft-crdop
```

Then attach HyBBX with `share/hybbx/crdop-host.ini.example`.

CRDOP is acoustically AX.25-compatible at 1200 baud+; host path uses native MAX25 SoftModem TCP (not ARDOP FEC by default).
