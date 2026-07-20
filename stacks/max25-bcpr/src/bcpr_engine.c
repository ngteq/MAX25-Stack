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
#include <stdint.h>

#if defined(__linux__)
#include <pthread.h>
#include <sched.h>
#include <sys/mman.h>
#endif

typedef struct {
    bcpr_engine_t *e;
    int idx;
} rx_ctx_t;

static unsigned now_us(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    /* Full monotonic µs — not nsec-within-second (gap spikes were misread). */
    return (unsigned)(ts.tv_sec * 1000000ull + (unsigned long long)ts.tv_nsec / 1000ull);
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
        bcpr_ser12_set_ptt_wd(&d->ser12, d->cfg.ptt_wd, d->cfg.ptt_wd_key_ms,
                              d->cfg.ptt_wd_pause_ms);

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
            /*
             * txd_bias=steady: assert UART break after open (LCR.SB).
             * THR framing cannot hold DC-steady TXD; break ≈ TFPCX +12 V.
             * Default remains pulse (Sailer THR 0x00). MCR unchanged.
             */
            if (d->cfg.txd_bias == BCPR_TXD_STEADY) {
                bcpr_uart_set_break(d->cfg.iobase, 1);
                d->break_set = 1;
            }
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
    for (i = 0; i < n; i++) {
        const bcpr_device_t *d = &e->dev[i];
        fprintf(stderr,
                "bcpr: bc%d ptt_wd=%s key_ms=%d pause_ms=%d txd_bias=%s\n",
                d->index, d->cfg.ptt_wd ? "on" : "off", d->cfg.ptt_wd_key_ms,
                d->cfg.ptt_wd_pause_ms,
                d->cfg.txd_bias == BCPR_TXD_STEADY ? "steady" : "pulse");
    }
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
            if (d->break_set) {
                bcpr_uart_set_break(d->cfg.iobase, 0);
                d->break_set = 0;
            }
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
    cpu_set_t set;
    int rc;
    memset(&sp, 0, sizeof(sp));
    /* Pin pages — fault during PTT = multi-ms TXD gap → pump collapse. */
    if (mlockall(MCL_CURRENT | MCL_FUTURE) != 0) {
        fprintf(stderr, "bcpr: mlockall failed errno=%d (page faults risk gaps)\n",
                errno);
    }
    /* Prefer one CPU — migration mid-PTT causes multi-ms gaps. */
    CPU_ZERO(&set);
    CPU_SET(0, &set);
    if (sched_setaffinity(0, sizeof(set), &set) != 0) {
        fprintf(stderr, "bcpr: sched_setaffinity(0) errno=%d\n", errno);
    }
    /*
     * High FIFO while bit-clocking — charge-pump cannot tolerate ms preemption.
     * Needs root or CAP_SYS_NICE; log hard if denied (S1++ gaps often follow).
     */
    sp.sched_priority = 80;
    rc = sched_setscheduler(0, SCHED_FIFO, &sp);
    if (rc != 0) {
        sp.sched_priority = 50;
        rc = pthread_setschedparam(pthread_self(), SCHED_FIFO, &sp);
    }
    if (rc != 0) {
        sp.sched_priority = 10;
        rc = pthread_setschedparam(pthread_self(), SCHED_FIFO, &sp);
    }
    if (rc != 0) {
        fprintf(stderr,
                "bcpr: SCHED_FIFO failed errno=%d — expect max_gap multi-ms "
                "(need root/CAP_SYS_NICE for bcprd)\n",
                errno);
    } else {
        fprintf(stderr, "bcpr: SCHED_FIFO ok prio=%d cpu0\n", sp.sched_priority);
    }
#endif
}

void bcpr_engine_set_cal(bcpr_engine_t *e, int cal_mode)
{
    int i;
    if (!e) {
        return;
    }
    if (cal_mode < BCPR_CAL_OFF || cal_mode > BCPR_CAL_ALT) {
        cal_mode = BCPR_CAL_OFF;
    }
    e->cal_mode = cal_mode;
    for (i = 0; i < e->n; i++) {
        bcpr_ser12_set_cal(&e->dev[i].ser12, cal_mode);
    }
}

static int64_t now_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (int64_t)ts.tv_sec * 1000000000LL + (int64_t)ts.tv_nsec;
}

