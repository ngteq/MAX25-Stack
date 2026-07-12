/*
 * tnc2c-find — detect host baud/format for Landolt TNC2C on a serial port.
 * Tries TERM jumper speeds (300..9600) with 7E1 and 8N1, scores cmd:/INFO replies.
 *
 * Build: make find
 * Run:   ./tnc2c-find /dev/ttyS4
 */

#if defined(__linux__) || defined(__GLIBC__)
#define _DEFAULT_SOURCE 1
#define _GNU_SOURCE 1
#endif

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>

typedef struct line_profile {
    const char *label;
    speed_t speed;
    unsigned int baud;
    tcflag_t databits;
    tcflag_t parity;
} line_profile_t;

static const line_profile_t PROFILES[] = {
    { "19200-8N1", B19200, 19200, CS8, 0 },
    { "19200-7E1", B19200, 19200, CS7, PARENB },
    { "9600-7E1",  B9600,  9600,  CS7, PARENB },
    { "2400-7E1",  B2400,  2400,  CS7, PARENB },
    { "4800-7E1",  B4800,  4800,  CS7, PARENB },
    { "1200-7E1",  B1200,  1200,  CS7, PARENB },
    { "9600-8N1",  B9600,  9600,  CS8, 0 },
    { "2400-8N1",  B2400,  2400,  CS8, 0 },
    { "4800-8N1",  B4800,  4800,  CS8, 0 },
    { "1200-8N1",  B1200,  1200,  CS8, 0 },
    { "600-7E1",   B600,   600,   CS7, PARENB },
    { "300-7E1",   B300,   300,   CS7, PARENB },
    { "600-8N1",   B600,   600,   CS8, 0 },
    { "300-8N1",   B300,   300,   CS8, 0 },
};

static int sleep_ms(unsigned ms)
{
    struct timespec ts;

    ts.tv_sec = (time_t)(ms / 1000u);
    ts.tv_nsec = (long)(ms % 1000u) * 1000000L;
    return nanosleep(&ts, NULL);
}

static int set_modem_lines(int fd)
{
#ifdef TIOCMGET
    int flags;

    if (ioctl(fd, TIOCMGET, &flags) != 0) {
        return -1;
    }
    flags |= TIOCM_RTS | TIOCM_DTR;
    return ioctl(fd, TIOCMSET, &flags);
#else
    (void)fd;
    return 0;
#endif
}

static int open_line(const char *device, const line_profile_t *profile)
{
    struct termios tty;
    int fd;

    fd = open(device, O_RDWR | O_NOCTTY | O_NONBLOCK);
    if (fd < 0) {
        return -1;
    }

    if (tcgetattr(fd, &tty) != 0) {
        close(fd);
        return -1;
    }

    cfmakeraw(&tty);
    tty.c_cflag |= (CLOCAL | CREAD);
    tty.c_cflag &= ~(CSIZE | PARENB | PARODD | CSTOPB);
    tty.c_cflag |= profile->databits;
    if (profile->parity != 0) {
        tty.c_cflag |= profile->parity;
    }
    tty.c_cc[VMIN] = 0;
    tty.c_cc[VTIME] = 10;

#if defined(__linux__) || defined(__GLIBC__)
    if (cfsetspeed(&tty, profile->speed) != 0) {
        cfsetispeed(&tty, profile->speed);
        cfsetospeed(&tty, profile->speed);
    }
#else
    cfsetispeed(&tty, profile->speed);
    cfsetospeed(&tty, profile->speed);
#endif

    if (tcsetattr(fd, TCSANOW, &tty) != 0) {
        close(fd);
        return -1;
    }

    tcflush(fd, TCIOFLUSH);
    (void)set_modem_lines(fd);
    return fd;
}

static size_t read_for(int fd, unsigned char *buf, size_t cap, unsigned ms)
{
    size_t total = 0;
    unsigned elapsed = 0;

    while (elapsed < ms && total < cap) {
        ssize_t n = read(fd, buf + total, cap - total);

        if (n > 0) {
            total += (size_t)n;
            elapsed = 0;
            continue;
        }
        if (n < 0 && errno != EAGAIN && errno != EWOULDBLOCK) {
            break;
        }
        sleep_ms(40);
        elapsed += 40;
    }

    return total;
}

