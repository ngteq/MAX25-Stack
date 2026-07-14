# CRDOP hardware interface specification

Generic specification for builders who manufacture **radio ↔ sound-card interfaces** for CRDOP (MAX25-SoftModem). **No product-specific wiring examples** — apply these rules to your own design.

**CRDOP** = **MAX25-SoftModem**. Project rule: [docs/CRDOP.md](../../../docs/CRDOP.md).

---

## Scope

CRDOP connects a host sound card to a transceiver via one of:

| Path | Typical use | Max practical baud |
|------|-------------|-------------------|
| **Audio AFSK** | Mic IN / speaker OUT / line level | **1200** (P0) |
| **Direct FSK** | Varactor TX + FM discriminator RX | **9600–19200** (P1) |
| **SSB audio** | USB/LSB suppressed carrier | **300** (P2 optional) |
| **Acoustic coupling** | Speaker ↔ microphone (test / field) | **1200** |

RF path matrix and delivery milestones: [ROADMAP.md](../ROADMAP.md).

---

## Audio levels

### Line level (preferred)

| Signal | Typical level | Notes |
|--------|---------------|-------|
| **Playback → radio mic IN** | −20 to −10 dBV (adjust per rig sensitivity) | Use potentiometer or fixed attenuator; verify with sniffer or oscilloscope |
| **Radio speaker/line → capture** | 0.1–1.0 V RMS typical | Attenuate hot speaker outputs before codec input |
| **Full-scale digital** | Avoid clipping on TX and RX | Leave 6–12 dB headroom |

### Mic level

Some transceivers expose mic-level inputs only. Attenuate line output to mic sensitivity (often 5–20 mV). Use coupling capacitor if DC bias is present on the mic jack.

### Isolation

| Method | Purpose |
|--------|---------|
| **Audio transformer** (1:1 or step-down) | Galvanic isolation; breaks ground loops |
| **Opto-isolator** (digital PTT path) | Isolate PTT from radio ground |
| **Separate ground reference** | Star ground at interface PCB; one tie point to radio chassis if required |

**Ground loops** cause hum, false transitions, and decode failures. Always isolate PC USB ground from radio chassis when using direct cable coupling.

---

## PTT control

CRDOP is **half-duplex by default**. The host must key the transmitter before playback and unkey after tail.

| Method | Interface | Caveats |
|--------|-----------|---------|
| **GPIO** | USB-serial RTS/DTR, parallel port, dedicated GPIO | Cleanest; software-controlled timing |
| **Serial CAT** | Radio command port | Latency depends on radio firmware |
| **VOX** | Audio-derived keying | **Not recommended** for packet — tail timing unpredictable; false keys from noise |
| **Manual** | Operator PTT | Acceptable for bench only |

### Timing parameters

Configure in `crdop.ini` / `max25d.ini`:

| Parameter | Typical half-duplex | Full-duplex |
|-----------|--------------------|-------------|
| Pre-TX delay (`extra_delay_ms`) | 80–200 ms | 0 |
| TXTAIL | Match radio requirement | N/A |
| PTT release | After last space tone + margin | N/A |

**Rule:** explicit GPIO/serial PTT beats VOX for AX.25 UI bursts.

---

## Acoustic coupling

Valid for **bench validation** and some field setups:

```
[Host speaker] ──air gap──► [Radio mic]
[Radio speaker] ──air gap──► [Host mic]
```

| Principle | Detail |
|-----------|--------|
| **Distance** | Minimize path loss; foam gasket reduces room noise |
| **Frequency response** | FM voice channel ≈ 3 kHz — sufficient for 1200/2200 Hz Bell 202 |
| **Level** | Low volume on playback; avoid speaker distortion |
| **Duplex** | Half-duplex only — acoustic feedback if TX and RX paths overlap |
| **Test** | Run `max25-signal-sniffer --loopback` on host before acoustic trial |

Acoustic coupling does **not** scale to G3RUH direct FSK (P1).

---

## Direct FSK path (P1 — G3RUH)

