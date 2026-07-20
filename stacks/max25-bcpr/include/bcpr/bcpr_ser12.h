#ifndef BCPR_SER12_H
#define BCPR_SER12_H

#include "bcpr/bcpr_hdlc.h"
#include <stdint.h>

typedef struct bcpr_ser12 {
    unsigned baud;
    unsigned baud_us;
    int opt_dcd; /* 0 soft, 1 hard, -1 hard inv */
    unsigned char tx_bit;
    unsigned char last_rxbit;
    int dcd_sum0, dcd_sum1, dcd_sum2;
    int dcd_time;
    unsigned pll_time;
    unsigned txshreg;
    unsigned shreg;
    int ptt_hw; /* modem PTT keyed */
} bcpr_ser12_t;

void bcpr_ser12_init(bcpr_ser12_t *s, unsigned baud, int opt_dcd);
void bcpr_ser12_set_mode(bcpr_ser12_t *s, const char *mode, unsigned *baud_out);
/* One bit-time / tick: sample cts (0/1), drive *mcr_out / *thr_feed */
void bcpr_ser12_tick(bcpr_ser12_t *s, bcpr_hdlc_t *h, int cts, int *mcr_out,
                     int *do_thr00, unsigned now_us);

#endif
