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

## Run

```bash
max25-terminal -H <linux-host> -p 7325 --ax25-ui
max25-terminal -U /run/max25/modem.sock
```

Daemon on Linux: [stacks/daemon/README.md](../daemon/README.md).
