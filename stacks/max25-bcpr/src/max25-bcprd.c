/*
 * max25-bcprd — BayCom/based SER12 userspace daemon (MAX25 max25-bcpr plugin).
 * Host face: max25e0:bc0 / bc1 via KISS PTY symlink.
 */
#define _GNU_SOURCE
#include "bcpr/bcpr_config.h"
#include "bcpr/bcpr_engine.h"

#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#if defined(__linux__)
#include <pty.h>
#else
#include <util.h>
#endif

static volatile sig_atomic_t g_stop;
static bcpr_engine_t g_engine;

typedef struct {
    int master_fd;
    char link_path[128];
    int idx;
} kiss_pty_t;

static kiss_pty_t g_pty[BCPR_MAX_DEVICES];
static int g_npty;

static void on_sig(int sig)
{
    (void)sig;
    g_stop = 1;
    g_engine.stop = 1;
}

static int ensure_dir(const char *path)
{
    char tmp[256];
    char *p;
    size_t len;

    if (!path || !path[0]) {
        return -1;
    }
    snprintf(tmp, sizeof(tmp), "%s", path);
    len = strlen(tmp);
    if (len == 0) {
        return -1;
    }
    if (tmp[len - 1] == '/') {
        tmp[len - 1] = '\0';
    }
    for (p = tmp + 1; *p; p++) {
        if (*p == '/') {
            *p = '\0';
            (void)mkdir(tmp, 0755);
            *p = '/';
        }
    }
    return mkdir(tmp, 0755) == 0 || errno == EEXIST ? 0 : -1;
}

static int kiss_pty_open(kiss_pty_t *kp, int idx, const char *link_path,
                         const char *state_dir)
{
    int master = -1, slave = -1;
    char slave_name[128];
    char dir[128];
    const char *slash;

    memset(kp, 0, sizeof(*kp));
    kp->idx = idx;
    kp->master_fd = -1;
    snprintf(kp->link_path, sizeof(kp->link_path), "%s", link_path);

    slash = strrchr(link_path, '/');
    if (slash && slash > link_path) {
        size_t n = (size_t)(slash - link_path);
        if (n >= sizeof(dir)) {
            n = sizeof(dir) - 1;
        }
        memcpy(dir, link_path, n);
        dir[n] = '\0';
        (void)ensure_dir(dir);
    } else {
        (void)ensure_dir(state_dir);
    }

    if (openpty(&master, &slave, slave_name, NULL, NULL) != 0) {
        perror("bcprd openpty");
        return -1;
    }
    close(slave);
    unlink(link_path);
    if (symlink(slave_name, link_path) != 0) {
        perror("bcprd symlink kiss_link");
        close(master);
        return -1;
    }
    fcntl(master, F_SETFL, O_NONBLOCK);
    kp->master_fd = master;
    fprintf(stderr, "max25-bcprd: max25e0:bc%d KISS → %s -> %s\n", idx, link_path,
            slave_name);
    return 0;
}

static void kiss_pty_close(kiss_pty_t *kp)
{
    if (!kp) {
        return;
    }
    if (kp->master_fd >= 0) {
        close(kp->master_fd);
        kp->master_fd = -1;
    }
    if (kp->link_path[0]) {
        unlink(kp->link_path);
    }
}

/* Escape and write one KISS frame (data already has cmd byte). */
static void kiss_write_frame(int fd, const uint8_t *kiss, int len)
{
    uint8_t out[BCPR_MAXFLEN * 2 + 4];
    int o = 0;
    int i;
    if (fd < 0 || !kiss || len <= 0) {
        return;
    }
    out[o++] = 0xC0;
    for (i = 0; i < len && o < (int)sizeof(out) - 2; i++) {
        if (kiss[i] == 0xC0) {
            out[o++] = 0xDB;
            out[o++] = 0xDC;
        } else if (kiss[i] == 0xDB) {
            out[o++] = 0xDB;
            out[o++] = 0xDD;
        } else {
            out[o++] = kiss[i];
        }
    }
    out[o++] = 0xC0;
    (void)write(fd, out, (size_t)o);
}

