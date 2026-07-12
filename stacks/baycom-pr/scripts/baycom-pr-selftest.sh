#!/bin/bash
# BayCom PR-Stack — full offline self-test for modem users (no RF required)
#
# Usage:
#   sudo bash scripts/baycom-pr-selftest.sh
#   sudo baycom-pr-ctl selftest
#
# Options (env):
#   BAYCOM_INI=/etc/baycom/baycom-pr.ini
#   BAYCOM_SELFTEST_START=yes   start stack if down (default yes)
#   BAYCOM_SELFTEST_FULL=yes    run baycom_test all, not just quick (default yes)

set -euo pipefail

SELF="$(readlink -f "${BASH_SOURCE[0]}")"
SELF_DIR="$(cd "$(dirname "${SELF}")" && pwd)"
REPO_CAND="$(cd "${SELF_DIR}/.." && pwd)"
PREFIX="${BAYCOM_PREFIX:-/usr/local}"
BINDIR="${BAYCOM_BINDIR:-${PREFIX}/sbin}"

if [[ -n "${BAYCOM_ROOT:-}" && -f "${BAYCOM_ROOT}/tools/baycom_ini_load.py" ]]; then
	ROOT="${BAYCOM_ROOT}"
elif [[ -f "${REPO_CAND}/tools/baycom_ini_load.py" && -f "${REPO_CAND}/config/baycom-pr.ini" ]]; then
	ROOT="${REPO_CAND}"
else
	ROOT=""
fi

find_helper() {
	local base="$1" d
	for d in "${SELF_DIR}" "${ROOT}/tools" "${BINDIR}"; do
		[[ -n "${d}" && -f "${d}/${base}" ]] || continue
		echo "${d}/${base}"
		return 0
	done
	return 1
}

INI="${BAYCOM_INI:-/etc/baycom/baycom-pr.ini}"
if [[ ! -r "${INI}" && -n "${ROOT}" ]]; then
	INI="${ROOT}/config/baycom-pr.ini"
fi
CTL="${BAYCOM_CTL:-/usr/local/sbin/baycom-pr-ctl}"
if [[ ! -x "${CTL}" && -n "${ROOT}" ]]; then
	CTL="${ROOT}/scripts/baycom-pr-ctl"
fi
VALIDATE="${BAYCOM_VALIDATE:-$(find_helper baycom_validate_config.py || true)}"
[[ -f "${VALIDATE}" ]] || VALIDATE="${BINDIR}/baycom_validate_config.py"
DO_START="${BAYCOM_SELFTEST_START:-yes}"
DO_FULL="${BAYCOM_SELFTEST_FULL:-no}"

FAIL=0
WARN=0

