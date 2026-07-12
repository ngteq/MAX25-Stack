# Device: BayCom SER12

Kernel bit-banged UART modem (PC-COM). **Not async USB serial** — HyBBX `baycom` plugin, not `packet_radio`.

**Status:** Active (v1). **Operator guide:** [docs/BAYCOM.md](../../../docs/BAYCOM.md)

```bash
./scripts/max25-ctl start --hardware modems --device baycom-ser12
```

Uses `baycom-pr-ctl -c` with `/etc/baycom/baycom-pr.ini` (or `local/baycom-pr.ini`). KISS PTY: `/var/run/baycom-pr/kiss` · Example INI: `share/baycom/baycom-pr.pccom-ttyS0-only.ini.example` · Client profile: `share/clients/baycom-ser12.yaml`
