#!/usr/bin/env bash
# Apply CRDOP patch series — only if vendor tree is still pristine upstream.
# Released CRDOP commits ship vendor/ardopcf with patches already integrated.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENDOR="${ROOT}/vendor/ardopcf"
PATCH_DIR="${ROOT}/patches/ardopcf"
STAMP="${VENDOR}/.crdop-patches-applied"
MARKER="${VENDOR}/src/common/ARDOPC.c"

if [[ ! -d "${VENDOR}/src" ]]; then
    echo "error: ${VENDOR} missing" >&2
    exit 1
fi

if grep -q 'CRDOP src/crdop_version.c' "${MARKER}" 2>/dev/null; then
    date -u +'%Y-%m-%dT%H:%M:%SZ' > "${STAMP}"
    echo "CRDOP vendor already integrated ($(cat "${STAMP}"))"
    exit 0
fi

if [[ ! -d "${PATCH_DIR}" ]] || ! compgen -G "${PATCH_DIR}/*.patch" >/dev/null; then
    echo "error: no patches in ${PATCH_DIR}" >&2
    exit 1
fi

cd "${VENDOR}"
for p in "${PATCH_DIR}"/*.patch; do
    echo "applying ${p#${ROOT}/}"
    git apply --check "${p}" 2>/dev/null || patch -p1 --forward -r - < "${p}"
    git apply "${p}" 2>/dev/null || patch -p1 --forward < "${p}"
done

date -u +'%Y-%m-%dT%H:%M:%SZ' > "${STAMP}"
echo "CRDOP patches applied ($(cat "${STAMP}"))"
