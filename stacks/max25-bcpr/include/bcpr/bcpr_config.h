#ifndef BCPR_CONFIG_H
#define BCPR_CONFIG_H

#include "bcpr/bcpr.h"

/* TXD charge-pump policy (English INI: txd_bias=pulse|steady). */
enum {
    BCPR_TXD_PULSE = 0,  /* Sailer/default: THR←0x00 every tick (framing edges) */
    BCPR_TXD_STEADY = 1  /* TFPCX-class experiment: UART break ≈ continuous SPACE */
};

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
    /*
     * FlexNet SER12.doc PTT watchdog mirror (cal / sustained key):
     * after ptt_wd_key_ms keyed → clear RTS ~ptt_wd_pause_ms → resume.
     * Defaults 14500 / 500. ptt_wd=0 disables.
     */
    int ptt_wd;
    int ptt_wd_key_ms;
    int ptt_wd_pause_ms;
    int txd_bias; /* BCPR_TXD_* */
} bcpr_dev_config_t;

typedef struct bcpr_config {
    bcpr_dev_config_t dev[BCPR_MAX_DEVICES];
    int n_dev;
    int dry_run; /* no ioperm / no setserial */
    char state_dir[128];
    /* Global defaults copied onto devices that omit per-bcN keys. */
    int ptt_wd;
    int ptt_wd_key_ms;
    int ptt_wd_pause_ms;
    int txd_bias;
} bcpr_config_t;

int bcpr_config_load(bcpr_config_t *cfg, const char *path);
void bcpr_config_defaults(bcpr_config_t *cfg);

#endif
