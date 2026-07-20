#ifndef BCPR_UART_H
#define BCPR_UART_H

#include <stdint.h>

/* When set, all UART I/O is a no-op (CI / --dry-run). */
void bcpr_uart_set_dry_run(int on);
int bcpr_uart_ioperm(unsigned iobase, int on);
void bcpr_uart_outb(unsigned char val, unsigned port);
unsigned char bcpr_uart_inb(unsigned port);
void bcpr_uart_set_divisor(unsigned iobase, unsigned divisor);
void bcpr_uart_open_ser12(unsigned iobase);
void bcpr_uart_close_ser12(unsigned iobase);
unsigned char bcpr_uart_msr(unsigned iobase);
void bcpr_uart_mcr(unsigned iobase, unsigned char v);
void bcpr_uart_thr00(unsigned iobase);
/* LCR bit6 Set Break — force TXD continuous SPACE (RS-232 +V). Clear = normal. */
void bcpr_uart_set_break(unsigned iobase, int on);
/* Poll LSR bit5 (THRE) until set or timeout_us. Returns 1 if empty, 0 on timeout. */
int bcpr_uart_wait_thre(unsigned iobase, unsigned timeout_us);

#endif
