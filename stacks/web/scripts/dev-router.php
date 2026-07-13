<?php
/**
 * PHP built-in server router for local dev (direct loopback WebSocket URL).
 */
$uri = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
$root = __DIR__ . '/../share/reverse-proxy/docroot/max25-websocket';

if ($uri === '/' || $uri === '/index.php') {
    $ws_url = getenv('MAX25_DEV_WS_URL') ?: 'ws://127.0.0.1:7326/max25';
    require $root . '/index.php';
    return true;
}

$file = $root . $uri;
if (is_file($file)) {
    return false;
}

http_response_code(404);
echo "not found\n";
return true;
