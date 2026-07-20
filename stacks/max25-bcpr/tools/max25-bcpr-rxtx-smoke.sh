#!/usr/bin/env bash
# max25-bcpr-rxtx-smoke.sh — L0…L4 nofreeze prove-out (BayCom/based / max25-bcpr).
# Default: offline L0 only, NO TX. Live RX: --live. TX: --live --tx.
# No calibrate. No baycom_ser_fdx product path.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
CTL="$SCRIPT_DIR/max25-bcpr-ctl"
INI="${MAX25_BCPR_INI:-${BCPR_INI:-$ROOT/stacks/max25-bcpr/share/max25-bcpr.ini.example}}"
SECONDS_LIVE=15
TX_SECONDS=3
DO_LIVE=0
DO_TX=0
FORCE_TX=0
BUILD_DIR=""
BCPRD=""
TEST_HDLC=""
ERR=0
BCPRD_PID=""
OWNED_BCPRD=0
REUSE_STACK=0
RX_ACTIVITY=0

usage() {
  cat <<'USAGE'
Usage: max25-bcpr-rxtx-smoke.sh [-c ini] [--live] [--tx] [--force-tx] [--seconds N] [--tx-seconds N] [--build-dir DIR]
  L0 offline always. Soft L1 if probes safe. L2/L3 need --live. L4 needs --tx.
  --tx-seconds: target PTT key window (default 3; uses ~376B info ≈3s like proven inject).
  Default: NO TX. Hard time caps. Stop only max25-bcprd started by this script.
  §0.20: --tx requires RX/DCD activity in this run unless --force-tx (debug only).
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -c) INI="$2"; shift 2 ;;
    --live) DO_LIVE=1; shift ;;
    --tx) DO_TX=1; shift ;;
    --force-tx) FORCE_TX=1; shift ;;
    --seconds) SECONDS_LIVE="$2"; shift 2 ;;
    --tx-seconds) TX_SECONDS="$2"; shift 2 ;;
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
if [[ "$TX_SECONDS" -lt 1 ]]; then
  TX_SECONDS=1
fi
if [[ "$TX_SECONDS" -gt 12 ]]; then
  echo "WARN: capping --tx-seconds from $TX_SECONDS to 12"
  TX_SECONDS=12
fi

log() { printf '%s\n' "$*"; }
ok() { log "PASS: $*"; }
fail() { log "FAIL: $*"; ERR=1; }
stage() { log ""; log "=== $* ==="; }

# Attach window must cover TX key + settle (tx_delay + bursts).
need_live=$((TX_SECONDS + 5))
if [[ "$DO_TX" -eq 1 && "$SECONDS_LIVE" -lt "$need_live" ]]; then
  log "NOTE: raising --seconds from $SECONDS_LIVE to $need_live for --tx-seconds $TX_SECONDS"
  SECONDS_LIVE=$need_live
fi

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
    "$ROOT/build-max25-bcpr" \
    "$ROOT/build-max25-bcpr-${USER:-user}" \
    "/tmp/max25-build-max25-bcpr-${USER:-user}"; do
    if [[ -d "$cand" && -w "$cand" ]]; then
      echo "$cand"
      return
    fi
    if [[ ! -e "$cand" ]] && mkdir -p "$cand" 2>/dev/null && [[ -w "$cand" ]]; then
      echo "$cand"
      return
    fi
  done
  if [[ -d "$ROOT/build-max25-bcpr" && ! -w "$ROOT/build-max25-bcpr" ]]; then
    cand="$ROOT/build-max25-bcpr-${USER:-user}"
    mkdir -p "$cand"
    echo "$cand"
    return
  fi
  echo "$ROOT/build-max25-bcpr-${USER:-user}"
}

