# MAX25 Terminal (`max25-terminal` / `max25-client`)

Official text-only operator client for `max25d`. Cross-platform; connects via M25/1 (TCP or Unix).

**Developer documentation:** [docs/MAX25-CLIENT.md](../../docs/MAX25-CLIENT.md)

**Operator documentation:** [docs/MAX25-TERMINAL.md](../../docs/MAX25-TERMINAL.md)

## Build

```bash
make all          # max25-terminal + max25-client symlink
make test
```

Requires a C11 compiler and ncurses (Linux: `libncurses-dev`).

## Run

```bash
./max25-terminal -H <linux-host> -p 7325 --ax25-ui
./max25-terminal -U /run/max25/modem.sock
```

Daemon must be running on Linux: `../daemon/max25d`.
