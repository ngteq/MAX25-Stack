/*
 * tnc2c-probe — scan /dev/ttyS* and /dev/ttyUSB* for a Landolt TNC2C.
 *
 * TNC2C host port (per manual): 7-bit, even parity, 1 stop bit.
 * Terminal speed set by TERM jumper (this unit: 19200; manual default often 9600).
 * RTS/CTS handshake; DTR asserted to wake some adapters.
 *
 * Build: make
 * Run:   ./tnc2c-probe
 *        ./tnc2c-probe /dev/ttyS4
 */

#if defined(__linux__) || defined(__GLIBC__)
#define _DEFAULT_SOURCE 1
#endif

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <glob.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>

#define PROBE_READ_MS   900
#define PROBE_GAP_MS    120
#define RX_BUF_SIZE     4096
#define MAX_DEVICES     64

typedef struct serial_profile {
    const char *label;
    speed_t speed;
    unsigned int baud_num;
    tcflag_t databits;
    tcflag_t parity;
} serial_profile_t;

typedef struct probe_result {
    char device[64];
    char profile[32];
    char command[32];
    int got_data;
    size_t len;
    char text[RX_BUF_SIZE];
    unsigned char raw[RX_BUF_SIZE];
} probe_result_t;

static const serial_profile_t PROFILES[] = {
    { "19200-7E1", B19200, 19200, CS7, PARENB },
    { "19200-8N1", B19200, 19200, CS8, 0 },
    { "9600-7E1", B9600, 9600, CS7, PARENB },
    { "9600-8N1", B9600, 9600, CS8, 0 },
    { "4800-7E1", B4800, 4800, CS7, PARENB },
    { "2400-7E1", B2400, 2400, CS7, PARENB },
    { "1200-7E1", B1200, 1200, CS7, PARENB },
};

static const char *PROBE_COMMANDS[] = {
    "\r",
    "INFO\r",
    "HELP\r",
    "?\r",
};

static int verbose = 0;

static int sleep_ms(unsigned ms)
{
    struct timespec ts;

    ts.tv_sec = (time_t)(ms / 1000u);
    ts.tv_nsec = (long)(ms % 1000u) * 1000000L;
    return nanosleep(&ts, NULL);
}

static int set_modem_lines(int fd, int rts_on, int dtr_on)
{
#ifdef TIOCMGET
    int flags;

    if (ioctl(fd, TIOCMGET, &flags) != 0) {
        return -1;
    }
    if (rts_on) {
        flags |= TIOCM_RTS;
    } else {
        flags &= ~TIOCM_RTS;
    }
    if (dtr_on) {
        flags |= TIOCM_DTR;
    } else {
        flags &= ~TIOCM_DTR;
    }
    return ioctl(fd, TIOCMSET, &flags);
#else
    (void)fd;
    (void)rts_on;
    (void)dtr_on;
    return 0;
#endif
}

static int read_modem_lines(int fd, int *rts, int *cts, int *dtr, int *dsr)
{
#ifdef TIOCMGET
    int flags;

    if (ioctl(fd, TIOCMGET, &flags) != 0) {
        return -1;
    }
    if (rts != NULL) {
        *rts = (flags & TIOCM_RTS) != 0;
    }
    if (cts != NULL) {
        *cts = (flags & TIOCM_CTS) != 0;
    }
    if (dtr != NULL) {
        *dtr = (flags & TIOCM_DTR) != 0;
    }
    if (dsr != NULL) {
        *dsr = (flags & TIOCM_DSR) != 0;
    }
    return 0;
#else
    (void)fd;
    if (rts) {
        *rts = -1;
    }
    if (cts) {
        *cts = -1;
    }
    if (dtr) {
        *dtr = -1;
    }
    if (dsr) {
        *dsr = -1;
    }
    return 0;
#endif
}

static int configure_port(int fd, const serial_profile_t *profile)
{
    struct termios tty;

    if (tcgetattr(fd, &tty) != 0) {
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
    tty.c_cc[VTIME] = 1;

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
        return -1;
    }

    tcflush(fd, TCIOFLUSH);
    return 0;
}

static int is_printable_ascii(unsigned char c)
{
    return c == '\r' || c == '\n' || c == '\t' || (c >= 0x20 && c <= 0x7e);
}

static void sanitize_text(const unsigned char *raw, size_t len, char *out, size_t out_cap)
{
    size_t i;
    size_t o = 0;

    if (out_cap == 0) {
        return;
    }

    for (i = 0; i < len && o + 1 < out_cap; i++) {
        unsigned char c = raw[i];

        if (c == '\r') {
            if (o + 2 < out_cap) {
                out[o++] = '\\';
                out[o++] = 'r';
            }
        } else if (c == '\n') {
            if (o + 2 < out_cap) {
                out[o++] = '\\';
                out[o++] = 'n';
            }
        } else if (is_printable_ascii(c)) {
            out[o++] = (char)c;
        } else {
            int n = snprintf(out + o, out_cap - o, "\\x%02x", c);
            if (n <= 0 || (size_t)n >= out_cap - o) {
                break;
            }
            o += (size_t)n;
        }
    }
    out[o] = '\0';
}

