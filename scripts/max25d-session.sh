#!/usr/bin/env bash
# max25d-session — run max25d inside tmux or GNU screen (operator attach/detach).
#
#   max25d-session start [--tmux|--screen] [-c /etc/max25/max25d.ini]
#   max25d-session attach [--tmux|--screen]
#   max25d-session status
#   max25d-session stop
#
# Environment overrides:
#   MAX25D_SESSION         session name (default: max25d)
#   MAX25D_SESSION_BACKEND tmux | screen (default: tmux)
#   MAX25D_INI             config path
set -euo pipefail

SESSION_NAME="${MAX25D_SESSION:-max25d}"
BACKEND="${MAX25D_SESSION_BACKEND:-tmux}"
CONFIG="${MAX25D_INI:-/etc/max25/max25d.ini}"
MAX25D_BIN="${MAX25D_BIN:-max25d}"

usage() {
  cat <<'EOF'
max25d-session — persistent max25d in tmux or screen

Commands:
  start   [--tmux|--screen] [-c ini]   start detached session
  attach  [--tmux|--screen]            attach to running session
  status                               show session + max25d hint
  stop                                 kill session

Examples:
  max25d-session start -c /etc/max25/max25d.ini
  max25d-session attach
  MAX25D_SESSION_BACKEND=screen max25d-session start

EOF
}

have_tmux() { command -v tmux >/dev/null 2>&1; }
have_screen() { command -v screen >/dev/null 2>&1; }

pick_backend() {
  case "${1:-$BACKEND}" in
    tmux)
      if ! have_tmux; then
        echo "max25d-session: tmux not installed" >&2
        exit 1
      fi
      echo tmux
      ;;
    screen)
      if ! have_screen; then
        echo "max25d-session: screen not installed" >&2
        exit 1
      fi
      echo screen
      ;;
    *)
      echo "max25d-session: unknown backend '$1' (use tmux or screen)" >&2
      exit 1
      ;;
  esac
}

session_running() {
  local b="$1"
  case "$b" in
    tmux) tmux has-session -t "$SESSION_NAME" 2>/dev/null ;;
    screen) screen -ls | grep -q "[[:space:]]*[0-9]*\.${SESSION_NAME}[[:space:]]" ;;
  esac
}

cmd_start() {
  local b
  b="$(pick_backend "$BACKEND")"
  if session_running "$b"; then
    echo "max25d-session: session '$SESSION_NAME' already running ($b)" >&2
    echo "  attach: max25d-session attach --$b" >&2
    exit 1
  fi
  local cmd="${MAX25D_BIN} -c ${CONFIG}"
  case "$b" in
    tmux)
      tmux new-session -d -s "$SESSION_NAME" \
        "${MAX25D_BIN} -c ${CONFIG}; echo; echo max25d exited \$?; read -r _"
      ;;
    screen)
      screen -dmS "$SESSION_NAME" bash -lc "${cmd}"
      ;;
  esac
  echo "max25d-session: started ($b) name=$SESSION_NAME config=$CONFIG"
  echo "max25d-session: attach with: max25d-session attach --$b"
}

cmd_attach() {
  local b
  b="$(pick_backend "$BACKEND")"
  if ! session_running "$b"; then
    echo "max25d-session: no session '$SESSION_NAME' ($b)" >&2
    exit 1
  fi
  case "$b" in
    tmux) exec tmux attach -t "$SESSION_NAME" ;;
    screen) exec screen -r "$SESSION_NAME" ;;
  esac
}

cmd_status() {
  local b
  b="$(pick_backend "$BACKEND")"
  if session_running "$b"; then
    echo "max25d-session: running backend=$b name=$SESSION_NAME"
    case "$b" in
      tmux) tmux list-panes -t "$SESSION_NAME" -F 'pane #{pane_index}: #{pane_current_command}' 2>/dev/null || true ;;
      screen) screen -ls | grep "${SESSION_NAME}" || true ;;
    esac
  else
    echo "max25d-session: not running (backend=$b name=$SESSION_NAME)"
  fi
  if command -v pgrep >/dev/null 2>&1 && pgrep -x max25d >/dev/null 2>&1; then
    echo "max25d-session: max25d process: $(pgrep -xa max25d || true)"
  fi
}

cmd_stop() {
  local b
  b="$(pick_backend "$BACKEND")"
  if ! session_running "$b"; then
    echo "max25d-session: not running" >&2
    exit 0
  fi
  case "$b" in
    tmux) tmux kill-session -t "$SESSION_NAME" ;;
    screen) screen -S "$SESSION_NAME" -X quit ;;
  esac
  echo "max25d-session: stopped ($b) name=$SESSION_NAME"
}

CMD="${1:-}"
shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --tmux) BACKEND=tmux; shift ;;
    --screen) BACKEND=screen; shift ;;
    -c|--config)
      CONFIG="${2:?config path required}"
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *) echo "max25d-session: unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

case "$CMD" in
  start) cmd_start ;;
  attach) cmd_attach ;;
  status) cmd_status ;;
  stop) cmd_stop ;;
  ""|-h|--help) usage ;;
  *) echo "max25d-session: unknown command: $CMD" >&2; usage >&2; exit 1 ;;
esac
