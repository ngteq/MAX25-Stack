#!/bin/bash
# Freeze / crash diagnostics — run as root after unexpected reboot
#   sudo bash scripts/check-freeze.sh
#
# Writes a copy to ~/baycom-pr-freeze-report.txt

set -euo pipefail

REPORT="${HOME}/baycom-pr-freeze-report.txt"
exec > >(tee "${REPORT}") 2>&1
echo "Report: ${REPORT}"
echo "Generated: $(date -Is)"
echo ""

echo "=== Uptime / boots ==="
uptime
who -b
last reboot | head -8

echo ""
echo "=== Previous boot (last 80 lines) ==="
journalctl -b -1 -n 80 --no-pager 2>/dev/null || tail -80 /var/log/messages 2>/dev/null || echo "(no journal/messages access)"

echo ""
echo "=== Previous boot: panic/OOM/watchdog/hung/baycom ==="
journalctl -b -1 --no-pager 2>/dev/null | grep -iE 'panic|oom|watchdog|hung|lockup|bug:|blocked|baycom|bcsf|mce|hard LOCKUP|soft LOCKUP' | tail -30 || \
	grep -iE 'panic|oom|watchdog|hung|lockup|bug:|blocked|baycom|bcsf|mce' /var/log/messages 2>/dev/null | tail -30 || true

echo ""
echo "=== Current boot errors/warnings ==="
journalctl -b -p warning --no-pager -n 30 2>/dev/null || true

echo ""
echo "=== Kernel ring buffer: panic/OOM/watchdog/hung ==="
dmesg -T 2>/dev/null | grep -iE 'panic|oom|watchdog|hung|lockup|bug:|blocked|mce|hard LOCKUP|soft LOCKUP' | tail -20 || true

echo ""
echo "=== Saved dmesg snapshot (mtime) ==="
ls -la /var/log/dmesg 2>/dev/null || true

echo ""
echo "=== baycom / serial ==="
lsmod | grep -E 'baycom|hdlc' || true
ip link show bcsf0 2>/dev/null || true
grep -E '^\s*[0-9]+:' /proc/interrupts | grep -iE 'baycom|ttyS|serial' | head -10 || true

echo ""
echo "=== If freeze repeats with stack running: try ==="
echo "  baycom-pr-ctl stop"
echo "  then: watch -n1 'grep baycom /proc/interrupts'"
