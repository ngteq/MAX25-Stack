/* macOS CoreAudio backend — ALSA-compatible surface for ALSASound.c */
#include "darwin/alsa_shim.h"

#include <AudioToolbox/AudioToolbox.h>
#include <CoreAudio/CoreAudioTypes.h>
#include <pthread.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CRDOP_CAPTURE_RING_SAMPLES (12000 * 2)
#define CRDOP_CAPTURE_BUFFERS 3
#define CRDOP_PLAYBACK_BUFFERS 3
#define CRDOP_PLAYBACK_FRAME_BYTES 2400

struct snd_pcm_hw_params {
	int unused;
};

struct crdop_pcm {
	AudioQueueRef queue;
	snd_pcm_stream_t stream;
	unsigned int rate;
	unsigned int channels;
	bool running;

	/* capture ring */
	short capture_ring[CRDOP_CAPTURE_RING_SAMPLES];
	unsigned int capture_write;
	unsigned int capture_read;
	unsigned int capture_count;
	pthread_mutex_t capture_lock;

	/* playback pending */
	pthread_mutex_t play_lock;
};

static char** s_out_names = NULL;
static int s_out_count = 0;
static char** s_in_names = NULL;
static int s_in_count = 0;

static AudioStreamBasicDescription crdop_audio_format(unsigned int rate, unsigned int channels)
{
	AudioStreamBasicDescription fmt = {0};
	fmt.mSampleRate = (Float64)rate;
	fmt.mFormatID = kAudioFormatLinearPCM;
	fmt.mFormatFlags = kLinearPCMFormatFlagIsSignedInteger | kLinearPCMFormatFlagIsPacked;
#if __BIG_ENDIAN__
	fmt.mFormatFlags |= kLinearPCMFormatFlagIsBigEndian;
#else
	fmt.mFormatFlags |= kLinearPCMFormatFlagIsLittleEndian;
#endif
	fmt.mBitsPerChannel = 16;
	fmt.mChannelsPerFrame = channels;
	fmt.mBytesPerFrame = (fmt.mBitsPerChannel / 8) * channels;
	fmt.mFramesPerPacket = 1;
	fmt.mBytesPerPacket = fmt.mBytesPerFrame;
	return fmt;
}

const char* snd_strerror(int err)
{
	static char buf[64];
	snprintf(buf, sizeof(buf), "coreaudio err %d", err);
	return buf;
}

static void capture_callback(void* user_data, AudioQueueRef queue, AudioQueueBufferRef buffer,
	const AudioTimeStamp* start_time, UInt32 num_packets, const AudioStreamPacketDescription* desc)
{
	(void)queue;
	(void)start_time;
	(void)num_packets;
	(void)desc;
	crdop_pcm_t* pcm = (crdop_pcm_t*)user_data;
	if (!pcm || !buffer || buffer->mAudioDataByteSize == 0)
		return;

	unsigned int nsamples = buffer->mAudioDataByteSize / (2 * pcm->channels);
	short* src = (short*)buffer->mAudioData;

	pthread_mutex_lock(&pcm->capture_lock);
	for (unsigned int i = 0; i < nsamples; ++i) {
		pcm->capture_ring[pcm->capture_write] = src[i * pcm->channels];
		pcm->capture_write = (pcm->capture_write + 1) % CRDOP_CAPTURE_RING_SAMPLES;
		if (pcm->capture_count < CRDOP_CAPTURE_RING_SAMPLES)
			pcm->capture_count++;
		else
			pcm->capture_read = (pcm->capture_read + 1) % CRDOP_CAPTURE_RING_SAMPLES;
	}
	pthread_mutex_unlock(&pcm->capture_lock);

	AudioQueueEnqueueBuffer(pcm->queue, buffer, 0, NULL);
}

static void playback_callback(void* user_data, AudioQueueRef queue, AudioQueueBufferRef buffer)
{
	(void)user_data;
	(void)queue;
	/* playback buffers are filled synchronously in writei */
	if (buffer)
		buffer->mAudioDataByteSize = 0;
}

