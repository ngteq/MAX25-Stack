# MAX25 Terminal — cross-platform operator client

CC ?= gcc
CFLAGS ?= -Wall -Wextra -std=c11 -O2
LDFLAGS ?=
LIBS ?=

UNAME_S := $(shell uname -s 2>/dev/null || echo unknown)
PKG_NCURSES := $(shell pkg-config --exists ncurses 2>/dev/null && echo yes)

ifeq ($(PKG_NCURSES),yes)
CFLAGS += -DMAX25_HAVE_NCURSES $(shell pkg-config --cflags ncurses)
LIBS += $(shell pkg-config --libs ncurses)
else
ifeq ($(UNAME_S),Linux)
LIBS += -lncurses -ltinfo
CFLAGS += -DMAX25_HAVE_NCURSES
endif
endif

SRCS := max25_terminal.c max25_proto.c max25_ui.c
OBJS := $(SRCS:.c=.o)
TARGET := max25-terminal
CLIENT_LINK := max25-client

.PHONY: all install test clean

all: $(TARGET) $(CLIENT_LINK)

$(TARGET): $(OBJS)
	$(CC) $(LDFLAGS) -o $@ $(OBJS) $(LIBS)

$(CLIENT_LINK): $(TARGET)
	ln -sf $(TARGET) $(CLIENT_LINK)

%.o: %.c max25_proto.h max25_ui.h
	$(CC) $(CFLAGS) -c -o $@ $<

install: all
	install -d "$(DESTDIR)$(PREFIX)/bin"
	install -m 755 $(TARGET) "$(DESTDIR)$(PREFIX)/bin/"
	ln -sf $(TARGET) "$(DESTDIR)$(PREFIX)/bin/$(CLIENT_LINK)"

test: all
	@test -x ./$(TARGET)
	@test -L ./$(CLIENT_LINK)
	./$(TARGET) --help >/dev/null
	python3 test_connect.py
	@echo "OK: max25-terminal"

clean:
	rm -f $(OBJS) $(TARGET) $(CLIENT_LINK)
