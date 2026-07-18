#!/usr/bin/env bash
# bcpr-rxtx-smoke.sh — L0…L4 nofreeze prove-out (BayCom/based / bcpr).
# Default: offline L0 only, NO TX. Live RX: --live. TX: --live --tx.
# No calibrate. No baycom_ser_fdx product path.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
CTL="$SCRIPT_DIR/bcpr-ctl"
INI="${BCPR_INI:-$ROOT/stacks/bcpr/share/bcpr.ini.example}"
SECONDS_LIVE=15
DO_LIVE=0
DO_TX=0
BUILD_DIR=""
BCPRD=""
TEST_HDLC=""
ERR=0
BCPRD_PID=""

usage() {
  cat <<'USAGE'
Usage: bcpr-rxtx-smoke.sh [-c ini] [--live] [--tx] [--seconds N] [--build-dir DIR]
  L0 offline always. Soft L1 if probes safe. L2/L3 need --live. L4 needs --tx.
  Default: NO TX. Hard time caps. Always stop.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -c) INI="$2"; shift 2 ;;
    --live) DO_LIVE=1; shift ;;
    --tx) DO_TX=1; shift ;;
    --seconds) SECONDS_LIVE="$2"; shift 2 ;;
    --build-dir) BUILD_DIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "ERROR: unknown arg: $1"; usage; exit 2 ;;
  esac
done

if [[ "$DO_TX" -eq 1 && "$DO_LIVE" -eq 0 ]]; then
  echo "ERROR: --tx requires --live"
  exit 2
fi

if [[ "$SECONDS_LIVE" -lt 1 ]]; then
  SECONDS_LIVE=1
fi
if [[ "$SECONDS_LIVE" -gt 60 ]]; then
  echo "WARN: capping --seconds from $SECONDS_LIVE to 60"
  SECONDS_LIVE=60
fi

log() { printf '%s\n' "$*"; }
ok() { log "PASS: $*"; }
fail() { log "FAIL: $*"; ERR=1; }
stage() { log ""; log "=== $* ==="; }

pick_build_dir() {
  local cand
  if [[ -n "${BCPR_BUILD_DIR:-}" ]]; then
    echo "$BCPR_BUILD_DIR"
    return
  fi
  if [[ -n "$BUILD_DIR" ]]; then
    echo "$BUILD_DIR"
    return
  fi
  for cand in \
    "$ROOT/build-bcpr" \
    "$ROOT/build-bcpr-${USER:-user}" \
    "/tmp/max25-build-bcpr-${USER:-user}"; do
    if [[ -d "$cand" && -w "$cand" ]]; then
      echo "$cand"
      return
    fi
    if [[ ! -e "$cand" ]] && mkdir -p "$cand" 2>/dev/null && [[ -w "$cand" ]]; then
      echo "$cand"
      return
    fi
  done
  if [[ -d "$ROOT/build-bcpr" && ! -w "$ROOT/build-bcpr" ]]; then
    cand="$ROOT/build-bcpr-${USER:-user}"
    mkdir -p "$cand"
    echo "$cand"
    return
  fi
  echo "$ROOT/build-bcpr-${USER:-user}"
}

ensure_binaries() {
  local bd="$1"
  BCPRD="$bd/bin/bcprd"
  TEST_HDLC="$bd/bin/test_hdlc_offline"
  if [[ -x "$BCPRD" && -x "$TEST_HDLC" ]]; then
    return 0
  fi
  log "Building bcpr into $bd (MAX25_BUILD_BCPR=ON)…"
  mkdir -p "$bd"
  cmake -S "$ROOT" -B "$bd" -DMAX25_BUILD_BCPR=ON
  cmake --build "$bd" --target bcprd test_hdlc_offline test_config_offline
  [[ -x "$BCPRD" && -x "$TEST_HDLC" ]]
}

stop_bcprd() {
  if [[ -n "${BCPRD_PID:-}" ]] && kill -0 "$BCPRD_PID" 2>/dev/null; then
    kill "$BCPRD_PID" 2>/dev/null || true
    local i
    for i in 1 2 3 4 5; do
      kill -0 "$BCPRD_PID" 2>/dev/null || break
      sleep 0.2
    done
    if kill -0 "$BCPRD_PID" 2>/dev/null; then
      kill -9 "$BCPRD_PID" 2>/dev/null || true
    fi
  fi
  BCPRD_PID=""
  if [[ -x "$CTL" ]]; then
    BCPRD="${BCPRD:-bcprd}" "$CTL" -c "$INI" stop >/dev/null 2>&1 || true
  fi
  pkill -x bcprd 2>/dev/null || true
}

trap 'stop_bcprd' EXIT INT TERM

stage "L0 offline HDLC"
BUILD="$(pick_build_dir)"
log "build_dir=$BUILD"
ensure_binaries "$BUILD" || { fail "build/binaries"; exit 1; }

if "$TEST_HDLC"; then
  ok "test_hdlc_offline"
else
  fail "test_hdlc_offline"
fi

if "$BCPRD" -c "$INI" --dry-run --once; then
  ok "bcprd --dry-run --once"
else
  fail "bcprd --dry-run --once"
fi

