#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${CRDOP_BIN:-${ROOT}/build/crdopc}"
VER="$(tr -d '[:space:]' < "${ROOT}/VERSION")"

[[ -x "${BIN}" ]] || { echo "FAIL: ${BIN} missing" >&2; exit 1; }

OUT="$("${BIN}" -h 2>&1 || true)"
echo "${OUT}" | grep -qi crdopc || { echo "FAIL: crdopc branding"; exit 1; }
echo "${OUT}" | grep -q "${VER}" || { echo "FAIL: expected version ${VER}"; exit 1; }

echo "OK: CRDOP ${VER} smoke test passed"
