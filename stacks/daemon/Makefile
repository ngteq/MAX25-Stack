# max25d — MainAX25-Stack daemon (Linux only)

.PHONY: all install test smoke clean

ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
REPO := $(ROOT)../..

all:
	@test -x "$(ROOT)max25d" || chmod +x "$(ROOT)max25d"
	@echo "max25d ready: $(ROOT)max25d"

install:
	install -d "$(DESTDIR)$(PREFIX)/bin" "$(DESTDIR)$(PREFIX)/share/max25"
	install -m 755 "$(ROOT)max25d" "$(DESTDIR)$(PREFIX)/bin/max25d"
	install -m 644 "$(REPO)/share/max25/max25d.ini.example" "$(DESTDIR)$(PREFIX)/share/max25/"
	install -m 644 "$(REPO)/share/max25/max25d.ini.pi.example" "$(DESTDIR)$(PREFIX)/share/max25/"
	install -m 644 "$(REPO)/share/max25/max25d.service.example" "$(DESTDIR)$(PREFIX)/share/max25/"

test smoke:
	python3 "$(REPO)/stacks/daemon/test_proto.py"
	python3 "$(REPO)/stacks/daemon/test_auth.py"

clean:
