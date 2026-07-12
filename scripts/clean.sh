#!/usr/bin/env bash
# MainAX25-Stack (MAX25-Stack) — remove CMake build trees.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

rm -rf build stacks/crdop/build
echo "Removed build/ and stacks/crdop/build/"
