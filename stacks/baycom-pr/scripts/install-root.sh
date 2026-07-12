#!/bin/bash
# Root install + smoke test for BayCom PR-Stack
#   sudo bash scripts/install-root.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "$(id -u)" -ne 0 ]]; then
	echo "Run as root: sudo bash $0" >&2
	exit 1
fi

echo "=== 1. Build ==="
make -C "${ROOT}" clean all

echo "=== 2. Install ==="
make -C "${ROOT}" install
install -m 755 "${ROOT}/scripts/baycom-pr-ctl" /usr/local/sbin/baycom-pr-ctl
install -m 755 "${ROOT}/scripts/pccom-ctl" /usr/local/sbin/pccom-ctl
install -d /etc/baycom/axports /etc/baycom/rc.d
install -m 644 "${ROOT}/config/baycom-pr.ini" /etc/baycom/baycom-pr.ini
install -m 644 "${ROOT}/config/modems.ini" /etc/baycom/modems.ini
install -m 644 "${ROOT}/config/axports/single.snippet" /etc/baycom/axports/single.snippet
install -m 644 "${ROOT}/config/axports/dual.snippet" /etc/baycom/axports/dual.snippet
install -m 755 "${ROOT}/scripts/rc.baycom-pr" /etc/baycom/rc.d/rc.baycom-pr
install -m 755 "${ROOT}/scripts/rc.baycom-pr" /etc/baycom/rc.d/rc.pccom
echo "Installed rc.baycom-pr under /etc/baycom/rc.d/ (optional)"

echo "=== 3. First-time setup (probe + preflight) ==="
if [[ ! -f /etc/baycom/baycom-pr.ini.bak ]]; then
	/usr/local/sbin/baycom-pr-ctl probe || true
	/usr/local/sbin/baycom-pr-ctl setup || true
fi
/usr/local/sbin/baycom-pr-ctl preflight || {
	echo "Preflight failed — fix /etc/baycom/baycom-pr.ini before start" >&2
	echo "Try: baycom-pr-ctl probe && baycom-pr-ctl setup && baycom-pr-ctl doctor" >&2
	exit 1
}

echo "=== 4. Start stack ==="
/usr/local/sbin/baycom-pr-ctl stop 2>/dev/null || true
/usr/local/sbin/baycom-pr-ctl start

echo "=== 5. Status ==="
/usr/local/sbin/baycom-pr-ctl status

echo "=== 6. Offline tests ==="
/usr/local/sbin/baycom-pr-ctl test || true

echo ""
echo "=== 7. Self-test (optional full suite) ==="
/usr/local/sbin/baycom-pr-ctl selftest || true

echo ""
echo "Done. KISS symlinks:"
ls -la /var/run/baycom-pr/ 2>/dev/null || true
