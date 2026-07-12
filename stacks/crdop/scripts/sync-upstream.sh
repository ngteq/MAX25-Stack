#!/usr/bin/env bash
# Test whether CRDOP patches still apply to fresh upstream (maintainers).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

REF="${ROOT}/vendor/ardopcf.ref"
PIN="$(grep '^commit_full=' "${REF}" | cut -d= -f2-)"
URL="https://github.com/pflarue/ardop.git"

git clone --depth 1 "${URL}" "${TMP}/ardopcf"
git -C "${TMP}/ardopcf" fetch --depth 1 origin "${PIN}"
git -C "${TMP}/ardopcf" checkout "${PIN}"

for p in "${ROOT}"/patches/ardopcf/*.patch; do
    git -C "${TMP}/ardopcf" apply --check "${p}"
done

echo "OK: patches apply to upstream ${PIN}"
