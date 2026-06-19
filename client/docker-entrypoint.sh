#!/bin/sh
set -e

# Cloud Run runtime env-bol generaljuk a config.js-t (build-time VITE_ valtozok nem mukodnek nginx kontenerben)
API_URL="${VITE_API_URL:-}"
cat > /usr/share/nginx/html/config.js <<EOF
window.__RUNTIME_CONFIG__ = { apiUrl: "${API_URL}" };
EOF

exec nginx -g 'daemon off;'
