#!/usr/bin/env bash
# MainAX25-Stack — build and install on Linux (daemon, bcpr, terminal, tests).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PREFIX="${PREFIX:-/usr/local}"
INSTALL_DEPS=0
BUILD_ONLY=0
BUILD_DIR="${BUILD_DIR:-build}"

usage() {
  cat <<EOF
MainAX25-Stack install — Linux

Usage: $0 [options]

Options:
  --deps         Install apt build dependencies
  --build-only   Build only, do not install
  --prefix DIR   Install prefix (default: /usr/local)
  --build-dir D  CMake build dir (default: build)
  -h, --help     This help

After install:
  run-max25d
  max25-tx-rx-test --device modem --live
  run-max25-terminal -U /run/max25/modem.sock

See docs/LINUX-HOST-SETUP.md · docs/DEV/TNC-MODEM-DEV.md
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --deps) INSTALL_DEPS=1; shift ;;
    --build-only) BUILD_ONLY=1; shift ;;
    --prefix) PREFIX="$2"; shift 2 ;;
    --build-dir) BUILD_DIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "install-max25.sh: Linux only" >&2
  exit 1
fi

echo "== MAX25 install: $(uname -s) $(uname -m) → ${PREFIX} =="

if [[ "$INSTALL_DEPS" -eq 1 ]]; then
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    pkgs=(build-essential make cmake pkg-config git python3 libncurses-dev libasound2-dev)
    sudo apt-get install -y "${pkgs[@]}" || true
  fi
fi

cd "$ROOT"
echo "-- cmake (BCPR+TERMINAL+DAEMON ON)"
cmake -B "${BUILD_DIR}" \
  -DCMAKE_BUILD_TYPE=Release \
  -DMAX25_BUILD_BCPR=ON \
  -DMAX25_BUILD_TERMINAL=ON \
  -DMAX25_BUILD_DAEMON=ON \
  -DMAX25_BUNDLE_AX25=OFF
cmake --build "${BUILD_DIR}" -j"$(nproc 2>/dev/null || echo 2)"

if [[ "$BUILD_ONLY" -eq 1 ]]; then
  echo "== build done (no install) =="
  exit 0
fi

echo "-- install to ${PREFIX}"
if [[ "$(id -u)" -eq 0 ]]; then
  cmake --install "${BUILD_DIR}" --prefix "$PREFIX"
else
  sudo cmake --install "${BUILD_DIR}" --prefix "$PREFIX"
fi

echo ""
echo "== MAX25 installed to ${PREFIX} =="
echo "  max25d, kiss_bridge.py, max25-terminal, max25-ctl -> ${PREFIX}/bin"
echo "  max25-bcpr-ctl -> ${PREFIX}/sbin (when MAX25_BUILD_MAX25_BCPR=ON)"
echo "  examples -> ${PREFIX}/share/max25/"
echo ""

echo ""
echo "Next steps (TNC host):"
echo "  sudo usermod -aG dialout \$USER   # serial access"
echo "  sudo cp share/max25/max25d.ini.host.example /etc/max25/max25d.ini"
echo "  sudo max25d -c /etc/max25/max25d.ini"
echo "  max25-terminal -U /run/max25/modem.sock"
echo ""
echo "BayCom/based (max25-bcpr): NOT USABLE by default (MAX25_BUILD_MAX25_BCPR=OFF)."
echo "  Experimental only: -DMAX25_BUILD_MAX25_BCPR=ON — see docs/BAYCOM.md"
