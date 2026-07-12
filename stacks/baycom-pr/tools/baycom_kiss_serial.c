/*
 * KISS modem on serial/USB (ttyUSB, ttyACM) <-> PTY symlink for clients.
 * BayCom PR-Stack — Copyright (C) 2026 BayCom PR-Stack contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>
#include <pty.h>
#include <stdint.h>
#include <sys/stat.h>

static volatile sig_atomic_t g_stop;

static void on_signal(int sig)
{
	(void)sig;
	g_stop = 1;
}

static speed_t baud_to_flag(int baud)
{
	switch (baud) {
	case 300: return B300;
	case 1200: return B1200;
	case 2400: return B2400;
	case 4800: return B4800;
	case 9600: return B9600;
	case 19200: return B19200;
	case 38400: return B38400;
	case 57600: return B57600;
	case 115200: return B115200;
	default: return B9600;
	}
}

static int open_serial(const char *dev, int baud)
{
	struct termios tio;
	int fd;

	fd = open(dev, O_RDWR | O_NOCTTY | O_NONBLOCK);
	if (fd < 0)
		return -1;

	if (tcgetattr(fd, &tio) < 0) {
		close(fd);
		return -1;
	}
	cfmakeraw(&tio);
	cfsetispeed(&tio, baud_to_flag(baud));
	cfsetospeed(&tio, baud_to_flag(baud));
	tio.c_cflag |= (CLOCAL | CREAD);
	tio.c_cc[VMIN] = 0;
	tio.c_cc[VTIME] = 1;
	if (tcsetattr(fd, TCSANOW, &tio) < 0) {
		close(fd);
		return -1;
	}
	return fd;
}

static int relay_loop(int ser_fd, int pty_fd)
{
	uint8_t buf[4096];
	struct pollfd pf[2];
	int n;

	while (!g_stop) {
		pf[0].fd = ser_fd;
		pf[0].events = POLLIN;
		pf[1].fd = pty_fd;
		pf[1].events = POLLIN;
		n = poll(pf, 2, 500);
		if (n < 0) {
			if (errno == EINTR)
				continue;
			return -1;
		}
		if (pf[0].revents & POLLIN) {
			ssize_t r = read(ser_fd, buf, sizeof(buf));
			if (r < 0 && errno != EAGAIN)
				return -1;
			if (r > 0 && write(pty_fd, buf, (size_t)r) != r)
				return -1;
		}
		if (pf[1].revents & POLLIN) {
			ssize_t r = read(pty_fd, buf, sizeof(buf));
			if (r < 0 && errno != EAGAIN)
				return -1;
			if (r > 0 && write(ser_fd, buf, (size_t)r) != r)
				return -1;
		}
		if (pf[0].revents & (POLLERR | POLLHUP | POLLNVAL))
			return -1;
		if (pf[1].revents & (POLLERR | POLLHUP | POLLNVAL))
			return -1;
	}
	return 0;
}

static void usage(const char *prog)
{
	fprintf(stderr,
		"Usage: %s -s <serial> -l <kiss-symlink> [-b baud] [-v]\n"
		"\n"
		"  Relay KISS bytes between a serial/USB modem and a PTY symlink.\n"
		"  Typical: -s /dev/ttyUSB0 -b 9600 -l /var/run/baycom-pr/kiss-a\n",
		prog);
}

int main(int argc, char **argv)
{
	const char *serial = NULL;
	const char *link = NULL;
	int baud = 9600;
	int opt, ser_fd, mfd, verbose = 0;
	char slave[256];

	while ((opt = getopt(argc, argv, "s:l:b:v")) != -1) {
		switch (opt) {
		case 's': serial = optarg; break;
		case 'l': link = optarg; break;
		case 'b': baud = atoi(optarg); break;
		case 'v': verbose = 1; break;
		default: usage(argv[0]); return 2;
		}
	}

	if (!serial || !link) {
		usage(argv[0]);
		return 2;
	}

	signal(SIGINT, on_signal);
	signal(SIGTERM, on_signal);

	ser_fd = open_serial(serial, baud);
	if (ser_fd < 0) {
		perror("open serial");
		return 1;
	}

	if (openpty(&mfd, NULL, slave, NULL, NULL) < 0) {
		perror("openpty");
		close(ser_fd);
		return 1;
	}

	unlink(link);
	if (symlink(slave, link) < 0) {
		perror("symlink");
		close(mfd);
		close(ser_fd);
		return 1;
	}

	if (verbose)
		printf("baycom_kiss_serial: %s (%d) <-> %s -> %s\n",
		       serial, baud, link, slave);

	relay_loop(ser_fd, mfd);

	unlink(link);
	close(mfd);
	close(ser_fd);
	return 0;
}
