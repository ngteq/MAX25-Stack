#!/usr/bin/env bash
# max25-terminal offline probe — binary + TCP connect test.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "${ROOT}/../.." && pwd)"
TERM="${MAX25_TERMINAL:-${REPO}/build/bin/max25-terminal}"

[[ -x "${TERM}" ]] || { echo "FAIL: ${TERM} missing" >&2; exit 1; }

CLIENT="${REPO}/build/bin/max25-client"
if [[ -L "${CLIENT}" ]] || [[ -x "${CLIENT}" ]]; then
  :
else
  echo "WARN: max25-client symlink missing until cmake --install" >&2
fi

"${TERM}" --help >/dev/null

# Unit: EVENT connected/disconnected updates status (header bug regression)
UNIT="${ROOT}/.test_apply_event"
gcc -std=c11 -Wall -Wextra -O2 -I"${ROOT}" \
    -o "${UNIT}" "${ROOT}/test_apply_event.c" "${ROOT}/max25_proto.c"
"${UNIT}"
rm -f "${UNIT}"

MAX25_TERMINAL="${TERM}" python3 "${ROOT}/test_connect.py"
echo "OK: max25-terminal"