static int crdop_open_queue(crdop_pcm_t** out_pcm, const char* name, snd_pcm_stream_t stream,
	unsigned int rate, unsigned int channels)
{
	(void)name;
	crdop_pcm_t* pcm = calloc(1, sizeof(*pcm));
	if (!pcm)
		return -1;

	pcm->stream = stream;
	pcm->rate = rate ? rate : 12000;
	pcm->channels = channels ? channels : 1;
	pthread_mutex_init(&pcm->capture_lock, NULL);
	pthread_mutex_init(&pcm->play_lock, NULL);

	AudioStreamBasicDescription fmt = crdop_audio_format(pcm->rate, pcm->channels);
	OSStatus st = AudioQueueNewOutput(&fmt, playback_callback, pcm, NULL, NULL, 0, &pcm->queue);
	if (stream == SND_PCM_STREAM_CAPTURE)
		st = AudioQueueNewInput(&fmt, capture_callback, pcm, NULL, NULL, 0, &pcm->queue);
	if (st != noErr) {
		free(pcm);
		return (int)st;
	}

	if (stream == SND_PCM_STREAM_PLAYBACK) {
		for (int i = 0; i < CRDOP_PLAYBACK_BUFFERS; ++i) {
			AudioQueueBufferRef buf = NULL;
			st = AudioQueueAllocateBuffer(pcm->queue, CRDOP_PLAYBACK_FRAME_BYTES, &buf);
			if (st != noErr)
				return (int)st;
			buf->mAudioDataByteSize = 0;
			AudioQueueEnqueueBuffer(pcm->queue, buf, 0, NULL);
		}
	} else {
		UInt32 buf_bytes = (UInt32)(240 * 2 * pcm->channels);
		for (int i = 0; i < CRDOP_CAPTURE_BUFFERS; ++i) {
			AudioQueueBufferRef buf = NULL;
			st = AudioQueueAllocateBuffer(pcm->queue, buf_bytes, &buf);
			if (st != noErr)
				return (int)st;
			buf->mAudioDataByteSize = buf_bytes;
			AudioQueueEnqueueBuffer(pcm->queue, buf, 0, NULL);
		}
	}

	*out_pcm = pcm;
	return 0;
}

int snd_pcm_open(snd_pcm_t** pcm, const char* name, snd_pcm_stream_t stream, int mode)
{
	(void)mode;
	return crdop_open_queue(pcm, name, stream, 12000, 1);
}

int snd_pcm_close(snd_pcm_t* pcm)
{
	if (!pcm)
		return 0;
	if (pcm->queue) {
		AudioQueueStop(pcm->queue, true);
		AudioQueueDispose(pcm->queue, true);
	}
	pthread_mutex_destroy(&pcm->capture_lock);
	pthread_mutex_destroy(&pcm->play_lock);
	free(pcm);
	return 0;
}

int snd_pcm_prepare(snd_pcm_t* pcm)
{
	(void)pcm;
	return 0;
}

int snd_pcm_start(snd_pcm_t* pcm)
{
	if (!pcm || !pcm->queue)
		return -1;
	OSStatus st = AudioQueueStart(pcm->queue, NULL);
	pcm->running = (st == noErr);
	return (st == noErr) ? 0 : (int)st;
}

snd_pcm_sframes_t snd_pcm_avail_update(snd_pcm_t* pcm)
{
	if (!pcm)
		return -1;
	if (pcm->stream == SND_PCM_STREAM_CAPTURE) {
		pthread_mutex_lock(&pcm->capture_lock);
		snd_pcm_sframes_t avail = (snd_pcm_sframes_t)pcm->capture_count;
		pthread_mutex_unlock(&pcm->capture_lock);
		return avail;
	}
	return 1200;
}

int snd_pcm_recover(snd_pcm_t* pcm, snd_pcm_sframes_t err, int silent)
{
	(void)silent;
	if (!pcm)
		return (int)err;
	if (pcm->queue && !pcm->running)
		return snd_pcm_start(pcm);
	return 0;
}

snd_pcm_sframes_t snd_pcm_writei(snd_pcm_t* pcm, const void* buffer, snd_pcm_uframes_t size)
{
	if (!pcm || !pcm->queue || !buffer || size == 0)
		return -1;

	UInt32 bytes = (UInt32)(size * 2 * pcm->channels);
	AudioQueueBufferRef buf = NULL;
	OSStatus st = AudioQueueAllocateBuffer(pcm->queue, bytes, &buf);
	if (st != noErr)
		return (int)st;

	memcpy(buf->mAudioData, buffer, bytes);
	buf->mAudioDataByteSize = bytes;
	st = AudioQueueEnqueueBuffer(pcm->queue, buf, 0, NULL);
	if (st != noErr)
		return (int)st;

	if (!pcm->running)
		snd_pcm_start(pcm);

	return (snd_pcm_sframes_t)size;
}

