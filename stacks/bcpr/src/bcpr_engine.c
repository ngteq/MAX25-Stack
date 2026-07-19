/*
 * Bit-clock engine: RT timer loop drives SER12 + HDLC for up to 2 devices.
 * Userspace timing (not kernel hard-IRQ). See NOTICE.md.
 */
#define _GNU_SOURCE
#include "bcpr/bcpr_engine.h"
#include "bcpr/bcpr_uart.h"

#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#if defined(__linux__)
#include <pthread.h>
#include <sched.h>
#endif

typedef struct {
    bcpr_engine_t *e;
    int idx;
} rx_ctx_t;

static unsigned now_us(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (unsigned)((ts.tv_nsec / 1000) % 1000000u);
}

static void on_frame_ctx(const uint8_t *kiss, int len, void *ud)
{
    rx_ctx_t *ctx = (rx_ctx_t *)ud;
    if (ctx && ctx->e && ctx->e->on_rx) {
        ctx->e->on_rx(ctx->idx, kiss, len, ctx->e->on_rx_ud);
    }
}

void bcpr_engine_set_rx(bcpr_engine_t *e, bcpr_rx_fn fn, void *ud)
{
    if (!e) {
        return;
    }
    e->on_rx = fn;
    e->on_rx_ud = ud;
}

int bcpr_engine_queue_kiss(bcpr_engine_t *e, int dev_idx, const uint8_t *kiss,
                           int len)
{
    int i;
    if (!e || !kiss) {
        return -1;
    }
    for (i = 0; i < e->n; i++) {
        if (e->dev[i].index == dev_idx) {
            return bcpr_hdlc_queue_kiss(&e->dev[i].hdlc, kiss, len);
        }
    }
    return -1;
}

int bcpr_engine_open(bcpr_engine_t *e, const bcpr_config_t *cfg)
{
    int i;
    int n = 0;

    if (!e || !cfg) {
        return -1;
    }
    memset(e, 0, sizeof(*e));
    e->cfg = *cfg;
    e->stop = 0;
    e->run_seconds = 0;
    bcpr_uart_set_dry_run(cfg->dry_run);

    for (i = 0; i < BCPR_MAX_DEVICES; i++) {
        bcpr_device_t *d;
        bcpr_channel_t ch;
        unsigned baud = 1200;
        int opt_dcd = 0;

        if (!cfg->dev[i].enabled) {
            continue;
        }
        d = &e->dev[n];
        memset(d, 0, sizeof(*d));
        d->cfg = cfg->dev[i];
        d->index = i;
        d->running = 0;

        if (bcpr_lock_acquire(&d->lock, &d->cfg, cfg->dry_run) != 0) {
            fprintf(stderr, "bcpr: lock failed for max25e0:bc%d\n", i);
            bcpr_engine_close(e);
            return -1;
        }

        bcpr_ser12_set_mode(&d->ser12, d->cfg.mode, &baud);
        if (d->cfg.baud) {
            baud = d->cfg.baud;
        }
        opt_dcd = d->ser12.opt_dcd;
        bcpr_ser12_init(&d->ser12, baud, opt_dcd);

        ch.tx_delay = d->cfg.tx_delay;
        ch.tx_tail = d->cfg.tx_tail;
        ch.slottime = d->cfg.slottime;
        ch.ppersist = d->cfg.ppersist;
        ch.fulldup = d->cfg.fulldup;
        bcpr_hdlc_init(&d->hdlc, (int)baud, &ch);

        if (!cfg->dry_run) {
            if (bcpr_uart_ioperm(d->cfg.iobase, 1) != 0) {
                fprintf(stderr, "bcpr: ioperm failed 0x%x\n", d->cfg.iobase);
                bcpr_engine_close(e);
                return -1;
            }
            bcpr_uart_set_divisor(d->cfg.iobase, 115200u / 100u / 8u);
            bcpr_uart_open_ser12(d->cfg.iobase);
        }
        d->running = 1;
        n++;
    }
    e->n = n;
    if (n == 0) {
        fprintf(stderr, "bcpr: no enabled devices in config\n");
        return -1;
    }
    fprintf(stderr, "bcpr: open max25e0 (%d device%s)%s\n", n,
            n == 1 ? "" : "s", cfg->dry_run ? " [dry-run]" : "");
    return 0;
}

