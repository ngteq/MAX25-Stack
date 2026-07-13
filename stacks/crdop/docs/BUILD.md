# Build

Standalone CRDOP (**CB/AR Digital Open Protocol** — MAX25-SoftModem) — embedded `vendor/ardopcf/`, no submodules.

## Requirements

- CMake ≥ 3.16
- **GCC** or **Clang / LLVM**
- Platform libraries (see table below)
- Optional tests: **cmocka** (Linux, *BSD)

## Platform matrix (tested)

| OS | Toolchain | Audio / libs | Status |
|----|-----------|----------------|--------|
| **Linux** | GCC, Clang | `libasound2-dev`, `pkg-config` | tested |
| **FreeBSD** | GCC, Clang | `alsa-lib`, `pkgconf` | tested |
| **OpenBSD / NetBSD** | GCC, Clang | `alsa-lib` if available | experimental |
| **Windows** | MinGW-w64, MSVC | WinMM (built-in) | **untested** |
| **macOS** | Clang (Xcode) | CoreAudio (built-in) | **untested** |

Other operating systems are not tested.

### Debian / Ubuntu

```bash
sudo apt install build-essential cmake libasound2-dev pkg-config
sudo apt install libcmocka-dev    # optional unit tests
```

### FreeBSD

```bash
pkg install cmake alsa-lib pkgconf cmocka
```

### macOS

```bash
xcode-select --install
# or: brew install cmake
```

### Windows (MinGW-w64 on Linux host)

```bash
sudo apt install mingw-w64
CRDOP_TOOLCHAIN=x86_64-w64-mingw32 ./scripts/build-crdop.sh
# → build/crdopc.exe
```

Native Windows: Visual Studio 2022+ with CMake, or MSYS2 MinGW.

## Build

```bash
./scripts/build-crdop.sh
CC=clang ./scripts/build-crdop.sh
./scripts/test-all.sh              # smoke + cmocka (Unix)
```

Output: `build/crdopc` (Windows: `build/crdopc.exe`)

## Install

```bash
./scripts/install-crdop.sh                    # → /usr/local
CRDOP_PREFIX=$HOME/.local ./scripts/install-crdop.sh
```

Installs:

| Path | Contents |
|------|----------|
| `bin/crdopc` | Modem binary |
| `bin/crdop` | Profile launcher (`scripts/crdopc`) |
| `share/crdop/` | INI examples, `VERSION` |

Run: `crdop` or `CRDOP_INI=~/.config/crdop/crdop.ini crdop`

## Cross-compile (Linux host)

```bash
CRDOP_TOOLCHAIN=aarch64-linux-gnu ./scripts/build-crdop.sh
CRDOP_TOOLCHAIN=arm-linux-gnueabihf ./scripts/build-crdop.sh
CRDOP_TOOLCHAIN=x86_64-w64-mingw32 ./scripts/build-crdop.sh
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `vendor/ardopcf missing` | Full repo checkout |
| No ALSA (Linux/BSD) | Install dev package / `alsa-lib` port |
| macOS build fails | Xcode CLI tools; CMake ≥ 3.16 |
| Tests skipped | Install cmocka dev package |
| Stale build | `rm -rf build && ./scripts/build-crdop.sh` |

Vendor refresh (maintainers): `./scripts/refresh-vendor-ardopcf.sh`
