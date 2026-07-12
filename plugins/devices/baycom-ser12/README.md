# Device: BayCom SER12

Kernel bit-banged UART modem (PC-COM). **Not async USB serial** — use HyBBX `baycom` plugin, not `packet_radio`.

**Status:** Active (v1).

```bash
sudo stacks/baycom-pr/scripts/baycom-pr-ctl probe
sudo stacks/baycom-pr/scripts/baycom-pr-ctl setup
sudo stacks/baycom-pr/scripts/baycom-pr-ctl start
```

KISS PTY: `/var/run/baycom-pr/kiss` · HyBBX INI: `share/hybbx/baycom-ser12-edge.ini.example`
