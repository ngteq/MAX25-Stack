# G3RUH FSK — CRDOP Phase 2 design spec (P1)

**Scope:** 9600–**19200** baud direct FSK. **Hard maximum 19200** — nothing above.

**Prerequisite:** Phase 1 (1200 AFSK) stable. **Not** CB FM mic path.

See [ROADMAP.md](../ROADMAP.md) Phase 2 (P1).

---

## PHY difference from P0

| | 1200 AFSK (P0) | G3RUH FSK (P1) |
|---|----------------|----------------|
| Modulation | Audio tones 1200/2200 Hz | Scrambled baseband FSK |
| RF path | Mic / speaker / line | **Direct** varactor + discriminator |
| CB FM voice channel | ✅ | ❌ |
| VHF backbone | Access only at 1200 | ✅ at 9600–19200 |

---

## Parameters (normative)

| Baud | Peak deviation | RF bandwidth (~-60 dB) |
|------|----------------|------------------------|
| 4800 | ±1.5 kHz | ~8 kHz |
| **9600** | **±3 kHz** | **~20 kHz** |
| **19200** | **±6 kHz** | **~30 kHz** |

CRDOP implements **up to 19200** only.

---

## Radio interface requirements

| Requirement | Detail |
|-------------|--------|
| TX | Direct modulation input (varactor), not acoustic |
| RX | Discriminator / data output, wide IF |
| Filter | Flat amplitude 10 Hz–5 kHz, constant group delay |
| Scrambler | G3RUH compatible — interoperate with standard 9600 peers |

Standard narrow FM voice audio **fails** eye-diagram tests at 9600+.

---

## Software modules (planned)

| Module | Path | Status |
|--------|------|--------|
| Scrambler | `stacks/crdop/lib/g3ruh_scrambler.py` | Not started |
| FSK modulator | `stacks/crdop/lib/g3ruh_modulator.py` | Not started |
| FSK demodulator | `stacks/crdop/lib/g3ruh_demodulator.py` | Not started |
| HDLC/framing | Reuse `hdlc_codec.py` | Done |

Host protocol unchanged — same M25/KISS TCP; baud selected via INI `speed_baud` (future).

---

## Phase 2 exit criteria

1. Loopback with recorded baseband fixtures at 9600.
2. Over-the-air exchange with reference 9600 FSK peer.
3. 19200 optional stretch after 9600 stable.

---

## Out of scope

- 38400+ satellite/backbone rates
- Acoustic coupling at 9600+
- CB 27 MHz deployment
