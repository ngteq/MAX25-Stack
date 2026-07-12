#!/bin/bash
# Verify deep-analysis claims against repo (offline, no root)
#   bash scripts/verify-analysis.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

pass() { printf 'OK:   %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

echo "======== verify-analysis (deep-scan checklist) ========"

# P0 automation
for f in tools/baycom_probe.py tools/baycom_doctor.py docs/GUIDE.md docs/REFERENCE.md docs/DEVELOPER.md; do
	[[ -f "${f}" ]] || fail "missing ${f}"
done
pass "core docs and automation tools present"

grep -q 'cmd_probe\|cmd_setup\|cmd_doctor' scripts/baycom-pr-ctl || fail "baycom-pr-ctl missing probe/setup/doctor"
pass "baycom-pr-ctl probe/setup/doctor wired"

grep -q 'staged_dual' scripts/baycom-pr-ctl || fail "staged dual probe missing"
grep -q 'post_start_irq_watch' scripts/baycom-pr-ctl || fail "IRQ watchdog missing"
grep -q 'cmd_recover\|recover' scripts/baycom-pr-ctl || fail "recover missing"
pass "freeze protection commands present"

# Single default / dual optional
grep -q 'modems = a$' config/baycom-pr.ini || fail "default INI not single-modem"
[[ -f config/examples/baycom-pr.dual.ini ]] || fail "dual example missing"
pass "single default + dual example"

# CB + HAM profiles (in GUIDE.md)
for f in config/examples/baycom-pr.cb.ini config/examples/baycom-pr.ham.ini; do
	[[ -f "${f}" ]] || fail "missing ${f}"
done
pass "CB + HAM example INIs"

python3 tools/baycom_validate_config.py config/examples/baycom-pr.cb.ini >/dev/null
python3 tools/baycom_validate_config.py config/examples/baycom-pr.ham.ini >/dev/null
pass "CB/HAM example INIs validate"

# /etc/baycom install paths
grep -q '/etc/baycom/' tools/Makefile || fail "Makefile not using /etc/baycom"
pass "/etc/baycom install layout"

# Kernel analysis doc
[[ -f docs/kernel/BAYCOM-DRIVER-ANALYSIS.md ]] || fail "kernel analysis missing"
pass "kernel driver analysis documented"

# Offline test suite
make test >/dev/null
pass "make test passed"

# Doctor offline mode
python3 tools/baycom_doctor.py --offline config/baycom-pr.ini >/dev/null
pass "doctor --offline on default INI"

echo ""
echo "======== verify-analysis passed ========"
echo "Hardware still required on target host:"
echo "  sudo baycom-pr-ctl doctor && sudo baycom-pr-ctl selftest"
