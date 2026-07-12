# MainAX25-Stack (MAX25-Stack) — unified Packet Radio / AX.25 build

.PHONY: help all clean test discover build plugins release-check daemon terminal amiga-terminal install pi-install

ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PREFIX ?= /usr/local

help:
	@echo "MainAX25-Stack (MAX25-Stack) — Packet Radio / AX.25 (HyBBX-compatible)"
	@echo ""
	@echo "  make all        Build stacks + max25d + max25-terminal"
	@echo "  make test       Offline tests"
	@echo "  make daemon     Build max25d (Linux)"
	@echo "  make terminal   Build max25-terminal / max25-client"
	@echo "  make amiga-terminal  Cross-build AmigaOS max25-terminal (/opt/amiga)"
	@echo "  make discover   List plugins"
	@echo "  make plugins    Validate plugin scaffolding"
	@echo "  make install      Install max25d, terminal, max25-ctl (PREFIX=/usr/local)"
	@echo "  make pi-install   Same as: scripts/install-max25.sh --deps"
	@echo "  make clean      Clean built binaries"
	@echo ""
	@echo "  ./scripts/max25-ctl help"

all:
	$(MAKE) -C stacks/tncs all
	$(MAKE) -C stacks/baycom-pr all
	$(MAKE) -C stacks/crdop all
	$(MAKE) -C stacks/daemon all
	$(MAKE) -C stacks/terminal all

daemon:
	$(MAKE) -C stacks/daemon all

terminal:
	$(MAKE) -C stacks/terminal all

amiga-terminal:
	bash scripts/build-amiga-terminal.sh

test:
	$(MAKE) -C stacks/baycom-pr test
	-$(MAKE) -C stacks/tncs test
	$(MAKE) -C stacks/daemon smoke
	$(MAKE) -C stacks/terminal test

discover:
	bash scripts/discover-plugins.sh

plugins:
	@test -f plugins/manifest.yaml
	@find plugins -name plugin.yaml | wc -l | xargs -I{} echo "plugin.yaml files: {}"
	bash scripts/discover-plugins.sh

clean:
	$(MAKE) -C stacks/tncs clean
	$(MAKE) -C stacks/baycom-pr clean
	$(MAKE) -C stacks/crdop clean
	$(MAKE) -C stacks/daemon clean
	$(MAKE) -C stacks/terminal clean

release-check:
	bash scripts/release-check.sh

install:
	$(MAKE) -C stacks/daemon install PREFIX=$(PREFIX)
	$(MAKE) -C stacks/terminal install PREFIX=$(PREFIX)
	install -d "$(DESTDIR)$(PREFIX)/bin" "$(DESTDIR)$(PREFIX)/share/max25"
	install -m 755 scripts/max25-ctl "$(DESTDIR)$(PREFIX)/bin/max25-ctl"
	install -m 644 share/max25/max25d.ini.example share/max25/max25d.ini.pi.example "$(DESTDIR)$(PREFIX)/share/max25/"
	@if [ -f share/max25/max25d.service.example ]; then \
		install -m 644 share/max25/max25d.service.example "$(DESTDIR)$(PREFIX)/share/max25/"; \
	fi

pi-install:
	bash scripts/install-max25.sh --deps

build: all discover