static int looks_like_tnc(const unsigned char *raw, size_t len)
{
    static const char *needles[] = {
        "cmd:", "CMD:", "TNC", "tnc", "INFO", "help", "HELP",
        "***", "connected", "DISCONNECTED", "kiss", "KISS",
        "MYCALL", "WA8DED", "NOCALL", "?"
    };
    char buf[RX_BUF_SIZE];
    size_t i;

    if (len == 0) {
        return 0;
    }

    sanitize_text(raw, len, buf, sizeof(buf));
    for (i = 0; i < sizeof(needles) / sizeof(needles[0]); i++) {
        if (strstr(buf, needles[i]) != NULL) {
            return 1;
        }
    }
    return len >= 3;
}

static size_t read_for_ms(int fd, unsigned char *buf, size_t cap, unsigned ms)
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

static int probe_once(const char *device, const serial_profile_t *profile,
                      const char *command, probe_result_t *result)
{
    int fd;
    ssize_t wlen;

    memset(result, 0, sizeof(*result));
    snprintf(result->device, sizeof(result->device), "%s", device);
    snprintf(result->profile, sizeof(result->profile), "%s", profile->label);
    snprintf(result->command, sizeof(result->command), "%s",
             command[0] == '\r' ? "<CR>" : command);

    fd = open(device, O_RDWR | O_NOCTTY | O_NONBLOCK);
    if (fd < 0) {
        return -1;
    }

    if (configure_port(fd, profile) != 0) {
        close(fd);
        return -1;
    }

    (void)set_modem_lines(fd, 1, 1);
    sleep_ms(80);
    (void)read_for_ms(fd, result->raw, sizeof(result->raw), 150);

    wlen = write(fd, command, strlen(command));
    if (wlen < 0) {
        close(fd);
        return -1;
    }

    sleep_ms(PROBE_GAP_MS);
    result->len = read_for_ms(fd, result->raw, sizeof(result->raw), PROBE_READ_MS);
    close(fd);

    result->got_data = result->len > 0;
    sanitize_text(result->raw, result->len, result->text, sizeof(result->text));
    return 0;
}

static int device_accessible(const char *path)
{
    return access(path, R_OK | W_OK) == 0;
}

static int collect_devices(char devices[][64], int max_devices)
{
    glob_t g;
    size_t i;
    int count = 0;
    static const char *patterns[] = {
        "/dev/ttyUSB[0-9]*",
        "/dev/ttyS[0-9]*",
        NULL
    };
    int p;

    for (p = 0; patterns[p] != NULL; p++) {
        if (glob(patterns[p], 0, NULL, &g) != 0) {
            continue;
        }
        for (i = 0; i < g.gl_pathc && count < max_devices; i++) {
            const char *path = g.gl_pathv[i];
            int j;
            int dup = 0;

            for (j = 0; j < count; j++) {
                if (strcmp(devices[j], path) == 0) {
                    dup = 1;
                    break;
                }
            }
            if (!dup) {
                snprintf(devices[count], 64, "%s", path);
                count++;
            }
        }
        globfree(&g);
    }

    return count;
}

static void print_device_header(const char *device)
{
    int fd;
    int rts = -1, cts = -1, dtr = -1, dsr = -1;

    printf("\n============================================================\n");
    printf("Device: %s\n", device);
    if (!device_accessible(device)) {
        printf("Access: NO (need dialout group or root)\n");
        return;
    }
    printf("Access: yes\n");

    fd = open(device, O_RDWR | O_NOCTTY | O_NONBLOCK);
    if (fd >= 0) {
        if (read_modem_lines(fd, &rts, &cts, &dtr, &dsr) == 0) {
            printf("Lines (before probe): RTS=%d CTS=%d DTR=%d DSR=%d\n",
                   rts, cts, dtr, dsr);
        }
        close(fd);
    }
}

static void listen_quiet(const char *device, const serial_profile_t *profile)
{
    int fd;
    unsigned char buf[512];
    size_t n;

    fd = open(device, O_RDWR | O_NOCTTY | O_NONBLOCK);
    if (fd < 0) {
        return;
    }
    if (configure_port(fd, profile) != 0) {
        close(fd);
        return;
    }
    (void)set_modem_lines(fd, 1, 1);
    n = read_for_ms(fd, buf, sizeof(buf), 1200);
    close(fd);

    if (n > 0) {
        char text[512];
        sanitize_text(buf, n, text, sizeof(text));
        printf("  Spontaneous traffic @ %s: %s\n", profile->label, text);
    } else if (verbose) {
        printf("  Spontaneous traffic @ %s: (none)\n", profile->label);
    }
}

