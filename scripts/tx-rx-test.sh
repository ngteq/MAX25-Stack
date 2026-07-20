#!/usr/bin/env bash
# tx-rx-test.sh — unified TX/RX release test (BayCom/based bcpr + classic TNC).
# Default: L0 offline only (CI / make test). Live/TX are operator-gated.
# Public: BayCom/based / max25-bcpr. Never Konverter/converter.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LEVEL=0
DEVICE=all   # all | modem | tnc
DO_LIVE=0
DO_TX=0
FORCE_TX=0
SECONDS_LIVE=15
TX_SECONDS=3
BCPR_INI="${BCPR_INI:-$ROOT/stacks/max25-bcpr/share/max25-bcpr.ini.example}"
SOCK="${MAX25_SOCK:-/run/max25/modem.sock}"
ERR=0

usage() {
  cat <<'USAGE'
Usage: tx-rx-test.sh [--level N] [--device all|modem|tnc] [--live] [--tx] [--seconds N] [--tx-seconds N] [-c bcpr.ini]

  L0  offline TX/RX proofs (default) — CI / release-check / ctest
  L1  soft preflight (no attach / no RF)
  L2  live attach (modem: max25-bcprd timed; tnc: max25d sock status)
  L3  live RX listen (same as L2 + RX readiness)
  L4  TX (--tx required; PTT / RF risk; default ~3s MCR key)

  --live implies at least L2. --tx requires --live (L4).
  --tx-seconds: modem PTT key target (default 3; proven ≈376B info).
  Default: NO TX. Hard time caps. Safe for make test / CI.

  Static rule (§0.20): live --tx is refused unless RX was detected in this
  run (modem: Soft-DCD/noise → state_dir/dcd-bc* or rx-activity-bc*;
  TNC: live CONNECT/RX path OK first). Override only with --force-tx
  (against policy — debug only).
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --level) LEVEL="$2"; shift 2 ;;
    --device) DEVICE="$2"; shift 2 ;;
    --live) DO_LIVE=1; shift ;;
    --tx) DO_TX=1; shift ;;
    --force-tx) FORCE_TX=1; shift ;;
    --seconds) SECONDS_LIVE="$2"; shift 2 ;;
    --tx-seconds) TX_SECONDS="$2"; shift 2 ;;
    -c) BCPR_INI="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "ERROR: unknown arg: $1"; usage; exit 2 ;;
  esac
done

case "$DEVICE" in
  all|modem|tnc) ;;
  *) echo "ERROR: --device must be all|modem|tnc"; exit 2 ;;
esac

if [[ "$DO_TX" -eq 1 && "$DO_LIVE" -eq 0 ]]; then
  echo "ERROR: --tx requires --live"
  exit 2
fi

if [[ "$DO_LIVE" -eq 1 && "$LEVEL" -lt 2 ]]; then
  LEVEL=2
fi
if [[ "$DO_TX" -eq 1 ]]; then
  LEVEL=4
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
need_live=$((TX_SECONDS + 5))
if [[ "$DO_TX" -eq 1 && "$SECONDS_LIVE" -lt "$need_live" ]]; then
  echo "NOTE: raising --seconds from $SECONDS_LIVE to $need_live for --tx-seconds $TX_SECONDS"
  SECONDS_LIVE=$need_live
fi

log() { printf '%s\n' "$*"; }
ok() { log "PASS: $*"; }
fail() { log "FAIL: $*"; ERR=1; }
stage() { log ""; log "=== $* ==="; }
want_modem() { [[ "$DEVICE" == "all" || "$DEVICE" == "modem" ]]; }
want_tnc() { [[ "$DEVICE" == "all" || "$DEVICE" == "tnc" ]]; }

run_l0() {
  stage "L0 offline TX/RX"
  if python3 stacks/daemon/test_tx_rx_offline.py; then
    ok "test_tx_rx_offline (TNC + bcpr host)"
  else
    fail "test_tx_rx_offline"
  fi

  if want_tnc; then
    if python3 stacks/tncs/test_tnc_serial_recovery.py >/dev/null; then
      ok "tnc serial recovery unit"
    else
      fail "tnc serial recovery unit"
    fi
    if python3 stacks/daemon/test_kiss_bridge.py >/dev/null; then
      ok "kiss_bridge unit (TNC KISS)"
    else
      fail "kiss_bridge unit"
    fi
  fi

  if want_modem; then
    if [[ -x stacks/max25-bcpr/tools/max25-bcpr-rxtx-smoke.sh ]]; then
      if bash stacks/max25-bcpr/tools/max25-bcpr-rxtx-smoke.sh -c "$BCPR_INI"; then
        ok "max25-bcpr-rxtx-smoke L0 (BayCom/based)"
      else
        fail "max25-bcpr-rxtx-smoke L0"
      fi
    else
      fail "max25-bcpr-rxtx-smoke.sh missing"
    fi
  fi
}

