#!/usr/bin/env bash
# MainAX25-Stack — build all merged stacks (max25-bcpr default OFF).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
BUILD_DIR="${BUILD_DIR:-build}"
BUILD_TYPE="${CMAKE_BUILD_TYPE:-Release}"
DO_INSTALL=0
PREFIX="${PREFIX:-/usr/local}"

usage() {
  cat <<USAGE
Usage: $0 [--install] [--prefix DIR] [--build-dir DIR]

  Default: cmake configure + build (TERMINAL/DAEMON ON; max25-bcpr OFF).
  --install   also cmake --install to PREFIX
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install) DO_INSTALL=1; shift ;;
    --prefix) PREFIX="$2"; shift 2 ;;
    --build-dir) BUILD_DIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown: $1" >&2; usage; exit 2 ;;
  esac
done

echo "== MainAX25-Stack build-all (${BUILD_DIR}, ${BUILD_TYPE}) =="
cmake -B "${BUILD_DIR}" \
  -DCMAKE_BUILD_TYPE="${BUILD_TYPE}" \
  -DMAX25_BUILD_MAX25_BCPR="${MAX25_BUILD_MAX25_BCPR:-OFF}" \
  -DMAX25_BUILD_TERMINAL=ON \
  -DMAX25_BUILD_DAEMON=ON \
  -DMAX25_BUNDLE_AX25=OFF
cmake --build "${BUILD_DIR}" -j"$(nproc 2>/dev/null || echo 2)"

echo "== plugin discovery =="
bash scripts/discover-plugins.sh || true

if [[ "$DO_INSTALL" -eq 1 ]]; then
  echo "== install → ${PREFIX} =="
  if [[ "$(id -u)" -eq 0 ]]; then
    cmake --install "${BUILD_DIR}" --prefix "${PREFIX}"
  else
    sudo cmake --install "${BUILD_DIR}" --prefix "${PREFIX}"
  fi
  echo "Launchers: ${PREFIX}/bin/run-max25d  ${PREFIX}/bin/run-max25-terminal"
  echo "Tests:     ${PREFIX}/sbin/max25-tx-rx-test  ${PREFIX}/sbin/max25-bcpr-rxtx-smoke.sh"
fi

echo "== done =="
