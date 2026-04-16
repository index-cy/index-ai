#!/usr/bin/env bash
# WaSender WhatsApp API helper — thin wrapper around curl.
#
# Usage:
#   wasender-api.sh POST /api/send-message '{"to":"35799123456","text":"Hello"}'
#   wasender-api.sh GET  /api/status
#
# Credentials are injected by Claude Code via CLAUDE_PLUGIN_OPTION_* env vars
# from the userConfig defined in plugin.json.

set -euo pipefail

WASENDER_KEY="${CLAUDE_PLUGIN_OPTION_WASENDER_API_KEY:-}"

if [[ -z "$WASENDER_KEY" ]]; then
  echo '{"error":"not_configured","message":"WaSender API key not set. Reinstall the plugin or update your plugin config to set wasender_api_key."}' >&2
  exit 1
fi

WASENDER_BASE="https://api.wasenderapi.com"

METHOD="${1:?Usage: wasender-api.sh METHOD PATH [BODY]}"
PATH_SEGMENT="${2:?Usage: wasender-api.sh METHOD PATH [BODY]}"
BODY="${3:-}"

FULL_URL="${WASENDER_BASE}${PATH_SEGMENT}"

CURL_ARGS=(
  -s -S
  -X "$METHOD"
  -H "Content-Type: application/json"
  -H "Accept: application/json"
  -H "Authorization: Bearer ${WASENDER_KEY}"
  --max-time 30
)

if [[ -n "$BODY" ]]; then
  CURL_ARGS+=(-d "$BODY")
fi

curl "${CURL_ARGS[@]}" "$FULL_URL"
