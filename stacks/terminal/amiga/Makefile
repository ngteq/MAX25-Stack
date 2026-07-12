# MAX25 Terminal — AmigaOS 3.9+ cross-build (bebbo-gcc / clib2)

AMIGA_SDK ?= /opt/amiga
CC := $(AMIGA_SDK)/bin/m68k-amigaos-gcc
CFLAGS ?= -Wall -Wextra -std=c11 -O2 -mcrt=clib2
LDFLAGS ?= -mcrt=clib2
LIBS := -lnet -lunix

PROTO_DIR := ..
SRCS := max25_terminal_amiga.c $(PROTO_DIR)/max25_proto.c
OBJS := max25_terminal_amiga.o max25_proto.o
TARGET := max25-terminal

.PHONY: all test clean

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(LDFLAGS) -o $@ $(OBJS) $(LIBS)

max25_terminal_amiga.o: max25_terminal_amiga.c $(PROTO_DIR)/max25_proto.h
	$(CC) $(CFLAGS) -DMAX25_AMIGA=1 -I$(PROTO_DIR) -c -o $@ max25_terminal_amiga.c

max25_proto.o: $(PROTO_DIR)/max25_proto.c $(PROTO_DIR)/max25_proto.h
	$(CC) $(CFLAGS) -DMAX25_AMIGA=1 -I$(PROTO_DIR) -c -o $@ $(PROTO_DIR)/max25_proto.c

test: all
	@test -x ./$(TARGET)
	file ./$(TARGET) | grep -qiE 'amiga|68k|m68k' && echo "OK: Amiga m68k binary"

clean:
	rm -f $(OBJS) $(TARGET)
