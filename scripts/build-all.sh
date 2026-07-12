#!/usr/bin/env bash
# MainAX25-Stack (MAX25-Stack) — build all merged stacks.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== MainAX25-Stack (MAX25-Stack) build-all =="
bash scripts/build.sh

echo "== plugin discovery =="
bash scripts/discover-plugins.sh

echo "== done =="
