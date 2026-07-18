#define _POSIX_C_SOURCE 200809L

#include "max25_proto.h"

#if defined(__AMIGA__) || defined(__amigaos__)
#define MAX25_AMIGA 1
#endif

#include <ctype.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>

#ifndef MAX25_AMIGA
#include <netdb.h>
#include <sys/socket.h>
#include <sys/un.h>
#else
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#endif

struct max25_client {
    int fd;
};

static int read_line_fd(int fd, char *line, size_t line_sz)
{
    size_t pos = 0;
    char ch;

    while (pos + 1 < line_sz) {
        ssize_t n = read(fd, &ch, 1);
        if (n < 0) {
            if (errno == EINTR) {
                continue;
            }
            return -1;
        }
        if (n == 0) {
            return -1;
        }
        if (ch == '\n') {
            line[pos] = '\0';
            return 0;
        }
        if (ch != '\r') {
            line[pos++] = ch;
        }
    }
    return -1;
}

static int write_cmd(int fd, const char *cmd)
{
    char buf[MAX25_LINE_MAX + 2];
    int len = snprintf(buf, sizeof(buf), "%s\n", cmd);
    ssize_t off = 0;

    if (len < 0 || (size_t)len >= sizeof(buf)) {
        return -1;
    }
    while (off < len) {
        ssize_t n = write(fd, buf + off, (size_t)len - (size_t)off);
        if (n < 0) {
            if (errno == EINTR) {
                continue;
            }
            return -1;
        }
        off += n;
    }
    return 0;
}

static int connect_tcp(const char *host, unsigned port)
{
#ifdef MAX25_AMIGA
    struct hostent *he;
    struct sockaddr_in addr;
    int fd;

    he = gethostbyname(host);
    if (he == NULL || he->h_addr_list[0] == NULL) {
        return -1;
    }

    fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        return -1;
    }

    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((uint16_t)port);
    memcpy(&addr.sin_addr, he->h_addr_list[0], (size_t)he->h_length);

    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) != 0) {
        close(fd);
        return -1;
    }
    return fd;
#else
    char portbuf[16];
    struct addrinfo hints;
    struct addrinfo *res = NULL;
    struct addrinfo *ai;
    int fd = -1;

    snprintf(portbuf, sizeof(portbuf), "%u", port);
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    if (getaddrinfo(host, portbuf, &hints, &res) != 0) {
        return -1;
    }

    for (ai = res; ai != NULL; ai = ai->ai_next) {
        fd = socket(ai->ai_family, ai->ai_socktype, ai->ai_protocol);
        if (fd < 0) {
            continue;
        }
        if (connect(fd, ai->ai_addr, ai->ai_addrlen) == 0) {
            break;
        }
        close(fd);
        fd = -1;
    }
    freeaddrinfo(res);
    return fd;
#endif
}

static int connect_unix(const char *path)
{
#ifndef MAX25_AMIGA
    struct sockaddr_un addr;
    int fd;

    if (path == NULL || path[0] == '\0') {
        return -1;
    }

    fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0) {
        return -1;
    }

    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, path, sizeof(addr.sun_path) - 1);

    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) != 0) {
        close(fd);
        return -1;
    }
    return fd;
#else
    (void)path;
    return -1;
#endif
}

static int tcp_authenticate(int fd, const char *password)
{
    char line[MAX25_LINE_MAX];
    char cmd[MAX25_LINE_MAX + 8];

    if (password == NULL || password[0] == '\0') {
        return -1;
    }
    snprintf(cmd, sizeof(cmd), "AUTH %s", password);
    if (write_cmd(fd, cmd) != 0) {
        return -1;
    }
    if (read_line_fd(fd, line, sizeof(line)) != 0) {
        return -1;
    }
    return strcmp(line, "OK") == 0 ? 0 : -1;
}

static int handshake(int fd, const char *tcp_password, max25_status_t *initial_status)
{
    char line[MAX25_LINE_MAX];

    if (read_line_fd(fd, line, sizeof(line)) != 0) {
        return -1;
    }
    if (strcmp(line, "AUTH required") == 0) {
        if (tcp_authenticate(fd, tcp_password) != 0) {
            return -1;
        }
        if (read_line_fd(fd, line, sizeof(line)) != 0 || strcmp(line, "OK") != 0) {
            return -1;
        }
    } else if (strcmp(line, "OK") != 0) {
        return -1;
    }

    if (read_line_fd(fd, line, sizeof(line)) != 0 ||
        strncmp(line, "STATUS ", 7) != 0) {
        return -1;
    }

    if (initial_status != NULL) {
        max25_client_parse_status(line, initial_status);
    }
    return 0;
}

int max25_client_connect(const char *host, unsigned port, const char *unix_path,
                         int tcp_only, const char *tcp_password,
                         max25_client_t **out, max25_status_t *initial_status)
{
    max25_client_t *client;
    int fd = -1;

    if (out == NULL) {
        return -1;
    }

    if (!tcp_only && unix_path != NULL && unix_path[0] != '\0') {
#ifndef MAX25_AMIGA
        fd = connect_unix(unix_path);
#endif
    }
    if (fd < 0 && host != NULL && host[0] != '\0') {
        fd = connect_tcp(host, port);
    }
    if (fd < 0) {
        return -1;
    }

    client = calloc(1, sizeof(*client));
    if (client == NULL) {
        close(fd);
        return -1;
    }
    client->fd = fd;

    if (handshake(fd, tcp_password, initial_status) != 0) {
        max25_client_free(client);
        return -1;
    }

    *out = client;
    return 0;
}

void max25_client_free(max25_client_t *client)
{
    if (client == NULL) {
        return;
    }
    if (client->fd >= 0) {
        close(client->fd);
    }
    free(client);
}

