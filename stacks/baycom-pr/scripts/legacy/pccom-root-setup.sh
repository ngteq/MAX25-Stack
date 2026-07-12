#!/bin/bash
# Deprecated — use scripts/install-root.sh
exec "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/install-root.sh" "$@"
