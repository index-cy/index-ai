#!/usr/bin/env bash
# coWork CRM API helper — thin wrapper around curl.
#
# Usage:
#   cowork-api.sh GET  /api/v2/properties?limit=10
#   cowork-api.sh POST /api/v2/properties '{"name":"Test"}'
#   cowork-api.sh PUT  /api/v2/properties/UUID '{"status":"available"}'
#   cowork-api.sh DELETE /api/v2/properties/UUID
#
# Credentials are injected by Claude Code via CLAUDE_PLUGIN_OPTION_* env vars
# from the userConfig defined in plugin.json.

set -euo pipefail

COWORK_URL="${CLAUDE_PLUGIN_OPTION_COWORK_BASE_URL:-}"
COWORK_KEY="${CLAUDE_PLUGIN_OPTION_COWORK_API_KEY:-}"

if [[ -z "$COWORK_URL" || -z "$COWORK_KEY" ]]; then
  echo '{"error":"not_configured","message":"coWork CRM credentials not set. Reinstall the plugin or update your plugin config to set cowork_base_url and cowork_api_key."}' >&2
  exit 1
fi

# Strip trailing slash from base URL
COWORK_URL="${COWORK_URL%/}"

METHOD="${1:?Usage: cowork-api.sh METHOD PATH [BODY]}"
PATH_SEGMENT="${2:?Usage: cowork-api.sh METHOD PATH [BODY]}"
BODY="${3:-}"

FULL_URL="${COWORK_URL}${PATH_SEGMENT}"

CURL_ARGS=(
  -s -S
  -X "$METHOD"
  -H "Content-Type: application/json"
  -H "Accept: application/json"
  -H "Authorization: Bearer ${COWORK_KEY}"
  --max-time 30
)

if [[ -n "$BODY" ]]; then
  CURL_ARGS+=(-d "$BODY")
fi

curl "${CURL_ARGS[@]}" "$FULL_URL"
