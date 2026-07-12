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

if [[ -f stacks/crdop/Makefile ]]; then
  echo "-- stacks/crdop (CRDOP soft modem)"
  make -C stacks/crdop all
fi

if [[ -f stacks/daemon/Makefile ]]; then
  echo "-- stacks/daemon (max25d)"
  make -C stacks/daemon all
fi

if [[ -f stacks/terminal/Makefile ]]; then
  echo "-- stacks/terminal (max25-terminal)"
  make -C stacks/terminal all
fi

echo "== plugin discovery =="
bash scripts/discover-plugins.sh

echo "== done =="
