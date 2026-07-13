/*
 * MAX25 sound-proxy — CRDOP ↔ kernel ALSA (no PulseAudio).
 *
 * In-process shim between modem DSP and libasound. Only this layer opens
 * snd_pcm capture/playback on hw:/plughw: devices. max25d does not touch audio.
 *
 * Eigenentwicklung — API stable for v1 scaffold; implementation in progress.
 */
#ifndef MAX25_CRDOP_SOUND_PROXY_H
#define MAX25_CRDOP_SOUND_PROXY_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/** ALSA backend policy — kernel path only; no PulseAudio/PipeWire route. */
#define MAX25_SOUND_BACKEND_ALSA_KERNEL "alsa-kernel"

typedef struct max25_sound_proxy max25_sound_proxy_t;

typedef struct max25_sound_config {
	const char *capture_device;  /* e.g. "hw:1,0" */
	const char *playback_device; /* e.g. "hw:1,0" */
	unsigned int sample_rate;    /* Hz — modem-dependent */
	unsigned int period_frames;
	unsigned int buffer_frames;
	int full_duplex;             /* 0 = half, 1 = full */
	int forbid_pulse;            /* non-zero: reject pulse/pipewire pseudo devices */
} max25_sound_config_t;

/** Open ALSA via kernel path; returns NULL on failure (pulse device rejected if forbid_pulse). */
max25_sound_proxy_t *max25_sound_proxy_open(const max25_sound_config_t *cfg);

void max25_sound_proxy_close(max25_sound_proxy_t *sp);

/** Capture PCM frames (RX path). Returns frames read or negative errno-style code. */
int max25_sound_proxy_read(max25_sound_proxy_t *sp, int16_t *buf, size_t frames);

/** Playback PCM frames (TX path). Returns frames written or negative code. */
int max25_sound_proxy_write(max25_sound_proxy_t *sp, const int16_t *buf, size_t frames);

/** Recover from xrun — modem may call between frames. */
int max25_sound_proxy_recover(max25_sound_proxy_t *sp);

#ifdef __cplusplus
}
#endif

#endif /* MAX25_CRDOP_SOUND_PROXY_H */
