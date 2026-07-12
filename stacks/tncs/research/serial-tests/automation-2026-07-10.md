# Automatisierte Tests — 2026-07-10 Abend

## Manuell bestätigt (User)

| Test | Ergebnis |
|------|----------|
| minicom 19200 8N1, `kiss off` + `INFO` | **Firmware 2.7b Banner**, Checksum DC0A |
| `tnc2c-boot-wait.sh` + Strom-Zyklus | **OK: HOST** — passives Boot-Banner |

## Automatisiert (ohne frischen Strom-Reset)

| Tool | Zeit | Ergebnis |
|------|------|----------|
| `tnc2c-health.sh` | ~44s | **DEGRADED** — ECHO auf 19200-8N1 |
| `tnc2c-integration-test.sh` | ~9s | **DEGRADED** — host-check ECHO/GARBAGE |
| `tnc2c-host-reset.sh` | ~12s | ECHO (ohne Power-Cycle) |

**Erwartung:** Ohne `boot-wait` + Strom-Zyklus ist ECHO normal — kein Hardware-Defekt.

## HyBBX-Readiness

- INI: `hybbx-tnc2c.ini` — 19200 8n1, tcm3105, CB K24
- Doku: `docs/HYBBX-TNC2C.md`
- Nächster Schritt: boot-wait → integration-test → HyBBX starten
