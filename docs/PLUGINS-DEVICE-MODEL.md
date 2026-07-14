# Plugin device model — unified operator workflow

**TNC (`tnc2c`) is the reference pattern.** BayCom and CRDOP follow the same mental model: one device id, one config surface, one `max25-ctl start` line, one M25/1 session flow.

Registry: [plugins/README.md](../plugins/README.md) · Discovery: `./scripts/discover-plugins.sh` · Protocol: [include/max25/protocol.md](../include/max25/protocol.md)

> **Host layout:** **1× Main** `max25d` plus **optional 5+ Secondaries** on a single server — [ARCHITECTURE.md](ARCHITECTURE.md#host-layout--main--secondaries). Legacy single-instance INI templates remain until wiring lands.

---

## Operator mental model (all devices)

Every active v1 device uses the same five steps:

| Step | What | TNC example | BayCom example | CRDOP example |
|------|------|-------------|----------------|---------------|
| **1. Pick device** | Plugin id + hardware family | `tnc2c` / `tncs` | `baycom-ser12` / `modems` | `soft-crdop` / `soft-modems` |
| **2. Site config** | Copy example → edit paths/callsign | `share/max25/serial/tnc2c-serial.env.example` → `/etc/max25/` | `share/baycom/baycom-pr.pccom-ttyS0-only.ini.example` → `/etc/baycom/baycom-pr.ini` | `stacks/crdop/share/crdop.ini.example` → site copy |
| **3. Daemon config** | `[devices]` entry in `max25d.ini` | `tnc2c = /dev/ttyS4` + `[serial.tnc2c]` | `baycom-ser12 = baycom:a` + `[device.baycom-ser12]` | `soft-crdop = crdop:default` + `[device.soft-crdop]` |
| **4. Stack start** | Hardware prep (root where needed) | `max25-ctl start --hardware tncs --device tnc2c` | `max25-ctl start --hardware modems --device baycom-ser12` | `max25-ctl start --hardware soft-modems --device soft-crdop` |
| **5. Terminal session** | M25/1 over TCP or Unix socket | `SET DEVICE tnc2c` → `CONNECT` → `SEND …` | `SET DEVICE baycom-ser12` → `CONNECT` → `SEND …` | `SET DEVICE soft-crdop` → `CONNECT` → `SEND …` |

With `[stack] auto_start = yes`, step 4 runs inside `max25d` on boot. The terminal never opens raw serial — it always talks to `max25d`.

```
Site config          max25d.ini              max25-ctl / auto_start
     │                    │                          │
     ▼                    ▼                          ▼
 serial.env          [devices] id            boot-wait / baycom-pr-ctl / crdopc
 baycom-pr.ini       [serial.*] or           ────────────────────────────────► RF
 crdop.ini           [device.*]                      │
                                                     ▼
                                            max25d backend (KISS / PTY / TCP)
                                                     │
                                                     ▼
                              max25-terminal: SET DEVICE · CONNECT · SEND
```

---

## TNC gold standard (`hardware/tncs`)

The TNC path is the template every other device mirrors.

### Config surfaces

| File | Purpose |
|------|---------|
| `share/max25/max25d.ini.example` | Daemon one-device template |
| `share/max25/serial/tnc2c-serial.env.example` | UART path, baud, line settings |
| `share/clients/tnc2c.yaml` | Terminal profile (connection + defaults) |
| `plugins/devices/tnc2c/plugin.yaml` | Registry metadata, HyBBX mapping |

Search order for serial env: `/etc/max25/` → `local/` → `share/max25/serial/` → `stacks/tncs/`.

### max25d.ini (minimal)

```ini
[devices]
default = tnc2c
tnc2c = /dev/ttyS4

[serial.tnc2c]
baud = 19200
line = 8n1
dtr_rts = yes
kiss_entry = kiss_on

[stack]
auto_start = yes
```

### Start and operate

```bash
# Manual stack prep (software recovery first; power-cycle boot-wait is rescue):
./scripts/max25-ctl start --hardware tncs --device tnc2c
# Or without power cycle: stacks/tncs/tnc2c-host-reset.sh --kiss

# Production: max25d with auto_start (recovery in kiss_bridge.attach_session)
sudo max25d -c /etc/max25/max25d.ini
max25-terminal -U /run/max25/modem.sock --ax25-ui
```

Terminal session (M25/1):

```text
SET DEVICE tnc2c
SET CALLERID CB-0
SET CALLID QST
CONNECT
SEND hello
```

Second TNC on the same Linux host is **not planned** — use another machine for `pktnc2`. `SET DEVICE` still selects the single configured id for this M25/1 session. See [PACKET-RADIO.md](PACKET-RADIO.md).

---

## BayCom (`hardware/modems`)

BayCom kernel modems use the **same M25/1 flow** as TNCs. Hardware config uses `baycom-pr.ini` instead of serial env; [`share/clients/baycom-ser12.yaml`](../share/clients/baycom-ser12.yaml) mirrors the TNC client-profile pattern for operators (connection + pointers — not loaded by `max25d`).

### Config surfaces

| File | Purpose |
|------|---------|
| `share/baycom/baycom-pr.pccom-ttyS0-only.ini.example` | **Default** — single PC-COM on `/dev/ttyS0` |
| `share/max25/max25d.ini.example` | `[device.baycom-ser12]` block |
| `share/clients/baycom-ser12.yaml` | Terminal profile (operator reference) |
| `plugins/devices/baycom-ser12/plugin.yaml` | Registry — `baycom_ini_direct: true` |

Full operator guide: [BAYCOM.md](BAYCOM.md).

### max25d.ini (single modem)

```ini
[devices]
default = baycom-ser12
baycom-ser12 = baycom:a

[device.baycom-ser12]
kiss_link = /var/run/baycom-pr/kiss
modem = a
baycom_ini = /etc/baycom/baycom-pr.ini

[stack]
auto_start = yes
```

### Start and operate

```bash
sudo cp share/baycom/baycom-pr.pccom-ttyS0-only.ini.example /etc/baycom/baycom-pr.ini
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini setup
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini preflight

./scripts/max25-ctl start --hardware modems --device baycom-ser12
```

Terminal session — **identical commands to TNC**:

```text
SET DEVICE baycom-ser12
CONNECT
SEND hello
```

PTT is kernel-driven on TX; there is no separate M25/1 PTT command.

### BayCom on Linux (one device per host)

Each Linux host running `max25d` picks **one** BayCom device id (`baycom-ser12` by default). UART assignment and site layout are still being designed — use the shipped single-modem template:

| Layout | Status | How |
|--------|--------|-----|
| **Single (default)** | **Target** for new sites | `baycom-pr.pccom-ttyS0-only.ini.example`; one `[devices]` id |
| **Dual / multi-id** | **Legacy** — not for new Linux hosts | `baycom-pr.dual.ini`, `max25d.dual-baycom.ini.example` — see [BAYCOM.md](BAYCOM.md) § Dual modem (deprecated) |

---

## CRDOP (`hardware/soft-modems`) — MAX25-SoftModem standard

**CRDOP** = stack acronym for **MAX25-SoftModem** (device id `soft-crdop`). CRDOP follows the same five-step model. Native M25/KISS host on TCP :8515/:8516 (acoustically AX.25-compatible).

MAX25 **develops and ships** native MAX25-SoftModem (`stacks/crdop/`). **ARDOP-plugin** (third-party ARDOP host) is a separate optional registry entry — [plugins/external/ardop/README.md](../plugins/external/ardop/README.md).

### Config surfaces

| File | Purpose |
|------|---------|
| `stacks/crdop/share/crdop.ini.example` | **Active v1** — CB / 500MAX |
| `share/clients/soft-crdop.yaml` | Terminal profile |
| `share/max25/max25d.ini.example` | `[device.soft-crdop]` block |
| `plugins/devices/soft-crdop/plugin.yaml` | Registry metadata |

Stack details: [stacks/crdop/README.md](../stacks/crdop/README.md) · HyBBX: [HYBBX.md](HYBBX.md) § CRDOP.

### max25d.ini (minimal)

```ini
[devices]
default = soft-crdop
soft-crdop = crdop:default

[device.soft-crdop]
host = 127.0.0.1
port = 8515
listen = yes

[stack]
auto_start = yes
```

### Start and operate

```bash
./scripts/max25-ctl start --hardware soft-modems --device soft-crdop
# native SoftModem listens on TCP :8515 (control) / :8516 (data)
```

Terminal session — **same M25/1 pattern**:

```text
SET DEVICE soft-crdop
CONNECT
SEND hello
```

Requires ALSA audio device configured in `crdop.ini`. No serial port, no kernel module.

### Deferred (v1.1+)

| Profile | INI template | v1 status |
|---------|--------------|-----------|
| CB | `crdop.ini.example` | **Active** |
| Dual | `crdop-dual.ini.example` | Template only |
| Amateur | `crdop-amateur.ini.example` | Template only |

---

## Config surface comparison

| Concern | TNC (`tnc2c`) | BayCom (`baycom-ser12`) | CRDOP (`soft-crdop`) |
|---------|---------------|-------------------------|----------------------|
| Site hardware config | `*serial.env` | `baycom-pr.ini` | `crdop.ini` |
| Daemon `[devices]` value | `/dev/ttyS4` | `baycom:a` | `crdop:default` |
| Per-device INI section | `[serial.tnc2c]` | `[device.baycom-ser12]` | `[device.soft-crdop]` |
| Client YAML | `share/clients/tnc2c.yaml` | `share/clients/baycom-ser12.yaml` (reference) | `share/clients/soft-crdop.yaml` |
| Stack start command | boot-wait script | `baycom-pr-ctl start` | `crdopc` |
| max25d backend | `kiss-serial` | `baycom-kiss` (KISS PTY) | `crdop-tcp` |
| On-air protocol | AX.25 UI via KISS | AX.25 via kernel | AX.25-compatible AFSK (CRDOP) |
| HyBBX plugin | `packet_radio` | `baycom` | `crdop` |

---

## M25/1 session commands (unified)

All devices share the same terminal protocol after connecting to `max25d`:

| Command | Purpose |
|---------|---------|
| `GET DEVICES` | List enabled device ids |
| `SET DEVICE <id>` | Select TX/RX target for this session |
| `SET CALLERID <id>` / `SET CALLID <id>` | Live callsigns |
| `SET AX25_UI on\|off` | UI framing (meaningful for AX.25 paths) |
| `CONNECT` | Attach session — required before `SEND` |
| `SEND <text>` | Transmit on selected device |
| `DISCONNECT` | Detach session |
| `RX device=<id> …` | Incoming traffic (daemon → client) |

**Legacy template (do not use on new Linux hosts):** `share/max25/max25d.full-station.ini.example` — multi-id heterogeneous station; superseded by one-device-per-host policy.

---

## Friction vs TNC (honest gaps)

These differences are **intentional** (kernel/audio constraints), not bugs. Operators should know them upfront:

| Friction | TNC | BayCom | CRDOP |
|----------|-----|--------|-------|
| Extra site config file | serial env only | `baycom-pr.ini` (+ one-time `setup`) | `crdop.ini` (+ ALSA audio) |
| Root for stack start | no (boot-wait) | **yes** (`baycom-pr-ctl`) | no (audio may need system config) |
| Two-process model | max25d owns serial | baycom-pr-ctl → KISS PTY → max25d | crdop launcher → native M25 TCP → max25d |
| Dual layout confusion | N/A (separate tty per TNC) | dual INI skipped by default (single-modem template) | dual profile deferred v1.1+ |
| Freeze risk | low | **high** if wrong IRQ | low |
| On-air protocol | AX.25/KISS | AX.25/KISS | AX.25-compatible AFSK (CRDOP) |
| CI backend tests | mature | `test_baycom_backend.py` | config-parse only |
| Terminal `SET DEVICE` in UI | F10 menu **7** + `-d` CLI flag | same | same |

**What is aligned:** plugin id, `[devices]` in `max25d.ini`, `max25-ctl start --hardware … --device …`, M25/1 `SET DEVICE` → `CONNECT` → `SEND`, `share/clients/*.yaml` operator profiles.

---

## Discovery and registry

```bash
./scripts/discover-plugins.sh          # hardware + device
./scripts/discover-plugins.sh --json
```

| Layer | Directory | CLI output |
|-------|-----------|------------|
| Operating mode | `betriebsform/` | manifest only |
| Hardware | `hardware/` | yes |
| Device | `devices/` | yes |

Client profile registry: [share/clients/index.yaml](../share/clients/index.yaml).

---

## See also

| Document | Content |
|----------|---------|
| [BAYCOM.md](BAYCOM.md) | BayCom operator guide, dual opt-in |
| [PACKET-RADIO.md](PACKET-RADIO.md) | AX.25 / KISS / one device per host |
| [LINUX-HOST-SETUP.md](LINUX-HOST-SETUP.md) | Host setup walkthrough |
| [MAX25-TERMINAL.md](MAX25-TERMINAL.md) | F10 menu, operator UI |
| [V1.0.0-SCOPE.md](V1.0.0-SCOPE.md) | v1 active vs deferred devices |
