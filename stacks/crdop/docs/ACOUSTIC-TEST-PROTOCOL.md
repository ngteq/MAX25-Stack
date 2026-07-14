# Acoustic bench test protocol — P0 bench acceptance

**Purpose:** Close CRDOP P0 bench without RF. All steps runnable offline in CI or on a dev host.

**Related:** [HOST-PROTOCOL-SPEC.md](HOST-PROTOCOL-SPEC.md) · [DEVELOPER.md](DEVELOPER.md) · [ROADMAP.md](../ROADMAP.md) P0 bench.

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| Build | `MAX25_BUILD_CRDOP=ON`, `cmake --install` or source tree |
| Python | 3.10+ with repo on `PYTHONPATH` |
| ALSA | Optional for tests 3–4; loopback tests need no hardware |
| PulseAudio | **Off** or bypassed (`no_pulse=yes` in INI) |

---

## Test matrix

| ID | Name | RF | Pass criteria |
|----|------|-----|---------------|
| **T0** | Bell 202 round-trip | No | `test_bell202_line_code.py` green |
| **T1** | HDLC + CRC | No | `hdlc_codec` round-trip in unit tests |
| **T2** | Software loopback | No | `max25-signal-sniffer.py --loopback` decodes AX.25 UI |
| **T3** | `acoustic_engine` self-test | No | `AcousticEngine.loopback_self_test()` returns True |
| **T4** | `audio-dummyd` + host TCP | No | Connect :8515/:8516, `PROTOCOLMODE KISS` → `OK` |
| **T5** | `max25d` audio-dummy backend | No | `test_audio_dummy_backend.py` green |
| **T6** | `max25d` crdop-tcp backend | No | `test_crdop_backend.py` green |
| **T7** | ALSA loopback cable | No* | Sniffer decodes tone from `aplay`/`arecord` pair |
| **T8** | WAV fixture | No | Sniffer `--wav` decodes recorded Bell 202 capture |

\*Requires `snd-aloop` or physical loopback interface.

---

## Commands (copy-paste)

```bash
cd MAX25-Stack
./scripts/build.sh

# T0–T1
python3 -m pytest stacks/crdop/test_bell202_line_code.py -q
python3 -m pytest stacks/daemon/test_crdop_backend.py stacks/daemon/test_audio_dummy_backend.py -q

# T2
python3 stacks/crdop/tools/max25-signal-sniffer.py --loopback

# T4 (background)
python3 stacks/crdop/tools/audio-dummyd.py --ctrl-port 8515 --data-port 8516 &
sleep 1
python3 -c "
import socket
c=socket.create_connection(('127.0.0.1',8515),timeout=2)
c.sendall(b'PROTOCOLMODE KISS\n')
print(c.recv(64))
"
```

---

## P0 bench exit gate

**100 % P0 bench** when:

- [x] T0, T1, T2, T5, T6 pass in `release-check.sh`
- [ ] T3 documented green in CI log (or explicit skip reason)
- [ ] T4 manual or scripted smoke in release-check
- [ ] Host ports unified: launcher, `audio-dummyd`, `max25d` use [HOST-PROTOCOL-SPEC.md](HOST-PROTOCOL-SPEC.md) defaults

P0 on-air starts only after P0 bench exit — see [docs/HARDWARE-ACCEPTANCE.md](../../docs/HARDWARE-ACCEPTANCE.md).

---

## Failure triage

| Symptom | Check |
|---------|-------|
| Wrong tones | Mark 1200 Hz / Space 2200 Hz, sample rate 48000 |
| CRC fail | `ax25_codec.ax25_crc` vs `hdlc_codec` |
| TCP refuse | Port 8515 free; `audio-dummyd` running for host tests |
| ALSA xrun | `period_frames`, cable levels — [SOUNDCARD-QUALIFICATION.md](SOUNDCARD-QUALIFICATION.md) |
