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
};

int bcpr_engine_open(bcpr_engine_t *e, const bcpr_config_t *cfg);
void bcpr_engine_close(bcpr_engine_t *e);
void bcpr_engine_set_rx(bcpr_engine_t *e, bcpr_rx_fn fn, void *ud);
int bcpr_engine_queue_kiss(bcpr_engine_t *e, int dev_idx, const uint8_t *kiss,
                           int len);
/* Run until e->stop or run_seconds elapses. Dry-run skips UART I/O. */
int bcpr_engine_run(bcpr_engine_t *e);

#endif
