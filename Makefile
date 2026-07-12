# MainAX25-Stack (MAX25-Stack) — unified Packet Radio / AX.25 build

BUILD_DIR ?= build
JOBS ?= $(shell nproc 2>/dev/null || echo 2)
CMAKE ?= cmake
PREFIX ?= /usr/local
BUILD_TYPE ?= Release

.PHONY: help all clean test discover build plugins release-check daemon terminal amiga-terminal install edge-install configure

help:
	@echo "MainAX25-Stack (MAX25-Stack) — Packet Radio / AX.25 (HyBBX-compatible)"
	@echo ""
	@echo "  make all            Configure + build (CMake → $(BUILD_DIR)/bin/)"
	@echo "  make configure      cmake -B $(BUILD_DIR) only"
	@echo "  make test           Offline tests (CMake targets + stack checks)"
	@echo "  make install        cmake --install $(BUILD_DIR)"
	@echo "  make daemon         max25d (Python, no compile)"
	@echo "  make terminal       Build max25-terminal only"
	@echo "  make amiga-terminal Cross-build AmigaOS max25-terminal (/opt/amiga)"
	@echo "  make discover       List plugins"
	@echo "  make plugins        Validate plugin scaffolding"
	@echo "  make edge-install   scripts/install-max25.sh --deps"
	@echo "  make clean          Remove $(BUILD_DIR)/ and legacy artifacts"
	@echo "  make release-check  Offline release gates"
	@echo ""
	@echo "  ./scripts/max25-ctl help"
	@echo ""
	@echo "Direct CMake:"
	@echo "  cmake -B $(BUILD_DIR) -DCMAKE_BUILD_TYPE=$(BUILD_TYPE)"
	@echo "  cmake --build $(BUILD_DIR) -j$(JOBS)"
	@echo "  cmake --install $(BUILD_DIR) --prefix $(PREFIX)"

configure:
	$(CMAKE) -B $(BUILD_DIR) -DCMAKE_BUILD_TYPE=$(BUILD_TYPE)

all: configure
	$(CMAKE) --build $(BUILD_DIR) -j$(JOBS)

daemon:
	@test -x stacks/daemon/max25d || chmod +x stacks/daemon/max25d
	@echo "max25d ready: stacks/daemon/max25d"

terminal: configure
	$(CMAKE) --build $(BUILD_DIR) -j$(JOBS) --target max25-terminal

amiga-terminal:
	bash scripts/build-amiga-terminal.sh

test: all
	$(CMAKE) --build $(BUILD_DIR) --target max25_test
	$(MAKE) -C stacks/baycom-pr test

discover:
	bash scripts/discover-plugins.sh

plugins:
	@test -f plugins/manifest.yaml
	@find plugins -name plugin.yaml | wc -l | xargs -I{} echo "plugin.yaml files: {}"
	bash scripts/discover-plugins.sh

clean:
	rm -rf $(BUILD_DIR)
	-$(MAKE) -C stacks/tncs clean
	-$(MAKE) -C stacks/baycom-pr clean
	-$(MAKE) -C stacks/crdop clean
	-$(MAKE) -C stacks/daemon clean
	-$(MAKE) -C stacks/terminal clean

release-check:
	bash scripts/release-check.sh

install: all
	$(CMAKE) --install $(BUILD_DIR) --prefix $(PREFIX)

edge-install:
	bash scripts/install-max25.sh --deps

pi-install: edge-install

build: all discover
