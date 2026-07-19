#!/usr/bin/env bash
# Canonical max25d start — escalate to root only when hardware needs it.
# Root needed: ttyS / USB serial / ioperm / /dev/port / bcpr SER12 (max25e0).
# Not always: plain TCP/unix-only (no SER12/TNC serial) may run unprivileged.
# Escalation order (when needed): already root → sudo -n → sudo → su → pkexec.
# After privileged init, drop to [daemon] user=/group= when implemented in max25d.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

DAEMON="${ROOT}/stacks/daemon/max25d"
if [[ ! -x "$DAEMON" ]]; then
  echo "run-max25d: missing $DAEMON" >&2
  exit 1
fi

# Match real daemon only (avoid agent/shell command lines containing the string).
if pgrep -x max25d >/dev/null 2>&1 || pgrep -f '[/]stacks/daemon/max25d\.py' >/dev/null 2>&1; then
  echo "run-max25d: max25d already running" >&2
  pgrep -af '[/]stacks/daemon/max25d' || true
  ls -la /run/max25/modem.sock 2>/dev/null || echo "run-max25d: WARNING no /run/max25/modem.sock" >&2
  exit 0
fi

INI="${1:-}"
if [[ -z "$INI" ]]; then
  if [[ -f "${ROOT}/local/max25d.ini" ]]; then
    INI="${ROOT}/local/max25d.ini"
  elif [[ -f /etc/max25/max25d.ini ]]; then
    INI=/etc/max25/max25d.ini
  else
    echo "run-max25d: no INI (pass path or create local/max25d.ini)" >&2
    exit 1
  fi
fi

# True if this INI needs privileged UART / SER12 / /run/max25 bring-up.
needs_root() {
  local f="$1"
  [[ -f "$f" ]] || return 1
  # Feature gates that imply hardware SER12 / legacy modem paths
  if grep -Eiq '^[[:space:]]*(bcpr|baycom|pccom)[[:space:]]*=[[:space:]]*yes' "$f"; then
    return 0
  fi
  # Device ids / specs that need tty or ioperm
  if grep -Eiq '^[[:space:]]*(max25e0|max25e0:bc[01]|tnc2c|pktnc2|baycom-kiss|pccom-kiss)[[:space:]]*=' "$f"; then
    return 0
  fi
  if grep -Eiq '^[[:space:]]*device[[:space:]]*=[[:space:]]*(max25e0|tnc2c|pktnc2)' "$f"; then
    return 0
  fi
  if grep -Eqi '/dev/(ttyS|ttyUSB|ttyACM|port)\b' "$f"; then
    return 0
  fi
  if grep -Eiq '^[[:space:]]*unix_socket[[:space:]]*=[[:space:]]*/run/max25/' "$f"; then
    # /run/max25 usually needs root to create; still escalate for sock dir
    return 0
  fi
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
      echo "run-max25d: hardware path — escalating via su (password may be required)" >&2
      exec su -c "$(printf '%q ' "$0" "$INI")"
    fi
    if command -v pkexec >/dev/null 2>&1; then
      echo "run-max25d: hardware path — escalating via pkexec" >&2
      exec pkexec "$0" "$INI"
    fi
    echo "run-max25d: ERROR need root for SER12/UART/ioperm (sudo/su/pkexec unavailable)" >&2
    exit 1
  fi
  echo "run-max25d: no SER12/UART path detected — starting unprivileged (uid=$(id -u))" >&2
else
  echo "run-max25d: running as root (uid=0)" >&2
fi

if [[ "$(id -u)" -eq 0 ]]; then
  mkdir -p /run/max25
fi
echo "run-max25d: ini=$INI"
exec "$DAEMON" -c "$INI"
