## Summary

<!-- What does this PR do and why? -->

## Type

- [ ] Bug fix
- [ ] Feature
- [ ] Documentation
- [ ] Refactor / internal
- [ ] Build / CI
- [ ] Plugin / stack integration

## Testing

<!-- How did you verify? e.g. ./scripts/test.sh, ./scripts/release-check.sh -->

- [ ] `./scripts/build.sh` succeeds
- [ ] `./scripts/test.sh` succeeds (offline)
- [ ] `./scripts/release-check.sh` succeeds
- [ ] Manual hardware verification (if TNC/modem/RF touched):

## Documentation

- [ ] Updated `plugins/manifest.yaml` and/or `plugins/**/plugin.yaml` (if plugin changed)
- [ ] Updated [docs/HYBBX.md](../docs/HYBBX.md) and/or `share/hybbx/*.ini.example` (if HyBBX attach changed)
- [ ] Updated [docs/PLATFORMS.md](../docs/PLATFORMS.md) (if platform limits changed)
- [ ] Updated [docs/V1.0.0-SCOPE.md](../docs/V1.0.0-SCOPE.md) (if v1 scope changed)

## Architecture

- [ ] Standalone-first: MAX25 owns TNC/modem lifecycle, not HyBBX sessions
- [ ] Plugin hierarchy unchanged or documented ([docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md))
- [ ] HyBBX remains external consumer — no vendoring hyBBX

## Notes

<!-- Optional: breaking changes, follow-ups -->
