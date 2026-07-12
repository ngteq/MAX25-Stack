#!/usr/bin/env bash
# Build and install CRDOP to PREFIX (default /usr/local).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PREFIX="${CRDOP_PREFIX:-/usr/local}"
BUILD="${CRDOP_BUILD_DIR:-${ROOT}/build}"

"${ROOT}/scripts/build-crdop.sh"

cmake --install "${BUILD}" --prefix "${PREFIX}"

echo "Installed:"
echo "  ${PREFIX}/bin/crdopc      — modem binary"
echo "  ${PREFIX}/bin/crdop       — profile launcher"
echo "  ${PREFIX}/share/crdop/    — INI examples, VERSION"