static void on_rx(int dev_idx, const uint8_t *kiss, int len, void *ud)
{
    int i;
    (void)ud;
    for (i = 0; i < g_npty; i++) {
        if (g_pty[i].idx == dev_idx) {
            kiss_write_frame(g_pty[i].master_fd, kiss, len);
            return;
        }
    }
}

static void kiss_feed(bcpr_engine_t *e, kiss_pty_t *kp)
{
    static uint8_t acc[BCPR_MAX_DEVICES][BCPR_MAXFLEN + 8];
    static int alen[BCPR_MAX_DEVICES];
    static int esc[BCPR_MAX_DEVICES];
    static int in_frame[BCPR_MAX_DEVICES];
    uint8_t buf[512];
    ssize_t n;
    int i;
    int di = kp->idx;

    if (di < 0 || di >= BCPR_MAX_DEVICES) {
        return;
    }
    n = read(kp->master_fd, buf, sizeof(buf));
    if (n <= 0) {
        return;
    }
    for (i = 0; i < (int)n; i++) {
        uint8_t b = buf[i];
        if (!in_frame[di]) {
            if (b == 0xC0) {
                in_frame[di] = 1;
                alen[di] = 0;
                esc[di] = 0;
            }
            continue;
        }
        if (esc[di]) {
            esc[di] = 0;
            if (b == 0xDC) {
                b = 0xC0;
            } else if (b == 0xDD) {
                b = 0xDB;
            }
            if (alen[di] < (int)sizeof(acc[di])) {
                acc[di][alen[di]++] = b;
            }
            continue;
        }
        if (b == 0xDB) {
            esc[di] = 1;
            continue;
        }
        if (b == 0xC0) {
            if (alen[di] >= 2) {
                /*
                 * Single pending slot: wait briefly for PTT/have_pending clear so
                 * intentional back-to-back SEND/KISS still keys (max25d returns OK
                 * either way). Cap ~3.5s (~70×50ms) to match long prove-out TX.
                 */
                int q;
                int w;
                for (w = 0; w < 70; w++) {
                    q = bcpr_engine_queue_kiss(e, di, acc[di], alen[di]);
                    if (q == 0) {
                        break;
                    }
                    usleep(50000);
                }
                if (q != 0) {
                    fprintf(stderr,
                            "max25-bcprd: queue_kiss drop bc%d len=%d (busy)\n", di,
                            alen[di]);
                }
            }
            in_frame[di] = 0;
            alen[di] = 0;
            continue;
        }
        if (alen[di] < (int)sizeof(acc[di])) {
            acc[di][alen[di]++] = b;
        }
    }
}

static void *kiss_thread(void *arg)
{
    bcpr_engine_t *e = (bcpr_engine_t *)arg;
    while (!g_stop && !e->stop) {
        struct pollfd pf[BCPR_MAX_DEVICES];
        int nf = 0;
        int map[BCPR_MAX_DEVICES];
        int i;
        int ret;
        int backoff = 0;
        for (i = 0; i < g_npty; i++) {
            if (g_pty[i].master_fd < 0) {
                continue;
            }
            pf[nf].fd = g_pty[i].master_fd;
            pf[nf].events = POLLIN | POLLHUP | POLLERR;
            map[nf] = i;
            nf++;
        }
        if (nf == 0) {
            usleep(50000);
            continue;
        }
        ret = poll(pf, (nfds_t)nf, 50);
        if (ret <= 0) {
            continue;
        }
        for (i = 0; i < nf; i++) {
            short re = pf[i].revents;
            /*
             * POLLIN before POLLHUP: a short-lived slave (open/write/close) often
             * reports both. Reading into a discard buffer first steals KISS bytes
             * and yields silent TX (MCR never keys). max25d keeps the slave open;
             * smoke/scripts that close after write hit this race.
             */
            if (re & POLLIN) {
                kiss_feed(e, &g_pty[map[i]]);
            }
            if (re & (POLLHUP | POLLERR | POLLNVAL)) {
                /* Slave closed: backoff only — do not drain via raw read(). */
                backoff = 1;
            }
        }
        if (backoff) {
            usleep(50000);
        }
    }
    return NULL;
}

