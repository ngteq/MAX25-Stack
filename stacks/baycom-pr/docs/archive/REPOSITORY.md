# Repository layout

**v0.5.0** · [github.com/ngteq/BayCom_PR-Stack](https://github.com/ngteq/BayCom_PR-Stack)

```
BayCom_PR-Stack/
├── Makefile              make help | all | install | test | clean
├── README.md
├── AGENTS.md             AI / agent onboarding map
├── CONTRIBUTING.md       contributor workflow
├── VERSION               0.5.0
├── LICENSE               GPL-3.0-or-later
├── COPYRIGHT
├── NOTICE                third-party and trademark notices
├── config/
│   ├── README.md
│   ├── baycom-pr.ini     → /etc/baycom/baycom-pr.ini (single, default)
│   ├── examples/baycom-pr.dual.ini   optional dual-modem profile
│   ├── modems.ini        → /etc/baycom/modems.ini
│   ├── axports/          example axports snippets
│   ├── examples/terminals/  socat KISS debug examples
│   └── legacy/           deprecated pccom.env*
├── docs/
│   ├── INDEX.md          documentation map
│   ├── DEVELOPMENT.md    local dev loop
│   ├── CONFIGURATION.md  canonical paths and env vars
│   ├── QUICKSTART.md … RELEASE-NOTES-0.5.0.txt
│   └── TERMINALS.md      max25-terminal, socat, listen/call
├── scripts/
│   ├── README.md
│   ├── baycom-pr-ctl     main control
│   ├── baycom-pr-selftest.sh
│   ├── install-root.sh
│   ├── test-all.sh       make test
│   ├── check-freeze.sh
│   ├── rc.baycom-pr        optional rc-style init wrapper
│   ├── pccom-ctl         legacy wrapper
│   └── legacy/
└── tools/
    ├── Makefile
    ├── baycom_*.c        C tools
    └── baycom_*.py       INI loader, validator
```

Build artifacts (`tools/baycom_*` binaries) are gitignored.

**Not in repository:** optional local `research/` archives (third-party, see [NOTICE](../NOTICE)).

## Runtime (after install)

| Path | Role |
|------|------|
| `/usr/local/sbin/baycom_*` | Tools and control |
| `/etc/baycom/baycom-pr.ini` | Site config |
| `/etc/baycom/modems.ini` | Catalog |
| `/etc/baycom/axports/` | AX.25 snippet examples |
| `/var/run/baycom-pr/` | State, KISS symlinks, PID files |

## Build and test

```bash
make help           # target summary
make all
make test           # offline, no root
make install        # needs root for /etc/baycom/
```

Contributor guide: [CONTRIBUTING.md](../CONTRIBUTING.md) · dev loop: [DEVELOPMENT.md](DEVELOPMENT.md).

## Scope

**In scope:** Linux BayCom modem stack (kernel-ser12 + kiss-serial), tools, INI catalog, KISS/AX.25 attachment points.

**Out of scope:** BBS daemons, terminal UIs, plugin loaders — [MANUAL — External clients](MANUAL.md#external-clients).
