#!/usr/bin/env python3
"""One-shot AX.25 UI beacon matching HyBBX [broadcast] INI (HyBBX must stay running).

Connects to the internal circuit hub and sends an HBX AX25_UI frame with TX flag
the same way hybbx_broadcast_ax25() does. Requires packet_radio1 linked with
link_password on the Main.
"""
import argparse
import socket
import struct
import sys
import time

MAGIC = b"HBX"
VERSION = 0x01
HEADER_SIZE = 12
PROTO_LINK_AUTH = 0x03
PROTO_LINK_AUTH_ACK = 0x04
PROTO_AX25_UI = 0x02
FLAG_TX = 0x0002
FLAG_PATH = 0x0004
ADDR_LEN = 7


def be16(v):
    return struct.pack(">H", v)


def be32(v):
    return struct.pack(">I", v)


def encode_frame(proto, flags, payload):
    return bytes([ord("H"), ord("B"), ord("X"), VERSION, proto]) + be16(flags) + be32(len(payload)) + payload


def encode_addr(call, ssid=0, last=False):
    call = call.upper().ljust(6)[:6]
    raw = bytes((ord(c) << 1) for c in call)
    ssid_b = ((ssid & 0x0F) << 1) | (0x60 if not last else 0x61)
    return raw + bytes([ssid_b])


def pack_ax25_ui(dest, src, message):
    body = bytes([0])  # digi count
    body += encode_addr(dest, last=False)
    body += encode_addr(src, last=True)
    body += message.encode("ascii", errors="replace")
    return encode_frame(PROTO_AX25_UI, FLAG_TX | FLAG_PATH, body)


def link_auth_payload(password, link_id, role, baud=2400, duplex="half", bandwidth="low", mhz="27.235"):
    lines = [
        f"password={password}",
        f"role={role}",
        f"id={link_id}",
        f"baud={baud}",
        f"duplex={duplex}",
        f"bandwidth={bandwidth}",
        f"frequency_mhz={mhz}",
    ]
    return "\n".join(lines).encode("ascii")


def recv_frames(sock, timeout=5.0):
    sock.settimeout(timeout)
    buf = b""
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
    except socket.timeout:
        pass
    return buf


def main():
    ap = argparse.ArgumentParser(description="HyBBX one-shot AX.25 RF beacon via circuit hub")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=7323)
    ap.add_argument("--password", default="changeme")
    ap.add_argument("--link-id", default="beacon-once")
    ap.add_argument("--mycall", default="UN1TME")
    ap.add_argument("--dest", default="*")
    ap.add_argument("--message", default="Broadcast: UN1TME online")
    args = ap.parse_args()

    sock = socket.create_connection((args.host, args.port), timeout=5)
    auth = link_auth_payload(args.password, args.link_id, "gateway")
    sock.sendall(encode_frame(PROTO_LINK_AUTH, 0, auth))
    ack = recv_frames(sock, 3.0)
    if b"ok=yes" not in ack:
        print("LINK_AUTH failed:", ack[:200], file=sys.stderr)
        sys.exit(1)
    print(f"LINK_AUTH ok — TX {args.mycall} -> {args.dest}: {args.message!r}")
    sock.sendall(pack_ax25_ui(args.dest, args.mycall, args.message))
    time.sleep(2)
    sock.close()
    print("Beacon frame sent to circuit hub.")


if __name__ == "__main__":
    main()