static void emit_tx_telemetry(const bcpr_engine_t *e, bcpr_device_t *d,
                              int64_t ptt_off_ns)
{
    char path[192];
    FILE *f;
    int64_t dur_ns;
    unsigned mean_gap = 0;
    double thr_rate = 0.0;
    double ptt_ms;

    if (!d || !e) {
        return;
    }
    dur_ns = ptt_off_ns - d->ptt_on_ns;
    if (dur_ns < 0) {
        dur_ns = 0;
    }
    ptt_ms = (double)dur_ns / 1.0e6;
    if (d->tick_count > 0) {
        mean_gap = (unsigned)(d->gap_sum_us / d->tick_count);
    }
    if (ptt_ms > 0.5) {
        thr_rate = (double)d->thr_writes * 1000.0 / ptt_ms;
    }
    fprintf(stderr,
            "bcpr: tx-telemetry bc%d ptt_ms=%.1f thr_writes=%u thr_rate=%.0f "
            "max_tick_gap_us=%u mean_gap_us=%u gaps_gt_2x=%u baud_us=%u\n",
            d->index, ptt_ms, d->thr_writes, thr_rate, d->max_tick_gap_us,
            mean_gap, d->gaps_gt_2x, d->ser12.baud_us);
    if (e->cfg.dry_run || e->cfg.state_dir[0] == '\0') {
        return;
    }
    snprintf(path, sizeof(path), "%s/tx-last-bc%d", e->cfg.state_dir, d->index);
    f = fopen(path, "w");
    if (!f) {
        return;
    }
    fprintf(f,
            "ptt_on_ns=%lld\nptt_off_ns=%lld\nptt_ms=%.1f\nthr_writes=%u\n"
            "thr_rate=%.0f\nmax_tick_gap_us=%u\nmean_gap_us=%u\n"
            "gaps_gt_2x=%u\nbaud_us=%u\ntick_count=%u\n",
            (long long)d->ptt_on_ns, (long long)ptt_off_ns, ptt_ms,
            d->thr_writes, thr_rate, d->max_tick_gap_us, mean_gap,
            d->gaps_gt_2x, d->ser12.baud_us, d->tick_count);
    fclose(f);
}

static unsigned tx_baud_div(const bcpr_device_t *d)
{
    unsigned baud = d->ser12.baud ? d->ser12.baud : 1200u;
    unsigned div = (115200u / 8u) / baud;
    return div ? div : 1u;
}

static void tick_device(bcpr_engine_t *e, bcpr_device_t *d, rx_ctx_t *ctx)
{
    int cts = 0;
    int mcr = 0x0d;
    int do_thr = 0;
    unsigned t = now_us();
    int ptt;
    int keyed = d->ptt_was; /* already in TX — keep path minimal for TXD pump */

    if (!e->cfg.dry_run && !keyed) {
        unsigned char msr = bcpr_uart_msr(d->cfg.iobase);
        cts = (msr & 0x10) ? 1 : 0;
        if (d->ser12.opt_dcd > 0) {
            d->hdlc.dcd = (msr & 0x80) ? 1 : 0;
        } else if (d->ser12.opt_dcd < 0) {
            d->hdlc.dcd = (msr & 0x80) ? 0 : 1;
        }
    }

    /* S0: tick-gap while PTT keyed (full monotonic µs; unsigned wrap OK). */
    if (d->ptt_was && d->last_tick_us) {
        unsigned gap = t - d->last_tick_us;
        unsigned lim2;
        if (gap > d->max_tick_gap_us) {
            d->max_tick_gap_us = gap;
        }
        d->gap_sum_us += gap;
        d->tick_count++;
        lim2 = d->ser12.baud_us * 2u;
        if (lim2 < 2u) {
            lim2 = 2u;
        }
        if (gap > lim2) {
            d->gaps_gt_2x++;
        }
    }
    d->last_tick_us = t;

    bcpr_ser12_tick(&d->ser12, &d->hdlc, cts, &mcr, &do_thr, t);
    ptt = d->ser12.ptt_hw ? 1 : 0;

    if (ptt && !d->ptt_was) {
        d->ptt_on_ns = now_ns();
        d->thr_writes = 0;
        d->max_tick_gap_us = 0;
        d->gap_sum_us = 0;
        d->tick_count = 0;
        d->gaps_gt_2x = 0;
        d->last_tick_us = t;
        d->tx_div_set = 0;
    } else if (!ptt && d->ptt_was) {
        if (!e->cfg.dry_run) {
            /* Match baycom_ser_fdx: idle divisor only on PTT fall. */
            bcpr_uart_set_divisor(d->cfg.iobase, 115200u / 100u / 8u);
            d->tx_div_set = 0;
        }
        emit_tx_telemetry(e, d, now_ns());
    }
    d->ptt_was = ptt;

    if (!e->cfg.dry_run) {
        /*
         * S1++: set baud_uartdiv once on PTT rise (kernel ser12_fdx).
         * Re-writing divisor every bit toggles DLAB mid-shift → intermittent
         * TXD charge-pump starve while MCR RTS still keys (MCR PASS / no RF).
         */
        if (ptt && !d->tx_div_set) {
            bcpr_uart_set_divisor(d->cfg.iobase, tx_baud_div(d));
            d->tx_div_set = 1;
        }
        /* Kernel order: THR 0x00 first (charge-pump), then MCR bit+PTT.
         * txd_bias=steady: skip THR — break already holds TXD SPACE;
         * pulse is Sailer default (framing edges feed BayCom pump). */
        if (d->cfg.txd_bias == BCPR_TXD_STEADY) {
            if (!d->break_set) {
                bcpr_uart_set_break(d->cfg.iobase, 1);
                d->break_set = 1;
            }
            if (ptt) {
                d->thr_writes++; /* count pump-equivalent ticks for telem */
            }
        } else {
            if (d->break_set) {
                bcpr_uart_set_break(d->cfg.iobase, 0);
                d->break_set = 0;
            }
            if (do_thr) {
                bcpr_uart_thr00(d->cfg.iobase);
                if (ptt) {
                    d->thr_writes++;
                }
            }
        }
        bcpr_uart_mcr(d->cfg.iobase, (unsigned char)mcr);
    }

    /* Defer HDLC RX drain while keyed — keeps bit deadline tight (S1+). */
    if (!ptt) {
        ctx->e = e;
        ctx->idx = d->index;
        bcpr_hdlc_receiver(&d->hdlc, on_frame_ctx, ctx);
    }
}

