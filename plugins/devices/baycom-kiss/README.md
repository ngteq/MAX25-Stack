# Device: BayCom KISS Serial

USB or async serial BayCom firmware TNC. Uses `kiss-serial` backend — no kernel `baycom_ser_fdx`, no **bcpr** SER12 path.

HyBBX `[transport.baycom1]` with `backend=kiss`, `device=/dev/ttyUSB0`.

See [docs/BAYCOM.md](../../../docs/BAYCOM.md) (KISS vs BayCom/based) and [docs/PLUGINS-DEVICE-MODEL.md](../../../docs/PLUGINS-DEVICE-MODEL.md).
