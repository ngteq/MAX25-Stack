#!/usr/bin/env bash
# MainAX25-Stack (MAX25-Stack) — offline tests via CMake targets.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -d build ]]; then
  bash "${ROOT}/scripts/build.sh"
fi

cmake --build build --target max25_test
