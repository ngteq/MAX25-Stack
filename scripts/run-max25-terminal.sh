#!/usr/bin/env bash
# Canonical max25-terminal launcher — never use a stale ELF under stacks/terminal/.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

pick() {
  local c
  for c in \
    "${ROOT}/build-max25-bcpr/bin/max25-terminal" \
    "${ROOT}/build/bin/max25-terminal" \
    /usr/local/bin/max25-terminal
  do
    if [[ -x "$c" ]]; then
      # Refuse if help lacks -d (stale)
      if "$c" -h 2>&1 | grep -q -- '-d, --device'; then
        echo "$c"
        return 0
      fi
    fi
  done
  if command -v max25-terminal >/dev/null 2>&1; then
    c="$(command -v max25-terminal)"
    if [[ "$(readlink -f "$c" 2>/dev/null || echo "$c")" != "$(readlink -f "${ROOT}/stacks/terminal/max25-terminal" 2>/dev/null || true)" ]]; then
      if "$c" -h 2>&1 | grep -q -- '-d, --device'; then
        echo "$c"
        return 0
      fi
    fi
  fi
  return 1
}

BIN="$(pick)" || {
  echo "run-max25-terminal: no current max25-terminal with -d/--device" >&2
  echo "  cmake -B build-max25-bcpr -DMAX25_BUILD_MAX25_BCPR=ON && cmake --build build-max25-bcpr" >&2
  echo "  Do not run stacks/terminal/max25-terminal leftovers." >&2
  exit 127
}

SOCK="${MAX25_UNIX:-/run/max25/modem.sock}"
if [[ ! -S "$SOCK" ]] && [[ "${1:-}" != "-h" ]] && [[ "${1:-}" != "--help" ]]; then
  # Still allow -T TCP-only; warn only for default unix path
  if [[ " $* " != *" -T "* ]] && [[ " $* " != *" --tcp-only "* ]]; then
    echo "run-max25-terminal: no socket $SOCK — start max25d first:" >&2
    echo "  ${ROOT}/scripts/run-max25d.sh" >&2
    echo "  or: ${ROOT}/stacks/daemon/max25d -c ${ROOT}/local/max25d.ini" >&2
    exit 1
  fi
fi

exec "$BIN" "$@"
