#!/usr/bin/env bash
# Local dev: max25-ws-proxy + PHP built-in server (direct WebSocket to loopback proxy).
set -euo pipefail

SRC="$(cd "$(dirname "$0")/../.." && pwd)"
WEB="$SRC/stacks/web"
DOCROOT="$WEB/share/reverse-proxy/docroot/max25-websocket"
PROXY_INI="${MAX25_WEB_PROXY_INI:-$WEB/share/web-proxy.ini.example}"
PHP_HOST="${MAX25_WEB_PHP_HOST:-127.0.0.1}"
PHP_PORT="${MAX25_WEB_PHP_PORT:-8080}"
PROXY_PORT="${MAX25_WEB_PROXY_PORT:-7326}"

cleanup() {
  if [[ -n "${PROXY_PID:-}" ]]; then
    kill "$PROXY_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

echo "MAX25 web dev"
echo "  max25d expected on 127.0.0.1:7325 (start separately)"
echo "  proxy ini: $PROXY_INI"
echo "  WebSocket: ws://127.0.0.1:$PROXY_PORT/max25"
echo "  PHP UI:    http://$PHP_HOST:$PHP_PORT/"
echo ""

python3 "$WEB/proxy/max25-ws-proxy.py" -c "$PROXY_INI" --port "$PROXY_PORT" &
PROXY_PID=$!
sleep 0.3

export MAX25_DEV_WS_URL="ws://127.0.0.1:${PROXY_PORT}/max25"
php -S "$PHP_HOST:$PHP_PORT" -t "$DOCROOT" "$WEB/scripts/dev-router.php"
