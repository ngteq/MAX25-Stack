#ifndef BCPR_ENGINE_H
#define BCPR_ENGINE_H

#include "bcpr/bcpr_config.h"
#include "bcpr/bcpr_hdlc.h"
#include "bcpr/bcpr_lock.h"
#include "bcpr/bcpr_ser12.h"

#include <stdint.h>

struct bcpr_device {
    bcpr_dev_config_t cfg;
    bcpr_port_lock_t lock;
    bcpr_ser12_t ser12;
    bcpr_hdlc_t hdlc;
    int running;
    int index; /* 0 = bc0, 1 = bc1 */
    /* S0 TX telemetry (reset on PTT rise, emit on PTT fall). */
    int ptt_was;
    int64_t ptt_on_ns;
    unsigned thr_writes;
    unsigned max_tick_gap_us;
    unsigned last_tick_us;
    unsigned tick_count;       /* bit ticks while keyed */
    unsigned long long gap_sum_us; /* for mean gap */
    unsigned gaps_gt_2x;       /* gaps > 2× baud_us */
    int tx_div_set;            /* UART baud_uartdiv applied for this PTT */
    int break_set;             /* txd_bias=steady: LCR break asserted */
};

typedef void (*bcpr_rx_fn)(int dev_idx, const uint8_t *kiss, int len, void *ud);

struct bcpr_engine {
    bcpr_config_t cfg;
    bcpr_device_t dev[BCPR_MAX_DEVICES];
    int n;
    volatile int stop;
    bcpr_rx_fn on_rx;
    void *on_rx_ud;
    /* 0 = forever; >0 stop after wall-clock seconds (tests / dry-run). */
    int run_seconds;
    /* BCPR_CAL_* on all enabled devices; 0 = normal KISS/HDLC. */
    int cal_mode;
};

int bcpr_engine_open(bcpr_engine_t *e, const bcpr_config_t *cfg);
void bcpr_engine_close(bcpr_engine_t *e);
void bcpr_engine_set_rx(bcpr_engine_t *e, bcpr_rx_fn fn, void *ud);
int bcpr_engine_queue_kiss(bcpr_engine_t *e, int dev_idx, const uint8_t *kiss,
                           int len);
/* Apply DOS-style cal (high/low/alt) before bcpr_engine_run. */
void bcpr_engine_set_cal(bcpr_engine_t *e, int cal_mode);
/* Run until e->stop or run_seconds elapses. Dry-run skips UART I/O. */
int bcpr_engine_run(bcpr_engine_t *e);

#endif
