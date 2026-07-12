# BayCom PR-Stack

Linux stack for **BayCom-compatible** packet modems (ser12, LPT par96, USB KISS). Brings one radio link online, exposes **KISS** and **AX.25** for connects.

Developed **primarily for HyBBX** (plugin). Works fully with **terminal clients** — call, be called, monitor, and usual CB and Amateur packet traffic.

**Repository:** [github.com/ngteq/BayCom_PR-Stack](https://github.com/ngteq/BayCom_PR-Stack) · **License:** [GPL-3.0-or-later](LICENSE) · **Stable:** v1.0.0

---

## I have a modem — start here

1. [Getting started](docs/GETTING-STARTED.md) — install (CB · HAM · USB KISS)
2. [Packet connects](docs/CONNECTS.md) — incoming / outgoing examples
3. [Glossary](docs/GLOSSARY.md) — terms

Your **station ID** is `callsign` in `/etc/baycom/baycom-pr.ini`.

---

## Quick install

```bash
make all && make test
sudo make install
sudo baycom-pr-ctl probe && sudo baycom-pr-ctl setup
sudo baycom-pr-ctl doctor && sudo baycom-pr-ctl start
sudo baycom-pr-ctl selftest
```

`setup` and `start` sync AX.25 ports from your INI automatically. Connect — [CONNECTS.md](docs/CONNECTS.md).

---

## Documentation

| Audience | Docs |
|----------|------|
| Modem owners | [GETTING-STARTED](docs/GETTING-STARTED.md) · [CONNECTS](docs/CONNECTS.md) · [GLOSSARY](docs/GLOSSARY.md) |
| Operators | [GUIDE](docs/GUIDE.md) · [REFERENCE](docs/REFERENCE.md) |
| HyBBX / integrators | [PLUGIN](docs/PLUGIN.md) |
| Contributors | [DEVELOPER](docs/DEVELOPER.md) · [CONTRIBUTING](CONTRIBUTING.md) |

Full index: [docs/INDEX.md](docs/INDEX.md)

---

## Profiles

| Profile | Template | Use |
|---------|----------|-----|
| Single (default) | `config/baycom-pr.ini` | One radio — everyone starts here |
| CB 27 MHz | `config/examples/baycom-pr.cb.ini` | CB packet |
| Amateur HAM | `config/examples/baycom-pr.ham.ini` | VHF/UHF packet |
| USB KISS | [GETTING-STARTED §C](docs/GETTING-STARTED.md#path-c--usb-kiss-no-kernel-baycom-driver) | USB TNC |
| Service dual | `config/examples/baycom-pr.dual.ini` | Two modems, 24/7 — HyBBX / automation only |
| LPT par96 | `config/examples/baycom-pr.par96.ini` | 9600 bd parallel port |

---

## Backends

| Backend | Hardware |
|---------|----------|
| kernel-ser12 | PC-COM, BayCom on UART (`/dev/ttyS*`) |
| kernel-par96 | LPT 9600 (`baycom_par`) |
| kiss-serial | USB KISS (`/dev/ttyUSB*`) |

---

## Commands

`probe` · `setup` · `doctor` · `preflight` · `start` · `stop` · `recover` · `status` · `check` · `selftest` · `axports` · `listen` · `call`

Details: [docs/GUIDE.md](docs/GUIDE.md)

---

## For contributors / AI

[AGENTS.md](AGENTS.md) · `make help`
