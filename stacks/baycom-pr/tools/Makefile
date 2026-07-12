CC ?= cc
CFLAGS ?= -O2 -Wall -Wextra
LDFLAGS ?=

BINARIES := baycom_test baycom_sethdlc baycom_kissbridge baycom_kiss_serial
LEGACY_ALIASES := pccom_test pccom_sethdlc pccom_kissbridge
PREFIX ?= /usr/local

.PHONY: all clean install test-config

all: $(BINARIES)

baycom_test: baycom_test.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

baycom_sethdlc: baycom_sethdlc.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

baycom_kissbridge: baycom_kissbridge.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS) -lutil

baycom_kiss_serial: baycom_kiss_serial.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS) -lutil

install: all
	install -d $(PREFIX)/sbin
	install -m 755 $(BINARIES) baycom_ini_load.py baycom_validate_config.py baycom_serial_status.py baycom_preflight.py baycom_probe.py baycom_doctor.py baycom_axports.py $(PREFIX)/sbin/
	@for a in $(LEGACY_ALIASES); do \
		t="$${a/pccom/baycom}"; \
		ln -sf "$$t" "$(PREFIX)/sbin/$$a"; \
	done
	install -d /etc/baycom/legacy /etc/baycom/minicom /etc/baycom/axports /etc/baycom/examples /etc/baycom/rc.d
	@test -f /etc/baycom/baycom-pr.ini || install -m 644 ../config/baycom-pr.ini /etc/baycom/baycom-pr.ini
	@test -f /etc/baycom/modems.ini || install -m 644 ../config/modems.ini /etc/baycom/modems.ini
	install -m 644 ../config/legacy/pccom.env /etc/baycom/legacy/pccom.env
	install -m 644 ../config/legacy/pccom.env.modem-a /etc/baycom/legacy/pccom.env.modem-a
	install -m 644 ../config/legacy/pccom.env.modem-b /etc/baycom/legacy/pccom.env.modem-b
	install -m 644 ../config/legacy/pccom.env.dual /etc/baycom/legacy/pccom.env.dual
	install -m 644 ../config/minicom/minirc.baycom-serial /etc/baycom/minicom/minirc.baycom-serial
	install -m 644 ../config/minicom/minirc.baycom-kiss /etc/baycom/minicom/minirc.baycom-kiss
	install -m 644 ../config/axports/single.snippet /etc/baycom/axports/single.snippet
	install -m 644 ../config/axports/dual.snippet /etc/baycom/axports/dual.snippet
	install -d /etc/baycom/systemd
	install -m 644 ../config/systemd/baycom-pr.service /etc/baycom/systemd/baycom-pr.service
	install -m 644 ../VERSION /etc/baycom/VERSION
	install -d /etc/baycom/examples
	install -m 644 ../config/examples/baycom-pr.dual.ini /etc/baycom/examples/baycom-pr.dual.ini
	install -m 644 ../config/examples/baycom-pr.cb.ini /etc/baycom/examples/baycom-pr.cb.ini
	install -m 644 ../config/examples/baycom-pr.ham.ini /etc/baycom/examples/baycom-pr.ham.ini
	install -m 644 ../config/examples/baycom-pr.par96.ini /etc/baycom/examples/baycom-pr.par96.ini
	install -m 644 ../config/examples/baycom-pr.picpar.ini /etc/baycom/examples/baycom-pr.picpar.ini
	install -m 755 ../scripts/rc.baycom-pr /etc/baycom/rc.d/rc.baycom-pr
	install -m 755 ../scripts/rc.baycom-pr /etc/baycom/rc.d/rc.pccom
	install -m 755 ../scripts/baycom-pr-ctl $(PREFIX)/sbin/baycom-pr-ctl
	install -m 755 ../scripts/baycom-pr-selftest.sh $(PREFIX)/sbin/baycom-pr-selftest.sh
	install -m 755 ../scripts/pccom-ctl $(PREFIX)/sbin/pccom-ctl

clean:
	rm -f $(BINARIES) $(LEGACY_ALIASES)

test-config:
	python3 baycom_validate_config.py ../config/baycom-pr.ini
