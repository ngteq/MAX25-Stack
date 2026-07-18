#ifndef BCPR_CONFIG_H
#define BCPR_CONFIG_H

#include "bcpr/bcpr.h"

typedef struct bcpr_dev_config {
    int enabled;
    char serial[64];
    unsigned int iobase;
    unsigned int irq; /* real UART IRQ — must match setserial */
    unsigned int baud;
    char mode[16]; /* ser12* / ser12 / ser12+ */
    char kiss_link[256];
    int tx_delay;  /* 10 ms units */
    int tx_tail;
    int slottime;
    int ppersist;
    int fulldup;
} bcpr_dev_config_t;

typedef struct bcpr_config {
    bcpr_dev_config_t dev[BCPR_MAX_DEVICES];
    int n_dev;
    int dry_run; /* no ioperm / no setserial */
    char state_dir[128];
} bcpr_config_t;

int bcpr_config_load(bcpr_config_t *cfg, const char *path);
void bcpr_config_defaults(bcpr_config_t *cfg);

#endif
