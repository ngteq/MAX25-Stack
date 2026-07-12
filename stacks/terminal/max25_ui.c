#include "max25_ui.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#ifdef MAX25_HAVE_NCURSES
#include <ncurses.h>
#endif

struct max25_ui {
    int menu_open;
    char rx_lines[MAX25_UI_RX_LINES][MAX25_LINE_MAX];
    int rx_count;
    int rx_head;
#ifdef MAX25_HAVE_NCURSES
    int ncurses_on;
#endif
};

int max25_ui_init(max25_ui_t **ui)
{
    max25_ui_t *u;

    if (ui == NULL) {
        return -1;
    }

    u = calloc(1, sizeof(*u));
    if (u == NULL) {
        return -1;
    }

#ifdef MAX25_HAVE_NCURSES
    if (isatty(STDOUT_FILENO) && isatty(STDIN_FILENO) && initscr() != NULL) {
        cbreak();
        noecho();
        keypad(stdscr, TRUE);
        nodelay(stdscr, TRUE);
        if (has_colors()) {
            start_color();
            init_pair(1, COLOR_WHITE, COLOR_BLACK);
        }
        bkgd(COLOR_PAIR(1));
        curs_set(0);
        clear();
        refresh();
        u->ncurses_on = 1;
    }
#endif

    *ui = u;
    return 0;
}

void max25_ui_shutdown(max25_ui_t *ui)
{
    if (ui == NULL) {
        return;
    }
#ifdef MAX25_HAVE_NCURSES
    if (ui->ncurses_on) {
        endwin();
    }
#endif
    free(ui);
}

void max25_ui_apply_palette(void)
{
    fputs(MAX25_TERM_SGR, stdout);
    fflush(stdout);
}

void max25_ui_clear_screen(void)
{
    fputs(MAX25_TERM_CLEAR, stdout);
    fputs(MAX25_TERM_SGR, stdout);
    fflush(stdout);
}

int max25_ui_has_ncurses(const max25_ui_t *ui)
{
#ifdef MAX25_HAVE_NCURSES
    return ui != NULL && ui->ncurses_on;
#else
    (void)ui;
    return 0;
#endif
}

void max25_ui_reset_rx(max25_ui_t *ui)
{
    if (ui == NULL) {
        return;
    }
    ui->rx_count = 0;
    ui->rx_head = 0;
    memset(ui->rx_lines, 0, sizeof(ui->rx_lines));
}

void max25_ui_append_rx(max25_ui_t *ui, const char *text)
{
    int slot;

    if (ui == NULL || text == NULL) {
        return;
    }

    slot = ui->rx_head;
    strncpy(ui->rx_lines[slot], text, MAX25_LINE_MAX - 1);
    ui->rx_lines[slot][MAX25_LINE_MAX - 1] = '\0';
    ui->rx_head = (ui->rx_head + 1) % MAX25_UI_RX_LINES;
    if (ui->rx_count < MAX25_UI_RX_LINES) {
        ui->rx_count++;
    }
}

static void draw_header_plain(const max25_status_t *status)
{
    printf("%sMAX25 Terminal  CALLERID: %-9s CALLID: %-9s  ax25-ui: %s  connected: %s  F10=Menu\n",
           MAX25_TERM_SGR,
           status->callerid, status->callid,
           status->ax25_ui ? "on" : "off",
           status->connected ? "yes" : "no");
    fflush(stdout);
}

static void draw_rx_plain(const max25_ui_t *ui)
{
    int i;
    int start;
    int idx;

    if (ui == NULL) {
        return;
    }

    start = ui->rx_count < MAX25_UI_RX_LINES ? 0 : ui->rx_head;
    for (i = 0; i < ui->rx_count; i++) {
        idx = (start + i) % MAX25_UI_RX_LINES;
        printf("%s%s\n", MAX25_TERM_SGR, ui->rx_lines[idx]);
    }
    fflush(stdout);
}

void max25_ui_draw_screen(max25_ui_t *ui, const max25_status_t *status,
                          const char *input_line)
{
    int i;
    int start;
    int idx;
    int rows;
    int y;

    if (ui == NULL || status == NULL) {
        return;
    }

#ifdef MAX25_HAVE_NCURSES
    if (ui->ncurses_on && !ui->menu_open) {
        getmaxyx(stdscr, rows, y);
        (void)y;
        if (rows < 4) {
            rows = 24;
        }

        attron(COLOR_PAIR(1));
        mvprintw(0, 0,
                 "MAX25 Terminal  CALLERID: %-9s CALLID: %-9s ax25-ui: %s connected: %s  F10=Menu",
                 status->callerid, status->callid,
                 status->ax25_ui ? "on" : "off",
                 status->connected ? "yes" : "no");
        clrtoeol();

        start = ui->rx_count < MAX25_UI_RX_LINES ? 0 : ui->rx_head;
        for (i = 0; i < ui->rx_count && i + 2 < rows - 2; i++) {
            idx = (start + i) % MAX25_UI_RX_LINES;
            mvprintw(i + 2, 0, "%.*s", (int)(rows > 0 ? 200 : 80), ui->rx_lines[idx]);
            clrtoeol();
        }

        mvprintw(rows - 2, 0, "%s", "--------------------------------------------------------");
        clrtoeol();
        mvprintw(rows - 1, 0, "> %s", input_line != NULL ? input_line : "");
        clrtoeol();
        attroff(COLOR_PAIR(1));
        refresh();
        return;
    }
#endif

    if (!ui->menu_open) {
        fputs(MAX25_TERM_CLEAR, stdout);
        fputs(MAX25_TERM_SGR, stdout);
        draw_header_plain(status);
        draw_rx_plain(ui);
        printf("%s> %s\n", MAX25_TERM_SGR, input_line != NULL ? input_line : "");
        fflush(stdout);
    }
}

