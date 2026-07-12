# HyBBX verbinden — TNC2C (ttyS4 only)

## Architektur

```
Du ──telnet :2323──► HyBBX BBS ──KISS/AX.25──► /dev/ttyS4 ──► TNC2C ──► CB
```

**minicom auf ttyS4** und **HyBBX** schließen sich aus — nur eines darf den Port.

| Modus | Tool | Wann |
|-------|------|------|
| HyBBX + Packet | `./hybbx-connect.sh` | Produktion |
| TNC Host debug | `minicom tnc2c` | HyBBX **aus**, boot-wait optional |

## HyBBX starten (nur TNC2C)

```bash
pkill minicom
sudo -u hybbx ~/Code/tnc2c/hybbx-start-tnc2c.sh &
```

Oder manuell:

```bash
sudo -u hybbx ~/Code/tnc2c/tnc2c-boot-wait.sh && sudo -u hybbx /usr/local/hybbx/hybbx-start &
```

Log prüfen:

```
[tnc] profile=tnc2c ... host=19200 8N1 rts_dtr=on
[tnc] KISS active (port 0)
[telnet] listening ... :2323
```

## HyBBX-Session (statt minicom auf Seriell)

```bash
~/Code/tnc2c/hybbx-connect.sh
# oder: telnet 127.0.0.1 2323
```

Guest-Login automatisch (`auto_login`). Befehle: `/help`, `/who`, …

## minicom-Configs installieren

```bash
mkdir -p ~/.minicom
cp ~/Code/tnc2c/minirc.tnc2c ~/.minicom/minirc.tnc2c
cp ~/Code/tnc2c/minirc.hybbx  ~/.minicom/minirc.hybbx
chmod +x ~/Code/tnc2c/hybbx-connect.sh ~/Code/tnc2c/hybbx-start-tnc2c.sh
```

- `minicom tnc2c` — direkter TNC-Host (**HyBBX muss aus**)
- Für HyBBX: **`hybbx-connect.sh`**, nicht minicom auf ttyS4

## PK-TNC2 (ttyS5)

Separat — HyBBX-INI hat aktuell nur `packet_radio1` auf ttyS4.
Unit B: `pktnc2-boot-wait.sh`, `minicom pktnc2`, On-Air: `pktnc2-to-hybbx.sh`.
Siehe [PACKET-ON-AIR.md](PACKET-ON-AIR.md).
