#ifndef BCPR_SER12_H
#define BCPR_SER12_H

#include "bcpr/bcpr_hdlc.h"
#include <stdint.h>

/* DOS cal.exe style: sticky/toggle DTR bit + RTS PTT (no HDLC). */
enum {
    BCPR_CAL_OFF = 0,
    BCPR_CAL_HIGH = 1,
    BCPR_CAL_LOW = 2,
    BCPR_CAL_ALT = 3
};

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
    int ptt_hw; /* modem PTT keyed (logical; stays 1 during WD pause) */
    int cal_mode; /* BCPR_CAL_* — bypasses HDLC TX */
    /* FlexNet SER12 PTT WD — see bcpr_ser12_set_ptt_wd(). */
    int ptt_wd;
    unsigned ptt_wd_key_us;
    unsigned ptt_wd_pause_us;
    unsigned ptt_wd_phase_start_us;
    int ptt_wd_pausing; /* 1 → force MCR idle (RTS clear) this tick */
} bcpr_ser12_t;

void bcpr_ser12_init(bcpr_ser12_t *s, unsigned baud, int opt_dcd);
void bcpr_ser12_set_mode(bcpr_ser12_t *s, const char *mode, unsigned *baud_out);
void bcpr_ser12_set_cal(bcpr_ser12_t *s, int cal_mode);
/* FlexNet defaults: key_ms=14500, pause_ms=500. enable=0 disables. */
void bcpr_ser12_set_ptt_wd(bcpr_ser12_t *s, int enable, int key_ms, int pause_ms);
/* One bit-time / tick: sample cts (0/1), drive *mcr_out / *thr_feed */
void bcpr_ser12_tick(bcpr_ser12_t *s, bcpr_hdlc_t *h, int cts, int *mcr_out,
                     int *do_thr00, unsigned now_us);

#endif
