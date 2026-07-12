/*
 * Bidirectional KISS <-> kernel AX.25 (bcsfX) bridge for external KISS clients.
 * BayCom PR-Stack — Copyright (C) 2026 BayCom PR-Stack contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <net/if.h>
#include <poll.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <pty.h>
#include <linux/if_arp.h>
#include <linux/if_packet.h>

#define KISS_FEND  0xC0
#define KISS_FESC  0xDB
#define KISS_TFEND 0xDC
#define KISS_TFESC 0xDD
#define KISS_CMD_DATA 0x00
#define KISS_MAX_FRAME 2048

static volatile sig_atomic_t g_stop;

static void on_signal(int sig)
{
	(void)sig;
	g_stop = 1;
}

static int set_nonblock(int fd)
{
	int flags = fcntl(fd, F_GETFL, 0);
	if (flags < 0)
		return -1;
	return fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

static int open_packet_socket(const char *ifname)
{
	struct sockaddr_ll sll;
	int fd, ifindex;

	ifindex = if_nametoindex(ifname);
	if (ifindex == 0)
		return -1;

	fd = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_AX25));
	if (fd < 0)
		return -1;

	memset(&sll, 0, sizeof(sll));
	sll.sll_family = AF_PACKET;
	sll.sll_protocol = htons(ETH_P_AX25);
	sll.sll_ifindex = ifindex;

	if (bind(fd, (struct sockaddr *)&sll, sizeof(sll)) < 0) {
		close(fd);
		return -1;
	}

	return fd;
}

typedef struct {
	uint8_t buf[KISS_MAX_FRAME];
	size_t len;
	bool escape;
} kiss_dec_t;

static void kiss_dec_init(kiss_dec_t *d)
{
	memset(d, 0, sizeof(*d));
}

static int kiss_dec_feed(kiss_dec_t *d, uint8_t byte, uint8_t *out, size_t *out_len)
{
	if (byte == KISS_FEND) {
		if (d->len > 1) {
			*out_len = d->len - 1; /* drop port/cmd byte */
			memcpy(out, d->buf + 1, *out_len);
			d->len = 0;
			d->escape = false;
			return 1;
		}
		d->len = 0;
		d->escape = false;
		return 0;
	}

	if (d->escape) {
		if (byte == KISS_TFEND)
			byte = KISS_FEND;
		else if (byte == KISS_TFESC)
			byte = KISS_FESC;
		d->escape = false;
	} else if (byte == KISS_FESC) {
		d->escape = true;
		return 0;
	}

	if (d->len >= sizeof(d->buf))
		return -1;

	d->buf[d->len++] = byte;
	return 0;
}

static size_t kiss_encode(const uint8_t *frame, size_t len, uint8_t *out, size_t cap)
{
	size_t pos = 0;

	if (cap < 4)
		return 0;

	out[pos++] = KISS_FEND;
	out[pos++] = KISS_CMD_DATA;

	for (size_t i = 0; i < len; i++) {
		uint8_t b = frame[i];
		if (b == KISS_FEND) {
			if (pos + 2 > cap)
				return 0;
			out[pos++] = KISS_FESC;
			out[pos++] = KISS_TFEND;
		} else if (b == KISS_FESC) {
			if (pos + 2 > cap)
				return 0;
			out[pos++] = KISS_FESC;
			out[pos++] = KISS_TFESC;
		} else {
			if (pos + 1 > cap)
				return 0;
			out[pos++] = b;
		}
	}

	if (pos + 1 > cap)
		return 0;
	out[pos++] = KISS_FEND;
	return pos;
}

static int ensure_parent_dir(const char *path)
{
	char tmp[512];
	char *slash;

	snprintf(tmp, sizeof(tmp), "%s", path);
	slash = strrchr(tmp, '/');
	if (!slash)
		return 0;
	*slash = '\0';
	if (tmp[0] == '\0')
		return 0;
	return mkdir(tmp, 0755);
}

