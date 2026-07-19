#define _POSIX_C_SOURCE 200809L

#include "max25_proto.h"
#include "max25_ui.h"

#include <errno.h>
#include <getopt.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

#ifdef MAX25_HAVE_NCURSES
#include <ncurses.h>
#endif

typedef struct {
    char host[256];
    unsigned port;
    char unix_path[256];
    char tcp_password[128];
    char default_device[32];
    int tcp_only;
    int ax25_ui;
    int verbose;
    int probe;
} terminal_config_t;

typedef struct {
    int waiting_reply;
    char last_err[MAX25_LINE_MAX];
} session_io_t;

static struct termios g_saved_tty;
static int g_tty_raw;

static void config_defaults(terminal_config_t *cfg)
{
    const char *env;

    memset(cfg, 0, sizeof(*cfg));
    strncpy(cfg->host, "127.0.0.1", sizeof(cfg->host) - 1);
    cfg->port = MAX25_DEFAULT_PORT;
    strncpy(cfg->unix_path, MAX25_DEFAULT_UNIX, sizeof(cfg->unix_path) - 1);
    cfg->ax25_ui = 1;

    env = getenv("MAX25_HOST");
    if (env != NULL && env[0] != '\0') {
        strncpy(cfg->host, env, sizeof(cfg->host) - 1);
    }
    env = getenv("MAX25_PORT");
    if (env != NULL && env[0] != '\0') {
        cfg->port = (unsigned)strtoul(env, NULL, 10);
    }
    env = getenv("MAX25_UNIX");
    if (env != NULL) {
        strncpy(cfg->unix_path, env, sizeof(cfg->unix_path) - 1);
    }
    env = getenv("MAX25_TCP_PASSWORD");
    if (env != NULL) {
        strncpy(cfg->tcp_password, env, sizeof(cfg->tcp_password) - 1);
    }
}

static void usage(const char *prog)
{
    fprintf(stderr,
            "MAX25 Terminal — CLI operator client (max25d via TCP/M25/1)\n\n"
            "Usage: %s [options] [host] [port]\n\n"
            "Options:\n"
            "  -H, --host HOST       max25d TCP host (default 127.0.0.1)\n"
            "  -p, --port PORT       max25d TCP port (default %u)\n"
            "  -T, --tcp-only        TCP only — do not try Unix socket\n"
            "  -U, --unix PATH       Unix socket (default %s, before TCP)\n"
            "      --ax25-ui         AX.25 UI mode (default on)\n"
            "      --no-ax25-ui      Plain SEND lines\n"
            "  -P, --password PASS   TCP auth password (plain-text M25/1 AUTH)\n"
            "  -d, --device ID       SET DEVICE after connect (configured device id)\n"
            "  -v, --verbose         Protocol log on stderr\n"
            "      --probe           Connect, print STATUS, exit (CI)\n"
            "  -h, --help            Show help\n\n"
            "Remote example:\n"
            "  %s -T -H linux-host.local -p 7325\n\n"
            "Environment: MAX25_HOST, MAX25_PORT, MAX25_UNIX, MAX25_TCP_PASSWORD\n"
            "Symlink: max25-client -> max25-terminal\n\n",
            prog, MAX25_DEFAULT_PORT, MAX25_DEFAULT_UNIX, prog);
}

static int tty_enable_raw(void)
{
    struct termios tty;

    if (!isatty(STDIN_FILENO)) {
        return 0;
    }
    if (tcgetattr(STDIN_FILENO, &g_saved_tty) != 0) {
        return -1;
    }
    tty = g_saved_tty;
    tty.c_lflag &= (tcflag_t)~(ICANON | ECHO);
    tty.c_cc[VMIN] = 0;
    tty.c_cc[VTIME] = 1;
    if (tcsetattr(STDIN_FILENO, TCSANOW, &tty) != 0) {
        return -1;
    }
    g_tty_raw = 1;
    return 0;
}

static void tty_restore(void)
{
    if (g_tty_raw) {
        tcsetattr(STDIN_FILENO, TCSANOW, &g_saved_tty);
        g_tty_raw = 0;
    }
}

static int begin_cmd(session_io_t *io)
{
    if (io == NULL) {
        return -1;
    }
    io->waiting_reply = 1;
    io->last_err[0] = '\0';
    return 0;
}

static int send_cmd_async(max25_client_t *client, session_io_t *io,
                          const char *cmd)
{
    if (max25_client_write(client, cmd) != 0) {
        return -1;
    }
    return begin_cmd(io);
}

