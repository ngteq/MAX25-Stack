/*
 * Set HDLC/baycom channel parameters when legacy sethdlc ioctl ABI breaks.
 * BayCom PR-Stack — Copyright (C) 2026 BayCom PR-Stack contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
#define _GNU_SOURCE
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <net/if.h>
#include <linux/if.h>
#include <linux/sockios.h>
#include <linux/hdlcdrv.h>

static int hdlc_ioctl(const char *ifname, struct hdlcdrv_ioctl *hi)
{
	struct ifreq ifr;
	int fd;

	fd = socket(AF_INET, SOCK_DGRAM, 0);
	if (fd < 0) {
		perror("socket");
		return -1;
	}

	memset(&ifr, 0, sizeof(ifr));
	strncpy(ifr.ifr_name, ifname, IFNAMSIZ - 1);
	ifr.ifr_data = (void *)hi;

	if (ioctl(fd, SIOCDEVPRIVATE, &ifr) < 0) {
		perror(ifname);
		close(fd);
		return -1;
	}

	close(fd);
	return 0;
}

static int get_params(const char *ifname, struct hdlcdrv_channel_params *cp)
{
	struct hdlcdrv_ioctl hi;

	memset(&hi, 0, sizeof(hi));
	hi.cmd = HDLCDRVCTL_GETCHANNELPAR;
	if (hdlc_ioctl(ifname, &hi) < 0)
		return -1;
	*cp = hi.data.cp;
	return 0;
}

static int set_params(const char *ifname, const struct hdlcdrv_channel_params *cp)
{
	struct hdlcdrv_ioctl hi;

	memset(&hi, 0, sizeof(hi));
	hi.cmd = HDLCDRVCTL_SETCHANNELPAR;
	hi.data.cp = *cp;
	return hdlc_ioctl(ifname, &hi);
}

static int get_stat(const char *ifname, struct hdlcdrv_channel_state *cs)
{
	struct hdlcdrv_ioctl hi;

	memset(&hi, 0, sizeof(hi));
	hi.cmd = HDLCDRVCTL_GETSTAT;
	if (hdlc_ioctl(ifname, &hi) < 0)
		return -1;
	*cs = hi.data.cs;
	return 0;
}

int main(int argc, char **argv)
{
	const char *ifname = "bcsf0";
	struct hdlcdrv_channel_params cp;
	struct hdlcdrv_channel_state cs;
	int txd = -1;

	if (argc > 1 && (!strcmp(argv[1], "-h") || !strcmp(argv[1], "--help"))) {
		fprintf(stderr, "Usage: %s [iface] [txd_units]\n", argv[0]);
		fprintf(stderr, "  txd_units: TX delay in 10 ms steps (e.g. 35 = 350 ms)\n");
		return 0;
	}

	if (argc > 1)
		ifname = argv[1];
	if (argc > 2)
		txd = atoi(argv[2]);

	if (get_params(ifname, &cp) < 0)
		return 1;

	printf("%s current channel params:\n", ifname);
	printf("  tx_delay=%d (%d ms)\n", cp.tx_delay, cp.tx_delay * 10);
	printf("  tx_tail=%d (%d ms)\n", cp.tx_tail, cp.tx_tail * 10);
	printf("  slottime=%d  ppersist=%d  fulldup=%d\n",
	       cp.slottime, cp.ppersist, cp.fulldup);

	if (txd >= 0) {
		cp.tx_delay = txd;
		if (set_params(ifname, &cp) < 0)
			return 1;
		printf("Set tx_delay to %d (%d ms)\n", txd, txd * 10);
	}

	if (get_stat(ifname, &cs) == 0) {
		printf("%s status:\n", ifname);
		printf("  ptt=%d dcd=%d ptt_keyed=%d\n", cs.ptt, cs.dcd, cs.ptt_keyed);
		printf("  rx=%lu tx=%lu rxerr=%lu txerr=%lu\n",
		       cs.rx_packets, cs.tx_packets, cs.rx_errors, cs.tx_errors);
	}

	return 0;
}
