# ARDOP-plugin

Optional **MAX25-Stack plugin** for operators who run **third-party ARDOP host software** alongside MAX25.

**CRDOP (MAX25-SoftModem)** is the MAX25 standard sound-card modem — native M25/KISS on TCP :8515/:8516. ARDOP is **not** part of CRDOP and is **not** enabled via `soft-crdop` or `crdop.ini`.

## When to use

| Path | Use |
|------|-----|
| **CRDOP (default)** | Native MAX25-SoftModem — M25/KISS host via `crdopc` / `audio-dummyd` |
| **ARDOP-plugin** | Operator-provided ARDOP host (Winlink-class wire) — separate from CRDOP |

## Platform

| Host | Notes |
|------|-------|
| **Linux / KLinux** | Typical for third-party ARDOP host software |
| **FreeBSD / *BSD** | CRDOP/OSS only — ARDOP host not integrated in MAX25 |
| **macOS / Windows** | Out of scope for MAX25 daemon path |

## Operator workflow

1. Install and run an ARDOP-capable modem host on the operator machine (third-party software).
2. Point HyBBX or another consumer at the ARDOP host TCP ports per that software's documentation.
3. Do **not** set CRDOP or `soft-crdop` INI flags for ARDOP — CRDOP remains native M25/KISS only.

## Metadata

[plugin.yaml](plugin.yaml) · [../README.md](../README.md)
