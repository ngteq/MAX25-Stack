# MAX25 Terminal (`max25-terminal` / `max25-client`)

Official text-only operator client for `max25d`. Cross-platform via M25/1 (TCP or Unix).

| Doc | Audience |
|-----|----------|
| [docs/MAX25-CLIENT.md](../../docs/MAX25-CLIENT.md) | Developer — M25/1 binding |
| [docs/MAX25-TERMINAL.md](../../docs/MAX25-TERMINAL.md) | Operator — F10 menu, usage |

## Build & test

```bash
./scripts/build.sh
bash stacks/terminal/test-terminal.sh
```

Requires C11 compiler and ncurses (`libncurses-dev` on Linux).

## Run (canonical)

Prefer install/PATH or `build*/bin/max25-terminal`. Tree binary may live at `./max25-terminal` after copy (gitignored).

```bash
max25-terminal -U /run/max25/modem.sock
# with [devices] default set in max25d.ini — no -d needed
# then: CONNECT (F10→6) → SEND …
```

Optional: `-d <id>` / `SET DEVICE` / F10→7 to override the default device.

Daemon: [stacks/daemon/README.md](../daemon/README.md) — **not** under this directory.
