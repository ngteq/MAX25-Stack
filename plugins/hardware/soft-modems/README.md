# Hardware: Soft Modems

Sound-card software modems — **MAX25-SoftModem (CRDOP — CB/AR Digital Open Protocol)** is the in-house standard. **CRDOP** = **CB/AR Digital Open Protocol** (CB = Citizens Band, AR = Amateur Radio).

| Device | Stack | HyBBX plugin | Protocol | v1 |
|--------|-------|--------------|----------|-----|
| `soft-crdop` | `stacks/crdop` | `crdop` | MAX25-native M25/KISS host | **active** |

## CRDOP vs ARDOP

- **CRDOP (MAX25-SoftModem)** — in-house standard (`stacks/crdop/`). Built by default (`MAX25_BUILD_CRDOP=ON`). Native M25 host protocol on TCP :8515/:8516.
- **ARDOP** — third-party implementations only. **Never** vendored or shipped by MAX25. Optional attach via `ardop_compat=true` — see [plugins/external/README.md](../external/README.md).

## Start (operator)

```bash
./scripts/max25-ctl start --hardware soft-modems --device soft-crdop
```

Then attach HyBBX with `share/hybbx/crdop-host.ini.example`.

CRDOP is acoustically AX.25-compatible at 1200 baud+; host path uses native MAX25 SoftModem TCP (not ARDOP FEC by default).
