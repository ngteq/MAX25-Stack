# Scripts

| Script | Purpose |
|--------|---------|
| `baycom-pr-ctl` | Main control — install to `/usr/local/sbin/` |
| `baycom-pr-selftest.sh` | Hardware self-test checklist |
| `install-root.sh` | Root install + smoke test |
| `test-all.sh` | Offline QA (`make test`) |
| `verify-analysis.sh` | Deep-scan checklist (`make verify`) |
| `check-freeze.sh` | Post-crash diagnostics |
| `rc.baycom-pr` | Optional init wrapper → `/etc/baycom/rc.d/` |

Legacy: `legacy/`, `pccom-ctl` (deprecated symlinks).

Docs: [docs/GUIDE.md](../docs/GUIDE.md)
