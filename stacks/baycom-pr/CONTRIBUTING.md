# Contributing to BayCom PR-Stack

Thank you for helping improve the Linux BayCom/ser12 and KISS modem stack. This guide covers the workflow from fork to pull request.

**AI agents:** see [AGENTS.md](AGENTS.md). **Modem owners:** [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) · [docs/CONNECTS.md](docs/CONNECTS.md).

**v1.0.0 stable contract:** site INI schema (`config/baycom-pr.ini`), catalog IDs, runtime paths under `/etc/baycom/` and `/var/run/baycom-pr/`, and HyBBX attachment points in [docs/PLUGIN.md](docs/PLUGIN.md) are the supported public API. Breaking changes require a major version bump and changelog entry.

## Scope

**In scope:** kernel-ser12 and kiss-serial backends, control tools, INI catalog, KISS/AX.25 attachment points, docs, offline tests.

**Out of scope:** BBS daemons, terminal UIs beyond examples, third-party archives in `research/`, distribution-specific packaging (unless trivial).

## Getting started

```bash
git clone https://github.com/ngteq/BayCom_PR-Stack.git
cd BayCom_PR-Stack
make all
make test && make verify   # offline — no root, no hardware
```

For hardware validation (optional):

```bash
sudo bash scripts/install-root.sh
sudo baycom-pr-ctl selftest
```

Developer guide: [docs/DEVELOPER.md](docs/DEVELOPER.md).

## Making changes

1. **Fork** the repository on GitHub.
2. **Branch** from `main` with a short descriptive name (`fix-ini-loader`, `docs-quickstart`).
3. **Edit** with minimal, focused diffs — match existing naming and style.
4. **Test** before opening a PR:
   ```bash
   make test
   make test-config
   ```
   If you touched start/stop or driver paths, run `sudo baycom-pr-ctl selftest` on hardware when possible.
5. **Document** user-visible behavior in [docs/GUIDE.md](docs/GUIDE.md) or [docs/REFERENCE.md](docs/REFERENCE.md).
6. **Open a PR** against `main` with a clear summary and test plan.

## Commit style

Follow recent history: short imperative subject, optional body for *why*.

```
Add preflight check for duplicate IRQ assignments

Dual-modem profiles now fail validation when two modems share an IRQ,
preventing host freezes during bring-up.
```

- One logical change per commit when practical.
- Do not commit `research/`, build artifacts, or secrets.
- GPL-3.0-or-later applies to contributed code.

## Pull request checklist

- [ ] `make test` and `make verify` pass
- [ ] Config templates validate (`make test-config`)
- [ ] Docs updated if paths, commands, or behavior changed
- [ ] No HyBBX or distro-specific references added
- [ ] Install paths use `/etc/baycom/` for site config
- [ ] Hardware-only claims marked as verified or not in PR description

## Code areas

| Area | Location | Notes |
|------|----------|-------|
| Control script | `scripts/baycom-pr-ctl` | Start/stop, tests, listen/call helpers |
| C tools | `tools/baycom_*.c` | Build via `tools/Makefile` |
| INI tools | `tools/baycom_*.py` | Stdlib only |
| Site config | `config/baycom-pr.ini` | Default single modem |
| Catalog | `config/modems.ini` | Hardware IDs |
| Offline QA | `scripts/test-all.sh` | Extend for new repo checks |

## Reporting issues

Include: Linux kernel version, modem backend (kernel-ser12 vs kiss-serial), relevant INI sections (redact callsigns if needed), output of `baycom-pr-ctl status` and `preflight`, and whether the issue involves RF or offline bring-up only.

## License

By contributing, you agree that your contributions are licensed under [GPL-3.0-or-later](LICENSE).
