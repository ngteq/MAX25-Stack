# AGENTS.md — BayCom PR-Stack

Map for AI agents. Human operators: [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md).

## Purpose

Linux stack for BayCom/ser12, par96 (LPT), and KISS modems. **Single modem default**; dual for **service mode** (HyBBX, 24/7). CB and HAM equal. HyBBX plugin target; terminal AX.25 clients supported.

## Docs (read these only)

| File | Content |
|------|---------|
| [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) | First install — CB, HAM, USB KISS |
| [docs/CONNECTS.md](docs/CONNECTS.md) | Incoming / outgoing examples |
| [docs/GLOSSARY.md](docs/GLOSSARY.md) | Terms |
| [docs/GUIDE.md](docs/GUIDE.md) | Operator commands, stability, service mode |
| [docs/PLUGIN.md](docs/PLUGIN.md) | HyBBX / external attachment |
| [docs/REFERENCE.md](docs/REFERENCE.md) | INI schema, backends, paths, catalog |
| [docs/DEVELOPER.md](docs/DEVELOPER.md) | Build, test, repo layout |

## Tree

```
config/          INI templates → /etc/baycom/
scripts/         baycom-pr-ctl, selftest, test-all, verify-analysis
tools/           C binaries + Python (ini_load, validate, preflight, probe, doctor)
docs/            GETTING-STARTED, CONNECTS, GLOSSARY, GUIDE, PLUGIN, REFERENCE, DEVELOPER, INDEX
```

## Commands

```bash
make all | test | verify | install
sudo baycom-pr-ctl probe | setup | doctor | preflight | start | recover | selftest
sudo baycom-pr-ctl axports apply | show | check
sudo baycom-pr-ctl listen [port] | call <port> <dest>
```

## Runtime paths

- `/etc/baycom/baycom-pr.ini` — site config
- `/etc/baycom/modems.ini` — catalog
- `/var/run/baycom-pr/` — state, KISS links

## Backends

| ID | Driver | Notes |
|----|--------|-------|
| kernel-ser12 | baycom_ser_fdx | Needs UART iobase/irq |
| kernel-par96 | baycom_par | LPT iobase only |
| kiss-serial | baycom_kiss_serial | USB/async |

## Pitfalls

- Wrong IRQ → host freeze; always preflight
- Dual: service mode only — staged start, unique IRQ per UART
- Never userspace serial client on raw UART while driver loaded
- Do not commit `research/`
- Generic Linux only in docs

## Conventions

Minimal diffs; match existing shell/Python style; run `make verify` before commit.
