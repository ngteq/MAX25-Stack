# Device: BayCom KISS Serial

USB or async serial BayCom firmware TNC. Uses `kiss-serial` backend — no kernel `baycom_ser_fdx`.

HyBBX `[transport.baycom1]` with `backend=kiss`, `device=/dev/ttyUSB0`.

See GETTING-STARTED §C in `stacks/baycom-pr/docs/`.
