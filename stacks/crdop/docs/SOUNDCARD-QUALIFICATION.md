# Sound card qualification — CRDOP / MAX25-SoftModem

**Purpose:** Measurable criteria for interface hardware used with CRDOP. No product endorsements — class-based requirements.

See also [ROADMAP.md](../ROADMAP.md) (P0/P1 audio requirements).

---

## Mandatory architecture

```
CRDOP DSP → sound_proxy → libasound (hw:) → codec → radio interface
```

| Forbidden in production path | Reason |
|------------------------------|--------|
| PulseAudio default route | Mixing, resampling, latency |
| PipeWire default | Variable buffer |
| Bluetooth A2DP/HFP | Codec + AGC |

INI: `[audio] backend = alsa-kernel`, `no_pulse = yes`.

---

## Sample rate

| Baud target | Minimum rate | CRDOP default |
|-------------|--------------|---------------|
| 1200 AFSK | 48000 Hz | **48000** |
| 9600 G3RUH (audio tap) | 48000–96000 | 48000 + tuning |
| 19200 | 96000 Hz | 96000 if hardware supports |

---

## Qualification tests

Run on candidate interface **before** field deployment.

| ID | Test | Pass |
|----|------|------|
| **Q1** | Loopback cable, 1200 Hz sine 2 s | THD acceptable by ear + FFT peak at 1200 ±2 Hz |
| **Q2** | Loopback Bell 202 sniffer | `max25-signal-sniffer --loopback` or ALSA loop |
| **Q3** | Mark/space calibration tones | `--mark` / `--space` tools within ±5 Hz |
| **Q4** | 60 s full-duplex record+play | No xrun in `dmesg` / ALSA log |
| **Q5** | Clock drift | 10 min loopback: no cumulative symbol slip at 1200 bd |

---

## Interface classes

| Class | Isolation | 1200 AFSK | 19200 path |
|-------|-----------|-----------|------------|
| **A** | Galvanic line I/O, fixed gain | Required minimum | Test Q1–Q5 |
| **B** | USB codec, headphone/mic level | Acceptable with level match | Not recommended |
| **C** | Onboard mic/speaker only | Acoustic bench only | Fail |

CRDOP production path: **Class A or B** with line-level radio interface — see [HARDWARE-INTERFACE.md](HARDWARE-INTERFACE.md).

---

## Level guidelines

| Path | Typical level |
|------|---------------|
| Line OUT → radio mic in | 100–300 mV RMS (adjust pad) |
| Radio speaker/line → Line IN | Attenuate to avoid clipping |
| DC offset | AC coupling required |

---

## Baud scaling

Requirements **rise faster than linear** above 1200 bd:

| Baud | Clock jitter tolerance | Filter flatness |
|------|------------------------|-----------------|
| 1200 | moderate | 300–3000 Hz FM audio path OK |
| 9600 | strict | 10 Hz–5 kHz flat, constant group delay |
| 19200 | professional | Direct FSK tap — not soundcard mic path |

---

## Failure actions

| Symptom | Action |
|---------|--------|
| xruns | Increase `period_frames`; reduce system load |
| Wrong tones | Verify 48000 Hz; check resampler not inserted |
| Intermittent decode | Replace Class C with A/B; check ground loop |

---

## Community list (planned)

Phase 0 exit: publish operator-submitted **class + Q1–Q2 result** table — no vendor ranking.
