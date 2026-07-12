/*
 * max25-terminal — AmigaOS 3.9+ reduced operator client (TCP/M25/1 only).
 *
 * HyBBX-style thin client: no ncurses/F10 menu; connects to Linux max25d.
 */
#define _DEFAULT_SOURCE 1

#include "../max25_proto.h"

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/select.h>

#ifdef __AMIGA__
#include <sys/socket.h>
#endif

typedef struct {
    char host[256];
    unsigned port;
    char tcp_password[128];
    int ax25_ui;
    int verbose;
    int probe;
} amiga_config_t;

static void config_defaults(amiga_config_t *cfg)
{
    const char *env;

    memset(cfg, 0, sizeof(*cfg));
    strncpy(cfg->host, "127.0.0.1", sizeof(cfg->host) - 1);
    cfg->port = MAX25_DEFAULT_PORT;
    cfg->ax25_ui = 1;

    env = getenv("MAX25_HOST");
    if (env != NULL && env[0] != '\0') {
        strncpy(cfg->host, env, sizeof(cfg->host) - 1);
    }
    env = getenv("MAX25_PORT");
    if (env != NULL && env[0] != '\0') {
        cfg->port = (unsigned)strtoul(env, NULL, 10);
    }
    env = getenv("MAX25_TCP_PASSWORD");
    if (env != NULL) {
        strncpy(cfg->tcp_password, env, sizeof(cfg->tcp_password) - 1);
    }
}

static void usage(const char *prog)
{
    fprintf(stderr,
            "MAX25 Terminal (AmigaOS) — reduced CLI client for max25d\n\n"
            "Usage: %s [options] [host] [port]\n\n"
            "Options:\n"
            "  -H HOST        max25d TCP host (default 127.0.0.1)\n"
            "  -p PORT        max25d TCP port (default %u)\n"
            "  -P PASSWORD    TCP auth password (plain-text AUTH)\n"
            "      --ax25-ui  AX.25 UI mode (default on)\n"
            "      --no-ax25-ui\n"
            "  -v             Verbose protocol log on stderr\n"
            "      --probe    Connect, print STATUS, exit\n"
            "  -h             Help\n\n"
            "Session: type a line to SEND; /status /callerid /callid /connect /quit\n"
            "Environment: MAX25_HOST, MAX25_PORT, MAX25_TCP_PASSWORD\n\n",
            prog, MAX25_DEFAULT_PORT);
}

static int parse_args(int argc, char **argv, amiga_config_t *cfg)
{
    int i;
    int positional = 0;

    for (i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            usage(argv[0]);
            return 1;
        }
        if (strcmp(argv[i], "-H") == 0 && i + 1 < argc) {
            strncpy(cfg->host, argv[++i], sizeof(cfg->host) - 1);
            continue;
        }
        if (strcmp(argv[i], "-p") == 0 && i + 1 < argc) {
            cfg->port = (unsigned)strtoul(argv[++i], NULL, 10);
            continue;
        }
        if ((strcmp(argv[i], "-P") == 0 || strcmp(argv[i], "--password") == 0) &&
            i + 1 < argc) {
            strncpy(cfg->tcp_password, argv[++i], sizeof(cfg->tcp_password) - 1);
            continue;
        }
        if (strcmp(argv[i], "-v") == 0 || strcmp(argv[i], "--verbose") == 0) {
            cfg->verbose = 1;
            continue;
        }
        if (strcmp(argv[i], "--probe") == 0) {
            cfg->probe = 1;
            continue;
        }
        if (strcmp(argv[i], "--ax25-ui") == 0) {
            cfg->ax25_ui = 1;
            continue;
        }
        if (strcmp(argv[i], "--no-ax25-ui") == 0) {
            cfg->ax25_ui = 0;
            continue;
        }
        if (argv[i][0] == '-') {
            fprintf(stderr, "%s: unknown option %s\n", argv[0], argv[i]);
            return -1;
        }
        if (positional == 0) {
            strncpy(cfg->host, argv[i], sizeof(cfg->host) - 1);
        } else if (positional == 1) {
            cfg->port = (unsigned)strtoul(argv[i], NULL, 10);
        }
        positional++;
    }
    return 0;
}

static void print_rx(const char *line, int verbose)
{
    if (verbose) {
        fprintf(stderr, "max25-terminal: << %s\n", line);
    }
    if (strncmp(line, "RX ", 3) == 0) {
        printf("<< %s\n", line + 3);
    } else if (strncmp(line, "ERR ", 4) == 0) {
        fprintf(stderr, "!! %s\n", line);
    } else if (strncmp(line, "EVENT ", 6) == 0) {
        printf("-- %s\n", line);
    }
    fflush(stdout);
    fflush(stderr);
}

static int drain_socket(max25_client_t *client, int verbose)
{
    char line[MAX25_LINE_MAX];
    int got = 0;

    for (;;) {
        fd_set rfds;
        struct timeval tv;
        int fd = max25_client_fd(client);

        FD_ZERO(&rfds);
        FD_SET(fd, &rfds);
        tv.tv_sec = 0;
        tv.tv_usec = 0;
        if (select(fd + 1, &rfds, NULL, NULL, &tv) <= 0) {
            break;
        }
        if (max25_client_read_line(client, line, sizeof(line)) != 0) {
            return -1;
        }
        print_rx(line, verbose);
        got = 1;
        if (strcmp(line, "OK") == 0) {
            break;
        }
    }
    return got ? 0 : 0;
}

