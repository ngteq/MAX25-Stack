<?php
/**
 * MAX25 browser terminal — copy this folder to your httpd document root.
 * WebSocket data comes from max25-ws-proxy only; this file is not part of max25d.
 */
$base = rtrim(dirname($_SERVER['SCRIPT_NAME'] ?? ''), '/');
$ws_path = ($base !== '' ? $base : '/max25-websocket') . '/ws';
$scheme = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'wss' : 'ws';
$host = $_SERVER['HTTP_HOST'] ?? 'localhost';
$dev_ws = getenv('MAX25_DEV_WS_URL');
$ws_url = ($dev_ws !== false && $dev_ws !== '') ? $dev_ws : ($scheme . '://' . $host . $ws_path);
?><!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MAX25</title>
  <style>
    html, body { height: 100%; margin: 0; }
    body {
      display: flex;
      flex-direction: column;
      background: #0a0a12;
      color: #c8d0d8;
      font-family: ui-monospace, "Cascadia Mono", "Consolas", monospace;
    }
    #status {
      position: fixed;
      top: 0;
      right: 0;
      padding: .5rem 1rem;
      font-size: .8rem;
      background: #1a1a28;
      z-index: 1;
    }
    #term {
      flex: 1;
      min-height: 0;
      box-sizing: border-box;
      width: 100%;
      margin: 0;
      padding: 1rem;
      padding-bottom: .5rem;
      white-space: pre-wrap;
      overflow-y: auto;
      overflow-x: hidden;
    }
    #input-bar {
      flex: none;
      display: flex;
      width: 100%;
      box-sizing: border-box;
      border-top: 1px solid #2a2a38;
      background: #12121c;
    }
    #cmd {
      flex: 1;
      width: 100%;
      min-width: 0;
      box-sizing: border-box;
      border: none;
      border-radius: 0;
      background: #12121c;
      color: #e0e4e8;
      font: inherit;
      font-size: 1rem;
      line-height: 1.4;
      padding: .75rem 1rem;
      outline: none;
    }
    #cmd::placeholder { color: #6a7280; }
    #cmd:focus { background: #161622; }
    #cmd:disabled { opacity: .55; cursor: not-allowed; }
  </style>
</head>
<body>
  <div id="status">disconnected</div>
  <pre id="term"></pre>
  <form id="input-bar" autocomplete="off">
    <input type="text" id="cmd" disabled
           autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false"
           enterkeyhint="send"
           placeholder="M25/1 command — Enter to send (e.g. GET STATUS)">
  </form>
  <script>
    window.MAX25_WS_URL = <?php echo json_encode($ws_url, JSON_UNESCAPED_SLASHES); ?>;
  </script>
  <script src="max25-terminal.js"></script>
</body>
</html>
