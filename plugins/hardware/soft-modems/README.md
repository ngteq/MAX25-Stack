# Hardware: Soft Modems

Sound-card software modems managed by MainAX25 — no serial TNC or kernel BayCom driver.

| Device | Stack | HyBBX plugin | Protocol |
|--------|-------|--------------|----------|
| `soft-crdop` | `stacks/crdop` | `crdop` | ARDOP (CB-first) |

## Build

```bash
./scripts/build.sh
# or: ./scripts/max25-ctl build
```

## Start (operator)

```bash
./scripts/max25-ctl start --hardware soft-modems --device soft-crdop
```

Then attach HyBBX with `share/hybbx/crdop-edge.ini.example`.

**Note:** CRDOP is ARDOP, not AX.25/KISS. It complements packet-radio stacks for CB digital links.
