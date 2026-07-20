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

#endif
