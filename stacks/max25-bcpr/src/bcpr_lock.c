/*
 * Exclusive lock on owned COM ports only (flock + optional setserial uart none).
 * Pass real IRQ — refuse mismatch. See vault IRQ/lock contract.
 */
#define _GNU_SOURCE
#include "bcpr/bcpr_lock.h"

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

static void tty_basename(const char *serial, char *out, size_t out_sz)
{
    const char *p = strrchr(serial, '/');
    p = p ? p + 1 : serial;
    snprintf(out, out_sz, "%s", p);
}

int bcpr_lock_verify_irq(const char *serial, unsigned expect_irq,
                         unsigned *got_irq, unsigned *got_io)
{
    char name[64];
    char path[128];
    char buf[64];
    FILE *f;
    unsigned irq = 0;
    unsigned io = 0;

    if (!serial || !serial[0]) {
        return -1;
    }
    tty_basename(serial, name, sizeof(name));
    snprintf(path, sizeof(path), "/sys/class/tty/%s/irq", name);
    f = fopen(path, "r");
    if (f) {
        if (fgets(buf, sizeof(buf), f)) {
            irq = (unsigned)strtoul(buf, NULL, 0);
        }
        fclose(f);
    } else {
        /* Fallback: setserial -g (best-effort). */
        char cmd[256];
        FILE *p;
        snprintf(cmd, sizeof(cmd), "setserial -g %s 2>/dev/null", serial);
        p = popen(cmd, "r");
        if (!p) {
            return -1;
        }
        if (fgets(buf, sizeof(buf), p)) {
            char *ip = strstr(buf, "IRQ: ");
            char *pp = strstr(buf, "Port: ");
            if (ip) {
                irq = (unsigned)strtoul(ip + 5, NULL, 0);
            }
            if (pp) {
                io = (unsigned)strtoul(pp + 6, NULL, 0);
            }
        }
        pclose(p);
    }

    snprintf(path, sizeof(path), "/sys/class/tty/%s/iomem_base", name);
    f = fopen(path, "r");
    if (f) {
        if (fgets(buf, sizeof(buf), f)) {
            io = (unsigned)strtoul(buf, NULL, 0);
        }
        fclose(f);
    }

    if (got_irq) {
        *got_irq = irq;
    }
    if (got_io) {
        *got_io = io;
    }
    if (expect_irq == 0) {
        return -1; /* never invent; refuse zero when required */
    }
    if (irq == 0 || irq != expect_irq) {
        return -1;
    }
    return 0;
}

static int make_lock_path(const bcpr_dev_config_t *dev, char *out, size_t sz)
{
    char name[64];
    const char *dir = "/var/run/max25-bcpr";
    tty_basename(dev->serial, name, sizeof(name));
    if (name[0] == '\0') {
        return -1;
    }
    snprintf(out, sz, "%s/lock-%s", dir, name);
    return 0;
}

int bcpr_lock_acquire(bcpr_port_lock_t *lk, const bcpr_dev_config_t *dev,
                      int dry_run)
{
    char lockpath[192];
    unsigned got_irq = 0, got_io = 0;

    if (!lk || !dev) {
        return -1;
    }
    memset(lk, 0, sizeof(*lk));
    snprintf(lk->serial, sizeof(lk->serial), "%s", dev->serial);
    lk->iobase = dev->iobase;
    lk->irq = dev->irq;
    lk->lock_fd = -1;
    lk->dry_run = dry_run ? 1 : 0;

    if (dry_run) {
        return 0;
    }
    if (!dev->serial[0] || dev->irq == 0 || dev->iobase == 0) {
        return -1;
    }
    if (bcpr_lock_verify_irq(dev->serial, dev->irq, &got_irq, &got_io) != 0) {
        fprintf(stderr,
                "bcpr: IRQ mismatch or unreadable for %s (expect %u got %u)\n",
                dev->serial, dev->irq, got_irq);
        return -1;
    }
    if (got_io && got_io != dev->iobase) {
        fprintf(stderr,
                "bcpr: iobase mismatch for %s (expect 0x%x got 0x%x)\n",
                dev->serial, dev->iobase, got_io);
        return -1;
    }

    if (make_lock_path(dev, lockpath, sizeof(lockpath)) != 0) {
        return -1;
    }
    (void)mkdir("/var/run/max25-bcpr", 0755);
    lk->lock_fd = open(lockpath, O_RDWR | O_CREAT | O_CLOEXEC, 0644);
    if (lk->lock_fd < 0) {
        perror("bcpr lock open");
        return -1;
    }
    if (flock(lk->lock_fd, LOCK_EX | LOCK_NB) != 0) {
        fprintf(stderr, "bcpr: port %s already locked\n", dev->serial);
        close(lk->lock_fd);
        lk->lock_fd = -1;
        return -1;
    }

    /* Release 8250 claim on this COM only so userspace can bit-bang. */
    {
        char cmd[256];
        snprintf(cmd, sizeof(cmd), "setserial %s uart none 2>/dev/null",
                 dev->serial);
        if (system(cmd) == 0) {
            lk->uart_released = 1;
        }
    }
    return 0;
}

void bcpr_lock_release(bcpr_port_lock_t *lk)
{
    if (!lk) {
        return;
    }
    if (lk->dry_run) {
        memset(lk, 0, sizeof(*lk));
        lk->lock_fd = -1;
        return;
    }
    if (lk->uart_released && lk->serial[0]) {
        char cmd[256];
        /* Restore 16550A claim — best effort. */
        snprintf(cmd, sizeof(cmd),
                 "setserial %s uart 16550A port 0x%x irq %u 2>/dev/null",
                 lk->serial, lk->iobase, lk->irq);
        (void)system(cmd);
        lk->uart_released = 0;
    }
    if (lk->lock_fd >= 0) {
        flock(lk->lock_fd, LOCK_UN);
        close(lk->lock_fd);
        lk->lock_fd = -1;
    }
    memset(lk, 0, sizeof(*lk));
    lk->lock_fd = -1;
}
