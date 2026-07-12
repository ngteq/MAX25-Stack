# Contributing

Standards: [AGENTS.md](AGENTS.md), [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

```bash
git clone https://github.com/ngteq/MAX25-Stack.git && cd MAX25-Stack
make all
make release-check
./scripts/max25-ctl help
```

## Pull requests

- Small, focused diffs; plugin hierarchy unchanged unless discussed
- Stack / plugin change → matching `plugin.yaml`, [docs/HYBBX.md](docs/HYBBX.md) if HyBBX attach affected
- Platform change → [docs/PLATFORMS.md](docs/PLATFORMS.md)
- Verify: `make test && make release-check`

Issues: `.github/ISSUE_TEMPLATE/`.