/* Publish Soft-/hard-DCD for RX-before-TX gates (state_dir/dcd-bcN).
 * Also refresh rx-activity-bcN whenever Soft-DCD is asserted so smoke/L3
 * can delete-and-rewait without a permanent false miss when dcd flickers. */
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
        snprintf(path, sizeof(path), "%s/rx-activity-bc%d", e->cfg.state_dir,
                 d->index);
        f = fopen(path, "w");
        if (f) {
            /* Latch: dcd=1 → activity; dcd=0 clears so L3 needs live Soft-DCD. */
            fprintf(f, "rx_activity=%d\n", dcd ? 1 : 0);
            fclose(f);
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
    int64_t bit_deadline_ns = 0;

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
        int any_ptt = 0;
        unsigned baud_us = e->dev[0].ser12.baud_us;

        for (i = 0; i < e->n; i++) {
            tick_device(e, &e->dev[i], &ctx);
            if (e->dev[i].ser12.ptt_hw || e->dev[i].ptt_was) {
                any_ptt = 1;
            }
        }
        /* ~100 ms at 1200 baud — skip file I/O while PTT (stretches TXD gaps). */
        if ((++tick % 120u) == 0u && !any_ptt) {
            publish_dcd_status(e);
        }

        /*
         * S1/S1+: while PTT, absolute bit deadline + busy-spin (not
         * nanosleep). THRE wait alone stacks with tick work → ~2× baud gaps.
         * Idle RX keeps absolute nanosleep schedule.
         */
        if (any_ptt && !e->cfg.dry_run) {
            int64_t now;

            if (baud_us < 200u) {
                baud_us = 200u;
            }
            now = now_ns();
            if (bit_deadline_ns == 0 ||
                now > bit_deadline_ns + (int64_t)baud_us * 1000LL * 4) {
                /* PTT edge / large slip — resync. */
                bit_deadline_ns = now + (int64_t)baud_us * 1000LL;
            } else {
                bit_deadline_ns += (int64_t)baud_us * 1000LL;
            }
            /*
             * Pure busy-spin to absolute bit deadline — no nanosleep, no
             * wait_thre syscalls (those stacked gaps and starved the pump).
             * Target: thr_writes ≈ baud for whole PTT; max_gap < ~2× baud_us.
             */
            while (now_ns() < bit_deadline_ns) {
            }
            clock_gettime(CLOCK_MONOTONIC, &next);
        } else {
            bit_deadline_ns = 0;
            next.tv_nsec += (long)period_ns;
            while (next.tv_nsec >= 1000000000L) {
                next.tv_nsec -= 1000000000L;
                next.tv_sec++;
            }
            while (clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &next,
                                   NULL) == EINTR) {
            }
        }
        if (e->run_seconds > 0 && (time(NULL) - t0) >= e->run_seconds) {
            break;
        }
    }
    return 0;
}
