#!/usr/bin/env bash
# Smoke test + optional upstream cmocka unit tests (CTest).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="${CRDOP_BUILD_DIR:-${ROOT}/build}"

export CRDOP_BUILD_TESTS="${CRDOP_BUILD_TESTS:-ON}"
export CRDOP_RUN_TESTS="${CRDOP_RUN_TESTS:-ON}"

"${ROOT}/scripts/build-crdop.sh"

if [[ ! -f "${BUILD}/CTestTestfile.cmake" ]]; then
    echo "NOTE: unit tests not built (libcmocka missing or unsupported platform)" >&2
fi

echo "OK: CRDOP test-all finished"
