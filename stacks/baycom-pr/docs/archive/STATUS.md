# Project status — facts vs deep analysis

**Target:** v0.6.0 (push only after reference station hardware OK) · **Updated:** 2026-07-08

## Offline verification (this machine)

| Check | Result |
|-------|--------|
| `make test` | **PASS** |
| `bash scripts/verify-analysis.sh` | **PASS** (P0 checklist) |
| `baycom-pr-ctl probe` | No UART/USB/LPT hardware in sandbox |
| `doctor --offline` | **PASS** (config + modules) |
| `doctor` (full) | Fails without UART — **expected** |

## Deep analysis → implementation map

| Analysis source | Claim | Status |
|-----------------|-------|--------|
| UX-AUTOMATION | probe/setup/doctor | **Done** (`055e28a`) |
| UX-AUTOMATION | Minimal INI (no manual iobase/irq) | **Done** |
| UX-AUTOMATION | Safe install-root preflight | **Done** |
| STABILITY | preflight / recover / IRQ watch | **Done** (`b97b2d6`) |
| STABILITY | Staged dual start | **Done** |
| KERNEL-ANALYSIS | Wrong IRQ = freeze P0 | **Mitigated userspace**; kernel unpatched |
| KERNEL-ANALYSIS | No BayCom USB driver | **By design** — use kiss-serial |
| PARPORT | baycom_par userspace | **Done** (`c463162`) |
| /etc/baycom | All config under one tree | **Done** (`de48c19`) |

## Operator time (design goal)

| Path | Commands | ~Time |
|------|----------|-------|
| First install | `make install` → `probe` → `setup` → `doctor` → `start` | **3–5 min** |
| Daily check | `baycom-pr-ctl status` or `check` | **30 s** |
| After freeze | `recover` → `doctor` → `start` | **2 min** |
| Dual upgrade | Copy dual.ini → `setup` → `preflight` → `start` | **+5 min** |

## Service profiles (CB = HAM stack)

| Profile | Template | Default |
|---------|----------|---------|
| Single ser12 | `config/baycom-pr.ini` | **yes** |
| CB 27 MHz | `config/examples/baycom-pr.cb.ini` | optional |
| Amateur HAM | `config/examples/baycom-pr.ham.ini` | optional |
| Dual (freeze-safe) | `config/examples/baycom-pr.dual.ini` | optional |
| par96 LPT | `config/examples/baycom-pr.par96.ini` | optional |
| USB KISS | comments in `baycom-pr.ini` | optional |

Doc: [RADIO-SERVICES.md](RADIO-SERVICES.md)

## Freeze protection stack (7 layers)

1. `validate` — schema, duplicate IRQ/iobase  
2. `preflight` — setserial match, lsof, parport  
3. `setup` — auto-fill from probe  
4. `staged dual probe` — one UART/LPT at a time  
5. `post_start_irq_watch` — auto-stop >80k IRQ/s  
6. `recover` — post-crash cleanup  
7. `check-freeze.sh` — diagnostics report  

## Hardware still required (reference station)

- [ ] `sudo baycom-pr-ctl doctor` — zero errors  
- [ ] `sudo baycom-pr-ctl selftest` — full offline suite  
- [ ] Single modem stable 24h — no freeze  
- [ ] Dual modem (if needed) — preflight + staged start  
- [ ] On-air RX/TX — operator responsibility  

## Git (local only)

Recent commits on `main` (not pushed): freeze prevention, /etc/baycom, DX, kernel analysis, parport, UX automation, this status batch.

## P1 backlog (post-v0.6.0)

- systemd unit + ExecStartPre=preflight  
- udev USB KISS hotplug  
- axports auto-merge helper  
- `doctor --json`  

See [UX-AUTOMATION-ANALYSIS.md](UX-AUTOMATION-ANALYSIS.md).