static int setup_pty(const char *link_path, int *master_out, char *slave_path, size_t slave_len)
{
	int master;

	master = posix_openpt(O_RDWR | O_NOCTTY);
	if (master < 0)
		return -1;
	if (grantpt(master) < 0) {
		close(master);
		return -1;
	}
	if (unlockpt(master) < 0) {
		close(master);
		return -1;
	}
	if (ptsname_r(master, slave_path, slave_len) != 0) {
		close(master);
		return -1;
	}

	if (ensure_parent_dir(link_path) < 0 && errno != EEXIST)
		return -1;

	unlink(link_path);
	if (symlink(slave_path, link_path) < 0) {
		close(master);
		return -1;
	}

	*master_out = master;
	return 0;
}

static void usage(const char *prog)
{
	fprintf(stderr,
		"Usage: %s -i bcsf0 -l /var/run/baycom-pr/kiss [-v]\n"
		"  KISS PTY bridge (protocol=kiss on -l path).\n",
		prog);
}

int main(int argc, char **argv)
{
	const char *ifname = "bcsf0";
	const char *link_path = "/var/run/baycom-pr/kiss";
	int verbose = 0;
	int opt, pkt_fd, pty_fd;
	char slave_path[256];
	kiss_dec_t dec;
	uint8_t frame[KISS_MAX_FRAME];
	uint8_t kiss_out[KISS_MAX_FRAME + 16];

	while ((opt = getopt(argc, argv, "i:l:vh")) != -1) {
		switch (opt) {
		case 'i': ifname = optarg; break;
		case 'l': link_path = optarg; break;
		case 'v': verbose = 1; break;
		case 'h':
		default:
			usage(argv[0]);
			return opt == 'h' ? 0 : 2;
		}
	}

	signal(SIGINT, on_signal);
	signal(SIGTERM, on_signal);

	pkt_fd = open_packet_socket(ifname);
	if (pkt_fd < 0) {
		perror("packet socket");
		return 1;
	}

	if (setup_pty(link_path, &pty_fd, slave_path, sizeof(slave_path)) < 0) {
		perror("pty");
		close(pkt_fd);
		return 1;
	}

	set_nonblock(pkt_fd);
	set_nonblock(pty_fd);
	kiss_dec_init(&dec);

	printf("baycom_kissbridge: if=%s kiss=%s -> %s\n", ifname, link_path, slave_path);
	fflush(stdout);

	while (!g_stop) {
		struct pollfd fds[2];
		int n;

		fds[0].fd = pkt_fd;
		fds[0].events = POLLIN;
		fds[1].fd = pty_fd;
		fds[1].events = POLLIN;

		n = poll(fds, 2, 500);
		if (n < 0) {
			if (errno == EINTR)
				continue;
			perror("poll");
			break;
		}

		if (fds[0].revents & POLLIN) {
			uint8_t buf[4096];
			ssize_t r = recv(pkt_fd, buf, sizeof(buf), 0);
			size_t klen;

			if (r <= 0)
				continue;
			klen = kiss_encode(buf, (size_t)r, kiss_out, sizeof(kiss_out));
			if (klen > 0) {
				(void)write(pty_fd, kiss_out, klen);
				if (verbose)
					fprintf(stderr, "air->kiss %zd bytes\n", r);
			}
		}

		if (fds[1].revents & POLLIN) {
			uint8_t buf[512];
			ssize_t r = read(pty_fd, buf, sizeof(buf));

			if (r <= 0)
				continue;

			for (ssize_t i = 0; i < r; i++) {
				size_t out_len = 0;
				int rc = kiss_dec_feed(&dec, buf[i], frame, &out_len);

				if (rc < 0) {
					kiss_dec_init(&dec);
					continue;
				}
				if (rc == 1 && out_len > 0) {
					struct sockaddr_ll sll;
					socklen_t slen = sizeof(sll);

					memset(&sll, 0, sizeof(sll));
					sll.sll_family = AF_PACKET;
					sll.sll_ifindex = if_nametoindex(ifname);
					sll.sll_halen = 0;

					if (sendto(pkt_fd, frame, out_len, 0,
						   (struct sockaddr *)&sll, slen) < 0) {
						perror("sendto");
					} else if (verbose) {
						fprintf(stderr, "kiss->air %zu bytes\n", out_len);
					}
				}
			}
		}
	}

	close(pty_fd);
	close(pkt_fd);
	unlink(link_path);
	return 0;
}