stage "L1 enhanced preflight"
if [[ ! -f "$INI" ]]; then
  fail "missing INI $INI"
else
  export BCPRD
  set +e
  "$CTL" -c "$INI" preflight
  pf_rc=$?
  set -e
  if [[ "$pf_rc" -eq 0 ]]; then
    ok "bcpr-ctl preflight"
  else
    if [[ "$DO_LIVE" -eq 1 ]]; then
      fail "bcpr-ctl preflight (required for --live)"
    else
      log "NOTE: preflight rc=$pf_rc without --live — L0 is the offline gate"
      # dry_run example: preflight skips UART and returns 0; real mismatch is soft-note only
      if [[ "$pf_rc" -ne 0 ]]; then
        log "WARN: fix INI before --live"
      fi
    fi
  fi
fi

if [[ "$DO_LIVE" -eq 0 ]]; then
  stage "summary (offline)"
  if [[ "$ERR" -eq 0 ]]; then
    ok "L0 complete — add --live for L2/L3 (RX), --live --tx for L4"
    exit 0
  fi
  exit "$ERR"
fi

stage "L2/L3 timed attach + RX listen (${SECONDS_LIVE}s)"
if [[ "$DO_TX" -eq 1 ]]; then
  log "WARN: --tx will assert PTT on the modem even if the radio is OFF"
fi

dry_val="$(awk -F= '
  $0 ~ /^\[/ { cur=$0; gsub(/[[:space:]]/,"",cur) }
  cur=="[bcpr]" && $1 ~ /^[[:space:]]*dry_run[[:space:]]*$/ {
    v=$2; gsub(/^[[:space:]]+|[[:space:]]+$/,"",v); print tolower(v); exit
  }' "$INI")"
case "$dry_val" in
  yes|true|on|1)
    fail "live requires dry_run=no in $INI"
    exit 1
    ;;
esac

export BCPRD
"$CTL" -c "$INI" preflight || { fail "preflight before attach"; exit 1; }

log "starting bcprd --seconds $SECONDS_LIVE …"
"$BCPRD" -c "$INI" --seconds "$SECONDS_LIVE" &
BCPRD_PID=$!

kiss_link="$(awk -F= '
  $0 ~ /^\[/ { cur=$0; gsub(/[[:space:]]/,"",cur) }
  cur=="[bc0]" && $1 ~ /^[[:space:]]*kiss_link[[:space:]]*$/ {
    v=$2; gsub(/^[[:space:]]+|[[:space:]]+$/,"",v); print v; exit
  }' "$INI")"
kiss_link="${kiss_link:-/tmp/bcpr/kiss-bc0}"

waited=0
while [[ "$waited" -lt 5 ]]; do
  if [[ -e "$kiss_link" ]] || ! kill -0 "$BCPRD_PID" 2>/dev/null; then
    break
  fi
  sleep 0.5
  waited=$((waited + 1))
done

if ! kill -0 "$BCPRD_PID" 2>/dev/null; then
  fail "bcprd exited early (attach)"
  wait "$BCPRD_PID" || true
  BCPRD_PID=""
  exit 1
fi

if [[ -e "$kiss_link" ]]; then
  ok "kiss_link present ($kiss_link) — RX listen active"
else
  log "WARN: kiss_link not yet visible — continuing timed run"
fi

if [[ "$DO_TX" -eq 1 ]]; then
  stage "L4 optional TX (capped)"
  if [[ ! -e "$kiss_link" ]]; then
    fail "no kiss_link for TX"
  else
    python3 - "$kiss_link" <<'PY' || fail "TX write"
import sys
path = sys.argv[1]
payload = bytes([
    0x00,
    0xA8, 0x8A, 0xA6, 0xA8, 0x40, 0x40, 0xE0,
    0x84, 0x86, 0xA0, 0xA4, 0x40, 0x40, 0x61,
    0x03, 0xF0,
]) + b"BCPR"
frame = b"\xC0" + payload + b"\xC0"
with open(path, "wb", buffering=0) as f:
    f.write(frame)
print("TX: wrote one KISS UI frame (%d bytes)" % len(frame))
PY
    ok "one KISS UI frame written (capped)"
    sleep 1
  fi
fi

stage "wait stop"
deadline=$((SECONDS_LIVE + 5))
elapsed=0
while kill -0 "$BCPRD_PID" 2>/dev/null; do
  if [[ "$elapsed" -ge "$deadline" ]]; then
    fail "bcprd still running after ${deadline}s — forcing stop"
    stop_bcprd
    break
  fi
  sleep 1
  elapsed=$((elapsed + 1))
done

set +e
wait "$BCPRD_PID" 2>/dev/null
rc=$?
set -e
if ! kill -0 "${BCPRD_PID:-}" 2>/dev/null; then
  ok "bcprd stopped (rc=$rc)"
  BCPRD_PID=""
else
  fail "bcprd still alive after wait"
fi

stage "summary"
if [[ "$ERR" -eq 0 ]]; then
  if [[ "$DO_TX" -eq 1 ]]; then
    ok "L0–L4 complete (live + TX)"
  else
    ok "L0–L3 complete (live RX, no TX)"
  fi
  exit 0
fi
fail "one or more stages failed"
exit 1
