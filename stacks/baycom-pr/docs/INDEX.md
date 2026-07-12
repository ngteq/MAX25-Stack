# Documentation

**BayCom PR-Stack** · [README](../README.md) · GPL-3.0-or-later

Developed primarily for **HyBBX**; fully supports **terminal AX.25 clients** for CB and Amateur packet (call, incoming, monitor, broadcast-style traffic).

---

## Start here (modem owners)

| Doc | Content |
|-----|---------|
| **[GETTING-STARTED.md](GETTING-STARTED.md)** | Install — CB single, HAM single, USB KISS |
| **[CONNECTS.md](CONNECTS.md)** | Incoming / outgoing — 11 examples |
| **[GLOSSARY.md](GLOSSARY.md)** | Terms in plain language |

---

## Operators

| Doc | Content |
|-----|---------|
| **[GUIDE.md](GUIDE.md)** | Commands, stability, profiles, service mode |
| **[REFERENCE.md](REFERENCE.md)** | INI schema, backends, catalog, paths |
| **[PLUGIN.md](PLUGIN.md)** | HyBBX and external software attachment |

---

## Contributors

| Doc | Content |
|-----|---------|
| **[DEVELOPER.md](DEVELOPER.md)** | Build, test, repo layout |
| **[AGENTS.md](../AGENTS.md)** | AI agent map |

---

## Quick links

| Task | Go to |
|------|-------|
| First modem, never used Linux packet | [GETTING-STARTED](GETTING-STARTED.md) |
| Call someone / wait for calls | [CONNECTS](CONNECTS.md) |
| HyBBX plugin | [PLUGIN](PLUGIN.md) |
| CB or HAM profile | [GETTING-STARTED §A/B](GETTING-STARTED.md) |
| Freeze / recover | [GUIDE §6](GUIDE.md#6-freeze-prevention) |
| Dual modem (24/7 service) | [GUIDE §11](GUIDE.md#11-service-mode-dual-modem) |
| INI fields | [REFERENCE](REFERENCE.md#site-ini-schema) |
| Unknown word | [GLOSSARY](GLOSSARY.md) |

---

## Config templates

| File | Purpose |
|------|---------|
| `config/baycom-pr.ini` | Single modem (default) |
| `config/examples/baycom-pr.cb.ini` | CB 27 MHz |
| `config/examples/baycom-pr.ham.ini` | Amateur HAM |
| `config/examples/baycom-pr.dual.ini` | Service mode — two modems |
| `config/examples/baycom-pr.par96.ini` | LPT 9600 |
| `config/modems.ini` | Hardware catalog |

**Station ID:** `callsign` in site INI.

---

## Archive and kernel

- Superseded docs: [archive/](archive/)
- Driver analysis (optional): [kernel/BAYCOM-DRIVER-ANALYSIS.md](kernel/BAYCOM-DRIVER-ANALYSIS.md)

---

## Release 1.0.0 (stable)

v1.0.0 declares the stack stable for operators and HyBBX integrators.

| Pillar | Delivered in |
|--------|----------------|
| Stack stable, hardware validated | 0.6.x |
| Operator documentation | 0.7.x |
| Jedermann paths + connects + HyBBX plugin contract | 1.0.0 |

Changelog: [CHANGELOG.md](../CHANGELOG.md)
