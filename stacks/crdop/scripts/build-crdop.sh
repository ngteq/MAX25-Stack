#!/usr/bin/env bash
# CRDOP unified build — vendor embedded; GCC, Clang, or MSVC via CMake.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="${CRDOP_BUILD_DIR:-${ROOT}/build}"
TYPE="${CRDOP_BUILD_TYPE:-Release}"
TOOLCHAIN="${CRDOP_TOOLCHAIN:-}"
BUILD_TESTS="${CRDOP_BUILD_TESTS:-OFF}"
RUN_TESTS="${CRDOP_RUN_TESTS:-OFF}"

"${ROOT}/scripts/import-ardopcf.sh"

CMAKE_ARGS=(-B "${BUILD}" -DCMAKE_BUILD_TYPE="${TYPE}" -DCRDOP_BUILD_TESTS="${BUILD_TESTS}")

if [[ -n "${TOOLCHAIN}" ]]; then
    CMAKE_ARGS+=(-DCMAKE_TOOLCHAIN_FILE="${ROOT}/cmake/toolchains/${TOOLCHAIN}.cmake")
fi

if [[ -n "${CC:-}" ]]; then
    CMAKE_ARGS+=(-DCMAKE_C_COMPILER="${CC}")
fi
if [[ -n "${CXX:-}" ]]; then
    CMAKE_ARGS+=(-DCMAKE_CXX_COMPILER="${CXX}")
fi

cmake "${ROOT}" "${CMAKE_ARGS[@]}"
cmake --build "${BUILD}" -j"$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)"

"${ROOT}/scripts/test-smoke.sh"

if [[ "${BUILD_TESTS}" == "ON" || "${BUILD_TESTS}" == "1" || "${RUN_TESTS}" == "ON" || "${RUN_TESTS}" == "1" ]]; then
    if [[ -f "${BUILD}/CTestTestfile.cmake" ]]; then
        ctest --test-dir "${BUILD}" --output-on-failure
    else
        echo "NOTE: CRDOP_BUILD_TESTS requested but no CTest targets (install libcmocka-dev?)" >&2
    fi
fi

echo "CRDOP $(cat "${ROOT}/VERSION") built: ${BUILD}/crdopc"
