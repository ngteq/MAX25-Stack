# Device: BayCom SER12

Kernel bit-banged UART modem (PC-COM, classic BayCom on COM port).

**Not async serial** — do not use `packet_radio` for native SER12; use HyBBX `baycom` plugin or stack KISS bridge.

```bash
sudo stacks/baycom-pr/scripts/baycom-pr-ctl probe
sudo stacks/baycom-pr/scripts/baycom-pr-ctl setup
sudo stacks/baycom-pr/scripts/baycom-pr-ctl start
```

KISS PTY: `/var/run/baycom-pr/kiss`