pass() { printf 'OK:   %s\n' "$*"; }
warn() { WARN=$((WARN + 1)); printf 'WARN: %s\n' "$*"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$*" >&2; }

section() {
	echo ""
	echo "======== $* ========"
}

need_root() {
	[[ "$(id -u)" -eq 0 ]] || { fail "run as root (sudo)"; exit 1; }
}

check_dep() {
	local name="$1"
	if command -v "${name}" >/dev/null 2>&1; then
		pass "${name} found ($(command -v "${name}"))"
	else
		fail "${name} not in PATH"
	fi
}

check_module() {
	local mod="$1"
	if modprobe -n "${mod}" >/dev/null 2>&1; then
		pass "kernel module ${mod} available"
	elif [[ -d "/lib/modules/$(uname -r)" ]] && find "/lib/modules/$(uname -r)" -name "${mod}.ko*" -print -quit | grep -q .; then
		pass "kernel module ${mod} present on disk"
	else
		fail "kernel module ${mod} missing — enable CONFIG_BAYCOM_SER_FDX / CONFIG_AX25"
	fi
}

test_kiss_link() {
	local link="$1" label="$2"
	local target

	if [[ ! -L "${link}" ]]; then
		fail "${label}: kiss link missing ${link}"
		return
	fi
	target="$(readlink -f "${link}" 2>/dev/null || readlink "${link}")"
	if [[ -c "${target}" ]]; then
		pass "${label}: KISS PTY ${link} -> ${target}"
	else
		fail "${label}: KISS target not a character device: ${target}"
	fi
}

section "BayCom PR-Stack self-test"
echo "ini=${INI}"
echo "time=$(date -Is 2>/dev/null || date)"

section "1. Config (no driver)"
if python3 "${VALIDATE}" "${INI}"; then
	pass "INI validation passed"
else
	fail "INI validation failed — fix baycom-pr.ini / modems.ini first"
	exit 1
fi

section "2. Host dependencies"
need_root
check_dep setserial
check_dep ip
check_dep python3
check_dep gcc
command -v socat >/dev/null && pass "socat found (optional KISS debug)" || warn "socat not installed (optional — see docs/TESTING.md)"
check_module ax25

section "3. Build tools"
if [[ -n "${ROOT}" && -f "${ROOT}/tools/Makefile" ]]; then
	make -C "${ROOT}/tools" baycom_test baycom_sethdlc baycom_kissbridge baycom_kiss_serial >/dev/null
	pass "tools built (${ROOT}/tools)"
else
	for t in baycom_test baycom_sethdlc baycom_kissbridge baycom_kiss_serial; do
		[[ -x "${BINDIR}/${t}" ]] || fail "${t} missing in ${BINDIR} (run: make install)"
	done
	pass "installed tools in ${BINDIR}"
fi

INI_LOADER="$(find_helper baycom_ini_load.py || true)"
[[ -n "${INI_LOADER}" ]] || fail "baycom_ini_load.py not found"
eval "$(python3 "${INI_LOADER}" "${INI}" 2>/dev/null || true)"
NEED_SER=0 NEED_PAR=0
for ((i = 0; i < ${BP_MODEM_COUNT:-0}; i++)); do
	eval "be=\$BP_M${i}_BACKEND"
	[[ "${be}" == "kernel-ser12" ]] && NEED_SER=1
	[[ "${be}" == "kernel-par96" ]] && NEED_PAR=1
done

section "3b. Kernel modules (profile)"
[[ "${NEED_SER}" -eq 1 ]] && check_module baycom_ser_fdx
[[ "${NEED_PAR}" -eq 1 ]] && check_module baycom_par
[[ "${NEED_SER}" -eq 0 && "${NEED_PAR}" -eq 0 ]] && pass "kiss-serial profile — no baycom kernel module required"

section "4. Stack state"
WAS_UP=0
if "${CTL}" -c "${INI}" status 2>/dev/null | grep -qE 'baycom_ser_fdx: loaded|baycom_par: loaded'; then
	WAS_UP=1
	pass "stack already running"
elif [[ "${DO_START}" == "yes" ]]; then
	echo "Preflight before start..."
	"${CTL}" -c "${INI}" preflight || fail "preflight failed — run: baycom-pr-ctl setup"
	echo "Starting stack..."
	"${CTL}" -c "${INI}" start
	pass "stack started"
else
	fail "stack not running — run: baycom-pr-ctl start"
	exit 1
fi

section "5. Quick health (per modem)"
"${CTL}" -c "${INI}" check || fail "quick check failed"

section "6. Modem tests (offline, no RF)"
if [[ "${DO_FULL}" == "yes" ]]; then
	"${CTL}" -c "${INI}" test || fail "full modem test suite failed"
else
	"${CTL}" -c "${INI}" check || fail "quick modem tests failed"
fi

section "7. KISS links"
eval "$(python3 "${INI_LOADER}" "${INI}")"
for ((i = 0; i < BP_MODEM_COUNT; i++)); do
	eval "kiss=\$BP_M${i}_KISS"
	eval "label=\$BP_M${i}_LABEL"
	test_kiss_link "${kiss}" "${label}"
done

section "8. AX.25 ports (reference)"
if [[ -r /etc/baycom/axports/axports ]]; then
	for ((i = 0; i < BP_MODEM_COUNT; i++)); do
		eval "port=\$BP_M${i}_PORT"
		[[ -n "${port}" ]] || continue
		if grep -qE "^[[:space:]]*${port}[[:space:]]" /etc/baycom/axports/axports; then
			pass "axports contains ${port}"
		else
			warn "axports missing ${port} — merge config/axports/dual.snippet for listen/call"
		fi
	done
else
	warn "/etc/baycom/axports/axports not found — optional for listen/call"
fi

section "Summary"
echo "errors=${FAIL} warnings=${WARN}"
if [[ "${FAIL}" -eq 0 ]]; then
	echo ""
	echo "Self-test passed (offline). On-air RX/TX not covered — connect radio when ready."
	exit 0
fi
echo ""
echo "Self-test failed. See docs/TESTING.md and docs/MANUAL.md — Troubleshooting."
exit 1
