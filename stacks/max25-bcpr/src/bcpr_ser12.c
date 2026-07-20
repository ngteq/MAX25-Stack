#include "bcpr/bcpr_ser12.h"

#include <stdlib.h>
#include <string.h>

void bcpr_ser12_set_mode(bcpr_ser12_t *s, const char *mode, unsigned *baud_out)
{
    unsigned baud = 1200;
    if (mode && strncmp(mode, "ser", 3) == 0) {
        unsigned n = (unsigned)strtoul(mode + 3, NULL, 10);
        if (n >= 3 && n <= 48) {
            baud = n * 100u;
        }
    }
    if (baud_out) {
        *baud_out = baud;
    }
    s->baud = baud;
    s->baud_us = 1000000u / baud;
    if (mode && strchr(mode, '*')) {
        s->opt_dcd = 0;
    } else if (mode && strchr(mode, '+')) {
        s->opt_dcd = -1;
    } else {
        s->opt_dcd = 1;
    }
}

void bcpr_ser12_init(bcpr_ser12_t *s, unsigned baud, int opt_dcd)
{
    memset(s, 0, sizeof(*s));
    s->baud = baud ? baud : 1200;
    s->baud_us = 1000000u / s->baud;
    s->opt_dcd = opt_dcd;
    s->shreg = 0x10000;
    s->dcd_sum0 = 2;
    s->dcd_time = 120;
    s->cal_mode = BCPR_CAL_OFF;
    /* FlexNet SER12.doc defaults until bcpr_ser12_set_ptt_wd(). */
    s->ptt_wd = 1;
    s->ptt_wd_key_us = 14500u * 1000u;
    s->ptt_wd_pause_us = 500u * 1000u;
}

void bcpr_ser12_set_ptt_wd(bcpr_ser12_t *s, int enable, int key_ms, int pause_ms)
{
    if (!s) {
        return;
    }
    s->ptt_wd = enable ? 1 : 0;
    if (key_ms < 1000) {
        key_ms = 1000;
    }
    if (pause_ms < 50) {
        pause_ms = 50;
    }
    s->ptt_wd_key_us = (unsigned)key_ms * 1000u;
    s->ptt_wd_pause_us = (unsigned)pause_ms * 1000u;
    s->ptt_wd_pausing = 0;
    s->ptt_wd_phase_start_us = 0;
}

void bcpr_ser12_set_cal(bcpr_ser12_t *s, int cal_mode)
{
    if (!s) {
        return;
    }
    if (cal_mode < BCPR_CAL_OFF || cal_mode > BCPR_CAL_ALT) {
        cal_mode = BCPR_CAL_OFF;
    }
    s->cal_mode = cal_mode;
    if (cal_mode != BCPR_CAL_OFF) {
        s->ptt_hw = 1;
        if (cal_mode == BCPR_CAL_HIGH) {
            s->tx_bit = 1;
        } else if (cal_mode == BCPR_CAL_LOW) {
            s->tx_bit = 0;
        } else {
            s->tx_bit = 0; /* alt starts low, toggles each tick */
        }
        s->txshreg = 1;
        s->ptt_wd_pausing = 0;
        s->ptt_wd_phase_start_us = 0;
    }
}

/*
 * FlexNet SER12.doc / PAR96: during long calibrate, drop PTT every ~14.5 s for
 * ~500 ms so the radio PTT watchdog can discharge. Mirror for --cal and any
 * sustained key. Logical ptt_hw stays 1 (keep baud divisor / telemetry); only
 * MCR RTS is cleared for the pause window.
 */
static void ser12_apply_ptt_wd(bcpr_ser12_t *s, int *mcr_out, unsigned now_us)
{
    unsigned elapsed;

    if (!s->ptt_wd || !s->ptt_hw) {
        s->ptt_wd_pausing = 0;
        s->ptt_wd_phase_start_us = 0;
        return;
    }
    if (s->ptt_wd_phase_start_us == 0) {
        s->ptt_wd_phase_start_us = now_us ? now_us : 1u;
        s->ptt_wd_pausing = 0;
        return;
    }
    elapsed = now_us - s->ptt_wd_phase_start_us;
    if (!s->ptt_wd_pausing) {
        if (elapsed >= s->ptt_wd_key_us) {
            s->ptt_wd_pausing = 1;
            s->ptt_wd_phase_start_us = now_us ? now_us : 1u;
            *mcr_out = 0x0d; /* RTS clear — PTT off */
        }
        return;
    }
    /* In pause: force idle MCR regardless of cal/HDLC bit. */
    *mcr_out = 0x0d;
    if (elapsed >= s->ptt_wd_pause_us) {
        s->ptt_wd_pausing = 0;
        s->ptt_wd_phase_start_us = now_us ? now_us : 1u;
        /* Next tick restores keyed MCR from cal/HDLC path. */
    }
}