static int run_device_scan(const char *device)
{
    size_t pi;
    size_t ci;
    int hits = 0;
    int best_score = 0;
    char best_profile[32] = "";
    char best_text[512] = "";

    print_device_header(device);
    if (!device_accessible(device)) {
        return 0;
    }

    listen_quiet(device, &PROFILES[0]);
    listen_quiet(device, &PROFILES[1]);

    for (pi = 0; pi < sizeof(PROFILES) / sizeof(PROFILES[0]); pi++) {
        for (ci = 0; ci < sizeof(PROBE_COMMANDS) / sizeof(PROBE_COMMANDS[0]); ci++) {
            probe_result_t result;
            int score;

            if (probe_once(device, &PROFILES[pi], PROBE_COMMANDS[ci], &result) != 0) {
                continue;
            }
            if (!result.got_data) {
                if (verbose) {
                    printf("  %s + %s -> (no data)\n",
                           result.profile, result.command);
                }
                continue;
            }

            score = looks_like_tnc(result.raw, result.len) ? 2 : 1;
            hits++;
            printf("  HIT  %s + %s (%zu bytes, score=%d)\n",
                   result.profile, result.command, result.len, score);
            printf("       %s\n", result.text);

            if (score > best_score) {
                best_score = score;
                snprintf(best_profile, sizeof(best_profile), "%s", result.profile);
                strncpy(best_text, result.text, sizeof(best_text) - 1);
                best_text[sizeof(best_text) - 1] = '\0';
            }
        }
    }

    if (hits == 0) {
        printf("  Result: no response on any profile/command.\n");
        printf("  Hint:   check power, cable (DTE<->DCE modem cable), baud jumper.\n");
    } else {
        printf("  Result: %d response(s); best profile=%s (score=%d)\n",
               hits, best_profile[0] ? best_profile : "?", best_score);
        if (best_text[0] != '\0') {
            printf("  Best:   %s\n", best_text);
        }
    }

    return hits;
}

static void usage(const char *argv0)
{
    fprintf(stderr,
            "Usage: %s [-v] [device ...]\n"
            "\n"
            "Scan serial ports for a Landolt TNC2C.\n"
            "Without device arguments, probes all /dev/ttyUSB* and /dev/ttyS*.\n"
            "\n"
            "Options:\n"
            "  -v   verbose (show silent probes too)\n"
            "  -h   this help\n",
            argv0);
}

int main(int argc, char **argv)
{
    char devices[MAX_DEVICES][64];
    int device_count = 0;
    int argi;
    int total_hits = 0;
    int scanned = 0;

    for (argi = 1; argi < argc; argi++) {
        if (strcmp(argv[argi], "-h") == 0 || strcmp(argv[argi], "--help") == 0) {
            usage(argv[0]);
            return 0;
        }
        if (strcmp(argv[argi], "-v") == 0 || strcmp(argv[argi], "--verbose") == 0) {
            verbose = 1;
            continue;
        }
        if (device_count < MAX_DEVICES) {
            snprintf(devices[device_count], 64, "%s", argv[argi]);
            device_count++;
        }
    }

    if (device_count == 0) {
        device_count = collect_devices(devices, MAX_DEVICES);
    }

    printf("TNC2C serial probe\n");
    printf("Profiles: 7E1 (manual) and 8N1 (HyBBX default) at common baud rates.\n");
    printf("Found %d serial device(s).\n", device_count);

    if (device_count == 0) {
        fprintf(stderr, "No /dev/ttyUSB* or /dev/ttyS* devices found.\n");
        return 1;
    }

    for (argi = 0; argi < device_count; argi++) {
        total_hits += run_device_scan(devices[argi]);
        scanned++;
    }

    printf("\n============================================================\n");
    printf("Summary: scanned %d port(s), %d response(s) total.\n",
           scanned, total_hits);

    if (total_hits == 0) {
        printf("\nCable note (TNC2C manual):\n");
        printf("  - TNC2C DB25 is wired like a modem (DCE).\n");
        printf("  - PC/USB-serial is DTE -> use a straight modem cable,\n");
        printf("    not a null-modem crossover cable.\n");
        printf("  - Some PCs need RTS-CTS bridged on the host side (pins 4+5).\n");
        printf("  - Host settings: 7-bit, even parity (7E1), baud per TERM jumper.\n");
        printf("  - LEDs after power-on: Power on; Status+Connected off after ~3 s.\n");
        return 2;
    }

    return 0;
}
