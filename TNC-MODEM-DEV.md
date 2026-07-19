# TNC / Modem bring-up · MAX25-Stack

English bring-up for **TNCs** (HDLC + KISS on host serial) and **BayCom/based** modems (bits↔AFSK + PTT; host owns HDLC). Applies to MAX25-Stack and to any stack that attaches the same hardware classes.

Public mark for SER12 / PC-COM class: **BayCom/based**. Never **Konverter** / **converter**. Live secrets stay in `./local/` (gitignored); site examples use `/etc/max25/…`.

---

## 1. Roles — TNC vs modem

| Class | What it is | Host owns | Typical face |
|-------|------------|-----------|--------------|
| **TNC** (TNC2C, PK-TNC2, TNC2multi, …) | Firmware does HDLC; host talks **command mode** then **KISS** on UART | Serial lifecycle, recovery, KISS entry | `tnc2c`, `pktnc2`, … |
| **BayCom/based** modem | Board is **modem-only** (TCM3105-class AFSK + PTT) | HDLC, SER12 bit clock, KISS PTY, PTT | **`max25e0`** (bcpr) |
| Soft-modem (CRDOP) | Soundcard AFSK | Audio + soft HDLC | `soft-crdop` |

```text
TNC path:     Radio AF  ↔  TNC (HDLC+modem)  ↔  UART KISS  ↔  host stack
Modem path:   Radio AF  ↔  BayCom/based chip  ↔  SER12 UART  ↔  host HDLC (bcpr)  ↔  KISS
```

Do **not** treat a BayCom/based board as a TNC. Do **not** open the same `/dev/tty*` from two processes.

---

## 2. KISS bring-up (any stack)

### 2.1 Serial ownership

| Rule | Why |
|------|-----|
| **One opener** per UART | Dual openers → garbled RX, failed recovery, flaky KISS |
| Hold **DTR+RTS high** while the port is owned | Landolt TNC2C terminal detect needs DTR high at power-on; drop on close → echo-only |
| Match **baud / line** to hardware | Wrong baud → garbage or echo only |

| Device class (typical) | Baud | Line | Notes |
|------------------------|------|------|-------|
| Landolt TNC2C | **19200** | 8N1 | Not 4800/9600/7E1 |
| PK-TNC2 / many TF boards | **9600** | 8N1 | Profile-dependent |
| BayCom/based SER12 | UART clocked by host SER12 | — | Product path: **bcpr**, not kernel `baycom_ser_fdx` |

### 2.2 Command sequence (TheFirmware / TNC-2 class)

| Step | Action |
|------|--------|
| 1 | Free the port (`pkill` stray terminals; one stack owns the fd) |
| 2 | Open UART with DTR+RTS high; settle ~2 s |
| 3 | Reach **terminal / host command mode** (banner / `cmd:`) — see recovery below |
| 4 | Set callsign / radio params as required by firmware |
| 5 | Enter KISS: TheFirmware **ESC `@K`** (`0x1B 40 4B`); legacy TAPR `kiss on` only as fallback |
| 6 | Keep the **same process** owning the port for KISS DATA |

KISS exit (if needed): `kiss off`, or frame `0xC0 0xFF 0xC0`, or firmware `RESTART`.

### 2.3 Boot-wait (cold start)

After mains loss or cold power without DTR, some boards (notably Landolt TNC2C) need **boot-wait with DTR high during power-on**:

```bash
cd stacks/tncs
./tnc2c-boot-wait.sh /dev/ttyS4     # keep script open; power OFF 10s → ON
# then start the stack immediately so DTR stays high
```

Quiet AF / closed squelch (CD off) during boot improves banner reliability.

---

## 3. Power-cycle history — and the correct path

| Era | Practice | Status |
|-----|----------|--------|
| Former | Power-cycle + boot-wait for almost every KISS/host recovery | Still valid as **rescue** |
| Root cause (hardware) | Landolt: DTR must be high **at** power-on; late open → echo/transparent | Not fully soft-fixable |
| Root cause (host) | Recovery answers lost if an RX thread races the drain; no escalation to boot-wait | Fixed / mitigated in product recovery path |
| Correct default | **Software recovery ladder first**; power-cycle only if echo-only after ladder | Prefer `tnc_serial_recovery` / `tnc2c-host-reset` |

### Software-first ladder (summary)

1. DTR+RTS high, passive listen  
2. KISS return `0xC0 0xFF 0xC0`  
3. JHOST 0 flush (`^Q^X` + nulls + `JHOST 0`)  
4. ESC `V` / ESC `QRES` (software cold boot; DTR stays high)  
5. Legacy `kiss off` + `INFO` (last resort)  
6. KISS entry ESC `@K`

Success markers: `TheFirmware`, `NORD`, `Version 2.7`, `Checksum`, `cmd:`.