static void ser12_rx(bcpr_ser12_t *s, bcpr_hdlc_t *h, unsigned curs,
                     unsigned now_us)
{
    int timediff;
    int bdus8 = (int)(s->baud_us >> 3);
    int bdus4 = (int)(s->baud_us >> 2);
    int bdus2 = (int)(s->baud_us >> 1);

    timediff = (int)(now_us - s->pll_time);
    /* wrap handling for us modulo ~1s window */
    while (timediff >= 500000) {
        timediff -= 1000000;
    }
    while (timediff <= -500000) {
        timediff += 1000000;
    }
    while (timediff >= bdus2) {
        timediff -= (int)s->baud_us;
        s->pll_time += s->baud_us;
        s->dcd_time--;
        if (s->shreg & 1) {
            bcpr_hdlc_putbits(h, (s->shreg >> 1) ^ 0xffffu);
            s->shreg = 0x10000;
        }
        s->shreg >>= 1;
    }
    if (s->dcd_time <= 0) {
        if (!s->opt_dcd) {
            h->dcd = (s->dcd_sum0 + s->dcd_sum1 + s->dcd_sum2) < 0;
        }
        s->dcd_sum2 = s->dcd_sum1;
        s->dcd_sum1 = s->dcd_sum0;
        s->dcd_sum0 = 2;
        s->dcd_time += 120;
    }
    if (s->last_rxbit != (unsigned char)curs) {
        s->last_rxbit = (unsigned char)curs;
        s->shreg |= 0x10000;
        if (timediff > 0) {
            s->pll_time += (unsigned)bdus8;
        } else {
            s->pll_time += 1000000u - (unsigned)bdus8;
        }
        if (abs(timediff) > bdus4) {
            s->dcd_sum0 += 4;
        } else {
            s->dcd_sum0--;
        }
    }
    while (s->pll_time >= 1000000u) {
        s->pll_time -= 1000000u;
    }
}

void bcpr_ser12_tick(bcpr_ser12_t *s, bcpr_hdlc_t *h, int cts, int *mcr_out,
                     int *do_thr00, unsigned now_us)
{
    *do_thr00 = 1;

    /* DOS cal.exe: continuous PTT + sticky/toggle DTR; no HDLC. */
    if (s->cal_mode != BCPR_CAL_OFF) {
        s->ptt_hw = 1;
        if (s->cal_mode == BCPR_CAL_HIGH) {
            s->tx_bit = 1;
        } else if (s->cal_mode == BCPR_CAL_LOW) {
            s->tx_bit = 0;
        } else {
            s->tx_bit = (unsigned char)!s->tx_bit;
        }
        *mcr_out = 0x0e | (!!s->tx_bit);
        ser12_apply_ptt_wd(s, mcr_out, now_us);
        return;
    }

    /*
     * While PTT: skip Soft-DCD RX PLL — PC-COM charge-pump needs unbroken
     * THR 0x00 @ baud; RX work causes multi-ms TXD gaps → underpowered AFSK.
     */
    if (!s->ptt_hw) {
        ser12_rx(s, h, cts ? 1u : 0u, now_us);
    }

    if (s->ptt_hw) {
        *mcr_out = 0x0e | (!!s->tx_bit);
    } else {
        *mcr_out = 0x0d;
    }

    if (s->ptt_hw) {
        if (s->txshreg <= 1) {
            s->txshreg = 0x10000u | bcpr_hdlc_getbits(h);
            if (!bcpr_hdlc_ptt(h)) {
                s->ptt_hw = 0;
                *mcr_out = 0x0d;
                ser12_apply_ptt_wd(s, mcr_out, now_us);
                return;
            }
        }
        s->tx_bit = (unsigned char)(!(s->tx_bit ^ (s->txshreg & 1)));
        s->txshreg >>= 1;
    } else {
        bcpr_hdlc_arbitrate(h);
        if (bcpr_hdlc_ptt(h)) {
            s->txshreg = 1;
            s->ptt_hw = 1;
        }
    }
    bcpr_hdlc_transmitter(h);
    ser12_apply_ptt_wd(s, mcr_out, now_us);
    /* Receiver drain is owned by bcpr_engine (RX callback). */
}
