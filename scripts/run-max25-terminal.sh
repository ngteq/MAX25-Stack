#!/usr/bin/env bash
# Canonical max25-terminal launcher — tree or PREFIX/bin.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

pick() {
  local c
  # Prefer installed binary beside this script
  if [[ -x "${SCRIPT_DIR}/max25-terminal" && ! -d "${SCRIPT_DIR}/../stacks/terminal" ]]; then
    c="${SCRIPT_DIR}/max25-terminal"
    if "$c" -h 2>&1 | grep -q -- '-d, --device'; then
      echo "$c"
      return 0
    fi
  fi
  local TREE=""
  if [[ -d "${SCRIPT_DIR}/../stacks/terminal" ]]; then
    TREE="$(cd "${SCRIPT_DIR}/.." && pwd)"
  fi
  for c in \
    ${TREE:+"${TREE}/build/bin/max25-terminal"} \
    ${TREE:+"${TREE}/build-max25-bcpr/bin/max25-terminal"} \
    "${ROOT}/build-max25-bcpr/bin/max25-terminal" \
    "${ROOT}/build/bin/max25-terminal" \
    /usr/local/bin/max25-terminal
  do
    [[ -n "$c" && -x "$c" ]] || continue
    if "$c" -h 2>&1 | grep -q -- '-d, --device'; then
      echo "$c"
      return 0
    fi
  done
  if command -v max25-terminal >/dev/null 2>&1; then
    c="$(command -v max25-terminal)"
    if "$c" -h 2>&1 | grep -q -- '-d, --device'; then
      echo "$c"
      return 0
    fi
  fi
  return 1
}

BIN="$(pick)" || {
  echo "run-max25-terminal: no current max25-terminal with -d/--device" >&2
  echo "  cmake -B build-max25-bcpr -DMAX25_BUILD_MAX25_BCPR=ON && cmake --build build-max25-bcpr" >&2
  echo "  install: scripts/install-max25.sh   or cmake --install build" >&2
  echo "  Do not run stacks/terminal/max25-terminal leftovers." >&2
  exit 127
}

SOCK="${MAX25_UNIX:-/run/max25/modem.sock}"
if [[ ! -S "$SOCK" ]] && [[ "${1:-}" != "-h" ]] && [[ "${1:-}" != "--help" ]]; then
  if [[ " $* " != *" -T "* ]] && [[ " $* " != *" --tcp-only "* ]]; then
    echo "run-max25-terminal: no socket $SOCK — start max25d first:" >&2
    echo "  run-max25d   # or: ${SCRIPT_DIR}/run-max25d.sh" >&2
    exit 1
  fi
fi

exec "$BIN" "$@"
