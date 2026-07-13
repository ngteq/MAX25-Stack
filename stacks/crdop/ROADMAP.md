# MAX25-SoftModem (CRDOP) — development roadmap

> **Static rule:** **CRDOP** = **CB/AR Digital Open Protocol** (CB = Citizens Band, AR = Amateur Radio). Authoritative everywhere CRDOP is named in MAX25-Stack.

**Product version:** **CRDOP-CUR999** (`CUR999` in `stacks/crdop/VERSION`) — pre-release development track until **v0.5** ships.

**Stack dependency:** CRDOP sources live in `stacks/crdop/` and are **standalone-capable** in principle, but **MAX25-Stack is required for integration** (build, `max25d`, INI, operator tooling) until **CRDOP-v1.0.0** (or later) marks a mature standalone release. Current stack product: **MAX25-Stack-v1.0.0**.

**Nature:** MAX25 in-house development — open development and test program for the kernel-ALSA sound-card modem. **ARDOP-plugin** is optional; CRDOP is the standard modem.

**Research synthesis:** 2026-07-13 — full vault analysis under `/home/akb/Code/0-RESEARCHES/` (see [Research vault coverage](#research-vault-coverage)). Actionable priorities below; depth stays in vault — **no duplicate re-copy** into this repo.

---

## Protocol taxonomy (research catalog)

| Class | Description | CRDOP relation |
|-------|-------------|----------------|
| **A** | Classic AX.25 packet (HDLC, frequency-toggle line code) | **P0/P1/P2 targets** — 1200 AFSK, G3RUH, 300 HF |
| **B** | AX.25 + FEC extension | **Reference** — FX.25 informs FEC block design |
| **C** | New L2 (not AX.25 on-air) | **Reference** — IL2P lessons (no bit-stuffing, RS FEC) |
| **D** | HF/VHF data modems (Winlink ecosystem) | **Out of scope** on-air — **ARDOP-plugin** optional for ARDOP wire |
| **E** | Keyboard/chat modes (PSK31, RTTY, …) | **Out of scope** — boundary only |

---

## MAX25-Stack integration (until CRDOP-v1.0.0+)

| Topic | Policy |
|-------|--------|
| **Source tree** | All CRDOP sources in `stacks/crdop/` — standalone CMake possible; **operator integration via MAX25-Stack** until mature **CRDOP-v1.0.0** (or later) |
| **Build** | `MAX25_BUILD_CRDOP=ON` default — installs launcher, `lib/`, tools, INI |
| **Daemon** | `max25d` → `CrdopTcpBackend` / `AudioDummyBackend` — see [docs/MAX25-USAGE.md](docs/MAX25-USAGE.md) |
| **AX.25 runtime** | Native `ax25_codec.py` in MAX25 — no libax25 bundle in releases |
| **HyBBX** | External consumer — serial ownership boundary; CRDOP via host TCP attach |
| **Docs entry** | [docs/INDEX.md](docs/INDEX.md) · project rule [docs/CRDOP.md](../../docs/CRDOP.md) |

Vault: `projects/integration/2026-07-12-max25-hybbx-boundary-final.md`

---

## Current phase: development and test

| Area | Status |
|------|--------|
| MAX25-Stack standard build/install (`MAX25_BUILD_CRDOP=ON`) | **Done** |
| `max25d` `crdop-tcp` backend + offline tests | **Done** |
| INI scaffold, launcher (`scripts/crdopc`), HyBBX attach examples | **Done** |
| Native modem DSP — 1200 baud Bell 202 AFSK (`stacks/crdop/lib/`) | **In progress** |
| Acoustic AX.25 validation vs reference 1200 AFSK paths | **In progress** |
| Half- and full-duplex operator paths + FEC strategy | **In progress** |
| Open hardware interface documentation | **In progress** |
| G3RUH 9600–19200 (direct FSK rig path) | **Planned** (Phase 2) |
| 300 baud HF AFSK | **Optional** (Phase 3) |
| Speeds >19200 baud | **Out of scope** |

---

## Modulation priority matrix

Synthesized from research catalog — implementation order for CRDOP native DSP.

| Priority | Mode | Modulation | Baud | RF path | Bands | CRDOP target |
|----------|------|------------|------|---------|-------|--------------|
| **P0** | AX.25 Packet | **AFSK Bell 202** (1200/2200 Hz) | **1200** | Audio AFSK (Mic/Spkr/Line) | **CB, VHF/UHF** | **Primary on-air** |
| **P0** | FEC + duplex profiles | Short frames, frequent TX | 1200 | same | CB, VHF | **Strategy** (see below) |
| **P1** | AX.25 Packet | **G3RUH FSK/GMSK** (scrambled baseband) | **9600–19200** | **Direct FSK** (varactor + discriminator) | VHF/UHF backbone | **Hard max 19200** |
| **P2** | AX.25 Packet | AFSK/FSK tone pairs | **300** | SSB audio (USB/LSB) | HF | **Optional** |
| — | 2400/4800 AFSK | V.26/V.27 class | 2400–4800 | Audio | VHF | Low priority incremental |
| 📋 | FX.25 / IL2P | FEC wrappers / new L2 | 1200+ | Audio or FSK PHY | VHF/HF | **Reference only** — inform FEC design |
| ❌ | VARA / PACTOR / WINMOR | Proprietary DSP | various | Audio / SSB / hardware | HF/VHF/CB | **Out of scope** |
| 📋 | ARDOP | 4FSK/PSK/QAM Winlink modes | adaptiv | Soundcard SSB | HF/VHF | **ARDOP-plugin** (`ardop_compat=true`) |

**Rule:** CRDOP on-air goal is **AX.25-compatible PHY + framing** at P0/P1/P2. Winlink-class protocols (VARA, PACTOR, ARDOP OTA) are **not** CRDOP targets.

---

## RF path matrix

What CRDOP implements per physical interface — hardware choice drives baud ceiling.

| RF path | Connection | Practical max baud | CB | Amateur (VHF/UHF) | Amateur (HF) | CRDOP phase |
|---------|------------|-------------------|-----|-------------------|--------------|-------------|
| **Audio AFSK** | Mic IN / Speaker OUT / Line | ~4800 theory; **1200 field** | ✅ K24/K25 | ✅ APRS, digipeater access | — | **Phase 0–1** (P0) |
| **Audio wide** | Line, de-emphasis off | up to ~9600 (difficult) | rare | experimental | — | not primary |
| **Direct FSK** | Varactor TX + FM discriminator RX | **9600–19200** | ❌ | ✅ backbone, sat | ❌ | **Phase 2** (P1) |
| **SSB audio** | USB/LSB suppressed carrier | **300** packet; kHz-BW modes separate | ❌ | 10 m APRS exception | ✅ | **Phase 3** (P2 optional) |

**CB note:** 9600+ G3RUH requires direct RF modulation and wide IF — standard CB FM rigs are **not** 9k6-ready. CRDOP does **not** target high baud on 27 MHz.

---

## Band context

### CB (27 MHz CEPT)

| Item | Detail |
|------|--------|
| **Primary channel** | **K24** (27.235 MHz) — Packet QSO, APRS-like traffic |
| **Net / forward** | **K25** (27.245 MHz) — nets, data traffic; proprietary FM-narrow DSP modes appear in practice (reference only — not CRDOP OTA) |
| **Legal (brief)** | EN 300 433 / ECC (11)03 — voice service primary; FM max **4 W** ERP typical; **data tolerated or explicit** on K24/K25 in several EU administrations. Operator responsibility. |
| **CRDOP mode** | **1200 AFSK Bell 202**, half-duplex, `persist=255`, short UI frames |
| **Why not 9600+** | CB rigs lack direct FSK port and wide-IF path; FM voice channel ≈3 kHz — fits 1200/2200 Hz, not G3RUH |

### VHF/UHF (2 m, 70 cm, …)

| Application | Baud | Modulation | CRDOP |
|-------------|------|------------|-------|
| **APRS**, packet BBS, digipeater **access** | 1200 | AFSK Bell 202 | **P0** — acoustic/line |
| Digipeater **backbone**, satellite | 9600–19200 | G3RUH FSK | **P1** — requires data-port radio |
| IL2P | 1200/2400 | BPSK/QPSK audio | 📋 reference |
| FX.25 | 1200+ | AX.25 + RS FEC wrapper | 📋 reference for FEC block sizing |

### HF (160 m – 10 m)

| Item | Detail |
|------|--------|
| **Standard packet** | **300 baud** AFSK/FSK, **200 Hz shift** |
| **Common tone pairs** | 1600/1800 Hz (common default), 2110/2310 Hz, others — dial frequency must match pair |
| **10 m exception** | 1200 AFSK on FM/USB for APRS — same PHY as VHF |
| **Winlink boundary** | Proprietary HF mail modems = **separate protocol ecosystems** — not CRDOP OTA goals |
| **CRDOP** | **P2 optional** — 300 bd after P0/P1 stable; SSB USB/LSB audio path |

### Satellite / space (reference)

| Application | Baud | Modulation | CRDOP |
|-------------|------|------------|-------|
| Legacy FM packet | 1200 | AFSK Bell 202 | P0 PHY same |
| Pacsat / wide-IF links | 9600–38400+ | G3RUH FSK/GMSK | P1 extended; >19200 out of scope |

---

## Layer model

CRDOP splits **host integration** from **on-air PHY**. Code mapping to `stacks/crdop/lib/`:

```
Application (APRS, BBS, HyBBX, max25-terminal)
    ↓
AX.25 v2.0 (UI / I-frames)          ← stacks/daemon/ax25_codec.py
    ↓
HDLC + frequency-toggle + CRC-16    ← hdlc_codec.py (+ bell202_line_code.py)
    ↓
Modem PHY (AFSK / future G3RUH)    ← afsk_modulator.py, afsk_demodulator.py
    ↓
MAX25 sound-proxy → kernel ALSA     ← sound_proxy.py (+ include/crdop/sound_proxy.h scaffold)
    ↓
Radio (FM audio / direct FSK / SSB)
```

| Layer | Responsibility | Module / tool |
|-------|----------------|---------------|
| **L2 AX.25** | Addresses, UI body, FCS semantics | `ax25_codec.py` (daemon), used by `acoustic_engine.py` |
| **Framing** | HDLC flags `0x7E`, bit-stuffing, CRC-16-CCITT | `hdlc_codec.py` |
| **Line code** | Bell 202 frequency-toggle (bit 0 → tone change) | `bell202_line_code.py` |
| **PHY 1200** | Continuous-phase AFSK 1200/2200 Hz, Goertzel demod | `afsk_modulator.py`, `afsk_demodulator.py` |
| **PHY 9k6+** | G3RUH scrambler + FSK — **not yet in lib/** | planned Phase 2 |
| **PHY 300 HF** | 200 Hz shift tone pairs — **not yet in lib/** | planned Phase 3 |
| **Audio I/O** | ALSA capture/playback, no PulseAudio | `sound_proxy.py` |
| **Bench integration** | Loopback encode/decode, sniffer | `acoustic_engine.py` |
| **Host TCP** | M25-family ctrl + KISS-semantics data | `m25_host_protocol.py` → `audio-dummyd` |
| **Operator tools** | Sniff, calibrate mark/space | `tools/max25-signal-sniffer` |

**Host vs on-air:** `m25_host_protocol.py` carries AX.25 UI **without** HDLC on the data port; `acoustic_engine.encode_ax25_ui()` builds full on-air HDLC + AFSK. Do not confuse MAX25 TCP host with ARDOP FEC/ARQ wire modes.

---

## FEC, duplex & retransmission strategy

**Leitprinzip:** *Lieber öfter senden als oft lange.*

Packet on CB/VHF (poor SNR, QRM, half-duplex collisions) favours **short UI frames** and **frequent repetition** over long payloads and heavy block FEC.

### Half-duplex (CB default)

| Aspect | Strategy |
|--------|----------|
| Channel access | CSMA + persist — CB: **`persist=255`** |
| TX slot | Short UI frames; minimal but stable TXDELAY/TXTAIL |
| FEC | Shorter codewords; optional 2–3 repeats vs one large block |
| Retransmit | Application/beacon: **send more often** with small payloads (≤128 B info) |
| PTT | Explicit — VOX off on CB |
| INI | `duplex = half`, `EXTRADELAY 150` (CB profile) |

### Full-duplex

| Aspect | Strategy |
|--------|----------|
| Channel | Simultaneous TX/RX — no CSMA |
| FEC | Stronger codes possible when bandwidth allows |
| Audio | Echo suppression / separate paths — full-duplex sound card |
| INI | `duplex = full`, `EXTRADELAY 0` |

### FEC layers

| Level | Mechanism | CRDOP status |
|-------|-----------|--------------|
| **L1 modem** | CRC-16-CCITT (mandatory), preamble sync | **Done** in `hdlc_codec.py` |
| **L1 optional** | Lightweight FEC for short blocks | **Planned** — offline AWGN simulator |
| **L2 AX.25** | UI = no ARQ; I-frames = host may ARQ | Host policy |
| **Application** | Frequent beacons, staggered dual-TNC | HyBBX / max25d INI |
| **Reference** | FX.25 (RS wrapper), IL2P (new L2) | Inform design; not mandatory on-air |

### FEC design takeaways (from vault `l2-fec-protocols.md`)

| Source | Lesson for CRDOP |
|--------|------------------|
| **FX.25** | Reed-Solomon FEC **wrapper** around AX.25 — backward-compatible idea; AX.25 bit-stuffing weakens naive FEC |
| **IL2P** | Eliminates bit-stuffing; packet-sync LFSR scramble; RS FEC — **reference** for future optional L2, not P0 on-air |
| **Operator** | UI frames have no L2-ARQ — reliability via **short payloads + frequent TX** before heavy block FEC |
| **VARA / IL2P DSP** | Multi-stage FEC and adaptive rate — **reference for DSP strategy only**, not protocol target |

### Host-protocol alignment

| Component | Status |
|-----------|--------|
| Spec | **[HOST-PROTOCOL-SPEC.md](docs/HOST-PROTOCOL-SPEC.md)** — frozen v1.0.0 |
| `max25d CrdopTcpBackend` (default) | `PROTOCOLMODE KISS`, `[CRDOP AX25 UI …]` display |
| `m25_host_protocol.py` | Defaults **8515/8516** — matches `crdopc` INI |
| `audio-dummyd` bench | Same ports via CLI; `audio-dummy` max25d **host** mode may use **8520** when :8515 busy |
| `ardop_compat=true` | **ARDOP-plugin** wire mode — not default |

---

## Implementation status (`stacks/crdop/lib/`)

Honest mapping — 2026-07-13.

| Component | File / tool | Status | Notes |
|-----------|-------------|--------|-------|
| Bell 202 line code | `bell202_line_code.py` | **Done** | Mark 1200 / Space 2200; frequency-toggle encode/decode |
| Line code tests | `test_bell202_line_code.py` | **Done** | Round-trip unit tests |
| AFSK modulator | `afsk_modulator.py` | **Done** | Continuous-phase PCM @ 48 kHz default |
| AFSK demodulator | `afsk_demodulator.py` | **Done** | Per-symbol Goertzel demod |
| HDLC + CRC | `hdlc_codec.py` | **Done** | Flags, bit-stuff, CRC-16 via `ax25_crc` |
| Sound-proxy (Python) | `sound_proxy.py` | **In progress** | `arecord`/`aplay` subprocess path; C header scaffold separate |
| Acoustic bench engine | `acoustic_engine.py` | **In progress** | Full loopback UI→HDLC→AFSK→demod→parse; RF path not closed |
| M25 host protocol | `m25_host_protocol.py` | **In progress** | TCP ctrl/data for bench; port alignment with `max25d` pending |
| `audio-dummyd` | `tools/audio-dummyd.py` | **In progress** | M25 host + `AcousticEngine`; default launcher target |
| `max25-signal-sniffer` | `tools/max25-signal-sniffer.py` | **In progress** | ALSA/WAV/loopback Bell 202 analysis |
| G3RUH 9600–19200 | — | **Planned** | No module yet; direct FSK radio required |
| 300 HF AFSK | — | **Planned** | Optional Phase 3 |
| FEC codec (short blocks) | — | **Planned** | Offline inject-bit-error tests first |
| `speed_baud` INI → launcher | — | **Not implemented** | Research gap |
| Native C `crdopc` DSP binary | `include/crdop/` | **Scaffold** | Python lib leads; C port follows validation |
| RF automated CI | — | **Planned** | Manual acoustic/TNC tests today |

---

## Milestones — phased delivery

### Phase 0 — Acoustic bench (current)

**Goal:** Prove Bell 202 + HDLC + AX.25 UI in software loopback and ALSA bench — no RF required.

| Deliverable | Status |
|-------------|--------|
| `bell202_line_code` + `afsk_*` + `hdlc_codec` unit path | Done |
| `acoustic_engine.loopback_self_test()` | Done |
| `max25-signal-sniffer --loopback` | In progress |
| `audio-dummyd` + `audio-dummy` max25d device | In progress |
| Document acceptable sound cards (community list) | Planned |
| Host protocol single definition (launcher ↔ max25d) | Planned |

**Exit criteria:** Stable loopback decode; sniffer reports AX.25 UI from generated PCM; `test_crdop_backend.py` green.

### Phase 1 — CB/VHF 1200 on-air

**Goal:** Field-validated 1200 AFSK interoperable with standard AX.25 packet peers on CB and VHF APRS-class paths.

| Deliverable | Status |
|-------------|--------|
| Acoustic and line-level coupling validation | In progress |
| Line interface to FM rig (CB channels) | Planned |
| Half-duplex PTT timing in INI + launcher | In progress |
| FEC strategy: short frames, beacon stagger | In progress |
| Hardware interface guide (generic spec) | In progress — [docs/HARDWARE-INTERFACE.md](docs/HARDWARE-INTERFACE.md) |
| Decode parity vs reference 1200 AFSK captures | Planned |

**Exit criteria:** Verified AX.25 UI exchange with at least one reference 1200 AFSK path (acoustic or line-level).

### Phase 2 — G3RUH 9600–19200

**Goal:** Direct-FSK VHF/UHF backbone rates up to **19200 baud** hard maximum.

| Deliverable | Status |
|-------------|--------|
| G3RUH scrambler + FSK mod/demod module | Planned |
| Data-port radio integration docs | Planned |
| Wide-IF rig requirements checklist | Planned |
| Loopback with recorded IQ/baseband fixtures | Planned |

**Prerequisite:** Phase 1 stable; radio with suitable data port and wide-IF path for direct FSK.

**Exit criteria:** Scrambler-compatible exchange with G3RUH reference captures or peer at 9600 minimum.

### Phase 3 — HF 300 baud (optional)

**Goal:** SSB USB/LSB 300 bd packet — 1600/1800 Hz pair first.

| Deliverable | Status |
|-------------|--------|
| 300 bd demod/mod (200 Hz shift) | Planned |
| Tone-pair INI selection | Planned |
| HF dial-frequency calculator notes | Planned |

**Scope:** Optional; does not block CRDOP-v0.5 if deferred.

---

## Validation targets (generic)

Interop validation uses **reference signal classes**, not product endorsements.

| Reference class | Mode | Interface | CRDOP phase |
|-----------------|------|-----------|-------------|
| **1200 AFSK hardware modem** | Bell 202 | Serial KISS or acoustic | Phase 0–1 |
| **Kernel bit-bang modem** | 1200 AFSK | Parallel/serial | Phase 0–1 tone reference |
| **Mobile KISS → audio** | 1200 AFSK | Bluetooth/audio bridge | Phase 1 mobile |
| **G3RUH FSK modem** | 4800–19200 | Direct FSK data port | Phase 2 golden reference |
| **Multi-mode HF TNC** | 300 HF + 1200 VHF | Multi-mode serial | Phase 3 optional |
| **Sound-card reference decoder** | 300–9600+ | ALSA | Software decode parity (1200) |

Open-hardware documentation: [docs/HARDWARE-INTERFACE.md](docs/HARDWARE-INTERFACE.md). Research depth: `acoustic-coupling-hardware.md` in vault (see [Reference index](#reference-index)).

---

## Technical goals (unchanged intent)

1. **1200 baud Bell 202** — reference AX.25 AFSK; primary on-air target (P0).
2. **Acoustic compatibility** — verifiable against standard 1200 AFSK tone paths.
3. **Hardware modem parity** — sound IN/OUT + radio usable like serial/KISS hardware in `max25d`.
4. **Documented DIY hardware** — generic interface spec for builders ([HARDWARE-INTERFACE.md](docs/HARDWARE-INTERFACE.md)).
5. **Good sound card enforcement** — kernel ALSA direct; MAX25 sound-proxy API; requirements scale with baud.
6. **G3RUH to 19200** — incremental after 1200 stable (P1).
7. **FEC via operator strategy** — frequent short sends before heavy on-air FEC (P0).

---

## Not in MAX25 releases

| Item | Policy |
|------|--------|
| Item | Policy |
|------|--------|
| **ARDOP-plugin** | Optional — `ardop_compat=true`; operator ARDOP host |
| `vendor/ardopcf` dev tree | Local dev only (`CRDOP_VENDOR_ARDOPCF=ON`); not in release install |
| **libax25 / ax25-tools / ax25-apps** bundles | Reference tarballs only — not shipped as CRDOP dependency |
| VARA / PACTOR / WINMOR implementations | Out of scope |
| Speeds **>19200 baud** | Out of scope (current phase) |

---

## Next release checklist (CRDOP-v0.5 target)

- [ ] Loopback + acoustic bench test automation in CI
- [ ] Published acceptable sound-card list (community + lab)
- [ ] Native `crdopc` / `audio-dummyd` path unified in default build
- [ ] Field validation on CB reference channel (K24)
- [ ] Hardware interface guide — [docs/HARDWARE-INTERFACE.md](docs/HARDWARE-INTERFACE.md)
- [ ] Host protocol alignment (`m25_host_protocol` ↔ `max25d` backend)
- [ ] `speed_baud` INI wired to launcher

---

## Research vault coverage

Full analysis **2026-07-13** — vault root `/home/akb/Code/0-RESEARCHES/`. Operator hardware runbooks and site-specific INI stay in vault only (not re-copied into CRDOP tree).

| Vault document | Synthesized in this ROADMAP |
|----------------|----------------------------|
| `reference/modems-packet-radio/MASTER-SOLUTIONS-CATALOG.md` | Taxonomy, baud table, RF matrix, CRDOP priorities |
| `cb-packet-solutions.md` | CB band context, K24/K25, legal, 1200-only rationale |
| `amateur-vhf-uhf-solutions.md` | VHF/UHF table, APRS, G3RUH backbone |
| `amateur-hf-packet-solutions.md` | HF 300 bd, Winlink boundary |
| `l2-fec-protocols.md` | FEC layers, FX.25/IL2P takeaways |
| `modern-softmodems.md` | Class D out-of-scope, decision matrix (generic) |
| `bell-202-afsk-1200.md` | P0 PHY parameters, Phase 0–1 |
| `g3ruh-fsk-9600-19200.md` | P1 direct FSK, Phase 2 |
| `hf-300-baud-afsk.md` | P2 tone pairs, SSB path |
| `nrzi-hdlc-ax25-layers.md` | Layer model + `lib/` mapping |
| `MODULATION-REFERENCE.md` | Modulation priority matrix |
| `soundcard-requirements.md` | ALSA requirements, baud scaling |
| `acoustic-coupling-hardware.md` | → [HARDWARE-INTERFACE.md](docs/HARDWARE-INTERFACE.md) |
| `projects/max25-stack/2026-07-13-crdop-development-master.md` | Product scope, MAX25 integration |
| `projects/max25-stack/2026-07-13-crdop-fec-duplex-strategy.md` | FEC/duplex section |
| `reference/2026-07-12-cb-eu-packet.md` | CB legal/channel detail |
| `reference/2026-07-12-packet-radio-fundamentals.md` | Background — no CRDOP code impact |
| `reference/2026-07-12-modems-linux.md` | Linux sound-modem landscape — reference |
| `reference/2026-07-12-linux-ax25-ecosystem.md` | Kernel AX.25 deprecation context |
| `projects/integration/2026-07-12-max25-hybbx-boundary-final.md` | HyBBX attach / serial ownership |
| `DEVELOPMENT.md` (vault root) | Operator P0–P2 — parallel to stack release, not duplicated |

**Not ingested into CRDOP docs:** `hardware/tnc2c/*`, `operations/ini/*`, site-specific serial tests — vault SSoT for lab hardware only.

### Scenario → CRDOP mode (generic, from research)

| Scenario | CRDOP mode |
|----------|------------|
| CB packet QSO (FM audio) | **P0** — 1200 AFSK AX.25 |
| CB net with heavy QRM | **P0** + short-frame FEC strategy; proprietary FM-narrow DSP = separate protocol |
| VHF APRS / digipeater access | **P0** — 1200 AFSK |
| VHF/UHF backbone | **P1** — G3RUH direct FSK (≤19200) |
| HF packet 300 bd | **P2** optional |
| HF mail / Winlink-class | **Out of scope** — separate protocols |
| MAX25 RF broadcast / soft-modem path | **P0** target — native CRDOP in stack |

---

## Reference index

External research vault — read for depth; synthesized above; do not duplicate full text into repo.

| Topic | Path |
|-------|------|
| **Vault index** | `/home/akb/Code/0-RESEARCHES/INDEX.md` |
| **Modem catalog index** | `/home/akb/Code/0-RESEARCHES/reference/modems-packet-radio/README.md` |
| **Master catalog** | `/home/akb/Code/0-RESEARCHES/reference/modems-packet-radio/MASTER-SOLUTIONS-CATALOG.md` |
| CB packet solutions | `/home/akb/Code/0-RESEARCHES/reference/modems-packet-radio/cb-packet-solutions.md` |
| VHF/UHF solutions | `/home/akb/Code/0-RESEARCHES/reference/modems-packet-radio/amateur-vhf-uhf-solutions.md` |
| HF packet solutions | `/home/akb/Code/0-RESEARCHES/reference/modems-packet-radio/amateur-hf-packet-solutions.md` |
| HF 300 bd AFSK detail | `/home/akb/Code/0-RESEARCHES/reference/modems-packet-radio/hf-300-baud-afsk.md` |
| L2 / FEC (FX.25, IL2P) | `/home/akb/Code/0-RESEARCHES/reference/modems-packet-radio/l2-fec-protocols.md` |
| Modern softmodems (comparison) | `/home/akb/Code/0-RESEARCHES/reference/modems-packet-radio/modern-softmodems.md` |
| Bell 202 / 1200 AFSK | `/home/akb/Code/0-RESEARCHES/reference/modems-packet-radio/bell-202-afsk-1200.md` |
| G3RUH 9600–19200 | `/home/akb/Code/0-RESEARCHES/reference/modems-packet-radio/g3ruh-fsk-9600-19200.md` |
| HDLC / AX.25 layers | `/home/akb/Code/0-RESEARCHES/reference/modems-packet-radio/nrzi-hdlc-ax25-layers.md` |
| Modulation parameter table | `/home/akb/Code/0-RESEARCHES/reference/modems-packet-radio/MODULATION-REFERENCE.md` |
| Sound-card requirements | `/home/akb/Code/0-RESEARCHES/reference/modems-packet-radio/soundcard-requirements.md` |
| Acoustic / interface hardware | `/home/akb/Code/0-RESEARCHES/reference/modems-packet-radio/acoustic-coupling-hardware.md` |
| Packet radio fundamentals | `/home/akb/Code/0-RESEARCHES/reference/2026-07-12-packet-radio-fundamentals.md` |
| Linux modems survey | `/home/akb/Code/0-RESEARCHES/reference/2026-07-12-modems-linux.md` |
| Linux AX.25 ecosystem | `/home/akb/Code/0-RESEARCHES/reference/2026-07-12-linux-ax25-ecosystem.md` |
| CRDOP development master | `/home/akb/Code/0-RESEARCHES/projects/max25-stack/2026-07-13-crdop-development-master.md` |
| FEC / duplex strategy | `/home/akb/Code/0-RESEARCHES/projects/max25-stack/2026-07-13-crdop-fec-duplex-strategy.md` |
| MAX25 ↔ HyBBX boundary | `/home/akb/Code/0-RESEARCHES/projects/integration/2026-07-12-max25-hybbx-boundary-final.md` |
| EU CB packet context | `/home/akb/Code/0-RESEARCHES/reference/2026-07-12-cb-eu-packet.md` |

### In-repo technical docs

| Document | Topic |
|----------|--------|
| [docs/INDEX.md](docs/INDEX.md) | Documentation index |
| [docs/SOFTMODEM.md](docs/SOFTMODEM.md) | Product definition |
| [docs/MAX25-USAGE.md](docs/MAX25-USAGE.md) | MAX25-Stack operator guide |
| [docs/DEVELOPER.md](docs/DEVELOPER.md) | Developer guide |
| [docs/HARDWARE-INTERFACE.md](docs/HARDWARE-INTERFACE.md) | Generic radio interface spec |
| [docs/LICENSE-USAGE.md](docs/LICENSE-USAGE.md) | GPLv3 private + commercial |
| [docs/HOST-PROTOCOL-SPEC.md](../stacks/crdop/docs/HOST-PROTOCOL-SPEC.md) | M25 host wire (frozen) |
| [docs/ACOUSTIC-TEST-PROTOCOL.md](../stacks/crdop/docs/ACOUSTIC-TEST-PROTOCOL.md) | Phase 0 bench |
| [docs/FEC-SPEC.md](../stacks/crdop/docs/FEC-SPEC.md) | FEC/duplex parameters |
| [docs/SOUNDCARD-QUALIFICATION.md](../stacks/crdop/docs/SOUNDCARD-QUALIFICATION.md) | Audio interface QA |
| [docs/G3RUH-DESIGN.md](../stacks/crdop/docs/G3RUH-DESIGN.md) | Phase 2 P1 |
| [docs/CRDOP.md](../../docs/CRDOP.md) | Static project rule |
| [docs/AUDIO-ARCHITECTURE.md](docs/AUDIO-ARCHITECTURE.md) | Kernel ALSA, sound-proxy |
| [docs/PROTOCOL.md](docs/PROTOCOL.md) | Host TCP interface |
| [docs/CONFIG.md](docs/CONFIG.md) | INI keys |

---

*Roadmap synthesized 2026-07-13 from full `/home/akb/Code/0-RESEARCHES/` vault analysis (modem catalog + MAX25 project notes). Update when phase gates close or modulation priorities change.*
