# Hardware: Modems

BayCom PR-Stack — kernel SER12/PAR96 and KISS serial. Merged from **baycom_pr-Stack** (`pc-com`).

## Stack location

`stacks/baycom-pr/` — `baycom-pr-ctl`, config templates, tools, docs.

## HyBBX

Use HyBBX `baycom` plugin (`-DHYBBX_PLUGIN_BAYCOM=ON`). Stack must be **running** before HyBBX starts.

| Backend | HyBBX `backend` | HyBBX `mode` |
|---------|-----------------|--------------|
| SER12 | `kernel` | `ser12*` |
| PAR96 | `kernel` | `par96` |
| USB KISS | `kiss` | — |

## Quick start

```bash
make -C stacks/baycom-pr all
sudo make -C stacks/baycom-pr install
sudo baycom-pr-ctl probe && sudo baycom-pr-ctl start
```

## Docs

- `stacks/baycom-pr/docs/PLUGIN.md` — HyBBX contract
- `stacks/baycom-pr/docs/GUIDE.md` — operator commands
