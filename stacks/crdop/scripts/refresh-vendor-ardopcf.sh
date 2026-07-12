#!/usr/bin/env bash
# Maintainer tool: re-download upstream ardopcf and re-apply CRDOP patches.
# Normal builds use the committed vendor/ardopcf tree — no network required.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENDOR="${ROOT}/vendor/ardopcf"
REF_FILE="${ROOT}/vendor/ardopcf.ref"
URL="${CRDOP_UPSTREAM_URL:-https://github.com/pflarue/ardop.git}"
PIN="$(grep '^commit_full=' "${REF_FILE}" 2>/dev/null | cut -d= -f2- | head -1)"
PIN="${PIN:-$(grep '^commit=' "${REF_FILE}" 2>/dev/null | cut -d= -f2- | head -1)}"

echo "This replaces vendor/ardopcf from upstream. Press Ctrl+C to abort."
sleep 2

rm -rf "${VENDOR}"
git clone --depth 1 --branch master "${URL}" "${VENDOR}"
if [[ -n "${PIN}" ]]; then
    git -C "${VENDOR}" fetch --depth 1 origin "${PIN}"
    git -C "${VENDOR}" checkout "${PIN}"
fi
rm -rf "${VENDOR}/.git"
rm -f "${VENDOR}/.crdop-patches-applied"

"${ROOT}/scripts/apply-vendor-patches.sh"
echo "Done. Review diff, update vendor/ardopcf.ref if needed, commit vendor/ardopcf/"
