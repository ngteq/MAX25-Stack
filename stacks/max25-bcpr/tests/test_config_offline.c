/*
 * Offline config parse test — no UART.
 */
#include "bcpr/bcpr_config.h"

#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(void)
{
    const char *path = "share/bcpr.ini.example";
    bcpr_config_t cfg;
    char cwd[512];

    if (!getcwd(cwd, sizeof(cwd))) {
        return 1;
    }
    /* Prefer path relative to build or source. */
    if (access(path, R_OK) != 0) {
        path = "../share/bcpr.ini.example";
    }
    if (access(path, R_OK) != 0) {
        path = "../../stacks/bcpr/share/bcpr.ini.example";
    }
    if (bcpr_config_load(&cfg, path) != 0) {
        /* Write a minimal temp INI. */
        FILE *f = fopen("/tmp/max25-bcpr-test.ini", "w");
        if (!f) {
            return 1;
        }
        fputs("[max25-bcpr]\ndry_run = yes\nstate_dir = /tmp/max25-bcpr\n"
              "[bc0]\nserial = /dev/ttyS0\niobase = 0x3f8\nirq = 4\n"
              "mode = ser12*\nkiss_link = /tmp/max25-bcpr/kiss-bc0\n",
              f);
        fclose(f);
        path = "/tmp/max25-bcpr-test.ini";
        if (bcpr_config_load(&cfg, path) != 0) {
            fprintf(stderr, "FAIL: load\n");
            return 1;
        }
    }
    if (cfg.n_dev < 1 || !cfg.dev[0].enabled) {
        fprintf(stderr, "FAIL: no bc0\n");
        return 1;
    }
    if (cfg.dev[0].irq != 4 || cfg.dev[0].iobase != 0x3f8) {
        fprintf(stderr, "FAIL: irq/iobase\n");
        return 1;
    }
    puts("OK: test_config_offline");
    return 0;
}