snd_pcm_sframes_t snd_pcm_readi(snd_pcm_t* pcm, void* buffer, snd_pcm_uframes_t size)
{
	if (!pcm || !buffer || size == 0)
		return -1;

	if (!pcm->running)
		snd_pcm_start(pcm);

	short* out = (short*)buffer;
	snd_pcm_uframes_t got = 0;

	pthread_mutex_lock(&pcm->capture_lock);
	while (got < size && pcm->capture_count > 0) {
		out[got++] = pcm->capture_ring[pcm->capture_read];
		pcm->capture_read = (pcm->capture_read + 1) % CRDOP_CAPTURE_RING_SAMPLES;
		pcm->capture_count--;
	}
	pthread_mutex_unlock(&pcm->capture_lock);

	return (snd_pcm_sframes_t)got;
}

int snd_pcm_hw_params_malloc(snd_pcm_hw_params_t** params)
{
	*params = calloc(1, sizeof(**params));
	return *params ? 0 : -1;
}

void snd_pcm_hw_params_free(snd_pcm_hw_params_t* params)
{
	free(params);
}

int snd_pcm_hw_params_any(snd_pcm_t* pcm, snd_pcm_hw_params_t* params)
{
	(void)pcm;
	(void)params;
	return 0;
}

int snd_pcm_hw_params_set_access(snd_pcm_t* pcm, snd_pcm_hw_params_t* params, snd_pcm_access_t access)
{
	(void)pcm;
	(void)params;
	(void)access;
	return 0;
}

int snd_pcm_hw_params_set_format(snd_pcm_t* pcm, snd_pcm_hw_params_t* params, snd_pcm_format_t format)
{
	(void)pcm;
	(void)params;
	(void)format;
	return 0;
}

int snd_pcm_hw_params_set_rate(snd_pcm_t* pcm, snd_pcm_hw_params_t* params, unsigned int rate, int dir)
{
	(void)params;
	(void)dir;
	if (pcm)
		pcm->rate = rate;
	return 0;
}

int snd_pcm_hw_params_set_channels(snd_pcm_t* pcm, snd_pcm_hw_params_t* params, unsigned int channels)
{
	(void)params;
	if (pcm)
		pcm->channels = channels;
	return 0;
}

int snd_pcm_hw_params_set_period_size_near(snd_pcm_t* pcm, snd_pcm_hw_params_t* params,
	snd_pcm_uframes_t* val, int* dir)
{
	(void)pcm;
	(void)params;
	(void)dir;
	if (val && *val == 0)
		*val = 120;
	return 0;
}

int snd_pcm_hw_params(snd_pcm_t* pcm, snd_pcm_hw_params_t* params)
{
	(void)pcm;
	(void)params;
	return 0;
}

static void crdop_free_device_list(char*** list, int* count)
{
	if (!list || !count)
		return;
	for (int i = 0; i < *count; ++i)
		free((*list)[i]);
	free(*list);
	*list = NULL;
	*count = 0;
}

static int crdop_build_default_device_list(char*** list, int* count)
{
	crdop_free_device_list(list, count);
	*list = calloc(2, sizeof(char*));
	if (!*list)
		return 0;
	(*list)[0] = strdup("default");
	(*list)[1] = strdup("ARDOP");
	*count = 2;
	return *count;
}

int darwin_get_output_device_collection(void)
{
	return crdop_build_default_device_list(&s_out_names, &s_out_count);
}

int darwin_get_input_device_collection(void)
{
	return crdop_build_default_device_list(&s_in_names, &s_in_count);
}

int darwin_get_next_output_device(char* dest, int max, int n)
{
	if (n >= s_out_count || !dest || max <= 0)
		return 0;
	strncpy(dest, s_out_names[n], (size_t)max - 1);
	dest[max - 1] = '\0';
	return (int)strlen(dest);
}

int darwin_get_next_input_device(char* dest, int max, int n)
{
	if (n >= s_in_count || !dest || max <= 0)
		return 0;
	strncpy(dest, s_in_names[n], (size_t)max - 1);
	dest[max - 1] = '\0';
	return (int)strlen(dest);
}