run_l1() {
  stage "L1 soft preflight"
  if want_modem; then
    if [[ -x stacks/max25-bcpr/tools/max25-bcpr-ctl ]]; then
      set +e
      stacks/max25-bcpr/tools/max25-bcpr-ctl -c "$BCPR_INI" preflight
      pf_rc=$?
      set -e
      if [[ "$pf_rc" -eq 0 ]]; then
        ok "max25-bcpr-ctl preflight"
      else
        if [[ "$DO_LIVE" -eq 1 ]]; then
          fail "max25-bcpr-ctl preflight (required for --live modem)"
        else
          log "NOTE: bcpr preflight rc=$pf_rc — soft at L1 without --live"
        fi
      fi
    else
      fail "max25-bcpr-ctl missing"
    fi
  fi
  if want_tnc; then
    if [[ -f share/clients/tnc2c.yaml ]] && [[ -f stacks/tncs/tnc_serial_recovery.py ]]; then
      ok "tnc client profile + recovery module present"
    else
      fail "tnc profile/recovery missing"
    fi
  fi
}

live_tnc_sock() {
  local mode="$1"  # rx|tx
  local sock="$SOCK"
  if [[ ! -S "$sock" ]]; then
    if [[ -S /tmp/max25/modem.sock ]]; then
      sock=/tmp/max25/modem.sock
    else
      fail "no max25d unix socket ($SOCK) — start max25d with TNC first"
      return 1
    fi
  fi
  log "using unix socket $sock (mode=$mode)"
  python3 - "$sock" "$mode" <<'PY' || return 1
import socket, sys, time

sock_path, mode = sys.argv[1], sys.argv[2]

class LineReader:
    def __init__(self, s):
        self.s = s
        self.buf = b""
    def read(self, timeout=8.0):
        self.s.settimeout(timeout)
        while b"\n" not in self.buf:
            chunk = self.s.recv(4096)
            if not chunk:
                raise RuntimeError("connection closed")
            self.buf += chunk
        line, self.buf = self.buf.split(b"\n", 1)
        return line.decode("utf-8", errors="replace")

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect(sock_path)
r = LineReader(s)
hello = r.read()
assert hello == "OK", hello
status = r.read()
assert status.startswith("STATUS "), status
s.sendall(b"CONNECT\n")
ev = r.read()
assert ev == "EVENT connected", ev
assert r.read() == "OK"
if mode == "tx":
    s.sendall(b"SEND TXRXTEST\n")
    rx = r.read()
    assert rx.startswith("RX "), rx
    assert r.read() == "OK"
    print("TNC live TX: SEND OK (host path)")
else:
    # RX readiness: connected + status shows device
    s.sendall(b"GET STATUS\n")
    st = r.read()
    assert "device=" in st, st
    assert r.read() == "OK"
    print("TNC live RX: CONNECT + STATUS OK (listen ready)")
s.close()
PY
}

run_live() {
  stage "L2/L3 live (${SECONDS_LIVE}s) device=$DEVICE"
  if want_modem; then
    local smoke_args=(-c "$BCPR_INI" --live --seconds "$SECONDS_LIVE")
    if [[ "$DO_TX" -eq 1 ]]; then
      smoke_args+=(--tx --tx-seconds "$TX_SECONDS")
      if [[ "${FORCE_TX:-0}" -eq 1 ]]; then
        smoke_args+=(--force-tx)
      fi
      log "WARN: modem --tx asserts PTT (~${TX_SECONDS}s; watch LED/wattmeter) — only after RX (§0.20)"
    fi
    if bash stacks/max25-bcpr/tools/max25-bcpr-rxtx-smoke.sh "${smoke_args[@]}"; then
      ok "bcpr live smoke (BayCom/based)"
    else
      fail "bcpr live smoke"
    fi
  fi
  if want_tnc; then
    local TNC_RX_OK=0
    if live_tnc_sock rx; then
      ok "tnc live CONNECT (RX ready)"
      TNC_RX_OK=1
    else
      fail "tnc live CONNECT"
    fi
    if [[ "$DO_TX" -eq 1 ]]; then
      if [[ "$TNC_RX_OK" -ne 1 && "${FORCE_TX:-0}" -eq 0 ]]; then
        fail "TNC TX blocked (§0.20): RX/CONNECT failed"
      else
        log "WARN: TNC --tx sends one UI frame over air if radio keyed"
        if live_tnc_sock tx; then
          ok "tnc live CONNECT+SEND"
        else
          fail "tnc live CONNECT+SEND"
        fi
      fi
    fi
  fi
}

# --- main ---
log "tx-rx-test level=$LEVEL device=$DEVICE live=$DO_LIVE tx=$DO_TX tx_seconds=$TX_SECONDS"
run_l0

if [[ "$LEVEL" -ge 1 ]]; then
  run_l1
fi

if [[ "$LEVEL" -ge 2 || "$DO_LIVE" -eq 1 ]]; then
  run_live
fi

stage "summary"
if [[ "$ERR" -eq 0 ]]; then
  if [[ "$DO_TX" -eq 1 ]]; then
    ok "TX/RX complete through L4 (live + TX)"
  elif [[ "$DO_LIVE" -eq 1 ]]; then
    ok "TX/RX complete through L2/L3 (live RX, no TX)"
  elif [[ "$LEVEL" -ge 1 ]]; then
    ok "TX/RX L0+L1 complete"
  else
    ok "TX/RX L0 offline complete — use --live / --tx for hardware"
  fi
  exit 0
fi
fail "one or more stages failed"
exit 1
