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
    ser12_rx(s, h, cts ? 1u : 0u, now_us);

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
    /* Receiver drain is owned by bcpr_engine (RX callback). */
}