static int dispatch_daemon_line(const char *line, session_io_t *io,
                                max25_ui_t *ui, max25_status_t *status,
                                terminal_config_t *cfg, int *need_redraw)
{
    max25_line_kind_t kind = max25_client_classify_line(line);

    if (need_redraw != NULL) {
        *need_redraw = 0;
    }

    if (cfg->verbose) {
        fprintf(stderr, "max25-terminal: << %s\n", line);
    }

    if (kind == MAX25_LINE_RX) {
        max25_ui_append_rx(ui, line + 3);
        if (need_redraw != NULL) {
            *need_redraw = 1;
        }
        return 0;
    }

    /* CONNECT/DISCONNECT emit EVENT before OK — update header even while waiting. */
    if (kind == MAX25_LINE_EVENT) {
        if (max25_client_apply_event(line, status)) {
            max25_ui_append_rx(ui, line);
            if (need_redraw != NULL) {
                *need_redraw = 1;
            }
        } else if (cfg->verbose) {
            max25_ui_append_rx(ui, line);
            if (need_redraw != NULL) {
                *need_redraw = 1;
            }
        }
        if (io->waiting_reply) {
            return 0;
        }
        return 0;
    }

    if (io->waiting_reply) {
        if (kind == MAX25_LINE_STATUS && status != NULL) {
            char summary[MAX25_LINE_MAX];

            max25_client_parse_status(line, status);
            /* Show STATUS in RX pane (F10→3 and other GET STATUS callers). */
            snprintf(summary, sizeof(summary),
                     "STATUS device=%s stack=%s connected=%s callerid=%s callid=%s",
                     status->device[0] != '\0' ? status->device : "-",
                     status->stack[0] != '\0' ? status->stack : "-",
                     status->connected ? "yes" : "no",
                     status->callerid[0] != '\0' ? status->callerid : "-",
                     status->callid[0] != '\0' ? status->callid : "-");
            max25_ui_append_rx(ui, summary);
            if (need_redraw != NULL) {
                *need_redraw = 1;
            }
            return 0;
        }
        if (kind == MAX25_LINE_OK) {
            io->waiting_reply = 0;
            if (need_redraw != NULL) {
                *need_redraw = 1;
            }
            return 0;
        }
        if (kind == MAX25_LINE_ERR) {
            strncpy(io->last_err, line, sizeof(io->last_err) - 1);
            io->last_err[sizeof(io->last_err) - 1] = '\0';
            io->waiting_reply = 0;
            max25_ui_append_rx(ui, line);
            if (need_redraw != NULL) {
                *need_redraw = 1;
            }
            return -1;
        }
        return 0;
    }

    if (kind == MAX25_LINE_ERR) {
        max25_ui_append_rx(ui, line);
        if (need_redraw != NULL) {
            *need_redraw = 1;
        }
    }
    return 0;
}


static int send_callsign(max25_client_t *client, session_io_t *io,
                         const char *field, const char *value)
{
    char cmd[MAX25_LINE_MAX];

    if (!max25_valid_callsign(value)) {
        fprintf(stderr, "max25-terminal: invalid %s\n", field);
        return -1;
    }
    snprintf(cmd, sizeof(cmd), "SET %s %s", field, value);
    return send_cmd_async(client, io, cmd);
}

static int send_line_async(max25_client_t *client, session_io_t *io,
                           const char *line)
{
    char cmd[MAX25_LINE_MAX + 8];
    size_t max_payload = sizeof(cmd) - 6;

    if (strlen(line) > max_payload) {
        return -1;
    }
    snprintf(cmd, sizeof(cmd), "SEND %s", line);
    return send_cmd_async(client, io, cmd);
}

static int refresh_status(max25_client_t *client, max25_status_t *status)
{
    char reply[MAX25_LINE_MAX];

    if (max25_client_command(client, "GET STATUS", reply, sizeof(reply)) != 0) {
        return -1;
    }
    return max25_client_parse_status(reply, status);
}

static int set_device_sync(max25_client_t *client, max25_status_t *status,
                           const char *device_id)
{
    char cmd[MAX25_LINE_MAX + 16];
    char reply[MAX25_LINE_MAX];

    if (device_id == NULL || device_id[0] == '\0') {
        return -1;
    }
    snprintf(cmd, sizeof(cmd), "SET DEVICE %s", device_id);
    if (max25_client_command(client, cmd, reply, sizeof(reply)) != 0) {
        return -1;
    }
    return refresh_status(client, status);
}

