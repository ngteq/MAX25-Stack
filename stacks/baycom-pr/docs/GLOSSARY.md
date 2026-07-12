# Glossary

Short definitions for BayCom PR-Stack documentation. CB and Amateur packet use the **same stack**.

| Term | Meaning |
|------|---------|
| **AX.25** | Amateur packet link protocol on Linux; apps use port names from `axports`. |
| **axports** | File listing radio ports (`cb0`, `radio`, …), callsign, speed. Tools: `listen`, `call`. |
| **Backend** | How the stack talks to hardware: `kernel-ser12`, `kernel-par96`, or `kiss-serial`. |
| **BayCom / ser12** | 1200 bd AFSK modem family; kernel driver `baycom_ser_fdx`, interface `bcsf0`. |
| **bcsf0** | Network interface for one ser12 modem (kernel). Apps use `ax25_port`, not `bcsf0` directly. |
| **Broadcast** | UI frames heard on channel — monitor with `listen -v`; not a separate stack command. |
| **call** | AX.25 command to **connect outgoing** to another station: `call <port> <dest>`. |
| **callsign** | **Your station ID** in INI (`[modem.a] callsign = …`). Must match `axports`. |
| **CB packet** | 27 MHz (typ.) 1200 bd packet; same stack as HAM, different profile example. |
| **Catalog** | `modems.ini` — hardware IDs (`albrecht-pc-com`, `kiss-serial-usb`, …). |
| **Connect** | Bidirectional AX.25 session — outgoing (`call`) or incoming (`listen`). |
| **HAM / Amateur** | Licensed amateur packet; profile example uses `ax25_port = radio`. |
| **HyBBX** | External BBS/application; primary integration target via KISS/AX.25 plugin. |
| **INI** | `/etc/baycom/baycom-pr.ini` — your site config (modem, callsign, ports). |
| **Incoming** | Wait for others to connect: `listen -a -c <port>`. |
| **IRQ** | UART interrupt line; wrong value can freeze the PC — always run `preflight`. |
| **KISS** | Serial framing protocol between PC and TNC; exposed as PTY (`kiss_link`). |
| **kiss_link** | Symlink to PTY, e.g. `/var/run/baycom-pr/kiss` — attach clients here. |
| **listen** | AX.25 command to **monitor or accept incoming** connects on a port. |
| **Outgoing** | You initiate: `call <port> <destination>`. |
| **par96** | 9600 bd LPT modem; driver `baycom_par`, interface `bcp0`. |
| **Port (AX.25)** | Logical name in INI (`ax25_port`) — not the serial device path. |
| **Preflight** | Safety check before `start` (IRQ, UART, duplicates). |
| **PTY** | Pseudo-terminal; KISS bridge creates it for HyBBX or terminal tools. |
| **PTT** | Push-to-talk; driver keys radio via serial lines. |
| **ser12** | 1200 bd Bell 202-style modem on real UART (`kernel-ser12` backend). |
| **Service mode** | Two modems, continuous run — for HyBBX/digipeater, not everyday single-radio use. |
| **Single (default)** | One modem profile — recommended for all modem owners starting out. |
| **Stack** | `baycom-pr-ctl` + tools: bring modem up, KISS, AX.25 attachment. |
| **txdelay** | Transmit delay (×10 ms); tune per radio/modem (CB often 30–35). |
| **USB KISS** | USB TNC; backend `kiss-serial`, no `baycom_ser_fdx`. |

See [GETTING-STARTED.md](GETTING-STARTED.md) · [CONNECTS.md](CONNECTS.md) · [PLUGIN.md](PLUGIN.md).
