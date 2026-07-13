Copy docroot/max25-websocket/ to HTTPD_DOCROOT (not $PREFIX).
max25-ws-proxy serves M25/1 on loopback only (default 127.0.0.1:7326).

  HTTPD_DOCROOT=/srv/www
  cp -r docroot/max25-websocket $HTTPD_DOCROOT/

Match URL paths in web-proxy.ini and the httpd snippets in stacks/web/README.md.
