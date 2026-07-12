#!/usr/bin/env bash
# MainAX25-Stack — build and install on Linux.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PREFIX="${PREFIX:-/usr/local}"
INSTALL_DEPS=0
BUILD_ONLY=0

usage() {
  cat <<EOF
MainAX25-Stack install — Linux

Usage: $0 [options]

Options:
  --deps        Install apt build dependencies (Debian / Ubuntu)
  --build-only  Build only, do not install to PREFIX
  --prefix DIR  Install prefix (default: /usr/local)
  -h, --help    This help

Examples:
  $0 --deps                 # apt + build + sudo install
  $0 --build-only           # Build in-tree only
  PREFIX=/opt/max25 $0      # Install to /opt/max25

After install:
  sudo cp share/max25/max25d.ini.edge.example /etc/max25/max25d.ini
  sudo max25d -c /etc/max25/max25d.ini
  max25-terminal -U /run/max25/modem.sock

See docs/LINUX-EDGE-SETUP.md
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --deps) INSTALL_DEPS=1; shift ;;
    --build-only) BUILD_ONLY=1; shift ;;
    --prefix) PREFIX="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "install-max25.sh: Linux only (max25d)" >&2
  exit 1
fi

arch="$(uname -m)"
echo "== MAX25 install: $(uname -s) ${arch} =="

if [[ "$INSTALL_DEPS" -eq 1 ]]; then
  if command -v apt-get >/dev/null 2>&1; then
    echo "-- apt dependencies"
    sudo apt-get update
    pkgs=(build-essential make cmake pkg-config git python3 libncurses-dev libasound2-dev)
    if apt-cache show "linux-headers-$(uname -r)" >/dev/null 2>&1; then
      pkgs+=("linux-headers-$(uname -r)")
    fi
    sudo apt-get install -y "${pkgs[@]}" || {
      echo "WARN: some optional headers failed — BayCom kernel build may need manual headers" >&2
      sudo apt-get install -y build-essential make cmake pkg-config git python3 libncurses-dev libasound2-dev
    }
  else
    echo "WARN: apt-get not found — install build deps manually (see docs/LINUX-EDGE-SETUP.md)" >&2
  fi
fi

cd "$ROOT"
echo "-- build"
make all

if [[ "$BUILD_ONLY" -eq 1 ]]; then
  echo "== build done (no install) =="
  exit 0
fi

echo "-- install to ${PREFIX}"
if [[ "$(id -u)" -eq 0 ]]; then
  make install PREFIX="$PREFIX"
else
  sudo make install PREFIX="$PREFIX"
fi

echo ""
echo "== MAX25 installed to ${PREFIX} =="
echo "  max25d, max25-terminal, max25-ctl → ${PREFIX}/bin"
echo "  examples → ${PREFIX}/share/max25/"
echo ""
echo "Next steps:"
echo "  sudo usermod -aG dialout \$USER   # serial access"
echo "  sudo cp share/max25/max25d.ini.edge.example /etc/max25/max25d.ini"
echo "  sudo max25d -c /etc/max25/max25d.ini"
echo "  max25-terminal -U /run/max25/modem.sock"
echo "  docs/LINUX-EDGE-SETUP.md"
