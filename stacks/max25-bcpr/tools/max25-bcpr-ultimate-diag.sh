#!/usr/bin/env bash
# max25-bcpr-ultimate-diag.sh — interactive BayCom/based (bcpr) TX/RX diagnostic ladder
# Public mark: BayCom/based. Internal path: max25-bcpr. Never Konverter/converter.
# Target: AX25WRK1 intermittent "host keys, RF sometimes" (mic OK 4W; host MCR OK).
#
# Soft-TNC RE (2026-07-19) — operator warnings only (no MCR/code patch here):
#   • FlexNet SER12 cal PTT watchdog: ~14.5 s keyed → ~500 ms unkey (discharge).
#     Long continuous force-tx/cal: max25-bcprd ptt_wd drops RTS ~500 ms every ~14.5 s
#     (FlexNet SER12 mirror; disable with ptt_wd=no / --no-ptt-wd).
#   • TXD: default pulse THR 0x00; experiment txd_bias=steady (UART break ≈ TFPCX).
#   • Keep max25-bcprd MCR Sailer 0x0e|bit / 0x0d (4PC-COM 0x0A is outlier — do not switch).
#
# Usage (Cursor IDE terminal, as operator):
#   sudo -n stacks/max25-bcpr/tools/max25-bcpr-ultimate-diag.sh
#   MAX25_BCPR_INI=/etc/max25/max25-bcpr.ini ./max25-bcpr-ultimate-diag.sh -c /etc/max25/max25-bcpr.ini
#   ./max25-bcpr-ultimate-diag.sh --help
#   ./max25-bcpr-ultimate-diag.sh --all          # run phases 1–9 with pauses
#   ./max25-bcpr-ultimate-diag.sh --menu         # interactive menu (default)
#
# Needs: /usr/bin/sudo -n for ioport / live smoke / cal. Does NOT change MCR code.
# Does NOT use USB as product TX path. Does NOT kill max25d carelessly.
#
# Relies on: max25-bcpr-ctl, max25-bcpr-rxtx-smoke.sh (same directory).

# Note: interactive prompts use read; keep pipefail but relax -e around optional probes.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." 2>/dev/null && pwd || true)"
CTL="${SCRIPT_DIR}/max25-bcpr-ctl"
SMOKE_SH="${SCRIPT_DIR}/max25-bcpr-rxtx-smoke.sh"
INI="${MAX25_BCPR_INI:-/etc/max25/max25-bcpr.ini}"
SUDO="/usr/bin/sudo"
LOG=""
MODE="menu"   # menu | all | phaseN
PHASE_ONLY=""
RUN_TS=""

# Result arrays for summary (parallel indices)
declare -a RES_PHASE=()
declare -a RES_HOST=()
declare -a RES_WATT=()
declare -a RES_BLED=()
declare -a RES_RDISP=()
declare -a RES_NOTE=()

usage() {
  cat <<'USAGE'
max25-bcpr-ultimate-diag.sh — BayCom/based (bcpr) interactive diagnostic / force-TX ladder

Usage:
  max25-bcpr-ultimate-diag.sh [-c INI] [--menu|--all|--phase N] [--help]

Options:
  -c INI       bcpr.ini (default: $MAX25_BCPR_INI or /etc/max25/max25-bcpr.ini)
  --menu       interactive German menu (default)
  --all        run phases 1–9 linearly with pauses + RF prompts
  --phase N    run a single phase (1–9, or 0=restart menu)
  -h, --help   this help

Environment:
  MAX25_BCPR_INI     same as -c
  BCPRD        optional path to max25-bcprd binary

Phases:
  1 Preflight (ttyS0, fuser, dosbox-x, max25-bcprd/max25d, INI, locks)
  2 Idle MCR sample via /dev/port
  3 max25-bcpr-ctl status + telem (tx-last / dcd / rx-activity)
  4 RX listen (soft-DCD) — open SQ reminder
  5 Force-TX ladder 1s / 3s / 5s / 8s + wattmeter/LED/display prompts
  6 Cal/high (max25-bcprd --cal high) if binary supports it
  7 Double-burst / back-to-back TX
  8 Contact hunt (DE-9 + 3.5mm) + 5s force-tx + wiggle
  9 Summary table + verdict hints
  0 Optional safe max25-bcprd restart (max25-bcpr-ctl stop/start only)
  U USB note (SER12 unsupported on USB — not product TX)

Log: /tmp/max25-bcpr-ultimate-diag-YYYYMMDD-HHMMSS.log

Examples:
  sudo -n stacks/max25-bcpr/tools/max25-bcpr-ultimate-diag.sh --all
  MAX25_BCPR_INI=/etc/max25/max25-bcpr.ini sudo -n ./max25-bcpr-ultimate-diag.sh --menu
USAGE
}

# ---------- logging / UI ----------

