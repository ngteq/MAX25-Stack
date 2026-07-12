/*
 * BayCom ser12 / baycom_ser_fdx offline test suite (no radio required).
 * BayCom PR-Stack — Copyright (C) 2026 BayCom PR-Stack contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <getopt.h>
#include <inttypes.h>
#include <net/if.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <termios.h>
#include <linux/if.h>
#include <linux/sockios.h>
#include <linux/hdlcdrv.h>

#define DEFAULT_IFACE "bcsf0"
#define DEFAULT_SERIAL "/dev/ttyS0"
#define DEFAULT_IOBASE 0x3f8
#define DEFAULT_IRQ 4
#define IRQ_SKIP -1
#define MAX_IRQ_SEC 5
#define MAX_MONITOR_SEC 10
#define MAX_CAL_SEC 2
#define IRQ_STORM_PER_SEC 80000UL

static int g_failures;
static int g_expect_iobase = DEFAULT_IOBASE;
static int g_expect_irq = DEFAULT_IRQ;
static int g_skip_serial;
static const char *g_expect_driver;
static const char *g_default_serial = DEFAULT_SERIAL;

static int parse_env_iobase(const char *s)
{
	if (!s || !*s)
		return DEFAULT_IOBASE;
	return (int)strtoul(s, NULL, 0);
}

static int parse_env_irq(const char *s)
{
	if (!s || !*s)
		return DEFAULT_IRQ;
	return (int)strtoul(s, NULL, 0);
}

static const char *env_or_legacy(const char *key, const char *legacy)
{
	const char *s = getenv(key);

	if (s && *s)
		return s;
	s = getenv(legacy);
	if (s && *s)
		return s;
	return NULL;
}

static void load_expectations(void)
{
	const char *s;

	g_expect_iobase = parse_env_iobase(env_or_legacy("BAYCOM_EXPECT_IOBASE", "PCCOM_EXPECT_IOBASE"));
	s = env_or_legacy("BAYCOM_EXPECT_IRQ", "PCCOM_EXPECT_IRQ");
	if (s && *s)
		g_expect_irq = parse_env_irq(s);
	else
		g_expect_irq = DEFAULT_IRQ;
	s = env_or_legacy("BAYCOM_SERIAL", "PCCOM_SERIAL");
	if (s)
		g_default_serial = s;
	s = getenv("BAYCOM_EXPECT_DRIVER");
	if (s && *s)
		g_expect_driver = s;
	s = getenv("BAYCOM_SKIP_SERIAL");
	g_skip_serial = s && !strcmp(s, "1");
	if (!g_skip_serial && g_expect_driver && !strcmp(g_expect_driver, "baycom_par"))
		g_skip_serial = 1;
}

static void fail(const char *msg)
{
	fprintf(stderr, "FAIL: %s\n", msg);
	g_failures++;
}

static void ok(const char *msg)
{
	printf("OK:   %s\n", msg);
}

static int hdlc_ioctl(const char *ifname, struct hdlcdrv_ioctl *hi)
{
	struct ifreq ifr;
	int fd;

	fd = socket(AF_INET, SOCK_DGRAM, 0);
	if (fd < 0)
		return -1;

	memset(&ifr, 0, sizeof(ifr));
	strncpy(ifr.ifr_name, ifname, IFNAMSIZ - 1);
	ifr.ifr_data = (void *)hi;

	if (ioctl(fd, SIOCDEVPRIVATE, &ifr) < 0) {
		close(fd);
		return -1;
	}

	close(fd);
	return 0;
}

static int hi_cmd(const char *ifname, int cmd, struct hdlcdrv_ioctl *hi)
{
	memset(hi, 0, sizeof(*hi));
	hi->cmd = cmd;
	return hdlc_ioctl(ifname, hi);
}

static int iface_flags(const char *ifname, unsigned int *flags, char *operstate,
		       size_t oslen)
{
	char path[128];
	FILE *f;

	snprintf(path, sizeof(path), "/sys/class/net/%s/flags", ifname);
	f = fopen(path, "r");
	if (!f)
		return -1;
	if (fscanf(f, "%x", flags) != 1) {
		fclose(f);
		return -1;
	}
	fclose(f);

	snprintf(path, sizeof(path), "/sys/class/net/%s/operstate", ifname);
	f = fopen(path, "r");
	if (!f)
		return -1;
	if (!fgets(operstate, oslen, f)) {
		fclose(f);
		return -1;
	}
	operstate[strcspn(operstate, "\n")] = '\0';
	fclose(f);
	return 0;
}

static unsigned long irq_line_sum(const char *line)
{
	const char *p;
	unsigned long sum = 0, v;

	p = strchr(line, ':');
	if (!p)
		return 0;
	p++;
	while (*p) {
		while (*p == ' ')
			p++;
		if (*p < '0' || *p > '9')
			break;
		if (sscanf(p, "%lu", &v) != 1)
			break;
		sum += v;
		while (*p >= '0' && *p <= '9')
			p++;
	}
	return sum;
}

static unsigned long irq_count(int irq)
{
	FILE *f = fopen("/proc/interrupts", "r");
	char line[512];
	unsigned long irqno;

	if (!f)
		return 0;

	while (fgets(line, sizeof(line), f)) {
		if (sscanf(line, " %lu:", &irqno) == 1 && irqno == (unsigned long)irq) {
			unsigned long sum = irq_line_sum(line);
			fclose(f);
			return sum;
		}
	}

	fclose(f);
	return 0;
}

static int read_modem_lines(const char *dev, int *dtr, int *rts, int *cts)
{
	int fd;
	int status;

	fd = open(dev, O_RDWR | O_NOCTTY | O_NONBLOCK);
	if (fd < 0)
		return -1;

	if (ioctl(fd, TIOCMGET, &status) < 0) {
		close(fd);
		return -1;
	}

	*dtr = !!(status & TIOCM_DTR);
	*rts = !!(status & TIOCM_RTS);
	*cts = !!(status & TIOCM_CTS);
	close(fd);
	return 0;
}

static void iface_path(char *buf, size_t len, const char *iface)
{
	snprintf(buf, len, "/sys/class/net/%s", iface);
}

static void test_interface(const char *iface)
{
	unsigned int flags = 0;
	char oper[32] = "?";
	char sysfs[128];

	printf("\n== Interface %s ==\n", iface);
	if (iface_flags(iface, &flags, oper, sizeof(oper)) < 0) {
		fail("network interface missing (is baycom_ser_fdx or baycom_par loaded?)");
		return;
	}

	printf("  operstate=%s flags=0x%x\n", oper, flags);
	if (flags & IFF_UP)
		ok("interface is UP");
	else
		fail("interface is DOWN — run: ip link set <iface> up");

	iface_path(sysfs, sizeof(sysfs), iface);
	if (access(sysfs, F_OK) == 0)
		ok("network device node exists");
}

static void test_ioctls(const char *iface)
{
	struct hdlcdrv_ioctl hi;

	printf("\n== HDLC ioctls ==\n");

	if (hi_cmd(iface, HDLCDRVCTL_GETMODEMPAR, &hi) == 0) {
		printf("  modem: iobase=0x%x irq=%d dma=%d\n",
		       hi.data.mp.iobase, hi.data.mp.irq, hi.data.mp.dma);
		if (hi.data.mp.iobase == (unsigned short)g_expect_iobase)
			ok("iobase matches expected");
		else
			fail("unexpected iobase");
		if (g_expect_irq < 0)
			ok("irq check skipped (parport assigns IRQ dynamically)");
		else if (hi.data.mp.irq == g_expect_irq)
			ok("irq matches expected");
		else
			fail("unexpected irq");
	} else {
		fail("HDLCDRVCTL_GETMODEMPAR");
	}

	if (hi_cmd(iface, HDLCDRVCTL_GETCHANNELPAR, &hi) == 0) {
		printf("  channel: tx_delay=%d (%d ms) tx_tail=%d slottime=%d ppersist=%d fulldup=%d\n",
		       hi.data.cp.tx_delay, hi.data.cp.tx_delay * 10,
		       hi.data.cp.tx_tail, hi.data.cp.slottime,
		       hi.data.cp.ppersist, hi.data.cp.fulldup);
		ok("GETCHANNELPAR");
	} else {
		fail("HDLCDRVCTL_GETCHANNELPAR");
	}

	if (hi_cmd(iface, HDLCDRVCTL_GETSTAT, &hi) == 0) {
		printf("  stat: ptt=%d dcd=%d ptt_keyed=%d rx=%lu tx=%lu rxerr=%lu txerr=%lu\n",
		       hi.data.cs.ptt, hi.data.cs.dcd, hi.data.cs.ptt_keyed,
		       hi.data.cs.rx_packets, hi.data.cs.tx_packets,
		       hi.data.cs.rx_errors, hi.data.cs.tx_errors);
		ok("GETSTAT");
	} else {
		fail("HDLCDRVCTL_GETSTAT");
	}

	if (hi_cmd(iface, HDLCDRVCTL_GETMODE, &hi) == 0) {
		printf("  mode: %s\n", hi.data.modename);
		ok("GETMODE");
	} else {
		fail("HDLCDRVCTL_GETMODE (baycom extension)");
	}

	if (hi_cmd(iface, HDLCDRVCTL_DRIVERNAME, &hi) == 0) {
		printf("  driver: %s\n", hi.data.drivername);
		if (hi.data.drivername[0]) {
			if (g_expect_driver && strncmp(hi.data.drivername, g_expect_driver,
						       strlen(g_expect_driver)) != 0)
				fail("unexpected driver name");
			else
				ok("DRIVERNAME");
		} else
			fail("empty driver name");
	} else {
		fail("HDLCDRVCTL_DRIVERNAME");
	}

	if (hi_cmd(iface, HDLCDRVCTL_MODELIST, &hi) == 0) {
		printf("  modes: %s\n", hi.data.modename);
		ok("MODELIST");
	} else {
		fail("HDLCDRVCTL_MODELIST");
	}
}

static void test_irq_activity(const char *iface, int seconds)
{
	unsigned long a, b;

	(void)iface;
	if (g_expect_irq < 0) {
		printf("\n== IRQ activity skipped (parport backend) ==\n");
		ok("parport IRQ managed by kernel — no INI irq to verify");
		return;
	}
	printf("\n== IRQ activity (%d s, expect baycom interrupts while UP) ==\n", seconds);
	a = irq_count(g_expect_irq);
	sleep(seconds);
	b = irq_count(g_expect_irq);
	printf("  IRQ %d total: %lu -> %lu (delta %lu, all CPUs)\n",
	       g_expect_irq, a, b, b - a);
	if (seconds > 0 && (b - a) / (unsigned long)seconds > IRQ_STORM_PER_SEC) {
		fail("IRQ rate extremely high — possible storm / wrong IRQ (host freeze risk)");
		return;
	}
	if (b > a)
		ok("UART/modem interrupts are firing");
	else
		fail("no IRQ activity ? driver may be stuck or interface down");
}

static void test_monitor(const char *iface, int seconds)
{
	struct hdlcdrv_ioctl hi;
	int i;

	printf("\n== Monitor %d s (no radio: DCD should stay 0) ==\n", seconds);
	for (i = 0; i < seconds; i++) {
		if (hi_cmd(iface, HDLCDRVCTL_GETSTAT, &hi) == 0) {
			printf("  [%2d] ptt=%d dcd=%d keyed=%d rx=%lu tx=%lu\n",
			       i, hi.data.cs.ptt, hi.data.cs.dcd,
			       hi.data.cs.ptt_keyed, hi.data.cs.rx_packets,
			       hi.data.cs.tx_packets);
		}
		sleep(1);
	}
	ok("monitor completed");
}

static void test_calibrate(const char *iface, const char *serial, unsigned int seconds)
{
	struct hdlcdrv_ioctl hi;
	int ptt_before = -1, ptt_during = 0;
	int ptt_line_during = 0;

	printf("\n== Calibrate TX %u s (keys modem PTT, no radio needed) ==\n", seconds);

	if (hi_cmd(iface, HDLCDRVCTL_GETSTAT, &hi) == 0)
		ptt_before = hi.data.cs.ptt_keyed;

	memset(&hi, 0, sizeof(hi));
	hi.cmd = HDLCDRVCTL_CALIBRATE;
	hi.data.calibrate = seconds;
	if (hdlc_ioctl(iface, &hi) < 0) {
		if (errno == EPERM) {
			printf("SKIP: calibrate needs root (run as root for PTT test)\n");
			return;
		}
		perror("FAIL: HDLCDRVCTL_CALIBRATE");
		g_failures++;
		return;
	}
	ok("calibrate ioctl accepted");

	/* poll while calibration runs */
	for (unsigned int i = 0; i < seconds * 5; i++) {
		usleep(200000);
		if (hi_cmd(iface, HDLCDRVCTL_GETSTAT, &hi) == 0) {
			if (hi.data.cs.ptt_keyed)
				ptt_during = 1;
			if (hi.data.cs.ptt)
				ptt_line_during = 1;
		}
	}

	if (hi_cmd(iface, HDLCDRVCTL_GETSTAT, &hi) == 0) {
		printf("  ptt=%d ptt_keyed before=%d during_keyed=%d during_ptt=%d after_keyed=%d\n",
		       hi.data.cs.ptt, ptt_before, ptt_during, ptt_line_during,
		       hi.data.cs.ptt_keyed);
	}

	if (ptt_during || ptt_line_during)
		ok("PTT active during calibration — modem path works");
	else {
		char msg[128];
		if (g_skip_serial)
			snprintf(msg, sizeof(msg),
				 "PTT not seen during calibration — check parport modem/cable on %s",
				 iface);
		else
			snprintf(msg, sizeof(msg),
				 "PTT not seen during calibration — check modem/cable on %s",
				 serial);
		fail(msg);
	}
}

