#!/usr/bin/env bash
# WaSender WhatsApp API helper — thin wrapper around curl.
#
# Usage:
#   wasender-api.sh POST /api/send-message '{"to":"35799123456","text":"Hello"}'
#   wasender-api.sh GET  /api/status
#
# Credential resolution order:
#   1. CLAUDE_PLUGIN_OPTION_WASENDER_API_KEY env var (from userConfig)
#   2. ~/.claude/plugins/data/real-estate-broker/credentials.json (from /setup)

set -euo pipefail

WASENDER_KEY="${CLAUDE_PLUGIN_OPTION_WASENDER_API_KEY:-}"

CREDS_FILE="$HOME/.claude/plugins/data/real-estate-broker/credentials.json"
if [[ -z "$WASENDER_KEY" && -f "$CREDS_FILE" ]]; then
  WASENDER_KEY=$(python3 -c "import json; print(json.load(open('$CREDS_FILE')).get('wasender_api_key',''))" 2>/dev/null || echo "")
fi

if [[ -z "$WASENDER_KEY" ]]; then
  echo '{"error":"not_configured","message":"WaSender API key not set. Either reinstall the plugin and enter credentials when prompted, or run /setup to configure them."}' >&2
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
