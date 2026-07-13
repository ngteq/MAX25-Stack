# CRDOP FEC and duplex — implementation spec

**Principle:** *Send more often with shorter frames rather than one long payload.*

**Vault source:** `0-RESEARCHES/projects/max25-stack/2026-07-13-crdop-fec-duplex-strategy.md`, `l2-fec-protocols.md`.

**Status:** **CRDOP-CUR999** — L1 optional FEC **planned**; operator-layer strategy **active now**.

---

## Layer model

| Layer | Mechanism | v1.0.0 |
|-------|-----------|--------|
| **L3 Application** | Short beacons, staggered intervals | HyBBX / `max25d.ini` |
| **L2 AX.25** | UI = no ARQ; I-frames optional ARQ via host | `ax25_codec.py` |
| **L1 Modem** | CRC-16-CCITT mandatory; optional repeat/FEC blocks | `hdlc_codec.py` — CRC done |
| **PHY** | Bell 202 AFSK (P0) | `afsk_*` |

---

## Half-duplex (CB default)

| Parameter | Value | INI / host |
|-----------|-------|------------|
| Duplex | half | `[modem] duplex = half` |
| CSMA persist | 255 | KISS `0x02` / CB profile |
| Extra TX delay | 150 ms class | `extra_delay_ms` / `EXTRADELAY` |
| Max UI info | **≤128 bytes** recommended | Application |
| PTT | explicit | No VOX on CB |

### Retransmission strategy (no L2 ARQ on UI)

1. Prefer **N small identical beacons** over one large burst.
2. Stagger dual-radio sites (`ax25_auto_interval` + offset).
3. Optional L1: **2–3 repeats** of same short codeword vs one RS block >256 B.

---

## Full-duplex

| Parameter | Value |
|-----------|-------|
| `duplex` | `full` |
| `EXTRADELAY` | `0` |
| FEC | Stronger codes allowed when bandwidth permits |
| Audio | Full-duplex sound card; echo control required |

---

## Reference protocols (not on-air targets)

| Protocol | Lesson for CRDOP |
|----------|------------------|
| **FX.25** | RS wrapper around AX.25; bit-stuffing hurts naive FEC |
| **IL2P** | No bit-stuffing; packet-sync scramble — reference for future L2 |
| **VARA DSP** | Multi-stage FEC — PHY reference only |

---

## Planned L1 FEC (post Phase 1)

| Requirement | Target |
|-------------|--------|
| Block size | ≤64 B payload + CRC per repeat unit |
| Latency | <300 ms added on 1200 bd half-duplex |
| Compatibility | Plain AX.25 receivers must not break (FX.25-style optional path) |
| Test | AWGN + FM clip simulator before on-air |

### INI keys (future)

```ini
[fec]
enabled = no          # default off v1.0.0
repeat_count = 0      # 0 = no repeat; 2–3 for CB marginal
profile = half        # half | full
```

---

## CB 1200 parameters (normative operator)

| Parameter | Value |
|-----------|-------|
| Baud | 1200 |
| Modulation | Bell 202 (1200/2200 Hz) |
| Frame | AX.25 UI |
| persist | 255 |
| Beacon | 300 s + stagger (site INI) |

---

## Implementation checklist

- [x] CRC-16 in `hdlc_codec.py`
- [x] Duplex INI keys in `crdop.ini.example`
- [ ] `fec.enabled` INI + launcher
- [ ] Offline BER vs frame-length simulator
- [ ] Document measured CB SNR thresholds (field)
