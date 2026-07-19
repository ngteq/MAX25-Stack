#include "bcpr/bcpr_hdlc.h"
#include "bcpr/bcpr_crc.h"

#include <string.h>
#include <stdlib.h>

static int hbuf_empty(const bcpr_hbuf_t *hb)
{
    return hb->rd == hb->wr;
}

static int hbuf_full(const bcpr_hbuf_t *hb)
{
    return !((BCPR_HDLC_BUF - 1 + hb->rd - hb->wr) % BCPR_HDLC_BUF);
}

static void hbuf_put(bcpr_hbuf_t *hb, uint16_t val)
{
    unsigned newp = (hb->wr + 1) % BCPR_HDLC_BUF;
    if (newp != hb->rd) {
        hb->buf[hb->wr] = val;
        hb->wr = newp;
    }
}

static uint16_t hbuf_get(bcpr_hbuf_t *hb)
{
    uint16_t val;
    if (hb->rd == hb->wr) {
        return 0;
    }
    val = hb->buf[hb->rd];
    hb->rd = (hb->rd + 1) % BCPR_HDLC_BUF;
    return val;
}

#define tenms_to_2flags(h, tenms) (((tenms) * (h)->bitrate) / 100 / 16)

void bcpr_hdlc_init(bcpr_hdlc_t *h, int bitrate, const bcpr_channel_t *ch)
{
    memset(h, 0, sizeof(*h));
    h->bitrate = bitrate > 0 ? bitrate : 1200;
    if (ch) {
        h->ch = *ch;
    } else {
        h->ch.tx_delay = 35;
        h->ch.tx_tail = 2;
        h->ch.slottime = 10;
        h->ch.ppersist = 40;
        h->ch.fulldup = 0;
    }
    h->slotcnt = 1;
    h->rx_bp = h->rx_buffer;
    h->tx_bp = h->tx_buffer;
}

void bcpr_hdlc_putbits(bcpr_hdlc_t *h, unsigned bits)
{
    hbuf_put(&h->rx_hbuf, (uint16_t)(bits & 0xffff));
}

unsigned bcpr_hdlc_getbits(bcpr_hdlc_t *h)
{
    if (hbuf_empty(&h->tx_hbuf)) {
        h->ptt = 0;
        return 0;
    }
    return hbuf_get(&h->tx_hbuf);
}

int bcpr_hdlc_ptt(const bcpr_hdlc_t *h)
{
    return h->ptt;
}

int bcpr_hdlc_queue_kiss(bcpr_hdlc_t *h, const uint8_t *kiss, int len)
{
    if (!kiss || len < 2 || len - 1 > BCPR_MAXFLEN) {
        return -1;
    }
    if (h->have_pending || h->ptt) {
        return -1;
    }
    /* strip KISS command byte */
    memcpy(h->pending, kiss + 1, (size_t)(len - 1));
    h->pending_len = len - 1;
    h->have_pending = 1;
    return 0;
}

static int hdlc_rx_add_bytes(bcpr_hdlc_t *h, unsigned bits, int num)
{
    int added = 0;
    while (h->rx_state && num >= 8) {
        if (h->rx_len >= (int)sizeof(h->rx_buffer)) {
            h->rx_state = 0;
            return 0;
        }
        *h->rx_bp++ = (uint8_t)(bits >> (32 - num));
        h->rx_len++;
        num -= 8;
        added += 8;
    }
    return added;
}

static void hdlc_rx_flag(bcpr_hdlc_t *h,
                         void (*on_frame)(const uint8_t *kiss, int len, void *ud),
                         void *ud)
{
    uint8_t kiss[BCPR_MAXFLEN + 3];
    int pkt_len;
    if (h->rx_len < 4) {
        return;
    }
    if (!bcpr_check_crc_ccitt(h->rx_buffer, h->rx_len)) {
        return;
    }
    pkt_len = h->rx_len - 2 + 1;
    kiss[0] = 0;
    memcpy(kiss + 1, h->rx_buffer, (size_t)(pkt_len - 1));
    if (on_frame) {
        on_frame(kiss, pkt_len, ud);
    }
}