void bcpr_engine_close(bcpr_engine_t *e)
{
    int i;
    if (!e) {
        return;
    }
    e->stop = 1;
    for (i = 0; i < e->n; i++) {
        bcpr_device_t *d = &e->dev[i];
        if (d->running && !e->cfg.dry_run) {
            bcpr_uart_close_ser12(d->cfg.iobase);
            (void)bcpr_uart_ioperm(d->cfg.iobase, 0);
        }
        bcpr_lock_release(&d->lock);
        d->running = 0;
    }
    e->n = 0;
}

static void try_rt(void)
{
#if defined(__linux__)
    struct sched_param sp;
    memset(&sp, 0, sizeof(sp));
    sp.sched_priority = 10;
    (void)pthread_setschedparam(pthread_self(), SCHED_FIFO, &sp);
#endif
}

static void tick_device(bcpr_engine_t *e, bcpr_device_t *d, rx_ctx_t *ctx)
{
    int cts = 0;
    int mcr = 0x0d;
    int do_thr = 0;
    unsigned t = now_us();

    if (!e->cfg.dry_run) {
        unsigned char msr = bcpr_uart_msr(d->cfg.iobase);
        cts = (msr & 0x10) ? 1 : 0;
        if (d->ser12.opt_dcd > 0) {
            d->hdlc.dcd = (msr & 0x80) ? 1 : 0;
        } else if (d->ser12.opt_dcd < 0) {
            d->hdlc.dcd = (msr & 0x80) ? 0 : 1;
        }
    }

    bcpr_ser12_tick(&d->ser12, &d->hdlc, cts, &mcr, &do_thr, t);

    if (!e->cfg.dry_run) {
        unsigned div;
        bcpr_uart_mcr(d->cfg.iobase, (unsigned char)mcr);
        if (do_thr) {
            bcpr_uart_thr00(d->cfg.iobase);
        }
        if (d->ser12.ptt_hw) {
            div = (115200u / 8u) / (d->ser12.baud ? d->ser12.baud : 1200u);
            if (div == 0) {
                div = 1;
            }
            bcpr_uart_set_divisor(d->cfg.iobase, div);
        } else {
            bcpr_uart_set_divisor(d->cfg.iobase, 115200u / 100u / 8u);
        }
    }

    ctx->e = e;
    ctx->idx = d->index;
    bcpr_hdlc_receiver(&d->hdlc, on_frame_ctx, ctx);
}

/* Publish Soft-/hard-DCD for RX-before-TX gates (state_dir/dcd-bcN). */
static void publish_dcd_status(const bcpr_engine_t *e)
{
    int i;
    char path[192];
    FILE *f;

    if (!e || e->cfg.dry_run || e->cfg.state_dir[0] == '\0') {
        return;
    }
    for (i = 0; i < e->n; i++) {
        const bcpr_device_t *d = &e->dev[i];
        int dcd = d->hdlc.dcd ? 1 : 0;
        snprintf(path, sizeof(path), "%s/dcd-bc%d", e->cfg.state_dir, d->index);
        f = fopen(path, "w");
        if (f) {
            fprintf(f, "dcd=%d\n", dcd);
            fclose(f);
        }
        if (dcd) {
            snprintf(path, sizeof(path), "%s/rx-activity-bc%d", e->cfg.state_dir,
                     d->index);
            f = fopen(path, "w");
            if (f) {
                fputs("rx_activity=1\n", f);
                fclose(f);
            }
        }
    }
}

int bcpr_engine_run(bcpr_engine_t *e)
{
    struct timespec next;
    rx_ctx_t ctx;
    time_t t0;
    unsigned period_ns;
    unsigned tick = 0;

    if (!e || e->n <= 0) {
        return -1;
    }
    try_rt();
    t0 = time(NULL);
    period_ns = e->dev[0].ser12.baud_us * 1000u;
    if (period_ns < 100000u) {
        period_ns = 833000u;
    }

    clock_gettime(CLOCK_MONOTONIC, &next);
    while (!e->stop) {
        int i;
        for (i = 0; i < e->n; i++) {
            tick_device(e, &e->dev[i], &ctx);
        }
        /* ~100 ms at 1200 baud (120 bit times). */
        if ((++tick % 120u) == 0u) {
            publish_dcd_status(e);
        }
        next.tv_nsec += (long)period_ns;
        while (next.tv_nsec >= 1000000000L) {
            next.tv_nsec -= 1000000000L;
            next.tv_sec++;
        }
        while (clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &next, NULL) ==
               EINTR) {
        }
        if (e->run_seconds > 0 && (time(NULL) - t0) >= e->run_seconds) {
            break;
        }
    }
    return 0;
}
