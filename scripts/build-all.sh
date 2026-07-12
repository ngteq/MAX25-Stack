#!/usr/bin/env bash
# MainAX25-Stack (MAX25-Stack) — build all merged stacks.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== MainAX25-Stack (MAX25-Stack) build-all =="

if [[ -f stacks/tncs/Makefile ]]; then
  echo "-- stacks/tncs"
  make -C stacks/tncs all
fi

if [[ -f stacks/baycom-pr/Makefile ]]; then
  echo "-- stacks/baycom-pr"
  make -C stacks/baycom-pr all
fi

echo "== plugin discovery =="
bash scripts/discover-plugins.sh

echo "== done =="