ensure_binaries() {
  local bd="$1"
  BCPRD="$bd/bin/max25-bcprd"
  TEST_HDLC="$bd/bin/test_hdlc_offline"
  if [[ -x "$BCPRD" && -x "$TEST_HDLC" ]]; then
    return 0
  fi
  # Also accept binaries from a default cmake build tree (opt-in ON only).
  local alt
  for alt in \
    "$ROOT/build/bin" \
    "$ROOT/build-default/bin" \
    "${BCPR_BUILD_DIR:-}/bin"; do
    if [[ -x "$alt/max25-bcprd" && -x "$alt/test_hdlc_offline" ]]; then
      BCPRD="$alt/max25-bcprd"
      TEST_HDLC="$alt/test_hdlc_offline"
      return 0
    fi
  done
  if [[ "${MAX25_BCPR_NO_AUTOBUILD:-0}" == "1" ]]; then
    log "SKIP: max25-bcprd not in build tree (MAX25_BCPR_NO_AUTOBUILD=1)"
    return 1
  fi
  log "Building max25-bcpr into $bd (MAX25_BUILD_MAX25_BCPR=ON)…"
  mkdir -p "$bd"
  cmake -S "$ROOT" -B "$bd" -DMAX25_BUILD_MAX25_BCPR=ON
  cmake --build "$bd" --target max25-bcprd test_hdlc_offline test_config_offline
  [[ -x "$BCPRD" && -x "$TEST_HDLC" ]]
}

stop_max25_bcprd() {
  # Only stop bcprd we started. Never blanket-pkill — max25d may own a live stack.
  if [[ -n "${KISS_HOLD_FD:-}" ]]; then
    eval "exec ${KISS_HOLD_FD}<&-" 2>/dev/null || true
    unset KISS_HOLD_FD
  fi
  if [[ "${OWNED_BCPRD:-0}" -ne 1 ]]; then
    BCPRD_PID=""
    return 0
  fi
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
  OWNED_BCPRD=0
}

trap 'stop_max25_bcprd' EXIT INT TERM

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
  ok "max25-bcprd --dry-run --once"
else
  fail "max25-bcprd --dry-run --once"
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
    ok "max25-bcpr-ctl preflight"
  else
    if [[ "$DO_LIVE" -eq 1 ]]; then
      fail "max25-bcpr-ctl preflight (required for --live)"
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
  log "WARN: --tx asserts PTT (~${TX_SECONDS}s key window; LED/wattmeter visible)"
fi

dry_val="$(awk -F= '
  $0 ~ /^\[/ { cur=$0; gsub(/[[:space:]]/,"",cur) }
  cur=="[max25-bcpr]" && $1 ~ /^[[:space:]]*dry_run[[:space:]]*$/ {
    v=$2; gsub(/^[[:space:]]+|[[:space:]]+$/,"",v); print tolower(v); exit
  }' "$INI")"
case "$dry_val" in
  yes|true|on|1)
    fail "live requires dry_run=no in $INI"
    exit 1
    ;;
esac

