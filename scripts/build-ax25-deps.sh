#!/usr/bin/env bash
# DEPRECATED — manual build of vendored libax25 / ax25-tools / ax25-apps (Linux).
#
# MAX25 default build does NOT invoke this script. Tarballs in third_party/ax25/
# are study reference only; max25d uses native ax25_codec.py.
#
# Use when you need host listen/call/kissattach without distro packages:
#   scripts/build-ax25-deps.sh --prefix /opt/ax25 --need-apps --need-tools
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR="${ROOT}/third_party/ax25"
PATCHES="${VENDOR}/patches"

LIBAX25_VER="0.0.12-rc5"
TOOLS_VER="0.0.10-rc5"
APPS_VER="0.0.8-rc5"

usage() {
  cat <<EOF
Usage: $0 --prefix DIR [options]

Options:
  --prefix DIR       Install prefix (required)
  --build-dir DIR    Extract/build tree (default: <prefix>/../build)
  --need-libax25     Build libax25 even if present on host
  --need-tools       Build ax25-tools
  --need-apps        Build ax25-apps
  -h, --help         This help

Environment:
  MAKE, CC, CXX      Passed to upstream make/configure
EOF
}

PREFIX=""
BUILD_DIR=""
NEED_LIBAX25=0
NEED_TOOLS=0
NEED_APPS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prefix) PREFIX="$2"; shift 2 ;;
    --build-dir) BUILD_DIR="$2"; shift 2 ;;
    --need-libax25) NEED_LIBAX25=1; shift ;;
    --need-tools) NEED_TOOLS=1; shift ;;
    --need-apps) NEED_APPS=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

[[ -n "$PREFIX" ]] || { echo "error: --prefix required" >&2; exit 1; }
PREFIX="$(cd "$(dirname "$PREFIX")" && pwd)/$(basename "$PREFIX")"
BUILD_DIR="${BUILD_DIR:-$(dirname "$PREFIX")/build}"
BUILD_DIR="$(mkdir -p "$BUILD_DIR" && cd "$BUILD_DIR" && pwd)"
PREFIX="$(mkdir -p "$PREFIX" && cd "$PREFIX" && pwd)"

verify_tarball() {
  local file="$1"
  [[ -f "$file" ]] || { echo "error: missing tarball $file" >&2; exit 1; }
  if [[ -f "${VENDOR}/SHA256SUMS" ]]; then
    local base
    base="$(basename "$file")"
    (cd "$VENDOR" && sha256sum -c SHA256SUMS 2>/dev/null | grep -q "^${base}: OK") \
      || echo "WARN: SHA256 mismatch for ${base} — continuing" >&2
  fi
}

extract() {
  local tarball="$1" dir="$2"
  verify_tarball "$tarball"
  rm -rf "$dir"
  tar xzf "$tarball" -C "$BUILD_DIR"
}

apply_patches() {
  local srcdir="$1"
  shift
  local patch failed=0
  for patch in "$@"; do
    [[ -f "$patch" ]] || continue
    echo "-- patch $(basename "$patch")"
    if ! patch -d "$srcdir" -p1 -N -s -f < "$patch"; then
      echo "error: patch failed: $(basename "$patch")" >&2
      failed=1
    fi
  done
  [[ "$failed" -eq 0 ]]
}

ax25_link_flags() {
  if [[ "$NEED_LIBAX25" -eq 1 ]]; then
    export CPPFLAGS="-I${PREFIX}/include ${CPPFLAGS:-}"
    export LDFLAGS="-L${PREFIX}/lib -Wl,-rpath,${PREFIX}/lib ${LDFLAGS:-}"
  elif [[ -d /usr/include/netax25 ]]; then
    export CPPFLAGS="-I/usr/include ${CPPFLAGS:-}"
    export LDFLAGS="${LDFLAGS:-}"
  fi
}

build_libax25() {
  local dir="${BUILD_DIR}/libax25-${LIBAX25_VER}"
  echo "== libax25 ${LIBAX25_VER} -> ${PREFIX}"
  extract "${VENDOR}/libax25-${LIBAX25_VER}.tar.gz" "$dir"
  (
    cd "$dir"
    ./configure --prefix="$PREFIX"
    "${MAKE:-make}" -j"$(nproc 2>/dev/null || echo 2)"
    "${MAKE:-make}" install
  )
}

build_ax25_tools() {
  local dir="${BUILD_DIR}/ax25-tools-${TOOLS_VER}"
  echo "== ax25-tools ${TOOLS_VER} -> ${PREFIX}"
  extract "${VENDOR}/ax25-tools-${TOOLS_VER}.tar.gz" "$dir"
  ax25_link_flags
  (
    cd "$dir"
    ./configure --prefix="$PREFIX"
    "${MAKE:-make}" -j"$(nproc 2>/dev/null || echo 2)"
    "${MAKE:-make}" install
  )
}

build_ax25_apps() {
  local dir="${BUILD_DIR}/ax25-apps-${APPS_VER}"
  echo "== ax25-apps ${APPS_VER} -> ${PREFIX}"
  extract "${VENDOR}/ax25-apps-${APPS_VER}.tar.gz" "$dir"
  apply_patches "$dir" "${PATCHES}/ax25-apps-0.0.8-termios.patch"
  ax25_link_flags
  (
    cd "$dir"
    ./configure --prefix="$PREFIX"
    "${MAKE:-make}" -j"$(nproc 2>/dev/null || echo 2)"
    "${MAKE:-make}" install
  )
}

[[ "$NEED_LIBAX25" -eq 1 ]] && build_libax25
[[ "$NEED_TOOLS" -eq 1 ]] && build_ax25_tools
[[ "$NEED_APPS" -eq 1 ]] && build_ax25_apps

echo "== AX.25 deps ready under ${PREFIX} =="
