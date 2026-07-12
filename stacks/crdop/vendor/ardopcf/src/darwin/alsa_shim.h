/* Minimal ALSA-like API for macOS CoreAudio (CRDOP darwin backend). */
#ifndef CRDOP_DARWIN_ALSA_SHIM_H
#define CRDOP_DARWIN_ALSA_SHIM_H

#include <stddef.h>
#include <stdint.h>

typedef struct crdop_pcm crdop_pcm_t;
typedef crdop_pcm_t* snd_pcm_t;
typedef long snd_pcm_sframes_t;
typedef unsigned long snd_pcm_uframes_t;

typedef enum {
	SND_PCM_STREAM_PLAYBACK = 0,
	SND_PCM_STREAM_CAPTURE = 1
} snd_pcm_stream_t;

typedef enum {
	SND_PCM_ACCESS_RW_INTERLEAVED = 0
} snd_pcm_access_t;

typedef enum {
	SND_PCM_FORMAT_S16_LE = 0
} snd_pcm_format_t;

#define SND_PCM_NONBLOCK 0x0001

typedef struct snd_pcm_hw_params snd_pcm_hw_params_t;

const char* snd_strerror(int err);

int snd_pcm_open(snd_pcm_t** pcm, const char* name, snd_pcm_stream_t stream, int mode);
int snd_pcm_close(snd_pcm_t* pcm);
int snd_pcm_prepare(snd_pcm_t* pcm);
int snd_pcm_start(snd_pcm_t* pcm);
snd_pcm_sframes_t snd_pcm_writei(snd_pcm_t* pcm, const void* buffer, snd_pcm_uframes_t size);
snd_pcm_sframes_t snd_pcm_readi(snd_pcm_t* pcm, void* buffer, snd_pcm_uframes_t size);
snd_pcm_sframes_t snd_pcm_avail_update(snd_pcm_t* pcm);
int snd_pcm_recover(snd_pcm_t* pcm, snd_pcm_sframes_t err, int silent);

int snd_pcm_hw_params_malloc(snd_pcm_hw_params_t** params);
void snd_pcm_hw_params_free(snd_pcm_hw_params_t* params);
int snd_pcm_hw_params_any(snd_pcm_t* pcm, snd_pcm_hw_params_t* params);
int snd_pcm_hw_params_set_access(snd_pcm_t* pcm, snd_pcm_hw_params_t* params, snd_pcm_access_t access);
int snd_pcm_hw_params_set_format(snd_pcm_t* pcm, snd_pcm_hw_params_t* params, snd_pcm_format_t format);
int snd_pcm_hw_params_set_rate(snd_pcm_t* pcm, snd_pcm_hw_params_t* params, unsigned int rate, int dir);
int snd_pcm_hw_params_set_channels(snd_pcm_t* pcm, snd_pcm_hw_params_t* params, unsigned int channels);
int snd_pcm_hw_params_set_period_size_near(snd_pcm_t* pcm, snd_pcm_hw_params_t* params, snd_pcm_uframes_t* val, int* dir);
int snd_pcm_hw_params(snd_pcm_t* pcm, snd_pcm_hw_params_t* params);

/* macOS device listing (replaces ALSA ctl enumeration in ALSASound.c). */
int darwin_get_output_device_collection(void);
int darwin_get_input_device_collection(void);
int darwin_get_next_output_device(char* dest, int max, int n);
int darwin_get_next_input_device(char* dest, int max, int n);

#endif