static int menu_action_needs_prompt(max25_menu_action_t action)
{
    return action == MAX25_MENU_CALLERID || action == MAX25_MENU_CALLID ||
           action == MAX25_MENU_SEND || action == MAX25_MENU_DEVICE;
}

/* Returns 1 to quit session, 0 otherwise. Hides menu before action. */
static int apply_menu_pick(max25_menu_action_t action, max25_client_t *client,
                           session_io_t *io, max25_ui_t *ui,
                           max25_status_t *status, const char *input_line)
{
    char buf[MAX25_LINE_MAX];
    char cmd[64];

    if (action == MAX25_MENU_NONE) {
        return 0;
    }
    if (action == MAX25_MENU_QUIT) {
        return 1;
    }

    /* Leave overlay so prompts / STATUS RX / header redraw are visible. */
    max25_ui_hide_menu(ui);
    max25_ui_draw_screen(ui, status, input_line != NULL ? input_line : "");

    switch (action) {
    case MAX25_MENU_CALLERID:
        if (max25_ui_prompt(ui, "CALLERID", buf, sizeof(buf)) > 0) {
            send_callsign(client, io, "CALLERID", buf);
        }
        break;
    case MAX25_MENU_CALLID:
        if (max25_ui_prompt(ui, "CALLID", buf, sizeof(buf)) > 0) {
            send_callsign(client, io, "CALLID", buf);
        }
        break;
    case MAX25_MENU_STATUS:
        send_cmd_async(client, io, "GET STATUS");
        break;
    case MAX25_MENU_SEND:
        if (max25_ui_prompt(ui, "Send", buf, sizeof(buf)) > 0) {
            send_line_async(client, io, buf);
        }
        break;
    case MAX25_MENU_MONITOR:
        snprintf(cmd, sizeof(cmd), "MONITOR %s",
                 status->monitor ? "off" : "on");
        status->monitor = !status->monitor;
        send_cmd_async(client, io, cmd);
        max25_ui_append_rx(ui, status->monitor ? "MONITOR on" : "MONITOR off");
        max25_ui_draw_screen(ui, status, input_line != NULL ? input_line : "");
        break;
    case MAX25_MENU_CONNECT:
        send_cmd_async(client, io,
                       status->connected ? "DISCONNECT" : "CONNECT");
        break;
    case MAX25_MENU_DEVICE:
        if (max25_ui_prompt(ui, "DEVICE id", buf, sizeof(buf)) > 0) {
            if (set_device_sync(client, status, buf) != 0) {
                max25_ui_append_rx(ui, "ERR SET DEVICE failed");
            }
            max25_ui_draw_screen(ui, status,
                                 input_line != NULL ? input_line : "");
        }
        break;
    default:
        break;
    }

    if (!menu_action_needs_prompt(action) && action != MAX25_MENU_MONITOR) {
        max25_ui_draw_screen(ui, status, input_line != NULL ? input_line : "");
    }
    return 0;
}

#ifdef MAX25_HAVE_NCURSES
static int read_key_ncurses(void)
{
    int ch = getch();

    if (ch == KEY_F(10)) {
        return 999;
    }
    return ch;
}
#endif

static int read_plain_key(void)
{
    unsigned char buf[8];
    ssize_t n;

    n = read(STDIN_FILENO, buf, sizeof(buf));
    if (n <= 0) {
        if (n < 0 && errno == EAGAIN) {
            return -1;
        }
        return 0;
    }

    if (buf[0] == 0x1b && n >= 3 && buf[1] == '[') {
        if (n >= 4 && buf[2] == '2' && buf[3] == '1' && (n < 5 || buf[4] == '~')) {
            return 999;
        }
    }

    return (int)buf[0];
}

