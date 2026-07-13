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
    && ok "default operating mode: standalone" \
    || fail "manifest missing default operating mode (default_betriebsform: standalone)"
else
  fail "plugins/manifest.yaml missing"
fi

# --- required docs ---
for doc in README.md CONTRIBUTING.md docs/README.md docs/ARCHITECTURE.md docs/DEVELOPMENT.md docs/HYBBX.md docs/PLATFORMS.md docs/V1.0.0-SCOPE.md docs/BAYCOM.md docs/MERGE-REPORT.md docs/MAX25-TERMINAL.md docs/MAX25-CLIENT.md docs/LINUX-HOST-SETUP.md docs/PACKET-RADIO.md stacks/daemon/README.md; do
  [[ -f "$doc" ]] && ok "doc $doc" || fail "missing $doc"
done

# --- scripts executable ---
for script in scripts/discover-plugins.sh scripts/build-all.sh scripts/build.sh scripts/test.sh scripts/clean.sh scripts/release-check.sh scripts/max25-ctl scripts/install-max25.sh; do
  if [[ -x "$script" ]]; then
    ok "executable $script"
  else
    fail "not executable: $script"
  fi
done

if [[ -x stacks/daemon/max25d ]]; then
  ok "executable stacks/daemon/max25d"
else
  fail "stacks/daemon/max25d not executable"
fi

if [[ -f stacks/daemon/kiss_bridge.py ]]; then
  ok "stacks/daemon/kiss_bridge.py"
else
  fail "missing stacks/daemon/kiss_bridge.py"
fi

if [[ -f share/max25/max25d.ini.example ]]; then
  ok "share/max25/max25d.ini.example"
else
  fail "missing share/max25/max25d.ini.example"
fi

if [[ -f share/max25/max25d.ini.host.example ]]; then
  ok "share/max25/max25d.ini.host.example"
else
  fail "missing share/max25/max25d.ini.host.example"
fi

if [[ -f share/baycom/baycom-pr.pccom-ttyS0-only.ini.example ]]; then
  ok "share/baycom single-modem example"
else
  fail "missing share/baycom/baycom-pr.pccom-ttyS0-only.ini.example"
fi

if [[ -f share/clients/index.yaml ]] && [[ -f share/clients/tnc2c.yaml ]]; then
  ok "share/clients registry"
else
  fail "missing share/clients/ (index.yaml or tnc2c.yaml)"
fi

if [[ -f local/README.md ]]; then
  ok "local/README.md (gitignored site overrides)"
else
  fail "missing local/README.md"
fi

if [[ -f include/max25/protocol.md ]]; then
  ok "include/max25/protocol.md"
else
  fail "missing include/max25/protocol.md"
fi

if [[ -f include/max25/packet-radio.md ]]; then
  ok "include/max25/packet-radio.md"
else
  fail "missing include/max25/packet-radio.md"
fi

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

# --- HyBBX INI templates (stack-local) ---
for ini in stacks/tncs/hybbx-tnc2c.ini \
           stacks/tncs/hybbx-dual.ini \
           share/hybbx/tnc2c-host.ini.example \
           share/hybbx/baycom-ser12-host.ini.example \
           share/hybbx/crdop-host.ini.example; do
  [[ -f "$ini" ]] && ok "ini $ini" || fail "missing $ini"
done

# --- build artifacts (CMake) ---
cmake -B build -DCMAKE_BUILD_TYPE=Release >/dev/null 2>&1 \
  && cmake --build build -j"$(nproc 2>/dev/null || echo 2)" >/dev/null 2>&1 \
  && ok "cmake build (build/bin/)" \
  || fail "cmake build"
[[ -x build/bin/tnc2c-probe ]] && ok "tnc2c-probe built" || fail "tnc2c-probe build"
[[ -x build/bin/baycom_test ]] && ok "baycom-pr tools built" || fail "baycom-pr build"
[[ -x build/bin/crdopc ]] && ok "crdopc built" || fail "crdopc missing"
[[ -x build/bin/max25-terminal ]] && ok "max25-terminal built" || fail "max25-terminal build"

# --- offline tests ---
if bash stacks/baycom-pr/scripts/test-all.sh >/dev/null 2>&1; then
  ok "baycom-pr test-all"
else
  fail "baycom-pr test-all"
fi

if CRDOP_BIN="${PWD}/build/bin/crdopc" bash stacks/crdop/scripts/test-smoke.sh >/dev/null 2>&1; then
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

# --- max25d + terminal ---
chmod +x stacks/daemon/max25d 2>/dev/null || true
[[ -x stacks/daemon/max25d ]] && ok "max25d ready" || fail "max25d"
if [[ -L build/bin/max25-client ]] || [[ -x build/bin/max25-client ]]; then
  ok "max25-client symlink"
else
  warn "max25-client symlink missing until cmake --install"
fi
if MAX25_TERMINAL="${PWD}/build/bin/max25-terminal" \
   bash stacks/terminal/test-terminal.sh >/dev/null 2>&1; then
  ok "max25-terminal TCP probe"
else
  fail "max25-terminal TCP probe"
fi

if python3 stacks/daemon/test_proto.py >/dev/null 2>&1; then
  ok "max25d protocol smoke"
else
  fail "max25d protocol smoke"
fi

if python3 stacks/daemon/test_auth.py >/dev/null 2>&1; then
  ok "max25d TCP auth smoke"
else
  fail "max25d TCP auth smoke"
fi

# --- AmigaOS terminal (optional cross-build) ---
if [[ -x /opt/amiga/bin/m68k-amigaos-gcc ]]; then
  if bash scripts/build-amiga-terminal.sh >/dev/null 2>&1; then
    ok "max25-terminal AmigaOS cross-build"
  else
    fail "max25-terminal AmigaOS cross-build"
  fi
else
  warn "Amiga SDK not at /opt/amiga; skip Amiga terminal build"
fi

# --- CI workflow ---
[[ -f .github/workflows/ci.yml ]] && ok "ci workflow" || fail "missing .github/workflows/ci.yml"

# --- tncs probe (warn without hardware) ---
if build/bin/tnc2c-probe >/dev/null 2>&1; then
  ok "tnc2c-probe (serial found)"
else
  warn "tnc2c-probe: no serial devices (OK for CI without hardware)"
fi

echo "======== release-check: ${PASS} passed, ${FAIL} failed, ${WARN} warnings ========"
if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
exit 0