static void test_serial_busy(const char *serial)
{
	int dtr, rts, cts;

	if (g_skip_serial) {
		printf("\n== Serial device skipped (kernel-par96 / BAYCOM_SKIP_SERIAL) ==\n");
		ok("no serial device for parallel port backend");
		return;
	}

	printf("\n== Serial device %s ==\n", serial);
	if (read_modem_lines(serial, &dtr, &rts, &cts) == 0) {
		printf("  modem lines: DTR=%d RTS=%d CTS=%d\n", dtr, rts, cts);
		ok("read modem control lines");
		printf("  note: while baycom owns UART, values reflect kernel driver state\n");
	} else if (errno == EBUSY || errno == EIO) {
		ok("serial port busy (expected while baycom_ser_fdx is active)");
	} else {
		perror("serial open");
		fail("cannot open serial device");
	}
}

static void usage(const char *prog)
{
	fprintf(stderr,
		"Usage: %s [options] [command]\n"
		"\n"
		"Offline tests for BayCom kernel modems via baycom_ser_fdx / baycom_par (no radio required).\n"
		"\n"
		"Environment:\n"
		"  BAYCOM_EXPECT_IOBASE   expected LPT/UART iobase\n"
		"  BAYCOM_EXPECT_IRQ      expected IRQ (-1 skips check for parport)\n"
		"  BAYCOM_EXPECT_DRIVER   expected driver name (e.g. baycom_par)\n"
		"  BAYCOM_SKIP_SERIAL=1   skip /dev/ttyS* line tests (par96)\n"
		"\n"
		"Commands:\n"
		"  all          run full suite (default)\n"
		"  quick        status + short IRQ sample (no PTT, ~3 s)\n"
		"  status       interface + ioctl snapshot\n"
		"  monitor [s]  poll PTT/DCD/counters (default 5 s)\n"
		"  irq [s]      measure IRQ 4 activity (default 2 s)\n"
		"  calibrate [s] TX calibration / PTT test (default 2 s, needs root)\n"
		"  serial       read /dev/ttyS0 modem lines if possible\n"
		"\n"
		"Options:\n"
		"  -i IFACE     network interface (default bcsf0)\n"
		"  -s DEV       serial device (default /dev/ttyS0)\n"
		"  -q           quiet (only failures)\n",
		prog);
}

