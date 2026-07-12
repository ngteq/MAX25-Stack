#!/usr/bin/env bash
# Verify vendor/ardopcf is present (embedded in repo — no submodule/download).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENDOR="${ROOT}/vendor/ardopcf"

if [[ ! -f "${VENDOR}/LICENSE" || ! -f "${VENDOR}/src/common/ARDOPC.c" ]]; then
    echo "error: vendor/ardopcf missing — clone CRDOP with full tree or run scripts/refresh-vendor-ardopcf.sh" >&2
    exit 1
fi

if ! grep -q 'CRDOP src/crdop_version.c' "${VENDOR}/src/common/ARDOPC.c" 2>/dev/null; then
    echo "warn: vendor/ardopcf may need CRDOP patches — run scripts/apply-vendor-patches.sh" >&2
fi

echo "vendor/ardopcf OK (embedded, commit $(grep '^commit=' "${ROOT}/vendor/ardopcf.ref" 2>/dev/null | cut -d= -f2 || echo unknown))"