static int send_cmd_wait(max25_client_t *client, const char *cmd, int verbose)
{
    char line[MAX25_LINE_MAX];

    if (verbose) {
        fprintf(stderr, "max25-terminal: >> %s\n", cmd);
    }
    if (max25_client_write(client, cmd) != 0) {
        return -1;
    }
    for (;;) {
        if (max25_client_read_line(client, line, sizeof(line)) != 0) {
            return -1;
        }
        print_rx(line, verbose);
        if (strncmp(line, "STATUS ", 7) == 0) {
            continue;
        }
        if (strncmp(line, "RX ", 3) == 0) {
            continue;
        }
        if (strncmp(line, "EVENT ", 6) == 0) {
            continue;
        }
        return strcmp(line, "OK") == 0 ? 0 : -1;
    }
}

static int run_session(max25_client_t *client, amiga_config_t *cfg,
                       max25_status_t *status)
{
    char line[MAX25_LINE_MAX];

    printf("MAX25 Terminal (Amiga) — connected to %s:%u\n", cfg->host, cfg->port);
    printf("Type text to SEND. Commands: /status /callerid X /callid X /connect /quit\n");

    if (!status->connected) {
        send_cmd_wait(client, "CONNECT", cfg->verbose);
        status->connected = 1;
    }

    while (fgets(line, sizeof(line), stdin) != NULL) {
        line[strcspn(line, "\r\n")] = '\0';
        if (line[0] == '\0') {
            continue;
        }
        if (strcmp(line, "/quit") == 0 || strcmp(line, "/exit") == 0) {
            break;
        }
        if (strcmp(line, "/status") == 0) {
            send_cmd_wait(client, "GET STATUS", cfg->verbose);
            continue;
        }
        if (strcmp(line, "/connect") == 0) {
            send_cmd_wait(client, "CONNECT", cfg->verbose);
            status->connected = 1;
            continue;
        }
        if (strcmp(line, "/disconnect") == 0) {
            send_cmd_wait(client, "DISCONNECT", cfg->verbose);
            status->connected = 0;
            continue;
        }
        if (strncmp(line, "/callerid ", 10) == 0) {
            char cmd[MAX25_LINE_MAX];
            if (!max25_valid_callsign(line + 10)) {
                fprintf(stderr, "invalid CALLERID\n");
                continue;
            }
            snprintf(cmd, sizeof(cmd), "SET CALLERID %s", line + 10);
            send_cmd_wait(client, cmd, cfg->verbose);
            continue;
        }
        if (strncmp(line, "/callid ", 8) == 0) {
            char cmd[MAX25_LINE_MAX];
            if (!max25_valid_callsign(line + 8)) {
                fprintf(stderr, "invalid CALLID\n");
                continue;
            }
            snprintf(cmd, sizeof(cmd), "SET CALLID %s", line + 8);
            send_cmd_wait(client, cmd, cfg->verbose);
            continue;
        }
        {
            char cmd[MAX25_LINE_MAX + 8];
            snprintf(cmd, sizeof(cmd), "SEND %s", line);
            send_cmd_wait(client, cmd, cfg->verbose);
        }
        (void)drain_socket(client, cfg->verbose);
    }
    return 0;
}

int main(int argc, char **argv)
{
    amiga_config_t cfg;
    max25_client_t *client = NULL;
    max25_status_t status;
    char reply[MAX25_LINE_MAX];
    int rc;

    config_defaults(&cfg);
    rc = parse_args(argc, argv, &cfg);
    if (rc != 0) {
        return rc < 0 ? EXIT_FAILURE : EXIT_SUCCESS;
    }

    if (max25_client_connect(cfg.host, cfg.port, "", 1, cfg.tcp_password,
                             &client, &status) != 0) {
        fprintf(stderr, "max25-terminal: connect failed (tcp %s:%u)\n",
                cfg.host, cfg.port);
        return EXIT_FAILURE;
    }

    if (cfg.probe) {
        printf("STATUS hardware=%s device=%s mode=%s callerid=%s callid=%s "
               "ax25_ui=%s connected=%s stack=%s\n",
               status.hardware, status.device, status.mode,
               status.callerid, status.callid,
               status.ax25_ui ? "on" : "off",
               status.connected ? "yes" : "no",
               status.stack);
        max25_client_write(client, "DISCONNECT");
        max25_client_free(client);
        return EXIT_SUCCESS;
    }

    if (cfg.ax25_ui) {
        max25_client_command(client, "SET AX25_UI on", reply, sizeof(reply));
        status.ax25_ui = 1;
    } else {
        max25_client_command(client, "SET AX25_UI off", reply, sizeof(reply));
        status.ax25_ui = 0;
    }

    run_session(client, &cfg, &status);
    max25_client_write(client, "DISCONNECT");
    max25_client_free(client);
    return EXIT_SUCCESS;
}
