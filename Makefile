# MainAX25-Stack (MAX25-Stack) — unified Packet Radio / AX.25 build

.PHONY: help all clean test discover build plugins

ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

help:
	@echo "MainAX25-Stack (MAX25-Stack) — Packet Radio / AX.25 (HyBBX-compatible)"
	@echo ""
	@echo "  make all        Build merged stacks (tncs + baycom-pr)"
	@echo "  make test       Offline tests"
	@echo "  make discover   List plugins"
	@echo "  make plugins    Validate plugin scaffolding"
	@echo "  make clean      Clean built binaries"
	@echo ""
	@echo "  ./scripts/max25-ctl help"

all:
	$(MAKE) -C stacks/tncs all
	$(MAKE) -C stacks/baycom-pr all

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

build: all discover
