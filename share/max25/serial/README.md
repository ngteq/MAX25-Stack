# Per-device serial env (max25d / boot-wait)

Install copies for site-specific paths:

```bash
sudo mkdir -p /etc/max25
sudo cp share/max25/serial/tnc2c-serial.env.example /etc/max25/tnc2c-serial.env
# edit device path and baud
```

Search order (`paths.py`): `/etc/max25/` → `local/` → `share/max25/serial/` → `stacks/tncs/`.

**Other device families** use different site config (same `[devices]` pattern in `max25d.ini`):

| Hardware | Site config (not serial env) |
|----------|------------------------------|
| BayCom kernel (`baycom-ser12`) | `share/baycom/baycom-pr.pccom-ttyS0-only.ini.example` → `/etc/baycom/baycom-pr.ini` |
| CRDOP (`soft-crdop`) | `stacks/crdop/share/crdop.ini.example` |

Unified workflow: [docs/PLUGINS-DEVICE-MODEL.md](../../docs/PLUGINS-DEVICE-MODEL.md).

Terminal client profiles (connection only): [`../clients/`](../clients/README.md).
