#ifndef MAX25_PROTO_H
#define MAX25_PROTO_H

#include <stddef.h>

#define MAX25_DEFAULT_PORT 7325
#define MAX25_DEFAULT_UNIX "/run/max25/modem.sock"
#define MAX25_LINE_MAX 512
#define MAX25_CALLSIGN_MAX 16

typedef struct max25_client max25_client_t;

typedef struct max25_status {
    char hardware[32];
    char device[32];
    char mode[32];
    char callerid[MAX25_CALLSIGN_MAX];
    char callid[MAX25_CALLSIGN_MAX];
    int ax25_ui;
    int connected;
    int monitor;
    char stack[32];
    char error[16];
    char voice[16];
} max25_status_t;

typedef enum {
    MAX25_LINE_IGNORE = 0,
    MAX25_LINE_OK,
    MAX25_LINE_ERR,
    MAX25_LINE_STATUS,
    MAX25_LINE_RX,
    MAX25_LINE_EVENT,
    MAX25_LINE_OTHER
} max25_line_kind_t;

int max25_client_connect(const char *host, unsigned port, const char *unix_path,
                         int tcp_only, const char *tcp_password,
                         max25_client_t **out, max25_status_t *initial_status);
void max25_client_free(max25_client_t *client);
int max25_client_fd(const max25_client_t *client);

int max25_client_write(max25_client_t *client, const char *cmd);
int max25_client_command(max25_client_t *client, const char *cmd,
                         char *reply, size_t reply_sz);
int max25_client_read_line(max25_client_t *client, char *line, size_t line_sz);
max25_line_kind_t max25_client_classify_line(const char *line);
int max25_client_parse_status(const char *line, max25_status_t *status);
/** Apply EVENT connected / EVENT disconnected to status. Returns 1 if handled. */
int max25_client_apply_event(const char *line, max25_status_t *status);

int max25_valid_callsign(const char *value);

#endif /* MAX25_PROTO_H */