log() {
  local line
  line="$(printf '%s' "$*")"
  printf '%s\n' "$line"
  if [[ -n "${LOG:-}" ]]; then
    printf '%s\n' "$line" >>"$LOG"
  fi
}

log_raw() {
  # stdin → stdout + log
  if [[ -n "${LOG:-}" ]]; then
    tee -a "$LOG"
  else
    cat
  fi
}

banner() {
  log ""
  log "════════════════════════════════════════════════════════════"
  log "$*"
  log "════════════════════════════════════════════════════════════"
}

pause_enter() {
  local msg="${1:-Weiter mit Enter …}"
  printf '\n%s ' "$msg" >/dev/tty
  # shellcheck disable=SC2034
  local _dummy
  read -r _dummy </dev/tty || true
  log "[pause] $msg"
}

ask() {
  # ask VAR "prompt"
  local __var="$1"
  local __prompt="$2"
  local __ans=""
  printf '%s ' "$__prompt" >/dev/tty
  read -r __ans </dev/tty || true
  printf -v "$__var" '%s' "$__ans"
  log "[antwort] $__prompt → ${__ans}"
}

ask_yn() {
  # ask_yn VAR "prompt"  → stores j/n/y/n normalized to j|n
  local __var="$1"
  local __prompt="$2"
  local __ans=""
  while true; do
    printf '%s [j/n]: ' "$__prompt" >/dev/tty
    read -r __ans </dev/tty || true
    case "${__ans,,}" in
      j|ja|y|yes) printf -v "$__var" 'j'; log "[antwort] $__prompt → j"; return 0 ;;
      n|nein|no)  printf -v "$__var" 'n'; log "[antwort] $__prompt → n"; return 0 ;;
      *) printf 'Bitte j oder n.\n' >/dev/tty ;;
    esac
  done
}

record_result() {
  local phase="$1" host="$2" watt="$3" bled="$4" rdisp="$5" note="${6:-}"
  RES_PHASE+=("$phase")
  RES_HOST+=("$host")
  RES_WATT+=("$watt")
  RES_BLED+=("$bled")
  RES_RDISP+=("$rdisp")
  RES_NOTE+=("$note")
}

need_sudo() {
  if [[ ! -x "$SUDO" ]]; then
    log "FEHLER: $SUDO fehlt — Live-Phasen brauchen sudo."
    return 1
  fi
  if ! "$SUDO" -n true 2>/dev/null; then
    log "FEHLER: sudo -n fehlgeschlagen."
    log "  Bitte einmalig: sudo -v   (oder NOPASSWD für diesen User)"
    log "  Dann Skript erneut starten."
    return 1
  fi
  return 0
}

run_sudo() {
  need_sudo || return 1
  "$SUDO" -n "$@"
}

