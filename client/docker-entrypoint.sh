#!/bin/sh
set -e

BACKEND_URL="${VITE_API_URL:-http://localhost:8000}"
BACKEND_HOST="${BACKEND_URL#*://}"
BACKEND_HOST="${BACKEND_HOST%%/*}"

# Ures apiUrl: a frontend same-origin /try-on-t hiv (nginx proxy)
cat > /usr/share/nginx/html/config.js <<'EOF'
window.__RUNTIME_CONFIG__ = { apiUrl: "" };
EOF

sed \
  -e "s|__BACKEND_URL__|${BACKEND_URL}|g" \
  -e "s|__BACKEND_HOST__|${BACKEND_HOST}|g" \
  /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
