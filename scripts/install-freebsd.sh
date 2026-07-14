#!/usr/bin/env bash
# MAX25-Stack — FreeBSD install helper (pkg deps + cmake install)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PREFIX="${PREFIX:-/usr/local}"

if [[ "$(uname -s)" != "FreeBSD" ]]; then
  echo "install-freebsd.sh is for FreeBSD hosts only" >&2
  exit 1
fi

pkgs=(cmake python3 ncurses sox git)
echo "Installing packages: ${pkgs[*]}"
pkg install -y "${pkgs[@]}"

"${ROOT}/scripts/build-freebsd.sh"
sudo cmake --install "${ROOT}/build" --prefix "${PREFIX}"

echo ""
echo "Next steps:"
echo "  sudo mkdir -p /var/run/max25 /usr/local/etc/max25"
echo "  cp ${PREFIX}/share/max25/max25d.freebsd.ini.example /usr/local/etc/max25/max25d.ini"
echo "  cp ${PREFIX}/share/crdop/crdop.freebsd.ini.example ~/.config/crdop/crdop.ini"
echo "  max25-ctl start --hardware soft-modems --device soft-crdop"
echo "  max25d -c /usr/local/etc/max25/max25d.ini"
echo "  max25-terminal -H 127.0.0.1 -p 7326"