ini_get() {
  local section="$1" key="$2"
  [[ -f "$INI" ]] || return 0
  awk -F= -v s="[$section]" -v k="$key" '
    $0 ~ /^\[/ { cur=$0; gsub(/[[:space:]]/,"",cur) }
    cur==s && $1 ~ "^[[:space:]]*"k"[[:space:]]*$" {
      v=$2; gsub(/^[[:space:]]+|[[:space:]]+$/,"",v); print v; exit
    }' "$INI" 2>/dev/null || true
}

resolve_max25-bcprd() {
  if [[ -n "${BCPRD:-}" && "$BCPRD" != "max25-bcprd" && -x "$BCPRD" ]]; then
    printf '%s\n' "$BCPRD"; return 0
  fi
  if command -v max25-bcprd >/dev/null 2>&1; then
    command -v max25-bcprd; return 0
  fi
  local cand
  for cand in \
    "${BCPR_BUILD_DIR:-}/bin/max25-bcprd" \
    "${ROOT}/build-max25-bcpr/bin/max25-bcprd" \
    "${ROOT}/build-max25-bcpr-${USER:-user}/bin/max25-bcprd" \
    "/tmp/max25-build-max25-bcpr-${USER:-user}/bin/max25-bcprd" \
    "${ROOT}/build/bin/max25-bcprd" \
    /usr/local/bin/max25-bcprd /usr/bin/max25-bcprd; do
    [[ -n "$cand" && -x "$cand" ]] && { printf '%s\n' "$cand"; return 0; }
  done
  return 1
}

serial_dev() {
  local s
  s="$(ini_get bc0 serial)"
  printf '%s\n' "${s:-/dev/ttyS0}"
}

state_dir() {
  local sd
  sd="$(ini_get bcpr state_dir)"
  printf '%s\n' "${sd:-/tmp/bcpr}"
}

iobase_val() {
  local b
  b="$(ini_get bc0 iobase)"
  printf '%s\n' "${b:-0x3f8}"
}

ensure_tools() {
  local err=0
  if [[ ! -x "$CTL" ]]; then
    log "FEHLER: max25-bcpr-ctl fehlt: $CTL"; err=1
  fi
  if [[ ! -x "$SMOKE_SH" ]]; then
    log "FEHLER: max25-bcpr-rxtx-smoke.sh fehlt: $SMOKE_SH"; err=1
  fi
  return "$err"
}

# ---------- Phase helpers ----------

# Last smoke host result (PASS|FAIL) — do not capture function stdout (log noise).
_LAST_HOST="—"

smoke_force_tx() {
  # smoke_force_tx SECONDS → sets _LAST_HOST
  local secs="$1"
  local listen=$((secs + 8))
  local rc=0
  [[ "$listen" -lt 12 ]] && listen=12
  log "→ L4 force-tx ${secs}s (smoke --live --tx --force-tx --tx-seconds ${secs})"
  run_sudo "$CTL" -c "$INI" smoke --live --tx --force-tx --seconds "$listen" --tx-seconds "$secs" 2>&1 | log_raw
  rc=${PIPESTATUS[0]}
  if [[ "$rc" -eq 0 ]]; then
    _LAST_HOST="PASS"
    log "HOST: PASS (MCR keyed ~${secs}s target)"
  else
    _LAST_HOST="FAIL"
    log "HOST: FAIL (smoke rc=$rc)"
  fi
}

prompt_rf_obs() {
  # prompt_rf_obs PHASE_LABEL HOST_RESULT
  # sets globals: _watt _bled _rdisp _extra
  local label="$1" host="$2"
  local watt bled rdisp extra
  log ""
  log "--- RF-Beobachtung: $label (Host=$host) ---"
  log "Bitte Wattmeter / Board-LED / Radio-Display während des Keys prüfen."
  ask watt "Wattmeter W (Zahl oder 0 / ?):"
  ask_yn bled "Board-LED (PC-COM) an während Key?"
  ask_yn rdisp "Radio-Display / TX-Anzeige an?"
  ask extra "Kurznotiz (Enter = keine):"
  _watt="$watt"
  _bled="$bled"
  _rdisp="$rdisp"
  _extra="$extra"
  record_result "$label" "$host" "$watt" "$bled" "$rdisp" "$extra"
}

# ---------- Phases ----------

phase_preflight() {
  banner "Phase 1 — Preflight"
  local serial sd iobase irq fulldup dry
  serial="$(serial_dev)"
  sd="$(state_dir)"
  iobase="$(iobase_val)"
  irq="$(ini_get bc0 irq)"
  fulldup="$(ini_get bc0 fulldup)"
  dry="$(ini_get bcpr dry_run)"

  log "INI: $INI"
  if [[ ! -f "$INI" ]]; then
    log "FEHLER: INI fehlt: $INI"
    log "  Hinweis: Beispiel → stacks/max25-bcpr/share/bcpr.ini.example → /etc/max25/max25-bcpr.ini"
    return 1
  fi

  log "--- INI Auszug [bcpr]/[bc0] ---"
  log "  dry_run=${dry:-?}  state_dir=${sd}"
  log "  serial=${serial}  iobase=${iobase}  irq=${irq:-?}  fulldup=${fulldup:-?}"
  log "  mode=$(ini_get bc0 mode)  kiss_link=$(ini_get bc0 kiss_link)"
  log "  baud=$(ini_get bc0 baud)  tx_delay=$(ini_get bc0 tx_delay)"

  log "--- Seriell ---"
  if [[ -e "$serial" ]]; then
    log "OK: $serial existiert"
    ls -l "$serial" 2>&1 | log_raw || true
  else
    log "FEHLER: $serial fehlt"
  fi

  log "--- fuser / lsof (wer hält Port?) ---"
  if command -v fuser >/dev/null 2>&1; then

    run_sudo fuser -v "$serial" 2>&1 | log_raw

  else
    log "WARN: fuser nicht installiert"
  fi
  if command -v lsof >/dev/null 2>&1; then

    run_sudo lsof "$serial" 2>&1 | log_raw

  fi

  log "--- dosbox-x / DOS-Gast ---"
  if pgrep -a -f 'dosbox-x|dosbox' 2>/dev/null | log_raw; then
    log "WARN: dosbox läuft — kann ttyS0/USB belegen (sniff/passthrough)."
  else
    log "OK: kein dosbox/dosbox-x Prozess"
  fi

  log "--- Prozesse max25-bcprd / max25d ---"
  pgrep -a -x max25-bcprd 2>/dev/null | log_raw || log "  max25-bcprd: nicht laufend"
  pgrep -a -x max25d 2>/dev/null | log_raw || log "  max25d: nicht laufend"
  # wrapper scripts
  pgrep -a -f 'run-max25d|max25d' 2>/dev/null | head -20 | log_raw || true

  log "--- Lock / State ($sd) ---"
  if [[ -d "$sd" ]]; then
    ls -la "$sd" 2>&1 | log_raw || true
    for f in "$sd"/lock* "$sd"/*.lock "$sd"/max25-bcprd.pid; do
      [[ -e "$f" ]] || continue
      log "  lock/pid: $f"
      [[ -f "$f" ]] && { log "    content:"; cat "$f" 2>&1 | log_raw || true; }
    done
  else
    log "WARN: state_dir fehlt: $sd"
  fi

  log "--- Kernel baycom_* Module (sollten NICHT geladen sein) ---"
  if command -v lsmod >/dev/null 2>&1; then
    lsmod 2>/dev/null | awk '/^baycom_/ {print}' | log_raw || log "OK: keine baycom_* Module"
  fi

  log "--- setserial (falls vorhanden) ---"
  local ss
  for ss in /usr/bin/setserial /bin/setserial /sbin/setserial /usr/sbin/setserial; do
    if [[ -x "$ss" ]]; then

      run_sudo "$ss" -g "$serial" 2>&1 | log_raw

      break
    fi
  done

  log "--- max25-bcpr-ctl preflight ---"

  run_sudo "$CTL" -c "$INI" preflight 2>&1 | log_raw
  local pf=$?

  if [[ "$pf" -eq 0 ]]; then
    log "OK: preflight PASS"
  else
    log "WARN: preflight rc=$pf (Port busy wenn Stack läuft — normal bei live max25d/max25-bcprd)"
  fi

  log "--- Tools ---"
  log "  CTL=$CTL"
  log "  SMOKE=$SMOKE_SH"
  local bin
  if bin="$(resolve_max25-bcprd)"; then
    log "  max25-bcprd=$bin"
  else
    log "  WARN: max25-bcprd Binary nicht gefunden (Build: -DMAX25_BUILD_BCPR=ON)"
  fi

  pause_enter "Phase 1 fertig — Enter für weiter …"
  return 0
}

phase_idle_mcr() {
  banner "Phase 2 — Idle MCR Sample (/dev/port)"
  local iobase mcr_off
  iobase="$(iobase_val)"
  # MCR = iobase+4
  mcr_off=$((iobase + 4))
  log "iobase=$iobase  MCR=$(printf '0x%x' "$mcr_off") (iobase+4)"
  log "Erwartung Idle (Sailer/bcpr): oft 0x0d (DTR+OUT2+RTS-clear) — Werte nur Info."

  if ! need_sudo; then
    log "überspringe MCR-Sample (kein sudo)"
    pause_enter
    return 0
  fi

  run_sudo python3 - "$iobase" <<'PY' 2>&1 | log_raw
import os, sys, time
iobase = int(sys.argv[1], 0)
mcr = iobase + 4
fd = os.open("/dev/port", os.O_RDONLY)
try:
    vals = []
    for i in range(20):
        os.lseek(fd, mcr, os.SEEK_SET)
        v = ord(os.read(fd, 1))
        vals.append(v)
        time.sleep(0.05)
    uniq = sorted(set(vals))
    print("Idle MCR samples (20×50ms): " + ",".join("0x%02x" % v for v in vals))
    print("Unique: " + ",".join("0x%02x" % v for v in uniq))
    rts = [(v & 0x02) != 0 for v in vals]
    print("RTS asserted in any sample: %s" % ("YES" if any(rts) else "no"))
    if all(v == 0 for v in vals):
        print("WARN: all-zero — /dev/port may be inaccessible or wrong iobase")
finally:
    os.close(fd)
PY
  local rc=$?

  if [[ "$rc" -ne 0 ]]; then
    log "WARN: Idle-MCR Sample fehlgeschlagen (rc=$rc) — CAP_SYS_RAWIO / iobase prüfen"
  fi
  pause_enter "Phase 2 fertig — Enter …"
  return 0
}

phase_status() {
  banner "Phase 3 — Status + Telemetrie"

  run_sudo "$CTL" -c "$INI" status 2>&1 | log_raw

  local sd
  sd="$(state_dir)"
  log "--- Telemetrie unter $sd ---"
  for f in "$sd"/tx-last-bc* "$sd"/dcd-bc* "$sd"/rx-activity-bc* "$sd"/kiss-bc*; do
    [[ -e "$f" ]] || continue
    log "FILE: $f"
    if [[ -L "$f" ]]; then
      log "  symlink → $(readlink -f "$f" 2>/dev/null || readlink "$f")"
    elif [[ -f "$f" ]]; then
      cat "$f" 2>&1 | log_raw || true
    fi
  done
  pause_enter "Phase 3 fertig — Enter …"
  return 0
}

phase_rx_listen() {
  banner "Phase 4 — RX Listen (soft-DCD)"
  log "OPERATOR: Squellch öffnen / Rauschen/SQ so dass Soft-DCD aktiv werden kann."
  log "  (§0.20 RX before TX — hier nur Listen, kein TX)"
  pause_enter "SQ bereit? Enter startet ~12s RX listen …"

  run_sudo "$CTL" -c "$INI" smoke --live --seconds 12 2>&1 | log_raw
  local rc=${PIPESTATUS[0]}

  if [[ "$rc" -eq 0 ]]; then
    log "OK: RX-Listen smoke beendet (rc=0)"
  else
    log "WARN: RX-Listen smoke rc=$rc (siehe Log; Stack/INI prüfen)"
  fi

  local sd
  sd="$(state_dir)"
  for f in "$sd"/dcd-bc0 "$sd"/rx-activity-bc0; do
    [[ -f "$f" ]] || continue
    log "Nach RX: $f"
    cat "$f" 2>&1 | log_raw || true
  done
  pause_enter "Phase 4 fertig — Enter …"
  return 0
}

phase_force_tx_ladder() {
  banner "Phase 5 — Force-TX Ladder (1 / 3 / 5 / 8 s)"
  log "WARNUNG: --force-tx ohne RX-Nachweis (§0.20 Override) — Debug / Intermittent-Hunt."
  log "Wattmeter bereithalten. USB-Pfad ist KEIN Produkt-TX."
  log ""
  log "PTT-WATCHDOG (FlexNet SER12 / WD-Boards):"
  log "  Hardware kann PTT nach ~14,5 s Dauer-Key abwerfen (Discharge ~500 ms)."
  log "  Bei langen Läufen / vielen Keys hintereinander: zwischendurch UNKEY / Pause ~14 s."
  log "  Sonst: RF fällt trotz Host-MCR PASS (Watchdog, kein UART-Fehler)."
  log ""
  log "BEOBACHTUNGSHINWEIS TXD (Charge-Pump):"
  log "  max25-bcprd/Sailer: THR 0x00 gepulst · TFPCX: TXD oft steady +12 V."
  log "  Notiz wenn RF mitten im Key einbricht / flackert (Pump/Bias-Kandidat)."
  pause_enter "Bereit für Ladder? Enter …"

  local secs host
  for secs in 1 3 5 8; do
    banner "Force-TX ${secs}s"
    pause_enter "Wattmeter beobachten — Enter startet ${secs}s Key …"
    smoke_force_tx "$secs"
    host="$_LAST_HOST"
    # show telem snapshot
    local sd tl
    sd="$(state_dir)"
    tl="$sd/tx-last-bc0"
    if [[ -f "$tl" ]]; then
      log "--- tx-last-bc0 nach ${secs}s ---"
      cat "$tl" 2>&1 | log_raw || true
    fi
    prompt_rf_obs "L4-${secs}s" "$host"
    pause_enter "Nächste Stufe — Enter …"
  done
  return 0
}

phase_cal_high() {
  banner "Phase 6 — Cal/high (max25-bcprd --cal high)"
  local bin
  if ! bin="$(resolve_max25-bcprd)"; then
    log "WARN: max25-bcprd nicht gefunden — Cal übersprungen"
    pause_enter
    return 0
  fi

  # Prefer strings(1); never start bare max25-bcprd. Source contract: --cal high|low|alt.
  if command -v strings >/dev/null 2>&1 && ! strings "$bin" 2>/dev/null | grep -qF -- '--cal'; then
    log "WARN: strings fand kein --cal in Binary — Phase trotzdem anbieten (Operator kann abbrechen)"
  fi

  log "max25-bcprd=$bin"
  log "Cal = kontinuierlicher SER12 Tone+PTT (DOS cal.exe Stil), kein KISS."
  log "Sicher: nur max25-bcprd stoppen via max25-bcpr-ctl — max25d Wrapper NICHT hart killen."
  log ""
  log "PTT-WATCHDOG: FlexNet cal pausiert alle ~14,5 s für ~500 ms (PTT-Discharge)."
  log "  Dieses Skript: --cal high ~10 s (unter WD). Längere manuelle Cal/"
  log "  Dauer-TX: UNKEY/Pause ~14 s einplanen — sonst RF-Tot auf WD-Boards."
  log "TXD: max25-bcprd pulst THR 0x00 (nicht TFPCX-steady) — RF-Einbruch mid-cal notieren."
  log ""
  local do_cal
  ask_yn do_cal "max25-bcprd stoppen und --cal high ~10s starten?"
  if [[ "$do_cal" != "j" ]]; then
    log "Cal übersprungen (Operator)"
    pause_enter
    return 0
  fi

  if ! need_sudo; then
    pause_enter
    return 0
  fi

  log "→ max25-bcpr-ctl stop"

  run_sudo "$CTL" -c "$INI" stop 2>&1 | log_raw

  sleep 1

  # Ensure no stray max25-bcprd
  if pgrep -x max25-bcprd >/dev/null 2>&1; then
    log "WARN: max25-bcprd noch aktiv nach stop — pkill -x max25-bcprd (kein max25d)"

    run_sudo pkill -x max25-bcprd 2>&1 | log_raw

    sleep 1
  fi

  log "→ $bin -c $INI --cal high --seconds 10"
  pause_enter "Wattmeter bereit — Enter startet cal high 10s …"

  run_sudo "$bin" -c "$INI" --cal high --seconds 10 2>&1 | log_raw
  local rc=$?

  local host="PASS"
  [[ "$rc" -eq 0 ]] || host="FAIL(rc=$rc)"
  prompt_rf_obs "CAL-high-10s" "$host"

  local restart
  ask_yn restart "max25-bcprd danach wieder starten (max25-bcpr-ctl start)?"
  if [[ "$restart" == "j" ]]; then

    run_sudo "$CTL" -c "$INI" start 2>&1 | log_raw

    log "Hinweis: wenn max25d den Stack besitzt, ggf. max25d neu starten (Operator, nicht dieses Skript)."
  fi
  pause_enter "Phase 6 fertig — Enter …"
  return 0
}

phase_double_burst() {
  banner "Phase 7 — Double Burst (back-to-back TX)"
  log "Zwei Force-TX 3s hintereinander (kurze Pause dazwischen)."
  pause_enter "Enter startet Burst A …"
  local host_a host_b
  smoke_force_tx 3
  host_a="$_LAST_HOST"
  sleep 1
  log "Burst B …"
  smoke_force_tx 3
  host_b="$_LAST_HOST"
  prompt_rf_obs "DoubleBurst-A+B" "${host_a}/${host_b}"
  pause_enter "Phase 7 fertig — Enter …"
  return 0
}

phase_contact_hunt() {
  banner "Phase 8 — Contact Hunt (DE-9 + 3.5mm)"
  log "OPERATOR-CHECKLISTE:"
  log "  1) DE-9 (PC-COM ↔ Host) und 3.5mm (Modem ↔ Radio) fest stecken"
  log "  2) Während dem nächsten Key leicht wackeln (Stecker/Kabel)"
  log "  3) Wattmeter + Board-LED + Radio-Display beobachten"
  log "  Ziel: intermittenter Kontakt vs. dauerhaft tot unterscheiden"
  pause_enter "Stecker fest? Enter startet 5s force-tx (währenddessen wackeln) …"

  local host
  smoke_force_tx 5
  host="$_LAST_HOST"
  local obs
  ask obs "Beobachtung während Wackeln (z.B. 'kurz 2W' / 'immer 0' / 'LED flackert'):"
  prompt_rf_obs "Contact-5s" "$host"
  # overwrite last note with wiggle observation if empty note
  if [[ -n "$obs" && ${#RES_NOTE[@]} -gt 0 ]]; then
    RES_NOTE[$((${#RES_NOTE[@]} - 1))]="$obs | ${_extra:-}"
    log "[contact-note] $obs"
  fi
  pause_enter "Phase 8 fertig — Enter …"
  return 0
}

phase_usb_note() {
  banner "Hinweis U — USB SER12 (kein Produkt-TX)"
  log "USB-UART (z.B. /dev/ttyUSB0 / FTDI) ist KEIN unterstützter max25-bcprd SER12-Pfad."
  log "  max25-bcprd braucht ioperm|/dev/port + echte ISA/LPC iobase — USB hat das nicht."
  log "  Station: RF nur ttyS0+CB; USB0 = Modem ohne Radio → Wattmeter ungültig."
  log "  DOSBox Soft-TNC auf USB ≠ bcpr Produkt-TX."
  pause_enter
  return 0
}

phase_restart_menu() {
  banner "Optional 0 — Sicheres max25-bcprd Restart"
  log "Methode (aus max25-bcpr-ctl): stop → start. Killt NICHT max25d."
  log "Wenn max25d den Stack besitzt: nach stop/start ggf. max25d-seitig neu binden."
  log ""
  log "  Aktueller Status:"

  run_sudo "$CTL" -c "$INI" status 2>&1 | log_raw

  local act
  ask act "Aktion: [s]top / [t]start / [r]estart / [a]bbruch:"
  case "${act,,}" in
    s|stop)
      run_sudo "$CTL" -c "$INI" stop 2>&1 | log_raw
      ;;
    t|start)
      run_sudo "$CTL" -c "$INI" start 2>&1 | log_raw
      ;;
    r|restart|re)
      run_sudo "$CTL" -c "$INI" stop 2>&1 | log_raw
      sleep 1
      run_sudo "$CTL" -c "$INI" start 2>&1 | log_raw
      ;;
    *)
      log "Abbruch — keine Änderung"
      ;;
  esac

  run_sudo "$CTL" -c "$INI" status 2>&1 | log_raw

  pause_enter
  return 0
}

phase_summary() {
  banner "Phase 9 — Summary + Verdict"
  log "Logdatei: $LOG"
  log ""
  log "┌──────────────────┬──────────┬──────────┬──────────┬──────────┐"
  log "│ Phase            │ Host     │ Watt W   │ BoardLED │ RadioTX  │"
  log "├──────────────────┼──────────┼──────────┼──────────┼──────────┤"
  local i n
  n=${#RES_PHASE[@]}
  if [[ "$n" -eq 0 ]]; then
    log "│ (keine TX-Phasen aufgezeichnet)                              │"
  else
    for ((i = 0; i < n; i++)); do
      printf '│ %-16s │ %-8s │ %-8s │ %-8s │ %-8s │\n' \
        "${RES_PHASE[$i]:0:16}" \
        "${RES_HOST[$i]:0:8}" \
        "${RES_WATT[$i]:0:8}" \
        "${RES_BLED[$i]:0:8}" \
        "${RES_RDISP[$i]:0:8}" | log_raw
      if [[ -n "${RES_NOTE[$i]:-}" ]]; then
        log "│   note: ${RES_NOTE[$i]}"
      fi
    done
  fi
  log "└──────────────────┴──────────┴──────────┴──────────┴──────────┘"

  # Verdict heuristics
  local any_host_pass=0 any_host_fail=0 any_rf=0 all_rf_zero=1
  for ((i = 0; i < n; i++)); do
    case "${RES_HOST[$i]}" in
      *PASS*) any_host_pass=1 ;;
      *FAIL*) any_host_fail=1 ;;
    esac
    case "${RES_WATT[$i]}" in
      ''|'0'|'0.0'|'?'|'n'|'nein') ;;
      *)
        # non-zero / non-empty that looks like power
        if [[ "${RES_WATT[$i]}" =~ ^[0-9]*\.?[0-9]+$ ]]; then
          if awk -v w="${RES_WATT[$i]}" 'BEGIN{exit !(w>0)}'; then
            any_rf=1
            all_rf_zero=0
          fi
        else
          # free text — if contains number >0 heuristic
          if [[ "${RES_WATT[$i]}" =~ [1-9] ]]; then
            any_rf=1
            all_rf_zero=0
          fi
        fi
        ;;
    esac
    if [[ "${RES_BLED[$i]}" == "j" || "${RES_RDISP[$i]}" == "j" ]]; then
      any_rf=1
      all_rf_zero=0
    fi
  done

  log ""
  log "=== Verdict-Hinweise (Heuristik, kein Automatik-Urteil) ==="
  if [[ "$n" -eq 0 ]]; then
    log "• Keine Ladder-Daten — nur Preflight/Status gelaufen."
  elif [[ "$any_host_pass" -eq 1 && "$all_rf_zero" -eq 1 && "$any_rf" -eq 0 ]]; then
    log "• HOST OK / RF tot oder 0 W: Fehlerklasse NACH UART"
    log "  → DE-9/3.5mm Kontakt, Charge-Pump/Vcc, PTT-Transistor, Mic-Buchse, Radio"
    log "  → Mic-alone 4 W OK stützt: Radio selbst ok; Pfad Modem↔Mic intermittierend"
  elif [[ "$any_host_pass" -eq 1 && "$any_rf" -eq 1 ]]; then
    log "• HOST OK / RF zeitweise sichtbar: INTERMITTENT RF (Kontakt/Pump/AF)"
    log "  → Contact-Hunt wiederholen; zwischen langen Keys Pause ~14 s (PTT-WD)"
    log "  → TXD pulse vs steady (TFPCX) als Beobachtung; Kabel/Stecker fest"
  elif [[ "$any_host_fail" -eq 1 && "$any_host_pass" -eq 0 ]]; then
    log "• HOST FAIL: zuerst Stack/KISS/fulldup/MCR — nicht primär Wattmeter"
    log "  → max25-bcpr-ctl status, kiss_link, fulldup=yes bei Soft-DCD, kein zweites max25-bcprd"
    log "  → MCR bleibt Sailer 0x0e|bit / 0x0d (nicht 4PC-COM 0x0A)"
  else
    log "• Gemischte Ergebnisse — Log + Notizen vergleichen; Phasen 5/8 wiederholen."
  fi
  log ""
  log "SSoT: operator research notes (private)"
  log "      2026-07-19-bcpr-mcr-ok-rf-zero-after-4w.md · winning-recipe · RF intermittent"
  log "      soft-TNC RE: 2026-07-19-baycom-soft-tnc-serial-ptt-re.md (WD · TXD · MCR)"
  log "USB: kein Produkt-TX (Phase U)."
  log ""
  log "Log gespeichert: $LOG"
  return 0
}

run_all() {
  phase_preflight
  phase_idle_mcr
  phase_status
  phase_rx_listen
  phase_force_tx_ladder
  phase_cal_high
  phase_double_burst
  phase_contact_hunt
  phase_usb_note
  phase_summary
}

menu_loop() {
  while true; do
    banner "max25-bcpr Ultimate Diag — Menü"
    log "INI=$INI"
    log "Log=$LOG"
    log ""
    log "  1) Preflight"
    log "  2) Idle MCR"
    log "  3) Status + Telem"
    log "  4) RX Listen"
    log "  5) Force-TX Ladder 1/3/5/8s"
    log "  6) Cal/high"
    log "  7) Double Burst"
    log "  8) Contact Hunt"
    log "  9) Summary / Verdict"
    log "  A) Alle Phasen 1–9 (+ USB-Hinweis)"
    log "  0) max25-bcprd stop/start (sicher)"
    log "  U) USB-Hinweis"
    log "  Q) Beenden"
    log ""
    local choice
    ask choice "Wahl:"
    case "${choice^^}" in
      1) phase_preflight ;;
      2) phase_idle_mcr ;;
      3) phase_status ;;
      4) phase_rx_listen ;;
      5) phase_force_tx_ladder ;;
      6) phase_cal_high ;;
      7) phase_double_burst ;;
      8) phase_contact_hunt ;;
      9) phase_summary ;;
      A|ALL) run_all ;;
      0) phase_restart_menu ;;
      U) phase_usb_note ;;
      Q|X|EXIT|QUIT)
        phase_summary
        log "Ende."
        return 0
        ;;
      *)
        log "Unbekannte Wahl: $choice"
        ;;
    esac
  done
}

# ---------- main ----------

while [[ $# -gt 0 ]]; do
  case "$1" in
    -c)
      [[ $# -ge 2 ]] || { echo "ERROR: -c needs INI path"; exit 2; }
      INI="$2"
      shift 2
      ;;
    --menu) MODE="menu"; shift ;;
    --all) MODE="all"; shift ;;
    --phase)
      [[ $# -ge 2 ]] || { echo "ERROR: --phase needs N"; exit 2; }
      MODE="phase"
      PHASE_ONLY="$2"
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "ERROR: unknown arg: $1"
      usage
      exit 2
      ;;
  esac
done

RUN_TS="$(date +%Y%m%d-%H%M%S)"
LOG="/tmp/max25-bcpr-ultimate-diag-${RUN_TS}.log"
: >"$LOG" || {
  echo "FEHLER: kann Log nicht schreiben: $LOG"
  exit 1
}

# Interactive reads use /dev/tty; log()/log_raw append to $LOG (no exec-tee double).
banner "max25-bcpr Ultimate Diag — BayCom/based (bcpr)"
log "Start: $(date -R 2>/dev/null || date)"
log "Host:  $(hostname 2>/dev/null || echo '?')"
log "User:  $(id -un 2>/dev/null || echo '?')  uid=$(id -u)"
log "INI:   $INI  (override: MAX25_BCPR_INI / -c)"
log "Log:   $LOG"
log "Tools: $CTL"
log ""
log "Hinweis: PTT-Watchdog ~14,5 s / 500 ms — bei langen Keys unkey/pausieren."
log "         TXD: max25-bcprd pulst (Sailer); TFPCX oft steady — RF mid-key notieren."
log "         MCR: Sailer belassen (kein 4PC-COM 0x0A-Experiment in diesem Skript)."
log ""

ensure_tools || {
  log "Abbruch: Tools fehlen."
  exit 1
}

# Soft check sudo early (warn only for menu; hard for --all live)
if ! need_sudo; then
  log "WARN: ohne sudo -n sind Live/TX/Cal/MCR-Phasen blockiert."
  if [[ "$MODE" == "all" ]]; then
    log "Abbruch (--all braucht sudo -n)."
    exit 1
  fi
fi

case "$MODE" in
  all)
    run_all
    ;;
  phase)
    case "$PHASE_ONLY" in
      1) phase_preflight ;;
      2) phase_idle_mcr ;;
      3) phase_status ;;
      4) phase_rx_listen ;;
      5) phase_force_tx_ladder ;;
      6) phase_cal_high ;;
      7) phase_double_burst ;;
      8) phase_contact_hunt ;;
      9) phase_summary ;;
      0) phase_restart_menu ;;
      U|u) phase_usb_note ;;
      *)
        log "FEHLER: unbekannte Phase $PHASE_ONLY"
        exit 2
        ;;
    esac
    ;;
  menu|*)
    menu_loop
    ;;
esac

log ""
log "Fertig. Log: $LOG"
exit 0
