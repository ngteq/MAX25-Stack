#ifndef BCPR_LOCK_H
#define BCPR_LOCK_H

#include "bcpr/bcpr_config.h"

typedef struct bcpr_port_lock {
    char serial[64];
    unsigned iobase;
    unsigned irq;
    int lock_fd;
    int uart_released;
    int dry_run;
} bcpr_port_lock_t;

/* Exclusive COM lock: flock + setserial uart none. irq must match setserial. */
int bcpr_lock_acquire(bcpr_port_lock_t *lk, const bcpr_dev_config_t *dev,
                      int dry_run);
void bcpr_lock_release(bcpr_port_lock_t *lk);
int bcpr_lock_verify_irq(const char *serial, unsigned expect_irq,
                         unsigned *got_irq, unsigned *got_io);

#endif
