#!/usr/bin/env bash
# Qobrix CRM API helper — thin wrapper around curl.
#
# Usage:
#   qobrix-api.sh GET  /api/v2/properties?limit=10
#   qobrix-api.sh POST /api/v2/properties '{"name":"Test"}'
#   qobrix-api.sh PUT  /api/v2/properties/UUID '{"status":"available"}'
#   qobrix-api.sh DELETE /api/v2/properties/UUID
#
# Credentials are injected by Claude Code via CLAUDE_PLUGIN_OPTION_* env vars
# from the userConfig defined in plugin.json.

set -euo pipefail

QOBRIX_URL="${CLAUDE_PLUGIN_OPTION_QOBRIX_API_URL:-}"
QOBRIX_KEY="${CLAUDE_PLUGIN_OPTION_QOBRIX_API_KEY:-}"
QOBRIX_USER="${CLAUDE_PLUGIN_OPTION_QOBRIX_API_USER:-}"

if [[ -z "$QOBRIX_URL" || -z "$QOBRIX_KEY" ]]; then
  echo '{"error":"not_configured","message":"Qobrix CRM credentials not set. Reinstall the plugin or update your plugin config to set qobrix_api_url, qobrix_api_key, and qobrix_api_user."}' >&2
  exit 1
fi

# Strip trailing slash from base URL
QOBRIX_URL="${QOBRIX_URL%/}"

METHOD="${1:?Usage: qobrix-api.sh METHOD PATH [BODY]}"
PATH_SEGMENT="${2:?Usage: qobrix-api.sh METHOD PATH [BODY]}"
BODY="${3:-}"

FULL_URL="${QOBRIX_URL}${PATH_SEGMENT}"

CURL_ARGS=(
  -s -S
  -X "$METHOD"
  -H "Content-Type: application/json"
  -H "Accept: application/json"
  -H "Authorization: Bearer ${QOBRIX_KEY}"
  -H "X-Api-User: ${QOBRIX_USER}"
  --max-time 30
)

if [[ -n "$BODY" ]]; then
  CURL_ARGS+=(-d "$BODY")
fi

curl "${CURL_ARGS[@]}" "$FULL_URL"
