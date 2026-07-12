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
	@if [ -f tools/Makefile ]; then \
		$(MAKE) -C tools all; \
	else \
		cmake -B ../../build -DCMAKE_BUILD_TYPE=Release && \
		cmake --build ../../build --target baycom_test baycom_sethdlc baycom_kissbridge baycom_kiss_serial; \
	fi

clean:
	@if [ -f tools/Makefile ]; then \
		$(MAKE) -C tools clean; \
	else \
		rm -f ../../build/bin/baycom_test ../../build/bin/baycom_sethdlc \
		      ../../build/bin/baycom_kissbridge ../../build/bin/baycom_kiss_serial; \
	fi

install:
	@if [ -f tools/Makefile ]; then \
		$(MAKE) -C tools install; \
	else \
		echo "Install BayCom tools from MAX25 root: cmake --install build --prefix /usr/local" >&2; \
		exit 1; \
	fi

test-config:
	@if [ -f tools/Makefile ]; then \
		$(MAKE) -C tools test-config; \
	else \
		python3 tools/baycom_validate_config.py config/baycom-pr.ini; \
	fi

test:
	bash scripts/test-all.sh

verify:
	bash scripts/verify-analysis.sh