static int score_reply(const unsigned char *buf, size_t len)
{
    size_t i;
    int score = 0;
    int printable = 0;

    if (len == 0) {
        return 0;
    }

    for (i = 0; i < len; i++) {
        unsigned char c = buf[i];

        if (c >= 0x20 && c < 0x7f) {
            printable++;
        }
    }

    score += printable;
    if (memmem(buf, len, "cmd:", 4) != NULL ||
        memmem(buf, len, "CMD:", 4) != NULL) {
        score += 200;
    }
    if (memmem(buf, len, "MYCALL", 6) != NULL ||
        memmem(buf, len, "mycall", 6) != NULL) {
        score += 120;
    }
    if (memmem(buf, len, "TXDELAY", 7) != NULL) {
        score += 80;
    }
    if (memmem(buf, len, "KISS", 4) != NULL) {
        score += 40;
    }
    if (len > 40) {
        score += 60;
    } else if (len > 15) {
        score += 20;
    }

    /* Pure echo of a short command is weak. */
    if (len <= 12 && printable > 0 && printable == (int)len) {
        score -= 10;
    }

    return score;
}

static void dump_ascii(const unsigned char *buf, size_t len)
{
    size_t i;

    for (i = 0; i < len; i++) {
        unsigned char c = buf[i];

        if (c == '\r') {
            fputs("\\r", stdout);
        } else if (c == '\n') {
            fputs("\\n", stdout);
        } else if (c >= 0x20 && c < 0x7f) {
            putchar((int)c);
        } else {
            printf("\\x%02x", c);
        }
    }
}

static int try_profile(const char *device, const line_profile_t *profile,
                       int *best_score, char *best_label, size_t label_cap,
                       unsigned char *best_buf, size_t *best_len,
                       size_t best_cap)
{
    int fd;
    unsigned char buf[4096];
    size_t len;
    int score;
    const char *seq[] = { "\r\r\r", "INFO\r" };
    size_t s;

    fd = open_line(device, profile);
    if (fd < 0) {
        return -1;
    }

    sleep_ms(200);
    len = 0;
    for (s = 0; s < sizeof(seq) / sizeof(seq[0]); s++) {
        (void)write(fd, seq[s], strlen(seq[s]));
        sleep_ms(400);
        len += read_for(fd, buf + len, sizeof(buf) - len, 3500);
    }

    close(fd);
    score = score_reply(buf, len);

    if (score > *best_score) {
        *best_score = score;
        snprintf(best_label, label_cap, "%s", profile->label);
        if (len > best_cap) {
            len = best_cap;
        }
        memcpy(best_buf, buf, len);
        *best_len = len;
    }

    if (score >= 30) {
        printf("  %-12s score=%4d len=%4zu  ",
               profile->label, score, len);
        dump_ascii(buf, len < 120 ? len : 120);
        putchar('\n');
    }

    return score;
}

int main(int argc, char **argv)
{
    const char *device;
    size_t i;
    int best_score = -1;
    char best_label[32] = "";
    unsigned char best_buf[4096];
    size_t best_len = 0;

    if (argc != 2) {
        fprintf(stderr, "Usage: %s <serial-device>\n", argv[0]);
        return 1;
    }

    device = argv[1];
    printf("TNC2C auto-detect on %s\n", device);
    printf("(RTS/DTR on, probe cmd:/INFO; best TERM jumper speeds)\n\n");

    for (i = 0; i < sizeof(PROFILES) / sizeof(PROFILES[0]); i++) {
        (void)try_profile(device, &PROFILES[i], &best_score, best_label,
                          sizeof(best_label), best_buf, &best_len,
                          sizeof(best_buf));
    }

    printf("\n");
    if (best_score < 0) {
        printf("No profile could open %s\n", device);
        return 2;
    }

    printf("Best profile: %s (score=%d, %zu bytes)\n",
           best_label[0] ? best_label : "?", best_score, best_len);
    if (best_len > 0) {
        printf("Sample: ");
        dump_ascii(best_buf, best_len < 200 ? best_len : 200);
        printf("\n");
    }

    if (best_score >= 200) {
        printf("\nHost mode OK — use baud/serial_line from profile above in HyBBX.\n");
        return 0;
    }

    if (best_score >= 30) {
        printf("\nPartial link — check TERM jumper; try: tnc2c-host-reset %s\n", device);
        return 3;
    }

    printf("\nNo usable TNC dialog detected.\n");
    return 4;
}
