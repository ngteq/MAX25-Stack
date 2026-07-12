# Betriebsform: HyBBX Edge

RF edge on a HyBBX **Secondary** node. MainAX25 (MAX25) prepares hardware; HyBBX opens KISS/serial and bridges AX.25 to Main over HBX.

## TNC path (packet_radio)

1. Stop HyBBX and minicom
2. `stacks/tncs/tnc2c-boot-wait.sh` → OK: HOST
3. `stacks/tncs/tnc2c-integration-test.sh`
4. Start HyBBX with `stacks/tncs/hybbx-tnc2c.ini` snippet

## BayCom path (baycom plugin)

1. `sudo stacks/baycom-pr/scripts/baycom-pr-ctl preflight`
2. `sudo stacks/baycom-pr/scripts/baycom-pr-ctl start`
3. HyBBX `[transport.baycom1]` → KISS at `/var/run/baycom-pr/kiss`

Full contract: [docs/HYBBX.md](../../docs/HYBBX.md)
