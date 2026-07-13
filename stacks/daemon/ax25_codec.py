"""
AX.25 UI frame codec for max25d — address fields, CRC-CCITT FCS, UI parse/build.

Derived from libax25 axutils.c (address encoding) and ax25ipd/crc.c (RFC 1171 FCS).
KISS DATA carries the AX.25 body without FCS; over-the-air and some paths include FCS.
"""
from __future__ import annotations

import re
from typing import Optional

# HDLC CRC-CCITT (polynomial 0x1021), RFC 1171 / ax25ipd table
_FCS_TABLE: tuple[int, ...] = (
    0x0000, 0x1189, 0x2312, 0x329B, 0x4624, 0x57AD, 0x6536, 0x74BF,
    0x8C48, 0x9DC1, 0xAF5A, 0xBED3, 0xCA6C, 0xDBE5, 0xE97E, 0xF8F7,
    0x1081, 0x0108, 0x3393, 0x221A, 0x56A5, 0x472C, 0x75B7, 0x643E,
    0x9CC9, 0x8D40, 0xBFDB, 0xAE52, 0xDAED, 0xCB64, 0xF9FF, 0xE876,
    0x2102, 0x308B, 0x0210, 0x1399, 0x6726, 0x76AF, 0x4434, 0x55BD,
    0xAD4A, 0xBCC3, 0x8E58, 0x9FD1, 0xEB6E, 0xFAE7, 0xC87C, 0xD9F5,
    0x3183, 0x200A, 0x1291, 0x0318, 0x77A7, 0x662E, 0x54B5, 0x453C,
    0xBDCB, 0xAC42, 0x9ED9, 0x8F50, 0xFBEF, 0xEA66, 0xD8FD, 0xC974,
    0x4204, 0x538D, 0x6116, 0x709F, 0x0420, 0x15A9, 0x2732, 0x36BB,
    0xCE4C, 0xDFC5, 0xED5E, 0xFCD7, 0x8868, 0x99E1, 0xAB7A, 0xBAF3,
    0x5285, 0x430C, 0x7197, 0x601E, 0x14A1, 0x0528, 0x37B3, 0x263A,
    0xDECD, 0xCF44, 0xFDDF, 0xEC56, 0x98E9, 0x8960, 0xBBFB, 0xAA72,
    0x6306, 0x728F, 0x4014, 0x519D, 0x2522, 0x34AB, 0x0630, 0x17B9,
    0xEF4E, 0xFEC7, 0xCC5C, 0xDDD5, 0xA96A, 0xB8E3, 0x8A78, 0x9BF1,
    0x7387, 0x620E, 0x5095, 0x411C, 0x35A3, 0x242A, 0x16B1, 0x0738,
    0xFFCF, 0xEE46, 0xDCDD, 0xCD54, 0xB9EB, 0xA862, 0x9AF9, 0x8B70,
    0x8408, 0x9581, 0xA71A, 0xB693, 0xC22C, 0xD3A5, 0xE13E, 0xF0B7,
    0x0840, 0x19C9, 0x2B52, 0x3ADB, 0x4E64, 0x5FED, 0x6D76, 0x7CFF,
    0x9489, 0x8500, 0xB79B, 0xA612, 0xD2AD, 0xC324, 0xF1BF, 0xE036,
    0x18C1, 0x0948, 0x3BD3, 0x2A5A, 0x5EE5, 0x4F6C, 0x7DF7, 0x6C7E,
    0xA50A, 0xB483, 0x8618, 0x9791, 0xE32E, 0xF2A7, 0xC03C, 0xD1B5,
    0x2942, 0x38CB, 0x0A50, 0x1BD9, 0x6F66, 0x7EEF, 0x4C74, 0x5DFD,
    0xB58B, 0xA402, 0x9699, 0x8710, 0xF3AF, 0xE226, 0xD0BD, 0xC134,
    0x39C3, 0x284A, 0x1AD1, 0x0B58, 0x7FE7, 0x6E6E, 0x5CF5, 0x4D7C,
    0xC60C, 0xD785, 0xE51E, 0xF497, 0x8028, 0x91A1, 0xA33A, 0xB2B3,
    0x4A44, 0x5BCD, 0x6956, 0x78DF, 0x0C60, 0x1DE9, 0x2F72, 0x3EFB,
    0xD68D, 0xC704, 0xF59F, 0xE416, 0x90A9, 0x8120, 0xB3BB, 0xA232,
    0x5AC5, 0x4B4C, 0x79D7, 0x685E, 0x1CE1, 0x0D68, 0x3FF3, 0x2E7A,
    0xE70E, 0xF687, 0xC41C, 0xD595, 0xA12A, 0xB0A3, 0x8238, 0x93B1,
    0x6B46, 0x7ACF, 0x4854, 0x59DD, 0x2D62, 0x3CEB, 0x0E70, 0x1FF9,
    0xF78F, 0xE606, 0xD49D, 0xC514, 0xB1AB, 0xA022, 0x92B9, 0x8330,
    0x7BC7, 0x6A4E, 0x58D5, 0x495C, 0x3DE3, 0x2C6A, 0x1EF1, 0x0F78,
)

