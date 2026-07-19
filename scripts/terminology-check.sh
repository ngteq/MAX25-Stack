#!/usr/bin/env bash
# terminology-check.sh — release gate for AGENT-INDEX §0.16 / §0.19
# Fail on forbidden product terms in shipped markdown (not tests/archives).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
ERR=0

check() {
  local pat="$1" msg="$2"
  local hits
  hits="$(grep -RInE --include='*.md' "$pat" README.md CHANGELOG.md RELEASE-READINESS.md docs share/clients plugins 2>/dev/null \
    | grep -vE 'Never |never |forbidden|LEGACY|removed|prefer bcpr|BayCom/based' || true)"
  if [[ -n "$hits" ]]; then
    echo "FAIL: $msg"
    echo "$hits" | head -40
    ERR=1
  else
    echo "OK: $msg"
  fi
}

check '\bbcpr-bc0\b' 'product device id bcpr-bc0 (use max25e0)'
check '\bbcpr-bc1\b' 'product device id bcpr-bc1 (use max25e0:bc1)'
# product device face for SER12 — allow historical "removed" lines
if grep -RInE --include='*.md' 'device = baycom-ser12|`baycom-ser12` \|' README.md docs 2>/dev/null \
  | grep -vE 'removed|LEGACY|kernel baycom|not a kernel|Never' | grep -q .; then
  echo "FAIL: product baycom-ser12 as active device face"
  grep -RInE --include='*.md' 'device = baycom-ser12|`baycom-ser12` \|' README.md docs 2>/dev/null | head -20 || true
  ERR=1
else
  echo "OK: no active baycom-ser12 product device face in README/docs"
fi
check '\bKonverter\b' 'Konverter in shipped docs'
check '\bAX25SRV\b|\bax25srv\b' 'AX25SRV in shipped docs'

if [[ "$ERR" -ne 0 ]]; then
  exit 1
fi
echo "terminology-check: PASS"
exit 0
