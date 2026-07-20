/*
 * Simple INI loader for max25-bcpr (max 2 devices: [bc0] / [bc1]).
 */
#include "bcpr/bcpr_config.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void bcpr_config_defaults(bcpr_config_t *cfg)
{
    int i;
    memset(cfg, 0, sizeof(*cfg));
    snprintf(cfg->state_dir, sizeof(cfg->state_dir), "%s", "/var/run/max25-bcpr");
    cfg->dry_run = 0;
    cfg->n_dev = 0;
    for (i = 0; i < BCPR_MAX_DEVICES; i++) {
        bcpr_dev_config_t *d = &cfg->dev[i];
        d->enabled = 0;
        d->baud = 1200;
        snprintf(d->mode, sizeof(d->mode), "%s", "ser12*");
        d->tx_delay = 35;
        d->tx_tail = 2;
        d->slottime = 10;
        d->ppersist = 40;
        d->fulldup = 0;
    }
}

static void trim(char *s)
{
    char *e;
    while (*s && isspace((unsigned char)*s)) {
        memmove(s, s + 1, strlen(s));
    }
    e = s + strlen(s);
    while (e > s && isspace((unsigned char)e[-1])) {
        *--e = '\0';
    }
}

static int parse_u(const char *v, unsigned *out)
{
    char *end = NULL;
    unsigned long x = strtoul(v, &end, 0);
    if (!v[0] || (end && *end)) {
        return -1;
    }
    *out = (unsigned)x;
    return 0;
}

static int parse_i(const char *v, int *out)
{
    char *end = NULL;
    long x = strtol(v, &end, 0);
    if (!v[0] || (end && *end)) {
        return -1;
    }
    *out = (int)x;
    return 0;
}

static int truthy(const char *v)
{
    return (strcasecmp(v, "yes") == 0 || strcasecmp(v, "true") == 0 ||
            strcasecmp(v, "on") == 0 || strcmp(v, "1") == 0);
}

static int apply_kv(bcpr_config_t *cfg, int section, const char *key,
                    const char *val)
{
    /* section: -1 = [max25-bcpr]/[bcpr] global, 0 = bc0, 1 = bc1 */
    if (section < 0) {
        if (strcmp(key, "dry_run") == 0) {
            cfg->dry_run = truthy(val);
            return 0;
        }
        if (strcmp(key, "state_dir") == 0) {
            snprintf(cfg->state_dir, sizeof(cfg->state_dir), "%s", val);
            return 0;
        }
        return 0;
    }
    if (section >= BCPR_MAX_DEVICES) {
        return -1;
    }
    {
        bcpr_dev_config_t *d = &cfg->dev[section];
        if (strcmp(key, "enabled") == 0) {
            d->enabled = truthy(val);
        } else if (strcmp(key, "serial") == 0 || strcmp(key, "tty") == 0) {
            snprintf(d->serial, sizeof(d->serial), "%s", val);
            d->enabled = 1;
        } else if (strcmp(key, "iobase") == 0) {
            return parse_u(val, &d->iobase);
        } else if (strcmp(key, "irq") == 0) {
            return parse_u(val, &d->irq);
        } else if (strcmp(key, "baud") == 0) {
            return parse_u(val, &d->baud);
        } else if (strcmp(key, "mode") == 0) {
            snprintf(d->mode, sizeof(d->mode), "%s", val);
        } else if (strcmp(key, "kiss_link") == 0) {
            snprintf(d->kiss_link, sizeof(d->kiss_link), "%s", val);
        } else if (strcmp(key, "tx_delay") == 0 || strcmp(key, "txdelay") == 0) {
            return parse_i(val, &d->tx_delay);
        } else if (strcmp(key, "tx_tail") == 0 || strcmp(key, "txtail") == 0) {
            return parse_i(val, &d->tx_tail);
        } else if (strcmp(key, "slottime") == 0) {
            return parse_i(val, &d->slottime);
        } else if (strcmp(key, "ppersist") == 0) {
            return parse_i(val, &d->ppersist);
        } else if (strcmp(key, "fulldup") == 0) {
            d->fulldup = truthy(val);
        }
    }
    return 0;
}

int bcpr_config_load(bcpr_config_t *cfg, const char *path)
{
    FILE *f;
    char line[512];
    int section = -1;
    int i;

    if (!cfg || !path) {
        return -1;
    }
    bcpr_config_defaults(cfg);
    f = fopen(path, "r");
    if (!f) {
        return -1;
    }
    while (fgets(line, sizeof(line), f)) {
        char *eq;
        char *p = line;
        trim(p);
        if (p[0] == '\0' || p[0] == '#' || p[0] == ';') {
            continue;
        }
        if (p[0] == '[') {
            char *end = strchr(p, ']');
            if (!end) {
                continue;
            }
            *end = '\0';
            p++;
            if (strcasecmp(p, "max25-bcpr") == 0 || strcasecmp(p, "bcpr") == 0 ||
                strcasecmp(p, "global") == 0) {
                section = -1;
            } else if (strcasecmp(p, "bc0") == 0 ||
                       strcasecmp(p, "device.bc0") == 0) {
                section = 0;
            } else if (strcasecmp(p, "bc1") == 0 ||
                       strcasecmp(p, "device.bc1") == 0) {
                section = 1;
            } else {
                section = -2; /* ignore unknown */
            }
            continue;
        }
        if (section == -2) {
            continue;
        }
        eq = strchr(p, '=');
        if (!eq) {
            continue;
        }
        *eq = '\0';
        trim(p);
        trim(eq + 1);
        (void)apply_kv(cfg, section, p, eq + 1);
    }
    fclose(f);

    cfg->n_dev = 0;
    for (i = 0; i < BCPR_MAX_DEVICES; i++) {
        if (cfg->dev[i].enabled && cfg->dev[i].serial[0]) {
            if (!cfg->dev[i].kiss_link[0]) {
                snprintf(cfg->dev[i].kiss_link, sizeof(cfg->dev[i].kiss_link),
                         "%s/kiss-bc%d", cfg->state_dir, i);
            }
            cfg->n_dev++;
        } else {
            cfg->dev[i].enabled = 0;
        }
    }
    if (cfg->n_dev > BCPR_MAX_DEVICES) {
        return -1;
    }
    return 0;
}
