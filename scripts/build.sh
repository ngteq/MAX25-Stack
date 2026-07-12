#!/usr/bin/env bash
# MainAX25-Stack (MAX25-Stack) — configure and build via CMake.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BUILD_TYPE="${CMAKE_BUILD_TYPE:-Release}"

cmake -B build -DCMAKE_BUILD_TYPE="${BUILD_TYPE}"
cmake --build build -j"$(nproc 2>/dev/null || echo 2)"
