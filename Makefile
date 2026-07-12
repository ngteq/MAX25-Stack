# MainAX25-Stack (MAX25-Stack) — unified Packet Radio / AX.25 build

.PHONY: help all clean test discover build plugins release-check

ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

help:
	@echo "MainAX25-Stack (MAX25-Stack) — Packet Radio / AX.25 (HyBBX-compatible)"
	@echo ""
	@echo "  make all        Build merged stacks (tncs + baycom-pr + crdop)"
	@echo "  make test       Offline tests"
	@echo "  make discover   List plugins"
	@echo "  make plugins    Validate plugin scaffolding"
	@echo "  make release-check  v1.0.0 offline release gates"
	@echo "  make clean      Clean built binaries"
	@echo ""
	@echo "  ./scripts/max25-ctl help"

all:
	$(MAKE) -C stacks/tncs all
	$(MAKE) -C stacks/baycom-pr all
	$(MAKE) -C stacks/crdop all

test:
	$(MAKE) -C stacks/baycom-pr test
	-$(MAKE) -C stacks/tncs test

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

release-check:
	bash scripts/release-check.sh

build: all discover
