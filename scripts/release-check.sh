#!/usr/bin/env bash
# MainAX25-Stack (MAX25-Stack) — v1.0.0 release gates (offline, no root).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PASS=0
FAIL=0
WARN=0

ok()   { echo "OK:   $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*" >&2; FAIL=$((FAIL + 1)); }
warn() { echo "WARN: $*"; WARN=$((WARN + 1)); }

echo "======== MainAX25-Stack release-check ($(tr -d '[:space:]' < VERSION)) ========"

# --- version & manifest ---
if [[ -f VERSION ]]; then
  VER="$(tr -d '[:space:]' < VERSION)"
  [[ -n "$VER" ]] && ok "VERSION=${VER}" || fail "VERSION file empty"
else
  fail "VERSION file missing"
fi

if [[ -f plugins/manifest.yaml ]]; then
  ok "plugins/manifest.yaml"
  grep -q 'default_betriebsform: standalone' plugins/manifest.yaml \
    && ok "default betriebsform: standalone" \
    || fail "manifest missing default_betriebsform: standalone"
else
  fail "plugins/manifest.yaml missing"
fi

# --- required docs ---
for doc in README.md CONTRIBUTING.md docs/ARCHITECTURE.md docs/DEVELOPMENT.md docs/HYBBX.md docs/PLATFORMS.md docs/V1.0.0-SCOPE.md docs/MERGE-REPORT.md; do
  [[ -f "$doc" ]] && ok "doc $doc" || fail "missing $doc"
done

# --- scripts executable ---
for script in scripts/discover-plugins.sh scripts/build-all.sh scripts/release-check.sh scripts/max25-ctl; do
  if [[ -x "$script" ]]; then
    ok "executable $script"
  else
    fail "not executable: $script"
  fi
done

# --- plugin count ---
YAML_COUNT="$(find plugins -name plugin.yaml | wc -l | tr -d ' ')"
if [[ "$YAML_COUNT" -ge 12 ]]; then
  ok "plugin.yaml count: ${YAML_COUNT}"
else
  fail "expected >=12 plugin.yaml, got ${YAML_COUNT}"
fi

# --- v1 active devices in manifest ---
for dev in tnc2c baycom-ser12 soft-crdop; do
  if grep -A6 "id: ${dev}" plugins/manifest.yaml | grep -q 'status: active'; then
    ok "device ${dev} status: active"
  else
    fail "device ${dev} not active in manifest"
  fi
done

# --- planned/scaffold devices stay out of v1 active set ---
for dev in pktnc2 baycom-par96 baycom-kiss; do
  if grep -A6 "id: ${dev}" plugins/manifest.yaml | grep -Eq 'status: (planned|scaffold)'; then
    ok "device ${dev} correctly non-active"
  else
    warn "device ${dev} status unexpected (should be planned/scaffold)"
  fi
done

# --- HyBBX INI examples ---
for ini in share/hybbx/tnc2c-edge.ini.example \
           share/hybbx/baycom-ser12-edge.ini.example \
           share/hybbx/crdop-edge.ini.example; do
  [[ -f "$ini" ]] && ok "ini $ini" || fail "missing $ini"
done

# --- build artifacts ---
make -C stacks/tncs all >/dev/null 2>&1 \
  && [[ -x stacks/tncs/tnc2c-probe ]] && ok "tnc2c-probe built" \
  || fail "tnc2c-probe build"

make -C stacks/baycom-pr all >/dev/null 2>&1 && ok "baycom-pr build" || fail "baycom-pr build"

if [[ -x stacks/crdop/build/crdopc ]]; then
  ok "crdopc binary"
else
  make -C stacks/crdop all >/dev/null 2>&1
  [[ -x stacks/crdop/build/crdopc ]] && ok "crdopc built" || fail "crdopc missing"
fi

# --- offline tests ---
if make -C stacks/baycom-pr test >/dev/null 2>&1; then
  ok "baycom-pr test-all"
else
  fail "baycom-pr test-all"
fi

if make -C stacks/crdop smoke >/dev/null 2>&1; then
  ok "crdop smoke"
else
  fail "crdop smoke"
fi

# --- discovery ---
if bash scripts/discover-plugins.sh --json >/dev/null 2>&1; then
  ok "discover-plugins --json"
else
  fail "discover-plugins --json"
fi

# --- CI workflow ---
[[ -f .github/workflows/ci.yml ]] && ok "ci workflow" || fail "missing .github/workflows/ci.yml"

# --- tncs probe (warn without hardware) ---
if stacks/tncs/tnc2c-probe >/dev/null 2>&1; then
  ok "tnc2c-probe (serial found)"
else
  warn "tnc2c-probe: no serial devices (OK for CI without hardware)"
fi

echo "======== release-check: ${PASS} passed, ${FAIL} failed, ${WARN} warnings ========"
if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
exit 0
