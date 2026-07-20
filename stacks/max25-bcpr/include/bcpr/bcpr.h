#ifndef BCPR_H
#define BCPR_H

#include <stdint.h>
#include <stddef.h>

#define BCPR_MAX_DEVICES 2
#define BCPR_SER12_EXTENT 8
#define BCPR_HDLC_BUF 32
#define BCPR_MAXFLEN 400
#define BCPR_MAGIC 0x42525052u /* 'BCPR' */

typedef struct bcpr_device bcpr_device_t;
typedef struct bcpr_engine bcpr_engine_t;

#endif