static int run_session(max25_client_t *client, max25_ui_t *ui,
                       terminal_config_t *cfg, max25_status_t *status)
{
    struct pollfd pfds[2];
    session_io_t io;
    char line[MAX25_LINE_MAX];
    char input[MAX25_UI_INPUT_MAX];
    size_t input_len = 0;
    int running = 1;
    int use_ncurses = max25_ui_has_ncurses(ui);
    int use_plain_raw = 0;

    memset(&io, 0, sizeof(io));
    input[0] = '\0';

    if (!use_ncurses) {
        max25_ui_apply_palette();
    }
    max25_ui_reset_rx(ui);
    max25_ui_draw_screen(ui, status, input);

    if (!status->connected) {
        send_cmd_async(client, &io, "CONNECT");
    }

    if (!use_ncurses && isatty(STDIN_FILENO)) {
        use_plain_raw = (tty_enable_raw() == 0);
    }

    while (running) {
        if (!io.waiting_reply) {
            max25_ui_draw_screen(ui, status, input);
        }

        pfds[0].fd = STDIN_FILENO;
        pfds[0].events = POLLIN;
        pfds[0].revents = 0;
        pfds[1].fd = max25_client_fd(client);
        pfds[1].events = POLLIN;
        pfds[1].revents = 0;

        if (poll(pfds, 2, 200) < 0) {
            if (errno == EINTR) {
                continue;
            }
            break;
        }

        if ((pfds[1].revents & (POLLERR | POLLHUP | POLLNVAL)) != 0) {
            max25_ui_append_rx(ui, "max25d connection lost");
            break;
        }

        if ((pfds[1].revents & POLLIN) != 0) {
            int need_redraw = 0;

            if (max25_client_read_line(client, line, sizeof(line)) != 0) {
                max25_ui_append_rx(ui, "max25d connection closed");
                break;
            }
            dispatch_daemon_line(line, &io, ui, status, cfg, &need_redraw);
            if (io.last_err[0] != '\0' && cfg->verbose) {
                fprintf(stderr, "max25-terminal: %s\n", io.last_err);
            }
            if (need_redraw && !max25_ui_menu_visible(ui)) {
                max25_ui_draw_screen(ui, status, input);
            }
            continue;
        }

        if ((pfds[0].revents & POLLIN) == 0) {
            continue;
        }

#ifdef MAX25_HAVE_NCURSES
        if (use_ncurses) {
            int ch = read_key_ncurses();
            if (ch == -1) {
                continue;
            }
            if (ch == 999) {
                if (max25_ui_menu_visible(ui)) {
                    max25_ui_hide_menu(ui);
                    max25_ui_draw_screen(ui, status, input);
                } else {
                    max25_ui_show_menu(ui, status);
                }
                continue;
            }
            if (max25_ui_menu_visible(ui)) {
                if (ch == 27) {
                    max25_ui_hide_menu(ui);
                    max25_ui_draw_screen(ui, status, input);
                    continue;
                }
                if (apply_menu_pick(max25_ui_menu_pick(ui, ch), client, &io, ui,
                                    status, input) != 0) {
                    running = 0;
                }
                continue;
            }
            if (ch >= 32 && ch < 127) {
                if (input_len + 1 < sizeof(input)) {
                    input[input_len++] = (char)ch;
                    input[input_len] = '\0';
                }
            } else if (ch == '\n' || ch == KEY_ENTER || ch == '\r') {
                if (input_len > 0) {
                    send_line_async(client, &io, input);
                    input_len = 0;
                    input[0] = '\0';
                }
            } else if (ch == KEY_BACKSPACE || ch == 127 || ch == '\b') {
                if (input_len > 0) {
                    input[--input_len] = '\0';
                }
            }
            continue;
        }
#endif

        if (use_plain_raw) {
            int ch = read_plain_key();
            if (ch <= 0) {
                continue;
            }
            if (ch == 999) {
                if (max25_ui_menu_visible(ui)) {
                    max25_ui_hide_menu(ui);
                    max25_ui_draw_screen(ui, status, input);
                } else {
                    max25_ui_show_menu(ui, status);
                }
                continue;
            }
            if (max25_ui_menu_visible(ui)) {
                if (ch == 27) {
                    max25_ui_hide_menu(ui);
                    max25_ui_draw_screen(ui, status, input);
                    continue;
                }
                if (apply_menu_pick(max25_ui_menu_pick(ui, ch), client, &io, ui,
                                    status, input) != 0) {
                    running = 0;
                }
                continue;
            }
            if (ch >= 32 && ch < 127) {
                if (input_len + 1 < sizeof(input)) {
                    input[input_len++] = (char)ch;
                    input[input_len] = '\0';
                }
            } else if (ch == '\n' || ch == '\r') {
                if (input_len > 0) {
                    send_line_async(client, &io, input);
                    input_len = 0;
                    input[0] = '\0';
                }
            } else if (ch == 127 || ch == '\b') {
                if (input_len > 0) {
                    input[--input_len] = '\0';
                }
            }
            continue;
        }

        if (fgets(input, sizeof(input), stdin) == NULL) {
            running = 0;
        } else {
            input[strcspn(input, "\r\n")] = '\0';
            if (max25_ui_menu_visible(ui)) {
                if (apply_menu_pick(max25_ui_menu_pick(ui, input[0]), client,
                                    &io, ui, status, "") != 0) {
                    running = 0;
                }
            } else if (input[0] != '\0') {
                send_line_async(client, &io, input);
            }
            input[0] = '\0';
            input_len = 0;
        }
    }

    tty_restore();
    return 0;
}