void bcpr_hdlc_receiver(bcpr_hdlc_t *h,
                        void (*on_frame)(const uint8_t *kiss, int len, void *ud),
                        void *ud)
{
    int i;
    unsigned mask1, mask2, mask3, mask4, mask5, mask6, word;

    while (!hbuf_empty(&h->rx_hbuf)) {
        word = hbuf_get(&h->rx_hbuf);
        h->bitstream >>= 16;
        h->bitstream |= word << 16;
        h->bitbuf >>= 16;
        h->bitbuf |= word << 16;
        h->numbits += 16;
        for (i = 15, mask1 = 0x1fc00, mask2 = 0x1fe00, mask3 = 0x0fc00,
            mask4 = 0x1f800, mask5 = 0xf800, mask6 = 0xffff;
             i >= 0; i--, mask1 <<= 1, mask2 <<= 1, mask3 <<= 1, mask4 <<= 1,
                       mask5 <<= 1, mask6 = (mask6 << 1) | 1) {
            if ((h->bitstream & mask1) == mask1) {
                h->rx_state = 0;
            } else if ((h->bitstream & mask2) == mask3) {
                if (h->rx_state) {
                    hdlc_rx_add_bytes(h, h->bitbuf << (8 + i),
                                      h->numbits - 8 - i);
                    hdlc_rx_flag(h, on_frame, ud);
                }
                h->rx_len = 0;
                h->rx_bp = h->rx_buffer;
                h->rx_state = 1;
                h->numbits = i;
            } else if ((h->bitstream & mask4) == mask5) {
                h->numbits--;
                h->bitbuf = (h->bitbuf & (~mask6)) |
                            ((h->bitbuf & mask6) << 1);
            }
        }
        h->numbits -= hdlc_rx_add_bytes(h, h->bitbuf, h->numbits);
    }
}

void bcpr_hdlc_transmitter(bcpr_hdlc_t *h)
{
    unsigned mask1, mask2, mask3;
    int i;

    for (;;) {
        if (h->tx_numbits >= 16) {
            if (hbuf_full(&h->tx_hbuf)) {
                return;
            }
            hbuf_put(&h->tx_hbuf, (uint16_t)(h->tx_bitbuf & 0xffff));
            h->tx_bitbuf >>= 16;
            h->tx_numbits -= 16;
        }
        switch (h->tx_state) {
        default:
            return;
        case 0:
        case 1:
            if (h->numflags) {
                h->numflags--;
                h->tx_bitbuf |= 0x7e7e << h->tx_numbits;
                h->tx_numbits += 16;
                break;
            }
            if (h->tx_state == 1) {
                return;
            }
            if (!h->have_pending) {
                int flgs = tenms_to_2flags(h, h->ch.tx_tail);
                if (flgs < 2) {
                    flgs = 2;
                }
                h->tx_state = 1;
                h->numflags = flgs;
                break;
            }
            /* pending[] holds up to BCPR_MAXFLEN; reject only oversize / empty. */
            if (h->pending_len > BCPR_MAXFLEN || h->pending_len < 2) {
                h->have_pending = 0;
                h->tx_state = 0;
                h->numflags = 1;
                break;
            }
            memcpy(h->tx_buffer, h->pending, (size_t)h->pending_len);
            h->have_pending = 0;
            h->tx_bp = h->tx_buffer;
            bcpr_append_crc_ccitt(h->tx_buffer, h->pending_len);
            h->tx_len = h->pending_len + 2;
            h->tx_state = 2;
            h->tx_bitstream = 0;
            break;
        case 2:
            if (!h->tx_len) {
                h->tx_state = 0;
                h->numflags = 1;
                break;
            }
            h->tx_len--;
            h->tx_bitbuf |= *h->tx_bp << h->tx_numbits;
            h->tx_bitstream >>= 8;
            h->tx_bitstream |= (*h->tx_bp++) << 16;
            mask1 = 0x1f000;
            mask2 = 0x10000;
            mask3 = 0xffffffffu >> (31 - h->tx_numbits);
            h->tx_numbits += 8;
            for (i = 0; i < 8;
                 i++, mask1 <<= 1, mask2 <<= 1, mask3 = (mask3 << 1) | 1) {
                if ((h->tx_bitstream & mask1) != mask1) {
                    continue;
                }
                h->tx_bitstream &= ~mask2;
                h->tx_bitbuf = (h->tx_bitbuf & mask3) |
                               ((h->tx_bitbuf & (~mask3)) << 1);
                h->tx_numbits++;
                mask3 = (mask3 << 1) | 1;
            }
            break;
        }
    }
}

void bcpr_hdlc_arbitrate(bcpr_hdlc_t *h)
{
    if (h->ptt || !h->have_pending) {
        return;
    }
    if (h->ch.fulldup) {
        h->tx_state = 0;
        h->numflags = tenms_to_2flags(h, h->ch.tx_delay);
        h->tx_bitbuf = h->tx_bitstream = 0;
        h->tx_numbits = 0;
        bcpr_hdlc_transmitter(h);
        h->ptt = 1;
        return;
    }
    if (!h->dcd && (--h->slotcnt <= 0)) {
        h->slotcnt = h->ch.slottime;
        if ((rand() % 256) > h->ch.ppersist) {
            return;
        }
        h->tx_state = 0;
        h->numflags = tenms_to_2flags(h, h->ch.tx_delay);
        h->tx_bitbuf = h->tx_bitstream = 0;
        h->tx_numbits = 0;
        bcpr_hdlc_transmitter(h);
        h->ptt = 1;
    }
}
