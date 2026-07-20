# systemd units (product)

| Unit | Role |
|------|------|
| `max25d.service` | Product max25d (optional example) |

Experimental orch units are **not** shipped in this freigegeben tree.

Install example: copy to `/etc/systemd/system/`, adjust `WorkingDirectory` / `ExecStart` / `Environment` to the site PREFIX and `./local/` INI (never commit secrets).