int main(int argc, char *argv[])
{
    terminal_config_t cfg;
    max25_client_t *client = NULL;
    max25_ui_t *ui = NULL;
    max25_status_t status;
    char reply[MAX25_LINE_MAX];
    int opt;
    int argi;
    static const struct option long_opts[] = {
        {"host", required_argument, NULL, 'H'},
        {"port", required_argument, NULL, 'p'},
        {"unix", required_argument, NULL, 'U'},
        {"tcp-only", no_argument, NULL, 'T'},
        {"ax25-ui", no_argument, NULL, 1000},
        {"no-ax25-ui", no_argument, NULL, 1001},
        {"password", required_argument, NULL, 'P'},
        {"device", required_argument, NULL, 'd'},
        {"verbose", no_argument, NULL, 'v'},
        {"probe", no_argument, NULL, 1002},
        {"help", no_argument, NULL, 'h'},
        {NULL, 0, NULL, 0}
    };

    config_defaults(&cfg);

    while ((opt = getopt_long(argc, argv, "H:p:TU:P:d:v:h", long_opts, NULL)) != -1) {
        switch (opt) {
        case 'H':
            strncpy(cfg.host, optarg, sizeof(cfg.host) - 1);
            break;
        case 'p':
            cfg.port = (unsigned)strtoul(optarg, NULL, 10);
            break;
        case 'T':
            cfg.tcp_only = 1;
            break;
        case 'U':
            strncpy(cfg.unix_path, optarg, sizeof(cfg.unix_path) - 1);
            break;
        case 'P':
            strncpy(cfg.tcp_password, optarg, sizeof(cfg.tcp_password) - 1);
            break;
        case 'd':
            strncpy(cfg.default_device, optarg, sizeof(cfg.default_device) - 1);
            break;
        case 'v':
            cfg.verbose = 1;
            break;
        case 1002:
            cfg.probe = 1;
            cfg.tcp_only = 1;
            break;
        case 'h':
            usage(argv[0]);
            return EXIT_SUCCESS;
        case 1000:
            cfg.ax25_ui = 1;
            break;
        case 1001:
            cfg.ax25_ui = 0;
            break;
        default:
            usage(argv[0]);
            return EXIT_FAILURE;
        }
    }

    argi = optind;
    if (argi < argc) {
        strncpy(cfg.host, argv[argi++], sizeof(cfg.host) - 1);
    }
    if (argi < argc) {
        cfg.port = (unsigned)strtoul(argv[argi++], NULL, 10);
    }

    if (max25_client_connect(cfg.host, cfg.port,
                             cfg.tcp_only ? "" : cfg.unix_path,
                             cfg.tcp_only, cfg.tcp_password,
                             &client, &status) != 0) {
        fprintf(stderr, "max25-terminal: connect failed");
        if (cfg.tcp_only) {
            fprintf(stderr, " (tcp %s:%u)", cfg.host, cfg.port);
        } else {
            fprintf(stderr, " (unix %s / tcp %s:%u)",
                    cfg.unix_path, cfg.host, cfg.port);
        }
        fputc('\n', stderr);
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

    if (max25_ui_init(&ui) != 0) {
        max25_client_free(client);
        return EXIT_FAILURE;
    }

    if (cfg.default_device[0] != '\0') {
        if (set_device_sync(client, &status, cfg.default_device) != 0) {
            fprintf(stderr, "max25-terminal: SET DEVICE %s failed\n",
                    cfg.default_device);
            max25_client_free(client);
            return EXIT_FAILURE;
        }
    }

    if (cfg.ax25_ui) {
        max25_client_command(client, "SET AX25_UI on", reply, sizeof(reply));
        status.ax25_ui = 1;
    } else {
        max25_client_command(client, "SET AX25_UI off", reply, sizeof(reply));
        status.ax25_ui = 0;
    }

    if (cfg.verbose) {
        fprintf(stderr, "max25-terminal: connected %s:%u tcp_only=%s ax25-ui=%s\n",
                cfg.host, cfg.port, cfg.tcp_only ? "yes" : "no",
                status.ax25_ui ? "on" : "off");
    }

    run_session(client, ui, &cfg, &status);

    max25_client_write(client, "DISCONNECT");
    max25_ui_shutdown(ui);
    max25_client_free(client);
    return EXIT_SUCCESS;
}