| If… | Then… |
|-----|--------|
| Ladder fails → echo only | `./tnc2c-boot-wait.sh` + power OFF→ON with DTR held |
| Standalone reset OK, stack FAIL | Check dual openers / RX race / start order |
| After boot-wait | Start stack **immediately** (avoid DTR drop gap) |

Detail: `stacks/tncs/docs/TNC-RECOVERY.md`.

---

## 4. Common failure modes

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Garbage / no banner | Wrong baud or 7E1 | Match profile (e.g. TNC2C **19200 8N1**) |
| Echo only (`INFO`→`INFO`) | No terminal mode; DTR missed at power-on | Recovery ladder → else boot-wait + power-cycle |
| Binary noise, no commands | Stuck in KISS | KISS return frame or `kiss off` |
| Intermittent recovery | Second process on same tty | One owner; kill minicom/`fuser` |
| Silent TX after good session (modem) | **Stale KISS PTY** (bcprd recycled outside max25d) | Restart **max25d only** (`auto_start` owns bcprd) |
| TX blocked with Soft-DCD busy | `fulldup=no` + Soft-DCD holds channel | Bench: `fulldup=yes`; production CSMA prove-out later |
| Closed squelch ≠ TX fail | No RX noise does not prove PTT failure | Separate MCR/keying from mic wiring |

---

## 5. MAX25-Stack

### 5.1 Paths

| Path | Role |
|------|------|
| **TNC** | `stacks/tncs/` · devices `tnc2c` / `pktnc2` / … · KISS-serial backend |
| **BayCom/based** | `stacks/bcpr/` · `[features] bcpr=yes` · device **`max25e0`** |
| **CRDOP** | `stacks/crdop/` · soft-modem (out of scope here beyond role table) |

### 5.2 Device face `max25e0`

| Surface | Name |
|---------|------|
| Product device id | **`max25e0`** |
| INI mapping | `max25e0 = bcpr:bc0` (right side = **backend:port tag**, not product id) |
| Multi-dev | Always forks **`max25e0:bcN`** |
| Forbidden ids | `bcpr`, `bcpr-bc0`, `bcpr-bc1`, any `bcpr-*` as product face |
| `max25e*` family | **MAX25-Stack only** |

### 5.3 Start

```bash
# Feature (site or ./local — never commit live secrets)
# [features]
# bcpr = yes
#
# [devices]
# max25e0 = bcpr:bc0

./scripts/run-max25d.sh                 # escalates root only when ttyS/USB/SER12 needs it
./scripts/run-max25-terminal.sh -U /run/max25/modem.sock
```

| Rule | Value |
|------|-------|
| Preferred ownership | **max25d** starts/stops bcprd (`auto_start`) |
| Do not | Recycle `bcprd` under a live max25d (stale PTY) |
| Root | **Only when necessary** (SER12 / ioperm / `/dev/port` / ttyS bind) — TCP/unix-only may stay unprivileged |
| Drop | After privileged init, drop to `[daemon] user=` / `group=` when set |

Site INI examples: `/etc/max25/max25d.ini`, `/etc/max25/bcpr.ini`. Tree secrets: `./local/`.

### 5.4 RX before TX (live RF)

Prove **RX** before live **`--tx`** / on-air SEND:

| Class | RX proof |
|-------|----------|
| BayCom/based | Soft-DCD / noise activity or decoded KISS RX |
| TNC | CONNECT + STATUS (RX ready) before SEND |
| Offline L0 | Encode/decode without PTT — allowed |

`--force-tx` is debug-only. See [TX-RX-TEST.md](docs/TX-RX-TEST.md).

### 5.5 Minimal matrices (no duplication)

| Goal | Doc |
|------|-----|
| Day-to-day ops | [MAX25-OPERATOR-RUNBOOK.md](docs/MAX25-OPERATOR-RUNBOOK.md) |
| BayCom/based / bcpr | [BAYCOM.md](docs/BAYCOM.md) · [BAYCOM-FREEZES.md](docs/BAYCOM-FREEZES.md) |
| Linear operator guide | [MASTER-GUIDE.md](docs/MASTER-GUIDE.md) |
| TNC software recovery | [stacks/tncs/docs/TNC-RECOVERY.md](stacks/tncs/docs/TNC-RECOVERY.md) |
| Device model | [PLUGINS-DEVICE-MODEL.md](docs/PLUGINS-DEVICE-MODEL.md) |
| Doc index | [docs/README.md](docs/README.md) |

---

## 6. Quick decision tree

```text
Need KISS on a UART TNC?
├─ Port free + correct baud?
│  └─ no → fix ownership / baud
├─ Terminal / cmd: present?
│  ├─ no → software recovery ladder
│  │     └─ still echo only → boot-wait + power-cycle (DTR high)
│  └─ yes → ESC @K (or profile kiss entry) → keep one owner
└─ BayCom/based?
   └─ [features] bcpr=yes · max25e0 · run-max25d.sh · RX proof → then TX
```
