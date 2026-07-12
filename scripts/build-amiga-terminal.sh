#!/usr/bin/env sh
# Cross-build max25-terminal for AmigaOS 3.9+ (bebbo-gcc / clib2).
set -eu

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
SDK="${AMIGA_SDK_PATH:-/opt/amiga}"

if [ ! -x "$SDK/bin/m68k-amigaos-gcc" ]; then
    echo "Amiga SDK not found at $SDK (set AMIGA_SDK_PATH)" >&2
    exit 1
fi

make -C "$ROOT/stacks/terminal/amiga" AMIGA_SDK="$SDK" all
make -C "$ROOT/stacks/terminal/amiga" AMIGA_SDK="$SDK" test

echo "AmigaOS client:"
echo "  $ROOT/stacks/terminal/amiga/max25-terminal"