_FCS_GOOD = 0xF0B8  # ax25ipd PPPGOODFCS — residual after valid frame + FCS

AX25_UI_CONTROL = 0x03
AX25_UI_PID = 0xF0
MIN_UI_FRAME = 16  # dest(7) + src(7) + ctrl + pid

_CALLSIGN_RE = re.compile(r"^([A-Z0-9]{1,6})(?:-([0-9]{1,2}))?$")


def parse_callsign(text: str) -> tuple[str, int]:
    """Parse operator callsign text; invalid SSID clamps to 0 (legacy helper)."""
    text = text.strip().upper()
    if "-" in text:
        call, ssid_s = text.split("-", 1)
        try:
            ssid = int(ssid_s)
        except ValueError:
            ssid = 0
        if ssid < 0 or ssid > 15:
            ssid = 0
        return call[:6], ssid
    return text[:6], 0


def validate_callsign(text: str) -> tuple[str, int]:
    """Strict callsign parse (libax25 ax25_aton_entry rules)."""
    text = text.strip().upper()
    match = _CALLSIGN_RE.match(text)
    if not match:
        raise ValueError(f"invalid AX.25 callsign: {text!r}")
    call = match.group(1)
    ssid = int(match.group(2)) if match.group(2) is not None else 0
    if ssid < 0 or ssid > 15:
        raise ValueError(f"invalid AX.25 SSID in {text!r}")
    return call, ssid


def format_callsign(call: str, ssid: int) -> str:
    """Textual callsign; omit -0 suffix (libax25 ax25_ntoa convention)."""
    call = call.strip().upper()
    if ssid <= 0:
        return call
    if ssid >= 10:
        return f"{call}-{ssid}"
    return f"{call}-{ssid}"


def ax25_crc(data: bytes) -> int:
    """Compute AX.25 FCS over body (addresses + control + PID + info)."""
    fcs = 0xFFFF
    for b in data:
        fcs = (fcs >> 8) ^ _FCS_TABLE[(fcs ^ b) & 0xFF]
    return fcs ^ 0xFFFF


def ax25_crc_valid(frame: bytes) -> bool:
    """True when frame includes a valid little-endian FCS trailer."""
    fcs = 0xFFFF
    for b in frame:
        fcs = (fcs >> 8) ^ _FCS_TABLE[(fcs ^ b) & 0xFF]
    return fcs == _FCS_GOOD


def ax25_encode_address(call: str, ssid: int, last: bool) -> bytes:
    """Seven-byte AX.25 address field (libax25 ax25_aton_entry layout)."""
    padded = call.upper().ljust(6)[:6]
    raw = bytes((ord(c) << 1) for c in padded)
    ssid_b = ((ssid & 0x0F) << 1) | (0x01 if last else 0x00)
    return raw + bytes([ssid_b])


def ax25_decode_address(raw: bytes) -> tuple[str, int, bool]:
    call = "".join(chr((b >> 1) & 0x7F) for b in raw[:6]).strip()
    ssid = (raw[6] >> 1) & 0x0F
    last = bool(raw[6] & 0x01)
    return call, ssid, last


def ax25_build_ui(src: str, dst: str, info: bytes) -> bytes:
    src_call, src_ssid = validate_callsign(src)
    dst_call, dst_ssid = validate_callsign(dst)
    body = (
        ax25_encode_address(dst_call, dst_ssid, last=False)
        + ax25_encode_address(src_call, src_ssid, last=True)
        + bytes([AX25_UI_CONTROL, AX25_UI_PID])
        + info
    )
    crc = ax25_crc(body)
    return body + bytes((crc & 0xFF, crc >> 8))


def ax25_parse_ui(frame: bytes) -> Optional[tuple[str, str, bytes]]:
    """
    Parse a UI frame. Strips FCS only when the trailer validates (ax25ipd ok_crc).
    KISS payloads are usually FCS-free; over-the-air captures may include FCS.
    """
    if len(frame) < MIN_UI_FRAME:
        return None

    body = frame
    if len(frame) >= MIN_UI_FRAME + 2 and ax25_crc_valid(frame):
        body = frame[:-2]

    pos = 0
    addresses: list[tuple[str, int, bool]] = []
    while pos + 7 <= len(body):
        call, ssid, last = ax25_decode_address(body[pos : pos + 7])
        addresses.append((call, ssid, last))
        pos += 7
        if last:
            break
    else:
        return None

    if len(addresses) < 2:
        return None
    if pos + 2 > len(body):
        return None
    if body[pos] != AX25_UI_CONTROL or body[pos + 1] != AX25_UI_PID:
        return None

    payload = body[pos + 2 :]
    dst_call, dst_ssid, _ = addresses[0]
    src_call, src_ssid, _ = addresses[-1]
    return (
        format_callsign(src_call, src_ssid),
        format_callsign(dst_call, dst_ssid),
        payload,
    )