static void draw_menu_plain(const max25_status_t *status)
{
    puts("");
    puts("┌─ MAX25 Terminal ────────────────────┐");
    printf("│ CALLERID: %-9s CALLID: %-9s │\n",
           status->callerid, status->callid);
    puts("├─────────────────────────────────────┤");
    puts("│ 1  Change CALLERID (live)           │");
    puts("│ 2  Change CALLID (live)             │");
    puts("│ 3  Status                           │");
    puts("│ 4  Send line                        │");
    puts("│ 5  RX only (Monitor)                │");
    puts("│ 6  Connection on/off                │");
    puts("│ 0  Quit client                      │");
    puts("└─────────────────────────────────────┘");
    puts("Pick a number · F10 closes");
    fflush(stdout);
}

void max25_ui_show_menu(max25_ui_t *ui, const max25_status_t *status)
{
    if (ui == NULL || status == NULL) {
        return;
    }
    ui->menu_open = 1;

#ifdef MAX25_HAVE_NCURSES
    if (ui->ncurses_on) {
        int y0 = 2;

        attron(COLOR_PAIR(1));
        mvprintw(y0, 0, "┌─ MAX25 Terminal ────────────────────┐");
        mvprintw(y0 + 1, 0, "│ CALLERID: %-9s CALLID: %-9s │",
                 status->callerid, status->callid);
        mvprintw(y0 + 2, 0, "├─────────────────────────────────────┤");
        mvprintw(y0 + 3, 0, "│ 1  Change CALLERID (live)           │");
        mvprintw(y0 + 4, 0, "│ 2  Change CALLID (live)             │");
        mvprintw(y0 + 5, 0, "│ 3  Status                           │");
        mvprintw(y0 + 6, 0, "│ 4  Send line                        │");
        mvprintw(y0 + 7, 0, "│ 5  RX only (Monitor)                │");
        mvprintw(y0 + 8, 0, "│ 6  Connection on/off                │");
        mvprintw(y0 + 9, 0, "│ 0  Quit client                      │");
        mvprintw(y0 + 10, 0, "└─────────────────────────────────────┘");
        mvprintw(y0 + 11, 0, "Pick a number · F10 closes");
        attroff(COLOR_PAIR(1));
        refresh();
        return;
    }
#endif
    draw_menu_plain(status);
}

void max25_ui_hide_menu(max25_ui_t *ui)
{
    if (ui == NULL) {
        return;
    }
    ui->menu_open = 0;
}

int max25_ui_menu_visible(const max25_ui_t *ui)
{
    return ui != NULL && ui->menu_open;
}

max25_menu_action_t max25_ui_menu_pick(max25_ui_t *ui, int ch)
{
    (void)ui;
    switch (ch) {
    case '1':
        return MAX25_MENU_CALLERID;
    case '2':
        return MAX25_MENU_CALLID;
    case '3':
        return MAX25_MENU_STATUS;
    case '4':
        return MAX25_MENU_SEND;
    case '5':
        return MAX25_MENU_MONITOR;
    case '6':
        return MAX25_MENU_CONNECT;
    case '0':
        return MAX25_MENU_QUIT;
    default:
        return MAX25_MENU_NONE;
    }
}

int max25_ui_prompt(max25_ui_t *ui, const char *label, char *buf, size_t buf_sz)
{
    if (label == NULL || buf == NULL || buf_sz == 0) {
        return -1;
    }

#ifdef MAX25_HAVE_NCURSES
    if (ui != NULL && ui->ncurses_on) {
        int ch;
        size_t len = 0;
        int rows;

        getmaxyx(stdscr, rows, ch);
        (void)rows;
        echo();
        curs_set(1);
        attron(COLOR_PAIR(1));
        mvprintw(14, 0, "%s: ", label);
        clrtoeol();
        refresh();
        buf[0] = '\0';

        nodelay(stdscr, FALSE);
        while (len + 1 < buf_sz) {
            ch = getch();
            if (ch == '\n' || ch == KEY_ENTER || ch == '\r') {
                break;
            }
            if (ch == 27) {
                nodelay(stdscr, TRUE);
                noecho();
                curs_set(0);
                return -1;
            }
            if (ch == KEY_BACKSPACE || ch == 127 || ch == '\b') {
                if (len > 0) {
                    len--;
                    buf[len] = '\0';
                    mvprintw(14, (int)strlen(label) + 2, "%s ", buf);
                    clrtoeol();
                    refresh();
                }
                continue;
            }
            if (ch >= 32 && ch < 127) {
                buf[len++] = (char)ch;
                buf[len] = '\0';
                mvprintw(14, (int)strlen(label) + 2, "%s", buf);
                refresh();
            }
        }
        nodelay(stdscr, TRUE);
        noecho();
        curs_set(0);
        attroff(COLOR_PAIR(1));
        return (int)len;
    }
#endif

    printf("%s%s: ", MAX25_TERM_SGR, label);
    fflush(stdout);
    if (fgets(buf, (int)buf_sz, stdin) == NULL) {
        return -1;
    }
    buf[strcspn(buf, "\r\n")] = '\0';
    return (int)strlen(buf);
}
