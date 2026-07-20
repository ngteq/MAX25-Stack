#!/usr/bin/env bash
# Canonical max25d start — escalate to root only when hardware needs it.
# Works from source tree (scripts/) and from PREFIX/bin after install.
# Root needed: ttyS / USB serial / ioperm / /dev/port / max25-bcpr SER12 (max25e0).
# Escalation: already root → sudo -n → sudo → su → pkexec.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -x "${SCRIPT_DIR}/max25d" && ! -d "${SCRIPT_DIR}/../stacks/daemon" ]]; then
  DAEMON="${SCRIPT_DIR}/max25d"
  TREE=""
else
  TREE="$(cd "${SCRIPT_DIR}/.." && pwd)"
  DAEMON="${TREE}/stacks/daemon/max25d"
fi

if [[ ! -x "$DAEMON" ]]; then
  echo "run-max25d: missing $DAEMON" >&2
  exit 1
fi

# Match real daemon only (not agent shells whose argv text mentions max25d).
if pgrep -x max25d >/dev/null 2>&1 \
   || pgrep -f -- '/max25d(\.py)?[[:space:]]+-c[[:space:]]' >/dev/null 2>&1; then
  echo "run-max25d: max25d already running" >&2
  pgrep -af -- '/max25d(\.py)?[[:space:]]+-c[[:space:]]' | head -5 || true
  pgrep -ax max25d | head -5 || true
  ls -la /run/max25/modem.sock 2>/dev/null || echo "run-max25d: WARNING no /run/max25/modem.sock" >&2
  exit 0
fi

# Accept path or max25d-style "-c path".
INI="${1:-}"
if [[ "$INI" == "-c" || "$INI" == "--config" ]]; then
  INI="${2:-}"
fi
if [[ -z "$INI" ]]; then
  if [[ -n "$TREE" && -f "${TREE}/local/max25d.ini" ]]; then
    INI="${TREE}/local/max25d.ini"
  elif [[ -f "${PWD}/local/max25d.ini" ]]; then
    INI="${PWD}/local/max25d.ini"
  elif [[ -f /etc/max25/max25d.ini ]]; then
    INI=/etc/max25/max25d.ini
  else
    echo "run-max25d: no INI (pass path or create local/max25d.ini / /etc/max25/max25d.ini)" >&2
    exit 1
  fi
fi
if [[ ! -f "$INI" ]]; then
  echo "run-max25d: INI not found: $INI" >&2
  exit 1
fi

needs_root() {
  local f="$1"
  [[ -f "$f" ]] || return 1
  if grep -Eiq '^[[:space:]]*(max25-bcpr|bcpr|baycom|pccom)[[:space:]]*=[[:space:]]*yes' "$f"; then return 0; fi
  if grep -Eiq '^[[:space:]]*(max25e0|max25e0:bc[01]|tnc2c|pktnc2|baycom-kiss|pccom-kiss)[[:space:]]*=' "$f"; then return 0; fi
  if grep -Eiq '^[[:space:]]*device[[:space:]]*=[[:space:]]*(max25e0|tnc2c|pktnc2)' "$f"; then return 0; fi
  if grep -Eqi '/dev/(ttyS|ttyUSB|ttyACM|port)\b' "$f"; then return 0; fi
  if grep -Eiq '^[[:space:]]*unix_socket[[:space:]]*=[[:space:]]*/run/max25/' "$f"; then return 0; fi
  return 1
}

if [[ "$(id -u)" -ne 0 ]]; then
  if needs_root "$INI"; then
    if command -v sudo >/dev/null 2>&1; then
      if sudo -n true 2>/dev/null; then
        echo "run-max25d: hardware path — escalating via sudo -n" >&2
        exec sudo -n "$0" "$INI"
      fi
      echo "run-max25d: hardware path — escalating via sudo (password may be required)" >&2
      exec sudo "$0" "$INI"
    fi
    if command -v su >/dev/null 2>&1; then
      echo "run-max25d: hardware path — escalating via su" >&2
      exec su -c "$(printf '%q ' "$0" "$INI")"
    fi
    if command -v pkexec >/dev/null 2>&1; then
      echo "run-max25d: hardware path — escalating via pkexec" >&2
      exec pkexec "$0" "$INI"
    fi
    echo "run-max25d: ERROR need root for SER12/UART/ioperm" >&2
    exit 1
  fi
  echo "run-max25d: starting unprivileged (uid=$(id -u))" >&2
else
  echo "run-max25d: running as root (uid=0)" >&2
fi

if [[ "$(id -u)" -eq 0 ]]; then
  mkdir -p /run/max25
fi
echo "run-max25d: ini=$INI"
exec "$DAEMON" -c "$INI"
