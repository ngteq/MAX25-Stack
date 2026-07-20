/*
 * Offline HDLC unit test — CRC, bitstuff roundtrip, no UART / UART I/O.
 */
#include "bcpr/bcpr_crc.h"
#include "bcpr/bcpr_hdlc.h"

#include <stdio.h>
#include <string.h>

static int g_got;
static uint8_t g_rx[BCPR_MAXFLEN + 4];
static int g_rx_len;

static void on_frame(const uint8_t *kiss, int len, void *ud)
{
    (void)ud;
    if (len > 0 && len <= (int)sizeof(g_rx)) {
        memcpy(g_rx, kiss, (size_t)len);
        g_rx_len = len;
        g_got = 1;
    }
}

static int test_crc(void)
{
    uint8_t buf[16];
    memcpy(buf, "TEST", 4);
    bcpr_append_crc_ccitt(buf, 4);
    if (!bcpr_check_crc_ccitt(buf, 6)) {
        fprintf(stderr, "FAIL: CRC check\n");
        return 1;
    }
    buf[0] ^= 0xff;
    if (bcpr_check_crc_ccitt(buf, 6)) {
        fprintf(stderr, "FAIL: CRC should fail on corrupt\n");
        return 1;
    }
    return 0;
}

static int test_roundtrip(void)
{
    bcpr_hdlc_t tx, rx;
    bcpr_channel_t ch = { .tx_delay = 2, .tx_tail = 1, .slottime = 1,
                          .ppersist = 255, .fulldup = 1 };
    uint8_t kiss[32];
    int i, words = 0;

    bcpr_hdlc_init(&tx, 1200, &ch);
    bcpr_hdlc_init(&rx, 1200, &ch);

    kiss[0] = 0; /* KISS DATA */
    memcpy(kiss + 1, "HELLO", 5);
    if (bcpr_hdlc_queue_kiss(&tx, kiss, 6) != 0) {
        fprintf(stderr, "FAIL: queue\n");
        return 1;
    }
    bcpr_hdlc_arbitrate(&tx);
    if (!bcpr_hdlc_ptt(&tx)) {
        fprintf(stderr, "FAIL: PTT not set\n");
        return 1;
    }

    g_got = 0;
    g_rx_len = 0;
    /* Drain TX bit words into RX putbits path. */
    for (i = 0; i < 4096 && !g_got; i++) {
        unsigned w;
        bcpr_hdlc_transmitter(&tx);
        w = bcpr_hdlc_getbits(&tx);
        if (w) {
            bcpr_hdlc_putbits(&rx, w);
            words++;
            bcpr_hdlc_receiver(&rx, on_frame, NULL);
        } else if (!bcpr_hdlc_ptt(&tx)) {
            bcpr_hdlc_transmitter(&tx);
            /* flush remaining */
            while (!g_got) {
                w = bcpr_hdlc_getbits(&tx);
                if (!w) {
                    break;
                }
                bcpr_hdlc_putbits(&rx, w);
                bcpr_hdlc_receiver(&rx, on_frame, NULL);
            }
            break;
        }
    }

    if (!g_got) {
        fprintf(stderr, "FAIL: no RX frame (words=%d)\n", words);
        return 1;
    }
    if (g_rx_len < 6 || g_rx[0] != 0 || memcmp(g_rx + 1, "HELLO", 5) != 0) {
        fprintf(stderr, "FAIL: payload mismatch len=%d\n", g_rx_len);
        return 1;
    }
    return 0;
}

int main(void)
{
    int rc = 0;
    rc |= test_crc();
    rc |= test_roundtrip();
    if (rc == 0) {
        puts("OK: test_hdlc_offline");
    }
    return rc;
}
