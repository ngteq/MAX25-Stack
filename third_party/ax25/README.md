# AX.25 upstream reference (not shipped)

Tarballs here are **analysis reference only** for MAX25-native AX.25 work. They are **not** built, bundled, or installed in v1 releases.

| Archive | Upstream |
|---------|----------|
| `libax25-0.0.12-rc5.tar.gz` | Linux AX.25 library |
| `ax25-tools-0.0.10-rc5.tar.gz` | `kissattach`, `ax25d`, … |
| `ax25-apps-0.0.8-rc5.tar.gz` | `listen`, `call`, … |

## MAX25 v1 behaviour

- `MAX25_BUNDLE_AX25` defaults **OFF** in `cmake/MAX25Ax25.cmake` — no vendored AX.25 build in release.
- `max25d` uses in-tree **`stacks/daemon/ax25_codec.py`** (RFC 1171 FCS, address rules) via `kiss_bridge.py`.
- BayCom **`listen`** / **`call`** terminal clients require **host** `ax25-apps` (distro package) or a future MAX25-native replacement — not bundled by MAX25.

## Optional developer build

To experiment with bundled upstream tools (not for release):

```bash
cmake -B build -DMAX25_BUNDLE_AX25=ON
cmake --build build --target max25_ax25_deps
```

Extracted trees under `third_party/ax25/*-rc5/` and `_build-test/` are gitignored.
