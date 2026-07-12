# BayCom PR-Stack — top-level build
#   make help | all | install | clean | test | test-config

.PHONY: help all clean install test test-config verify

help:
	@echo "BayCom PR-Stack — common targets:"
	@echo ""
	@echo "  make all          Build C tools (tools/)"
	@echo "  make install      Install to /usr/local/sbin and /etc/baycom/"
	@echo "  make test         Offline repo QA (scripts/test-all.sh, no root)"
	@echo "  make verify       Deep-analysis checklist + make test"
	@echo "  make test-config  Validate config/baycom-pr.ini + catalog"
	@echo "  make clean        Remove built binaries"
	@echo ""
	@echo "Hardware (root):"
	@echo "  sudo bash scripts/install-root.sh"
	@echo "  sudo baycom-pr-ctl preflight && sudo baycom-pr-ctl start"
	@echo "  sudo baycom-pr-ctl selftest"
	@echo ""
	@echo "Docs: docs/INDEX.md · docs/GETTING-STARTED.md · docs/CONNECTS.md"

all:
	$(MAKE) -C tools all

clean:
	$(MAKE) -C tools clean

install:
	$(MAKE) -C tools install

test-config:
	$(MAKE) -C tools test-config

test:
	bash scripts/test-all.sh

verify:
	bash scripts/verify-analysis.sh
