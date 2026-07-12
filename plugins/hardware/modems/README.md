# Hardware: Modems

BayCom PR-Stack — kernel SER12/PAR96 and KISS serial (`stacks/baycom-pr/`).

## HyBBX

`baycom` plugin (`-DHYBBX_PLUGIN_BAYCOM=ON`). Stack must be **running** before HyBBX starts.

| Backend | HyBBX `backend` | HyBBX `mode` |
|---------|-----------------|--------------|
| SER12 | `kernel` | `ser12*` |
| PAR96 | `kernel` | `par96` |
| USB KISS | `kiss` | — |

## Quick start

```bash
./scripts/build.sh
sudo make -C stacks/baycom-pr install
sudo baycom-pr-ctl probe && sudo baycom-pr-ctl start
```

## Docs

- [stacks/baycom-pr/docs/PLUGIN.md](../../stacks/baycom-pr/docs/PLUGIN.md)
- [stacks/baycom-pr/docs/GETTING-STARTED.md](../../stacks/baycom-pr/docs/GETTING-STARTED.md)