int max25_client_fd(const max25_client_t *client)
{
    return client != NULL ? client->fd : -1;
}

int max25_client_write(max25_client_t *client, const char *cmd)
{
    if (client == NULL || cmd == NULL) {
        return -1;
    }
    return write_cmd(client->fd, cmd);
}

max25_line_kind_t max25_client_classify_line(const char *line)
{
    if (line == NULL || line[0] == '\0') {
        return MAX25_LINE_IGNORE;
    }
    if (strcmp(line, "OK") == 0) {
        return MAX25_LINE_OK;
    }
    if (strncmp(line, "ERR ", 4) == 0) {
        return MAX25_LINE_ERR;
    }
    if (strncmp(line, "STATUS ", 7) == 0) {
        return MAX25_LINE_STATUS;
    }
    if (strncmp(line, "RX ", 3) == 0) {
        return MAX25_LINE_RX;
    }
    if (strncmp(line, "EVENT ", 6) == 0) {
        return MAX25_LINE_EVENT;
    }
    return MAX25_LINE_OTHER;
}

int max25_client_command(max25_client_t *client, const char *cmd,
                         char *reply, size_t reply_sz)
{
    char line[MAX25_LINE_MAX];

    if (client == NULL || cmd == NULL) {
        return -1;
    }
    if (write_cmd(client->fd, cmd) != 0) {
        return -1;
    }
    for (;;) {
        if (read_line_fd(client->fd, line, sizeof(line)) != 0) {
            return -1;
        }
        if (strncmp(line, "STATUS ", 7) == 0) {
            if (reply != NULL && reply_sz > 0) {
                strncpy(reply, line, reply_sz - 1);
                reply[reply_sz - 1] = '\0';
            }
            continue;
        }
        if (strncmp(line, "RX ", 3) == 0) {
            continue;
        }
        if (strncmp(line, "EVENT ", 6) == 0) {
            continue;
        }
        /* GET STATUS replies: STATUS … then OK — keep STATUS in reply. */
        if (strcmp(line, "OK") == 0) {
            if (reply != NULL && reply_sz > 0 &&
                strncmp(reply, "STATUS ", 7) != 0) {
                strncpy(reply, line, reply_sz - 1);
                reply[reply_sz - 1] = '\0';
            }
            return 0;
        }
        if (reply != NULL && reply_sz > 0) {
            strncpy(reply, line, reply_sz - 1);
            reply[reply_sz - 1] = '\0';
        }
        return -1;
    }
}

int max25_client_read_line(max25_client_t *client, char *line, size_t line_sz)
{
    if (client == NULL) {
        return -1;
    }
    return read_line_fd(client->fd, line, line_sz);
}

static void copy_field(const char *src, char *dst, size_t dst_sz)
{
    if (dst == NULL || dst_sz == 0) {
        return;
    }
    if (src == NULL) {
        dst[0] = '\0';
        return;
    }
    strncpy(dst, src, dst_sz - 1);
    dst[dst_sz - 1] = '\0';
}

int max25_client_parse_status(const char *line, max25_status_t *status)
{
    char buf[MAX25_LINE_MAX];
    char *save = NULL;
    char *tok;

    if (line == NULL || status == NULL || strncmp(line, "STATUS ", 7) != 0) {
        return -1;
    }

    strncpy(buf, line + 7, sizeof(buf) - 1);
    buf[sizeof(buf) - 1] = '\0';

    memset(status, 0, sizeof(*status));
    for (tok = strtok_r(buf, " ", &save); tok != NULL;
         tok = strtok_r(NULL, " ", &save)) {
        char *eq = strchr(tok, '=');
        if (eq == NULL) {
            continue;
        }
        *eq = '\0';
        if (strcmp(tok, "hardware") == 0) {
            copy_field(eq + 1, status->hardware, sizeof(status->hardware));
        } else if (strcmp(tok, "device") == 0) {
            copy_field(eq + 1, status->device, sizeof(status->device));
        } else if (strcmp(tok, "mode") == 0) {
            copy_field(eq + 1, status->mode, sizeof(status->mode));
        } else if (strcmp(tok, "callerid") == 0) {
            copy_field(eq + 1, status->callerid, sizeof(status->callerid));
        } else if (strcmp(tok, "callid") == 0) {
            copy_field(eq + 1, status->callid, sizeof(status->callid));
        } else if (strcmp(tok, "ax25_ui") == 0) {
            status->ax25_ui = (strcmp(eq + 1, "on") == 0);
        } else if (strcmp(tok, "connected") == 0) {
            status->connected = (strcmp(eq + 1, "yes") == 0);
        } else if (strcmp(tok, "stack") == 0) {
            copy_field(eq + 1, status->stack, sizeof(status->stack));
        } else if (strcmp(tok, "error") == 0) {
            copy_field(eq + 1, status->error, sizeof(status->error));
        } else if (strcmp(tok, "voice") == 0) {
            copy_field(eq + 1, status->voice, sizeof(status->voice));
        }
    }
    return 0;
}

int max25_valid_callsign(const char *value)
{
    const char *dash;
    size_t call_len;
    unsigned long ssid;
    char *end = NULL;
    size_t i;

    if (value == NULL) {
        return 0;
    }

    dash = strchr(value, '-');
    if (dash != NULL) {
        call_len = (size_t)(dash - value);
        ssid = strtoul(dash + 1, &end, 10);
        if (end == dash + 1 || ssid > 15) {
            return 0;
        }
    } else {
        call_len = strlen(value);
    }

    if (call_len == 0 || call_len > 6) {
        return 0;
    }

    for (i = 0; i < call_len; i++) {
        char c = (char)toupper((unsigned char)value[i]);
        if (!((c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9'))) {
            return 0;
        }
    }

    return 1;
}
