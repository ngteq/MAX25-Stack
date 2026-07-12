# On-Air: PK-TNC2 (Client) ↔ TNC2C + HyBBX (Server)

## Architektur

```
Unit B (Stabo)                         Unit A (AX25SRV)
┌─────────────────┐    RF AX.25      ┌──────────────────┐
│ minicom pktnc2  │                    │ hybbx-connect    │
│   └─ ttyS5      │                    │   └─ telnet:2323 │
│ PK-TNC2 1200    │◄──── Funk ────────►│ TNC2C 2400       │
│ Stabo CB        │   gleiche MHz!     │ HyBBX KISS       │
└─────────────────┘                    └──────────────────┘
```

- **HyBBX** = BBS/Server (nur **TNC2C / ttyS4**)
- **minicom pktnc2** = lokales Terminal am **PK-TNC2** (ttyS5) — **nicht** Telnet zu HyBBX
- **On-Air** = AX.25-Frames zwischen den beiden TNCs über CB

## Kritisch: gleicher Kanal

| Unit | Gerät | Funk | Host |
|------|-------|------|------|
| A | TNC2C + HyBBX | **27,235 MHz K24**, 2400 | ttyS4 19200 |
| B | PK-TNC2 + Stabo | **dieselbe MHz**, 1200 | ttyS5 9600 |

K25 (27,245) und K24 (27,235) hören sich **nicht** — für On-Air-Test beide auf **K24** (oder beide K25).

## Unit A — HyBBX (Server)

```bash
pkill minicom
sudo -u hybbx ~/Code/tnc2c/hybbx-start-tnc2c.sh &
# TNC2C: aus → boot-wait → an
```

Lokal: `~/Code/tnc2c/hybbx-connect.sh` (telnet BBS)

Log: `[tnc] KISS active`, `ax25_mycall = UN1TME`

## Unit B — PK-TNC2 (Client, On-Air)

```bash
pkill hybbx    # HyBBX darf ttyS5 nicht nutzen
~/Code/tnc2c/pktnc2-boot-wait.sh
# PK-TNC2: aus → Skript → an
```

**Lokal am PK-TNC2:**

```bash
minicom pktnc2          # Host-Terminal (INFO, CONNECT, …)
# oder direkt ein Frame Richtung HyBBX:
~/Code/tnc2c/pktnc2-to-hybbx.sh "HI HyBBX" UN1TME-2 UN1TME
```

## Ablauf On-Air-Test

1. Unit A: HyBBX läuft, Funk K24, SQ zu
2. Unit B: pktnc2-boot-wait, Stabo **auch K24**, SQ zu
3. Unit B: `./pktnc2-to-hybbx.sh "CONNECT"` (oder minicom + manuelles Senden)
4. Unit A: am HyBBX-Telnet oder Log prüfen ob RX-Frames ankommen (LED3 CD bei Empfang)

## minicom installieren

```bash
mkdir -p ~/.minicom
cp ~/Code/tnc2c/minirc.tnc2c  ~/.minicom/
cp ~/Code/tnc2c/minirc.pktnc2 ~/.minicom/
cp ~/Code/tnc2c/minirc.hybbx  ~/.minicom/
chmod +x ~/Code/tnc2c/pktnc2-to-hybbx.sh
```

| Wo | Tool | Wohin |
|----|------|-------|
| Unit A Operator | `hybbx-connect.sh` | HyBBX BBS (lokal) |
| Unit A TNC debug | `minicom tnc2c` | ttyS4 (HyBBX aus) |
| Unit B Operator | `minicom pktnc2` | PK-TNC2 Host ttyS5 |
| Unit B → HyBBX | `pktnc2-to-hybbx.sh` | **On-Air AX.25** → UN1TME |

## Hinweis

Telnet/minicom **über Funk** gibt es nicht — nur **AX.25 UI** (1200/2400 je nach TNC).
HyBBX empfängt auf TNC2C per KISS-RX; sichtbar je nach HyBBX-Version in Log/Circuit.