static void usage(const char *argv0)
{
    fprintf(stderr,
            "Usage: %s -c <bcpr.ini> [--dry-run] [--once] [--seconds N] [--version]\n"
            "  Host face: max25e0:bc0 / bc1 (KISS PTY via kiss_link)\n"
            "  No kernel baycom_ser_fdx; no calibrate.\n",
            argv0);
}

int main(int argc, char **argv)
{
    const char *cfg_path = NULL;
    int dry = 0;
    int seconds = 0;
    int i;
    bcpr_config_t cfg;
    pthread_t thr;
    int thr_ok = 0;
    char ver[32] = "0.1.0";

    for (i = 1; i < argc; i++) {
        if ((strcmp(argv[i], "-c") == 0 || strcmp(argv[i], "--config") == 0) &&
            i + 1 < argc) {
            cfg_path = argv[++i];
        } else if (strcmp(argv[i], "--dry-run") == 0) {
            dry = 1;
        } else if (strcmp(argv[i], "--once") == 0) {
            if (seconds <= 0) {
                seconds = 1;
            }
        } else if (strcmp(argv[i], "--seconds") == 0 && i + 1 < argc) {
            seconds = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--version") == 0 ||
                   strcmp(argv[i], "-V") == 0) {
            FILE *vf = fopen("/usr/local/share/max25/max25-bcpr/VERSION", "r");
            if (!vf) {
                vf = fopen("stacks/max25-bcpr/VERSION", "r");
            }
            if (vf) {
                if (fgets(ver, sizeof(ver), vf)) {
                    ver[strcspn(ver, "\r\n")] = '\0';
                }
                fclose(vf);
            }
            printf("bcprd %s\n", ver);
            return 0;
        } else if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            usage(argv[0]);
            return 0;
        } else {
            usage(argv[0]);
            return 2;
        }
    }
    if (!cfg_path) {
        usage(argv[0]);
        return 2;
    }

    signal(SIGINT, on_sig);
    signal(SIGTERM, on_sig);

    if (bcpr_config_load(&cfg, cfg_path) != 0) {
        fprintf(stderr, "max25-bcprd: cannot load %s\n", cfg_path);
        return 1;
    }
    if (dry) {
        cfg.dry_run = 1;
    }

    (void)ensure_dir(cfg.state_dir);

    /* Dry-run / offline CI: skip KISS PTY (openpty may be unavailable). */
    g_npty = 0;
    if (!cfg.dry_run) {
        for (i = 0; i < BCPR_MAX_DEVICES; i++) {
            if (!cfg.dev[i].enabled) {
                continue;
            }
            if (kiss_pty_open(&g_pty[g_npty], i, cfg.dev[i].kiss_link,
                              cfg.state_dir) != 0) {
                while (g_npty > 0) {
                    g_npty--;
                    kiss_pty_close(&g_pty[g_npty]);
                }
                return 1;
            }
            g_npty++;
        }
    } else {
        fprintf(stderr, "max25-bcprd: dry-run (no KISS PTY, no UART I/O)\n");
    }

    if (bcpr_engine_open(&g_engine, &cfg) != 0) {
        for (i = 0; i < g_npty; i++) {
            kiss_pty_close(&g_pty[i]);
        }
        return 1;
    }
    g_engine.run_seconds = seconds;
    bcpr_engine_set_rx(&g_engine, on_rx, NULL);

    if (g_npty > 0 &&
        pthread_create(&thr, NULL, kiss_thread, &g_engine) == 0) {
        thr_ok = 1;
    }

    (void)bcpr_engine_run(&g_engine);

    g_stop = 1;
    g_engine.stop = 1;
    if (thr_ok) {
        pthread_join(thr, NULL);
    }
    bcpr_engine_close(&g_engine);
    for (i = 0; i < g_npty; i++) {
        kiss_pty_close(&g_pty[i]);
    }
    fprintf(stderr, "max25-bcprd: stopped\n");
    return 0;
}
