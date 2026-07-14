# WebSocket transport (browser terminal)

> **Status: DEV-Level 3 — planned.**  
> Implementation waits until **DEV-Level 1** (modular TCP/IP + Linux/FreeBSD compat) and **DEV-Level 2** (supervision, cross-host, `max25-tun`) are solid. The hyBBX-style stack (PHP UI, loopback WebSocket proxy, nginx/Apache/lighttpd examples) exists as a **scaffold** under `stacks/web/`. It is **not** a supported production surface in MAX25-Stack v1.0.0. This document describes the **target design** and current work-in-progress layout.

**Roadmap:** [V2.0.0-SCOPE.md](V2.0.0-SCOPE.md#dev-levels-roadmap-stack-wide).

**MAX25-Stack** — browser access to **max25d** M25/1 via a WebSocket forward-proxy on loopback. Public TLS terminates on **nginx**, **Apache httpd**, or **lighttpd**; the daemon does not serve PHP or static files.

This will be the **first Web UI step** — a terminal page for M25/1 commands. It is **not** a replacement for `max25-terminal` (text client stays canonical for live operator sessions). See [MAX25-TERMINAL.md](MAX25-TERMINAL.md).

---

## Implementation roadmap

| DEV-Level | Scope | Status |
|-----------|--------|--------|
| **DEV-Level 1** (*ca.* current) | Modular TCP/IP + Linux/FreeBSD platform base | **active** — gates WebSocket work |
| **DEV-Level 2** (*ca.*) | Main + Secondary supervision · cross-host · `max25-tun` | **planned** |
| **Scaffold** | PHP/JS UI shell, Python `max25-ws-proxy`, httpd config examples, dev helper, smoke test | **In tree** — experimental only |
| **DEV-Level 3** (*ca.* target) | Production-hardened proxy, operator docs, systemd integration, release install path | **Planned** |
| **Later** | Admin/monitoring dashboard (separate from browser terminal) · AI/assistant | **Deferred** |

Until DEV-Level 3 ships, use **`max25-terminal`** for all operator sessions.

---

## Layout

```
$SRC/                                 MAX25-Stack checkout
├── stacks/web/
│   ├── proxy/max25-ws-proxy.py       loopback WebSocket → M25/1 TCP
│   └── share/reverse-proxy/
│       ├── docroot/max25-websocket/  → copy to HTTPD_DOCROOT
│       ├── nginx.conf.example
│       ├── apache2.conf.example
│       └── lighttpd.conf.example
└── docs/WEBSOCKET.md                 (this file)

$HTTPD_DOCROOT/max25-websocket/       served by httpd
├── index.php
└── max25-terminal.js
```

After `cmake --install` (when Web UI build is enabled): `$PREFIX/share/max25/reverse-proxy/` and `$PREFIX/bin/max25-ws-proxy`.

**Current tree:** sources live in `stacks/web/`; dev smoke test only — not part of v1.0.0 release gates.

---

## Steps (production — target, not yet released)

1. **`max25d`** running with M25/1 TCP (default `0.0.0.0:7325` or loopback-only).
2. **`web-proxy.ini`** — copy `share/max25/web-proxy.ini.example` to `/etc/max25/web-proxy.ini`.
3. **`max25-ws-proxy`** — listens `127.0.0.1:7326`, path `/max25`, forwards to `127.0.0.1:7325`.
4. **Copy UI** to httpd document root:
   ```sh
   HTTPD_DOCROOT=/srv/www
   cp -r $PREFIX/share/max25/reverse-proxy/docroot/max25-websocket $HTTPD_DOCROOT/
   ```
5. **httpd snippet** — one section below; adjust `HTTPD_DOCROOT` and PHP-FPM socket paths.

| Public URL | Handler |
|------------|---------|
| `GET /max25-websocket/` | httpd → PHP + `max25-terminal.js` |
| `WS /max25-websocket/ws` | httpd reverse-proxy → `ws://127.0.0.1:7326/max25` |

Keep proxy idle timeouts at **3600s** or higher (long-lived sessions).

---

## web-proxy.ini

```ini
[proxy]
bind = 127.0.0.1
port = 7326
path = /max25
max_connections = 10

[upstream]
host = 127.0.0.1
port = 7325
tcp_password =
```

| Key | Default | Role |
|-----|---------|------|
| `port` | `7326` | Loopback WebSocket listen |
| `path` | `/max25` | Upgrade path (httpd maps `…/ws` here) |
| `upstream.port` | `7325` | max25d M25/1 TCP |
| `upstream.tcp_password` | *(empty)* | When `max25d.ini` has `tcp_password`, set the same value — proxy sends `AUTH` once |

Env: `MAX25_WEB_PROXY_INI` overrides config path.

---

## systemd (optional)

Example unit: `share/max25/max25-ws-proxy.service.example`

```sh
sudo cp $PREFIX/share/max25/max25-ws-proxy.service.example /etc/systemd/system/max25-ws-proxy.service
sudo systemctl daemon-reload
sudo systemctl enable --now max25-ws-proxy
```

Requires `max25d` already running.

---

## nginx

Set `root` to `HTTPD_DOCROOT` (example `/srv/www`).

```nginx
location = /max25-websocket/ws {
    proxy_pass http://127.0.0.1:7326/max25;
    proxy_http_version 1.1;
    proxy_socket_keepalive on;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
}

location /max25-websocket/ {
    root /srv/www;
    index index.php;
    location ~ \.php$ {
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_pass unix:/run/php-fpm/www.sock;
    }
}
```

Full file: `$PREFIX/share/max25/reverse-proxy/nginx.conf.example`

```sh
nginx -t && systemctl reload nginx
```

---

## Apache httpd 2.4

```apache
<IfModule mod_proxy.c>
    ProxyPreserveHost On
    ProxyTimeout 3600

    ProxyPass "/max25-websocket/ws" "ws://127.0.0.1:7326/max25" timeout=3600 keepalive=On
    ProxyPassReverse "/max25-websocket/ws" "ws://127.0.0.1:7326/max25"
</IfModule>

Alias /max25-websocket /srv/www/max25-websocket
<Directory /srv/www/max25-websocket>
    DirectoryIndex index.php
    Require all granted
    <FilesMatch \.php$>
        SetHandler application/x-httpd-php
    </FilesMatch>
</Directory>
```

Full file: `$PREFIX/share/max25/reverse-proxy/apache2.conf.example`

---

## lighttpd 1.4

```lighttpd
server.max-read-idle = 3600
server.max-write-idle = 3600

$HTTP["url"] == "/max25-websocket/ws" {
    proxy.server = ( "" => (
        "max25" => (
            "proxy"   => "http://127.0.0.1:7326/max25",
            "upgrade" => "enable"
        )
    ))
    proxy.header = ( "upgrade" => "enable" )
}

alias.url += ( "/max25-websocket/" => "/srv/www/max25-websocket/" )
```

Full file: `$PREFIX/share/max25/reverse-proxy/lighttpd.conf.example`

---

## Local development (scaffold — developers only)

From `$SRC`:

```bash
# Terminal 1 — max25d
python3 stacks/daemon/max25d.py --tcp-port 7325

# Terminal 2 — dev helper (proxy + PHP)
./stacks/web/scripts/dev-server.sh
```

Browser: `http://127.0.0.1:8080/` — try `GET STATUS`, `PING`, `GET DEVICES`.

Details: [stacks/web/README.md](../stacks/web/README.md).

---

## Architecture

```
Browser
  │
  ├─ GET /max25-websocket/ ──► httpd + PHP (index.php, max25-terminal.js)
  │
  └─ WS  /max25-websocket/ws ──► httpd reverse-proxy
                                   └─ ws://127.0.0.1:7326/max25
                                        └─ max25-ws-proxy (RFC6455)
                                             └─ TCP M25/1 → max25d :7325
```

M25/1 uses `\n` line endings. The proxy forwards bytes after the connect handshake (`OK` / `STATUS` or `AUTH`).

---

## Security

- WebSocket proxy binds **loopback only** by default — public access only through TLS on httpd.
- Match `tcp_password` in `web-proxy.ini` when max25d requires TCP auth.
- Browser UI has no built-in operator auth beyond what max25d enforces on M25/1.

---

## Related

- [MAX25-TERMINAL.md](MAX25-TERMINAL.md) — operator client vs Web UI roadmap
- [MAX25-CLIENT.md](MAX25-CLIENT.md) — M25/1 client contract
- [include/max25/protocol.md](../include/max25/protocol.md) — protocol spec
- [PATHS.md](PATHS.md) — `$PREFIX`, `$ETC_MAX25`
