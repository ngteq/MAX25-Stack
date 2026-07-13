MAX25 reverse-proxy examples. WebSocket proxy = M25/1 data on loopback only.

1. HTTPD_DOCROOT=/srv/www   # your httpd document root
2. cp -r docroot/max25-websocket $HTTPD_DOCROOT/
3. Add nginx/apache/lighttpd snippet (adjust paths)
4. web-proxy.ini — see stacks/web/README.md
