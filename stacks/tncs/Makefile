CC ?= gcc
CFLAGS ?= -std=c99 -Wall -Wextra -O2
LDFLAGS ?=

.PHONY: all clean test find check listen health autotest host-reset boot-wait integration

integration: tnc2c-integration-test.sh
	./tnc2c-integration-test.sh

health: tnc2c-health.sh
	./tnc2c-health.sh

autotest: tnc2c-autotest.sh
	./tnc2c-autotest.sh

host-reset: tnc2c-host-reset.sh
	./tnc2c-host-reset.sh

boot-wait: tnc2c-boot-wait.sh
	./tnc2c-boot-wait.sh

listen:
	./tnc2c-listen.sh

all: tnc2c-probe tnc2c-find

find: tnc2c-find

tnc2c-probe: tnc2c-probe.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

tnc2c-find: tnc2c-find.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -f tnc2c-probe tnc2c-find

test: tnc2c-probe
	@./tnc2c-probe; rc=$$?; \
	if [ $$rc -eq 1 ]; then \
		echo "WARN: no serial devices — offline test skipped (exit 0)" >&2; \
		exit 0; \
	fi; \
	exit $$rc

check: tnc2c-probe
	./tnc2c-check.sh
