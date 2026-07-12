# Contributing

Standards: [AGENTS.md](AGENTS.md), [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

```bash
git clone git@github.com:ngteq/MAX25-Stack.git && cd MAX25-Stack
make all
make release-check
./scripts/max25-ctl help
```

## Git identity

**Only** this identity — no alternatives:

```
user.name  = ngteq
user.email = info@un1t.me
```

Local `.git/config`. Push **only** via SSH `~/.ssh/id_ed25519_ngteq` to `git@github.com:ngteq/MAX25-Stack.git`.

## Pull requests

- Small, focused diffs; plugin hierarchy unchanged unless discussed
- Stack / plugin change → matching `plugin.yaml`, [docs/HYBBX.md](docs/HYBBX.md) if HyBBX attach affected
- Platform change → [docs/PLATFORMS.md](docs/PLATFORMS.md)
- Verify: `make test && make release-check`

Issues: `.github/ISSUE_TEMPLATE/`.
