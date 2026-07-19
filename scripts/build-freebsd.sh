#!/usr/bin/env bash
# MAX25-Stack — FreeBSD build (server + CRDOP/OSS, no BayCom/TNC)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
cmake -B build \
  -DMAX25_BUILD_TNCS=OFF \
  -DMAX25_BUILD_BCPR=ON \
  -DMAX25_BUILD_CRDOP=ON \
  -DMAX25_BUILD_DAEMON=ON \
  -DMAX25_BUILD_TERMINAL=ON \
  -DMAX25_BUILD_WEB=OFF \
  "$@"
cmake --build build -j"$(sysctl -n hw.ncpu 2>/dev/null || echo 2)"