When audio AFSK is insufficient (9600–19200 baud):

| Element | Requirement |
|---------|-------------|
| **TX** | Discriminator input bypassed; varactor or dedicated FSK input on data port |
| **RX** | Flat FM discriminator output (de-emphasis off or compensated) |
| **Bandwidth** | ~20 kHz IF for 9600; wider for 19200 |
| **Scrambler** | G3RUH polynomial — implemented in future `lib/` module |
| **Radio** | Data-port capable; standard FM mic/speaker path **not** sufficient |

CB FM rigs at 27 MHz are generally **not** direct-FSK capable at 9600+ — P1 targets VHF/UHF amateur backbone paths.

---

## Sound card requirements

| Requirement | 1200 baud (P0) | 9600–19200 (P1) |
|-------------|----------------|-----------------|
| **Sample rate** | ≥ 48 kHz recommended | ≥ 48 kHz; 96 kHz preferred |
| **Bit depth** | 16-bit mono | 16-bit mono |
| **Duplex** | Full-duplex USB codec or half-duplex with PTT | Full-duplex, low jitter |
| **Clock** | Stable crystal; avoid drift during TX | Jitter < 50 ppm class |
| **Driver** | Kernel ALSA (`hw:` / `plughw:`) | Same |
| **Isolation** | Transformer on radio side | Same + verified loopback |

### Unsuitable interfaces

- Onboard laptop mic/speaker without external interface
- Bluetooth audio bridges
- PulseAudio / PipeWire virtual devices
- Consumer "USB sound sticks" without galvanic isolation

Configure devices in `crdop.ini`:

```ini
[audio]
backend = alsa-kernel
no_pulse = yes
capture = plughw:1,0
playback = plughw:1,0
sample_rate = 48000
```

Verify with:

```bash
max25-signal-sniffer --loopback
max25-signal-sniffer -D plughw:1,0 -t 2.0
```

---

## Compliance and operator responsibility

| Topic | Policy |
|-------|--------|
| **Transmit licence** | Operator must hold valid authorization for the band and mode |
| **CB (27 MHz EU)** | EN 300 433 / national rules — voice primary; data may be restricted or channel-specific |
| **Amateur bands** | Band plan, power limits, identification |
| **EMC** | Builder responsible for conducted/radiated emissions from interface hardware |
| **CRDOP software** | GPLv3 — no warranty; see [LICENSE-USAGE.md](LICENSE-USAGE.md) |

CRDOP documentation does **not** constitute legal advice. Check local regulations before on-air operation.

---

## Acceptance checklist (builder)

| Step | Pass criterion |
|------|----------------|
| Loopback | `max25-signal-sniffer --loopback` decodes test UI |
| Level | Mark/space tones within radio spec; no clipping |
| Isolation | No hum on decode when PC and radio share mains |
| PTT | Key before TX audio; clean tail; no truncation |
| On-air | AX.25 UI exchange with known-good peer at 1200 baud |
| Duplex | Half-duplex CSMA behaviour matches `persist` / `extra_delay` INI |

---

## Related in-repo docs

| Topic | Document |
|-------|----------|
| Sound-card requirements | [SOUNDCARD-QUALIFICATION.md](SOUNDCARD-QUALIFICATION.md) |
| Bell 202 / 1200 AFSK (P0) | [ROADMAP.md](../ROADMAP.md) · [SOFTMODEM.md](SOFTMODEM.md) |
| G3RUH 9600–19200 (P1) | [G3RUH-DESIGN.md](G3RUH-DESIGN.md) |
| AX.25 / packet context | [docs/PACKET-RADIO.md](../../../docs/PACKET-RADIO.md) |

---

## Related

| Doc | Topic |
|-----|--------|
| [AUDIO-ARCHITECTURE.md](AUDIO-ARCHITECTURE.md) | Kernel ALSA, sound-proxy |
| [MAX25-USAGE.md](MAX25-USAGE.md) | Stack integration and bench modes |
| [ROADMAP.md](../ROADMAP.md) | P0/P1/P2 phases |
