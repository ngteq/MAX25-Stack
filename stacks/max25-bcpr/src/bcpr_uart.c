/*
 * Userspace 8250/16550 register access for SER12 bit-bang.
 * Prefer ioperm(2); fall back to /dev/port. Dry-run: no-ops.
 * Algorithms match Linux baycom_ser_fdx (see NOTICE.md).
 */
#define _GNU_SOURCE
#include "bcpr/bcpr_uart.h"

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/io.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

static int g_dry;
static int g_port_fd = -1;
static int g_ioperm_ok;

void bcpr_uart_set_dry_run(int on)
{
    g_dry = on ? 1 : 0;
}

int bcpr_uart_ioperm(unsigned iobase, int on)
{
    if (g_dry) {
        return 0;
    }
    if (ioperm((unsigned long)iobase, 8, on ? 1 : 0) == 0) {
        g_ioperm_ok = on ? 1 : 0;
        return 0;
    }
    /* Fallback: /dev/port (needs CAP_SYS_RAWIO / root). */
    if (on) {
        if (g_port_fd < 0) {
            g_port_fd = open("/dev/port", O_RDWR | O_CLOEXEC);
            if (g_port_fd < 0) {
                return -1;
            }
        }
        return 0;
    }
    if (g_port_fd >= 0) {
        close(g_port_fd);
        g_port_fd = -1;
    }
    g_ioperm_ok = 0;
    return 0;
}

static int port_rw(unsigned port, int do_write, unsigned char *val)
{
    off_t off = (off_t)port;
    if (g_port_fd < 0) {
        return -1;
    }
    if (lseek(g_port_fd, off, SEEK_SET) != off) {
        return -1;
    }
    if (do_write) {
        return (write(g_port_fd, val, 1) == 1) ? 0 : -1;
    }
    return (read(g_port_fd, val, 1) == 1) ? 0 : -1;
}

void bcpr_uart_outb(unsigned char val, unsigned port)
{
    if (g_dry) {
        return;
    }
    if (g_ioperm_ok) {
        outb(val, port);
        return;
    }
    (void)port_rw(port, 1, &val);
}

unsigned char bcpr_uart_inb(unsigned port)
{
    unsigned char v = 0;
    if (g_dry) {
        return 0;
    }
    if (g_ioperm_ok) {
        return inb(port);
    }
    (void)port_rw(port, 0, &v);
    return v;
}

void bcpr_uart_set_divisor(unsigned iobase, unsigned divisor)
{
    unsigned char lcr;
    if (g_dry) {
        return;
    }
    lcr = bcpr_uart_inb(iobase + 3);
    bcpr_uart_outb((unsigned char)(lcr | 0x80), iobase + 3); /* DLAB */
    bcpr_uart_outb((unsigned char)(divisor & 0xff), iobase + 0);
    bcpr_uart_outb((unsigned char)((divisor >> 8) & 0xff), iobase + 1);
    bcpr_uart_outb((unsigned char)(lcr & 0x7f), iobase + 3);
}

void bcpr_uart_open_ser12(unsigned iobase)
{
    if (g_dry) {
        return;
    }
    /* Match baycom_ser_fdx open: FIFO off, 6-bit word, IER THRE+MSR. */
    bcpr_uart_outb(0x00, iobase + 2); /* FCR */
    bcpr_uart_outb(0x01, iobase + 3); /* LCR 6N1 */
    bcpr_uart_outb(0x0a, iobase + 1); /* IER */
    bcpr_uart_outb(0x0d, iobase + 4); /* MCR idle */
    bcpr_uart_thr00(iobase);
}

void bcpr_uart_close_ser12(unsigned iobase)
{
    if (g_dry) {
        return;
    }
    bcpr_uart_outb(0x00, iobase + 1); /* IER off */
    bcpr_uart_outb(0x01, iobase + 4); /* MCR close */
}

unsigned char bcpr_uart_msr(unsigned iobase)
{
    if (g_dry) {
        return 0;
    }
    return bcpr_uart_inb(iobase + 6);
}

void bcpr_uart_mcr(unsigned iobase, unsigned char v)
{
    if (g_dry) {
        return;
    }
    bcpr_uart_outb(v, iobase + 4);
}

void bcpr_uart_thr00(unsigned iobase)
{
    if (g_dry) {
        return;
    }
    bcpr_uart_outb(0x00, iobase + 0);
}

void bcpr_uart_set_break(unsigned iobase, int on)
{
    unsigned char lcr;
    if (g_dry) {
        return;
    }
    /*
     * 8250 LCR bit6 (Set Break): force TXD to continuous SPACE (RS-232 +V).
     * Honest limit: THR writes alone cannot hold DC-steady TXD — each byte is
     * framed (start/data/stop). Break is the practical TFPCX-class approximation
     * (docs: static ≈ +12 V modem supply). Does not change MCR/PTT.
     */
    lcr = bcpr_uart_inb(iobase + 3);
    if (on) {
        bcpr_uart_outb((unsigned char)(lcr | 0x40), iobase + 3);
    } else {
        bcpr_uart_outb((unsigned char)(lcr & (unsigned char)~0x40), iobase + 3);
    }
}

int bcpr_uart_wait_thre(unsigned iobase, unsigned timeout_us)
{
    struct timespec t0, now;
    unsigned char lsr;

    if (g_dry) {
        return 1;
    }
    if (clock_gettime(CLOCK_MONOTONIC, &t0) != 0) {
        return 0;
    }
    for (;;) {
        lsr = bcpr_uart_inb(iobase + 5);
        if (lsr & 0x20) { /* THRE */
            return 1;
        }
        if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) {
            return 0;
        }
        {
            long elapsed = (long)(now.tv_sec - t0.tv_sec) * 1000000L +
                           (now.tv_nsec - t0.tv_nsec) / 1000L;
            if (elapsed >= (long)timeout_us) {
                return 0;
            }
        }
    }
}
