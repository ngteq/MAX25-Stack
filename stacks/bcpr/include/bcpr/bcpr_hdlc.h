#ifndef BCPR_HDLC_H
#define BCPR_HDLC_H

#include "bcpr/bcpr.h"
#include <stdint.h>

typedef struct bcpr_hbuf {
    unsigned rd, wr;
    uint16_t buf[BCPR_HDLC_BUF];
} bcpr_hbuf_t;

typedef struct bcpr_channel {
    int tx_delay, tx_tail, slottime, ppersist, fulldup;
} bcpr_channel_t;

typedef struct bcpr_hdlc {
    int bitrate;
    bcpr_channel_t ch;
    bcpr_hbuf_t rx_hbuf;
    bcpr_hbuf_t tx_hbuf;
    int rx_state;
    unsigned bitstream, bitbuf;
    int numbits;
    int dcd;
    int rx_len;
    uint8_t *rx_bp;
    uint8_t rx_buffer[BCPR_MAXFLEN + 2];
    int tx_state;
    int numflags;
    unsigned tx_bitstream;
    int ptt;
    int slotcnt;
    unsigned tx_bitbuf;
    int tx_numbits;
    int tx_len;
    uint8_t *tx_bp;
    uint8_t tx_buffer[BCPR_MAXFLEN + 2];
    /* pending KISS payload (without FEND/cmd) queued for TX */
    uint8_t pending[BCPR_MAXFLEN];
    int pending_len;
    int have_pending;
} bcpr_hdlc_t;

void bcpr_hdlc_init(bcpr_hdlc_t *h, int bitrate, const bcpr_channel_t *ch);
void bcpr_hdlc_putbits(bcpr_hdlc_t *h, unsigned bits);
unsigned bcpr_hdlc_getbits(bcpr_hdlc_t *h);
void bcpr_hdlc_receiver(bcpr_hdlc_t *h,
                        void (*on_frame)(const uint8_t *kiss, int len, void *ud),
                        void *ud);
void bcpr_hdlc_transmitter(bcpr_hdlc_t *h);
void bcpr_hdlc_arbitrate(bcpr_hdlc_t *h);
int bcpr_hdlc_queue_kiss(bcpr_hdlc_t *h, const uint8_t *kiss, int len);
int bcpr_hdlc_ptt(const bcpr_hdlc_t *h);

#endif
