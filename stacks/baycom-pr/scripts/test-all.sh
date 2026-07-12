#!/bin/bash
# Offline test suite (no root, no radio) — run from repo root: make test
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

pass() { printf 'OK:   %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

echo "======== BayCom PR-Stack test-all (v$(cat VERSION | tr -d '[:space:]')) ========"

echo ""
echo "=== 1. Shell syntax ==="
bash -n scripts/verify-analysis.sh
for f in \
	scripts/baycom-pr-ctl \
	scripts/baycom-pr-selftest.sh \
	scripts/install-root.sh \
	scripts/check-freeze.sh \
	scripts/rc.baycom-pr \
	scripts/pccom-ctl \
	scripts/legacy/baycom-kernel-test.sh \
	scripts/legacy/rc.pccom; do
	[[ -f "${f}" ]] || fail "missing ${f}"
	bash -n "${f}"
done
pass "shell scripts"

echo ""
echo "=== 2. Build ==="
REPO_ROOT="$(cd "${ROOT}/../.." && pwd)"
BIN_DIR=""
if [[ -x "${REPO_ROOT}/build/bin/baycom_test" ]]; then
	BIN_DIR="${REPO_ROOT}/build/bin"
elif [[ -f tools/Makefile ]]; then
	make -C tools clean all
	BIN_DIR="tools"
else
	cmake -B "${REPO_ROOT}/build" -DCMAKE_BUILD_TYPE=Release >/dev/null
	cmake --build "${REPO_ROOT}/build" --target baycom_test baycom_sethdlc baycom_kissbridge baycom_kiss_serial >/dev/null
	BIN_DIR="${REPO_ROOT}/build/bin"
fi
for b in baycom_test baycom_sethdlc baycom_kissbridge baycom_kiss_serial; do
	[[ -x "${BIN_DIR}/${b}" ]] || fail "binary missing: ${BIN_DIR}/${b}"
done
pass "tools built"

echo ""
echo "=== 3. Site config ==="
python3 tools/baycom_validate_config.py config/baycom-pr.ini || fail "baycom-pr.ini invalid"
pass "baycom-pr.ini"
python3 tools/baycom_validate_config.py config/examples/baycom-pr.par96.ini || fail "par96 example invalid"
python3 tools/baycom_ini_load.py config/examples/baycom-pr.par96.ini >/tmp/baycom-par96-load.out
grep -q 'BP_M0_BACKEND=kernel-par96' /tmp/baycom-par96-load.out || fail "par96 ini loader backend"
pass "baycom-pr.par96.ini example"
python3 tools/baycom_validate_config.py config/examples/baycom-pr.cb.ini || fail "CB example invalid"
python3 tools/baycom_validate_config.py config/examples/baycom-pr.ham.ini || fail "HAM example invalid"
pass "CB + HAM example INIs"

echo ""
echo "=== 4. INI loader ==="
python3 tools/baycom_ini_load.py config/examples/baycom-pr.dual.ini >/tmp/baycom-ini-load.out
grep -q '^BP_MODEM_COUNT=' /tmp/baycom-ini-load.out || fail "ini loader output"
python3 tools/baycom_probe.py >/dev/null
pass "baycom_ini_load.py + baycom_probe.py"

echo ""
echo "=== 5. Modem catalog ==="
python3 tools/baycom_validate_config.py config/baycom-pr.ini >/dev/null
python3 - <<'PY'
import configparser
from collections import Counter
from pathlib import Path

cp = configparser.ConfigParser()
cp.read("config/modems.ini", encoding="utf-8")
mods = [s for s in cp.sections() if s.startswith("modem.")]
if len(mods) < 20:
    raise SystemExit(f"expected 20+ catalog entries, got {len(mods)}")
stack = Counter(cp[s].get("stack", "?").strip().lower() for s in mods)
print(f"catalog entries: {len(mods)}")
for k, v in sorted(stack.items()):
    print(f"  {k}: {v}")
PY
pass "modems.ini"

echo ""
echo "=== 6. Python tools ==="
python3 -m py_compile tools/baycom_ini_load.py tools/baycom_validate_config.py tools/baycom_preflight.py tools/baycom_serial_status.py tools/baycom_probe.py tools/baycom_doctor.py tools/baycom_axports.py
pass "python syntax"

echo ""
echo "=== 6b. AX.25 axports ==="
tmpdir="$(mktemp -d)"
trap 'rm -rf "${tmpdir}"' EXIT
python3 tools/baycom_axports.py config/baycom-pr.ini show | grep -q 'radio' || fail "axports show missing radio port"
python3 tools/baycom_axports.py config/baycom-pr.ini apply --dry-run | grep -q 'baycom-pr-stack managed' || fail "axports dry-run apply"
python3 tools/baycom_axports.py config/baycom-pr.ini apply --dry-run --axports-file "${tmpdir}/axports" --ax25-link "${tmpdir}/ax25-axports" >/dev/null
python3 tools/baycom_axports.py config/baycom-pr.ini apply --axports-file "${tmpdir}/axports" --ax25-link "${tmpdir}/ax25-axports" >/dev/null
python3 tools/baycom_axports.py config/baycom-pr.ini check --axports-file "${tmpdir}/axports" --ax25-link "${tmpdir}/ax25-axports" || fail "axports check temp files"
[[ -L "${tmpdir}/ax25-axports" ]] || fail "ax25 symlink not created"
python3 tools/baycom_doctor.py config/baycom-pr.ini --offline >/dev/null || fail "doctor offline with axports"
pass "baycom_axports.py"

echo ""
echo "=== 7. Repo layout ==="
for p in \
	config/baycom-pr.ini \
	config/modems.ini \
	config/axports/single.snippet \
	config/examples/baycom-pr.dual.ini \
	config/examples/baycom-pr.cb.ini \
	config/examples/baycom-pr.ham.ini \
	config/examples/baycom-pr.par96.ini \
	config/examples/baycom-pr.picpar.ini \
	config/minicom/minirc.baycom-kiss \
	docs/INDEX.md \
	docs/GUIDE.md \
	docs/REFERENCE.md \
	docs/DEVELOPER.md \
	tools/baycom_preflight.py \
	tools/baycom_probe.py \
	tools/baycom_doctor.py \
	tools/baycom_axports.py \
	config/systemd/baycom-pr.service \
	config/examples/terminals/README.md \
	AGENTS.md \
	CONTRIBUTING.md \
	CHANGELOG.md \
	LICENSE VERSION COPYRIGHT NOTICE; do
	[[ -e "${p}" ]] || fail "missing ${p}"
done
pass "required paths"

echo ""
echo "=== 8. Parport example configs ==="
python3 tools/baycom_validate_config.py config/examples/baycom-pr.par96.ini
python3 tools/baycom_validate_config.py config/examples/baycom-pr.picpar.ini
python3 tools/baycom_ini_load.py config/examples/baycom-pr.par96.ini | grep -q '^BP_M0_BACKEND=kernel-par96$' || fail "par96 ini loader backend"
python3 tools/baycom_ini_load.py config/examples/baycom-pr.par96.ini | grep -q '^BP_M0_IOBASE=0x378$' || fail "par96 ini loader iobase"
pass "par96/picpar example INIs"

echo ""
echo "======== test-all passed (offline) ========"
echo "On hardware: sudo bash scripts/install-root.sh  OR  sudo baycom-pr-ctl selftest"