kiss_link="$(awk -F= '
  $0 ~ /^\[/ { cur=$0; gsub(/[[:space:]]/,"",cur) }
  cur=="[bc0]" && $1 ~ /^[[:space:]]*kiss_link[[:space:]]*$/ {
    v=$2; gsub(/^[[:space:]]+|[[:space:]]+$/,"",v); print v; exit
  }' "$INI")"
kiss_link="${kiss_link:-/tmp/max25-bcpr/kiss-bc0}"

iobase="$(awk -F= '
  $0 ~ /^\[/ { cur=$0; gsub(/[[:space:]]/,"",cur) }
  cur=="[bc0]" && $1 ~ /^[[:space:]]*iobase[[:space:]]*$/ {
    v=$2; gsub(/^[[:space:]]+|[[:space:]]+$/,"",v); print v; exit
  }' "$INI")"
iobase="${iobase:-0x3f8}"

export BCPRD
"$CTL" -c "$INI" preflight || { fail "preflight before attach"; exit 1; }

# Prefer live stack (max25d-owned bcprd) — proven KISS inject path.
# Starting a second bcprd races UART MCR and can yield no visible TX.
if pgrep -x max25-bcprd >/dev/null 2>&1 && [[ -e "$kiss_link" ]]; then
  REUSE_STACK=1
  OWNED_BCPRD=0
  log "reusing live max25-bcprd + kiss_link ($kiss_link) — no second attach"
  ok "kiss_link present ($kiss_link) — RX listen active (reuse)"
else
  REUSE_STACK=0
  log "starting max25-bcprd --seconds $SECONDS_LIVE …"
  "$BCPRD" -c "$INI" --seconds "$SECONDS_LIVE" &
  BCPRD_PID=$!
  OWNED_BCPRD=1

  waited=0
  while [[ "$waited" -lt 5 ]]; do
    if [[ -e "$kiss_link" ]] || ! kill -0 "$BCPRD_PID" 2>/dev/null; then
      break
    fi
    sleep 0.5
    waited=$((waited + 1))
  done

  if ! kill -0 "$BCPRD_PID" 2>/dev/null; then
    fail "max25-bcprd exited early (attach)"
    wait "$BCPRD_PID" || true
    BCPRD_PID=""
    OWNED_BCPRD=0
    exit 1
  fi

  if [[ -e "$kiss_link" ]]; then
    ok "kiss_link present ($kiss_link) — RX listen active"
  else
    log "WARN: kiss_link not yet visible — continuing timed run"
  fi
  # Hold KISS slave open — without a peer, POLLHUP drops TX before MCR keys.
  exec {KISS_HOLD_FD}<>"$kiss_link" || true
fi

# Also hold when reusing (max25d already holds; extra open is harmless).
if [[ "$REUSE_STACK" -eq 1 && -e "$kiss_link" && -z "${KISS_HOLD_FD:-}" ]]; then
  exec {KISS_HOLD_FD}<>"$kiss_link" || true
fi

state_dir="$(dirname "$kiss_link")"
rm -f "${state_dir}/rx-activity-bc0" "${state_dir}/rx-activity-bc1" 2>/dev/null || true

poll_rx_activity() {
  local f
  for f in "${state_dir}/dcd-bc0" "${state_dir}/dcd-bc1" \
           "${state_dir}/rx-activity-bc0" "${state_dir}/rx-activity-bc1"; do
    if [[ -f "$f" ]] && grep -qE 'dcd=1|rx_activity=1' "$f" 2>/dev/null; then
      RX_ACTIVITY=1
      return 0
    fi
  done
  return 1
}

stage "L3 RX prove (${SECONDS_LIVE}s)"
log "listening for Soft-DCD/noise (dcd-bc* / rx-activity-bc*)…"
elapsed=0
while [[ "$elapsed" -lt "$SECONDS_LIVE" ]]; do
  poll_rx_activity || true
  if [[ "$REUSE_STACK" -eq 0 ]] && ! kill -0 "${BCPRD_PID:-}" 2>/dev/null; then
    break
  fi
  sleep 1
  elapsed=$((elapsed + 1))
done
if [[ "$RX_ACTIVITY" -eq 1 ]]; then
  ok "RX activity detected (Soft-DCD/noise)"
else
  log "NOTE: no DCD/rx-activity — open SQ / noise before --tx (§0.20)"
fi

# §0.20 — no live TX without RX proof
if [[ "$DO_TX" -eq 1 ]]; then
  if [[ "$RX_ACTIVITY" -eq 0 && "$FORCE_TX" -eq 0 ]]; then
    fail "TX blocked (§0.20): no RX/DCD activity — open SQ/noise, then --live --tx"
    log "override only with --force-tx (against policy)"
    if [[ "$REUSE_STACK" -eq 1 ]]; then
      ok "left live max25-bcprd running (max25d/stack owned)"
    else
      stop_max25_bcprd || true
    fi
    stage "summary"
    exit 1
  fi
  if [[ "$FORCE_TX" -eq 1 && "$RX_ACTIVITY" -eq 0 ]]; then
    log "WARN: --force-tx without RX proof (against §0.20 policy)"
  fi
fi

if [[ "$DO_TX" -eq 1 ]]; then
  stage "L4 TX (~${TX_SECONDS}s PTT / MCR)"
  if [[ ! -e "$kiss_link" ]]; then
    fail "no kiss_link for TX"
  else
    if [[ -z "${KISS_HOLD_FD:-}" ]]; then
      exec {KISS_HOLD_FD}<>"$kiss_link" || true
    fi
    if python3 - "$kiss_link" "$iobase" "$TX_SECONDS" <<'PY'
import os, sys, threading, time

path, iobase_s, tx_sec_s = sys.argv[1], sys.argv[2], sys.argv[3]
tx_sec = max(1, int(tx_sec_s))
iobase = int(iobase_s, 0)
mcr_port = iobase + 4  # UART MCR

REF_INFO, REF_MS = 376, 3005
MAX_INFO = 376

def call_addr(call, ssid, last=False):
    call = call.upper().ljust(6)[:6]
    b = bytes([(ord(c) << 1) & 0xFF for c in call])
    ssid_byte = 0x60 | ((ssid & 0x0F) << 1)
    if last:
        ssid_byte |= 0x01
    return b + bytes([ssid_byte])

def kiss_frame(info: bytes) -> bytes:
    body = call_addr("QST", 0) + call_addr("CB-0", 0, last=True) + bytes([0x03, 0xF0]) + info
    return b"\xC0\x00" + body + b"\xC0"

def read_mcr(fd):
    os.lseek(fd, mcr_port, os.SEEK_SET)
    return ord(os.read(fd, 1))

def mcr_keyed(v):
    return (v & 0x02) != 0

def monitor_mcr(fd, duration, sample_ms=4):
    t0 = time.monotonic()
    first = last = None
    vals = set()
    while time.monotonic() - t0 < duration:
        v = read_mcr(fd)
        if mcr_keyed(v):
            vals.add(v)
            now = time.monotonic()
            if first is None:
                first = now
            last = now
        time.sleep(sample_ms / 1000.0)
    keyed_ms = 0.0 if first is None else (last - first) * 1000.0
    return keyed_ms, vals

remaining_ms = tx_sec * 1000
bursts = 0
total_keyed = 0.0
all_vals = set()
port_fd = os.open("/dev/port", os.O_RDONLY)

try:
    while remaining_ms > 200:
        info_len = min(MAX_INFO, max(32, int(remaining_ms * REF_INFO / REF_MS)))
        expect_ms = info_len * REF_MS / REF_INFO
        mon_s = expect_ms / 1000.0 + 1.5
        info = (b"TXRX" + b"X" * info_len)[:info_len]
        frame = kiss_frame(info)
        box = {}

        def run():
            box["m"] = monitor_mcr(port_fd, mon_s)

        t = threading.Thread(target=run)
        t.start()
        time.sleep(0.12)
        f = open(path, "r+b", buffering=0)
        try:
            f.write(frame)
            t.join()
        finally:
            f.close()
        km, kvals = box["m"]
        bursts += 1
        total_keyed += km
        all_vals |= kvals
        kv = ",".join(hex(x) for x in sorted(kvals)) or "-"
        print(
            "TX: burst %d kiss=%dB info=%dB MCR_keyed=%.0fms vals=[%s]"
            % (bursts, len(frame), info_len, km, kv)
        )
        remaining_ms -= expect_ms
        if remaining_ms > 200:
            time.sleep(0.4)
finally:
    os.close(port_fd)

lo = tx_sec * 1000 * 0.55
hi = tx_sec * 1000 * 1.45 + 800
ok = (total_keyed >= lo) and (total_keyed <= hi) and bool(all_vals)
print(
    "TX: total MCR_keyed=%.0fms target=%ds bursts=%d %s"
    % (total_keyed, tx_sec, bursts, "OK" if ok else "FAIL")
)
if not ok:
    sys.exit(1)
PY
    then
      ok "L4 TX MCR keyed (~${TX_SECONDS}s target)"
    else
      fail "L4 TX — no/short MCR key (check fulldup, stack, /dev/port)"
    fi
  fi
fi

if [[ "$REUSE_STACK" -eq 1 ]]; then
  stage "reuse settle"
  ok "left live max25-bcprd running (max25d/stack owned)"
else
  stage "wait stop"
  deadline=5
  elapsed=0
  while kill -0 "${BCPRD_PID:-}" 2>/dev/null; do
    if [[ "$elapsed" -ge "$deadline" ]]; then
      fail "max25-bcprd still running after ${deadline}s — forcing stop"
      stop_max25_bcprd
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
    ok "max25-bcprd stopped (rc=$rc)"
    BCPRD_PID=""
    OWNED_BCPRD=0
  else
    fail "max25-bcprd still alive after wait"
  fi
fi

stage "summary"
if [[ "$ERR" -eq 0 ]]; then
  if [[ "$DO_TX" -eq 1 ]]; then
    ok "L0–L4 complete (live + TX; RX proven)"
  else
    ok "L0–L3 complete (live RX, no TX)"
  fi
  exit 0
fi
fail "one or more stages failed"
exit 1
