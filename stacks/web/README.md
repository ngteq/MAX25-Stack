# MAX25 Web UI (DEV-Level 3 — planned)

> **Status: DEV-Level 3 — planned until TCP/IP + Linux/FreeBSD compat (DEV-Level 1) and supervision extras (DEV-Level 2) are solid.** Scaffold ported from the hyBBX reverse-proxy pattern. **Not production-ready** in MAX25-Stack v1.0.0.

**Roadmap:** [docs/V2.0.0-SCOPE.md](../../docs/V2.0.0-SCOPE.md#dev-levels-roadmap-stack-wide) · [docs/WEBSOCKET.md](../../docs/WEBSOCKET.md).

Browser terminal scaffold for **max25d** M25/1 — target architecture below.

| Layer | Component | Role |
|-------|-----------|------|
| Browser UI | PHP + JS (`share/reverse-proxy/docroot/`) | Dark terminal page; generates WebSocket URL |
| HTTP reverse-proxy | nginx / Apache / lighttpd examples | `WS /max25-websocket/ws` → loopback proxy |
| WebSocket proxy | `proxy/max25-ws-proxy.py` | RFC6455 ↔ M25/1 TCP forward (no translation) |
| Daemon | `max25d` | M25/1 on TCP `7325` (or Unix socket) |

This is **not** a replacement for `max25-terminal` — see [docs/MAX25-TERMINAL.md](../../docs/MAX25-TERMINAL.md).

## Implementation status

| Item | State |
|------|--------|
| PHP + JS UI (`docroot/max25-websocket/`) | Scaffold — hyBBX look |
| `max25-ws-proxy.py` | Scaffold — dev smoke test passes |
| httpd examples (nginx, Apache, lighttpd) | Draft configs |
| Production deploy / systemd on site | **DEV-Level 3** (planned) |
| Admin dashboard | **Later** (beyond DEV-Level 3) |

Operator doc (target design): [docs/WEBSOCKET.md](../../docs/WEBSOCKET.md).

## Quick start (local dev — developers only)

From `$SRC`:

```bash
# 1. Start max25d (another terminal)
python3 stacks/daemon/max25d.py --tcp-port 7325

# 2. Start WebSocket proxy (loopback)
python3 stacks/web/proxy/max25-ws-proxy.py -c stacks/web/share/web-proxy.ini.example -v

# 3. Serve PHP UI (another terminal)
php -S 127.0.0.1:8080 -t stacks/web/share/reverse-proxy/docroot/max25-websocket

# 4. Open browser — needs a WS path match; use the dev helper instead:
./stacks/web/scripts/dev-server.sh
```

**Recommended:** `./stacks/web/scripts/dev-server.sh` starts proxy + PHP with correct routing.

Browser: `http://127.0.0.1:8080/` (dev script) or your httpd `…/max25-websocket/`.

Try: `GET STATUS`, `PING`, `GET DEVICES`.

## Configuration

Copy `share/web-proxy.ini.example` to `/etc/max25/web-proxy.ini` (or set `MAX25_WEB_PROXY_INI`).

| Section | Key | Default | Meaning |
|---------|-----|---------|---------|
| `[proxy]` | `bind` | `127.0.0.1` | Loopback only — expose via httpd |
| `[proxy]` | `port` | `7326` | WebSocket listen port |
| `[proxy]` | `path` | `/max25` | WebSocket upgrade path |
| `[upstream]` | `host` | `127.0.0.1` | max25d host |
| `[upstream]` | `port` | `7325` | max25d TCP port |
| `[upstream]` | `tcp_password` | *(empty)* | If set, proxy sends `AUTH` on connect |

When `max25d.ini` has `[network] tcp_password` set, copy the same value into `web-proxy.ini` `[upstream] tcp_password` so browsers do not handle auth manually.

## Production deploy

```bash
cmake --install $BUILD --prefix $PREFIX
```

Installs:

- `$PREFIX/bin/max25-ws-proxy`
- `$PREFIX/share/max25/web-proxy.ini.example`
- `$PREFIX/share/max25/reverse-proxy/` (httpd snippets + `docroot/`)

Operator steps:

1. `HTTPD_DOCROOT=/srv/www`
2. `cp -r $PREFIX/share/max25/reverse-proxy/docroot/max25-websocket $HTTPD_DOCROOT/`
3. Add httpd snippet from `$PREFIX/share/max25/reverse-proxy/*.conf.example`
4. Copy and edit `web-proxy.ini`; run `max25-ws-proxy` (systemd unit — TODO)
5. Ensure `max25d` is running

## Architecture

```
Browser
  │
  ├─ GET /max25-websocket/ ──► httpd + PHP
  │                              └─ index.php + max25-terminal.js
  │
  └─ WS  /max25-websocket/ws ──► httpd reverse-proxy
                                   └─ ws://127.0.0.1:7326/max25
                                        └─ max25-ws-proxy
                                             └─ TCP 127.0.0.1:7325 (max25d M25/1)
```

M25/1 uses `\n` line endings (not hyBBX `\r`). The proxy forwards bytes after the initial connect handshake.

## TODO (near-term release)

- [ ] Production-harden `max25-ws-proxy` (packaging, logging, edge cases)
- [ ] Operator release gate + [WEBSOCKET.md](../../docs/WEBSOCKET.md) aligned with shipped behaviour
- [ ] systemd unit wired into site install docs
- [x] systemd unit example — `share/max25/max25-ws-proxy.service.example`
- [x] Dev smoke test (`max25_web_smoke`)
- [ ] Admin/monitoring pages (status dashboard — separate from browser terminal)
- [ ] RX live stream UI polish (`MONITOR`, `SEND`, device picker)
- [ ] F10-style menus — out of scope for web; keep `max25-terminal`

## Related docs

- [include/max25/protocol.md](../../include/max25/protocol.md) — M25/1 spec
- [docs/MAX25-CLIENT.md](../../docs/MAX25-CLIENT.md) — client contract
- [docs/PATHS.md](../../docs/PATHS.md) — `$SRC`, `$PREFIX`, `$ETC_MAX25`
