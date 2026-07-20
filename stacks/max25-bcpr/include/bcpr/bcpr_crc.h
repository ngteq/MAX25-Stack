#ifndef BCPR_CRC_H
#define BCPR_CRC_H

#include <stddef.h>
#include <stdint.h>

/* CRC-CCITT as used by Linux hdlcdrv (good frame residue 0xf0b8). */
uint16_t bcpr_crc_ccitt(uint16_t crc, const uint8_t *buf, size_t len);
void bcpr_append_crc_ccitt(uint8_t *buffer, int len);
int bcpr_check_crc_ccitt(const uint8_t *buf, int cnt);

#endif
