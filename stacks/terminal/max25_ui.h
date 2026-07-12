#ifndef MAX25_UI_H
#define MAX25_UI_H

#include "max25_proto.h"

#define MAX25_TERM_SGR "\033[37;40m"
#define MAX25_TERM_CLEAR "\033[2J\033[H"
#define MAX25_UI_RX_LINES 12
#define MAX25_UI_INPUT_MAX 256

typedef struct max25_ui max25_ui_t;

typedef enum {
    MAX25_MENU_NONE = 0,
    MAX25_MENU_CALLERID,
    MAX25_MENU_CALLID,
    MAX25_MENU_STATUS,
    MAX25_MENU_SEND,
    MAX25_MENU_MONITOR,
    MAX25_MENU_CONNECT,
    MAX25_MENU_DEVICE,
    MAX25_MENU_QUIT
} max25_menu_action_t;

int max25_ui_init(max25_ui_t **ui);
void max25_ui_shutdown(max25_ui_t *ui);

void max25_ui_apply_palette(void);
void max25_ui_clear_screen(void);

int max25_ui_has_ncurses(const max25_ui_t *ui);

void max25_ui_reset_rx(max25_ui_t *ui);
void max25_ui_append_rx(max25_ui_t *ui, const char *text);
void max25_ui_draw_screen(max25_ui_t *ui, const max25_status_t *status,
                          const char *input_line);
void max25_ui_show_menu(max25_ui_t *ui, const max25_status_t *status);
void max25_ui_hide_menu(max25_ui_t *ui);
int max25_ui_menu_visible(const max25_ui_t *ui);

max25_menu_action_t max25_ui_menu_pick(max25_ui_t *ui, int ch);
int max25_ui_prompt(max25_ui_t *ui, const char *label, char *buf, size_t buf_sz);

#endif /* MAX25_UI_H */