int main(int argc, char **argv)
{
	const char *iface = DEFAULT_IFACE;
	const char *serial = NULL;
	const char *cmd = "all";
	int monitor_sec = 5;
	int irq_sec = 2;
	int cal_sec = 2;
	int opt;

	load_expectations();
	if (!serial)
		serial = g_default_serial;

	while ((opt = getopt(argc, argv, "i:s:q")) != -1) {
		switch (opt) {
		case 'i': iface = optarg; break;
		case 's': serial = optarg; break;
		case 'q': break;
		default: usage(argv[0]); return 2;
		}
	}

	argc -= optind;
	argv += optind;
	if (argc > 0)
		cmd = argv[0];
	if (argc > 1 && !strcmp(cmd, "monitor"))
		monitor_sec = atoi(argv[1]);
	if (argc > 1 && !strcmp(cmd, "irq"))
		irq_sec = atoi(argv[1]);
	if (argc > 1 && !strcmp(cmd, "calibrate"))
		cal_sec = atoi(argv[1]);

	if (irq_sec < 1)
		irq_sec = 1;
	if (irq_sec > MAX_IRQ_SEC)
		irq_sec = MAX_IRQ_SEC;
	if (monitor_sec < 1)
		monitor_sec = 1;
	if (monitor_sec > MAX_MONITOR_SEC)
		monitor_sec = MAX_MONITOR_SEC;
	if (cal_sec < 1)
		cal_sec = 1;
	if (cal_sec > MAX_CAL_SEC)
		cal_sec = MAX_CAL_SEC;

	printf("BayCom offline test\n");
	printf("  iface=%s serial=%s command=%s\n", iface, serial, cmd);

	if (!strcmp(cmd, "all")) {
		test_interface(iface);
		test_ioctls(iface);
		if (g_expect_irq >= 0)
			test_irq_activity(iface, irq_sec);
		test_monitor(iface, monitor_sec);
		if (!g_skip_serial) {
			test_serial_busy(serial);
			test_calibrate(iface, serial, cal_sec);
		}
	} else if (!strcmp(cmd, "quick")) {
		test_interface(iface);
		test_ioctls(iface);
		if (g_expect_irq >= 0)
			test_irq_activity(iface, 1);
	} else if (!strcmp(cmd, "status")) {
		test_interface(iface);
		test_ioctls(iface);
	} else if (!strcmp(cmd, "monitor")) {
		test_monitor(iface, monitor_sec);
	} else if (!strcmp(cmd, "irq")) {
		test_irq_activity(iface, irq_sec);
	} else if (!strcmp(cmd, "calibrate")) {
		test_calibrate(iface, serial, cal_sec);
	} else if (!strcmp(cmd, "serial")) {
		test_serial_busy(serial);
	} else {
		usage(argv[0]);
		return 2;
	}

	printf("\n== Summary: %d failure(s) ==\n", g_failures);
	return g_failures ? 1 : 0;
}
