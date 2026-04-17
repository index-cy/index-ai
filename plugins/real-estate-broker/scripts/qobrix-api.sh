#!/usr/bin/env bash
# Qobrix CRM API helper — thin wrapper around curl.
#
# Usage:
#   qobrix-api.sh GET  /api/v2/properties?limit=10
#   qobrix-api.sh POST /api/v2/properties '{"name":"Test"}'
#   qobrix-api.sh PUT  /api/v2/properties/UUID '{"status":"available"}'
#   qobrix-api.sh DELETE /api/v2/properties/UUID
#
# Credential resolution order:
#   1. CLAUDE_PLUGIN_OPTION_* env vars (set by Claude Code from userConfig in plugin.json)
#   2. ~/.claude/plugins/data/real-estate-broker/credentials.json (created by /setup)

set -euo pipefail

# Prefer env vars injected by Claude Code from userConfig
QOBRIX_URL="${CLAUDE_PLUGIN_OPTION_QOBRIX_API_URL:-}"
QOBRIX_KEY="${CLAUDE_PLUGIN_OPTION_QOBRIX_API_KEY:-}"
QOBRIX_USER="${CLAUDE_PLUGIN_OPTION_QOBRIX_API_USER:-}"

# Fall back to local credentials file
CREDS_FILE="$HOME/.claude/plugins/data/real-estate-broker/credentials.json"
if [[ -z "$QOBRIX_URL" && -f "$CREDS_FILE" ]]; then
  QOBRIX_URL=$(python3 -c "import json; print(json.load(open('$CREDS_FILE')).get('qobrix_api_url',''))" 2>/dev/null || echo "")
fi
if [[ -z "$QOBRIX_KEY" && -f "$CREDS_FILE" ]]; then
  QOBRIX_KEY=$(python3 -c "import json; print(json.load(open('$CREDS_FILE')).get('qobrix_api_key',''))" 2>/dev/null || echo "")
fi
if [[ -z "$QOBRIX_USER" && -f "$CREDS_FILE" ]]; then
  QOBRIX_USER=$(python3 -c "import json; print(json.load(open('$CREDS_FILE')).get('qobrix_api_user',''))" 2>/dev/null || echo "")
fi

if [[ -z "$QOBRIX_URL" || -z "$QOBRIX_KEY" || -z "$QOBRIX_USER" ]]; then
  echo '{"error":"not_configured","message":"Qobrix credentials not set. Either reinstall the plugin and enter credentials when prompted, or run /setup to configure them."}' >&2
  exit 1
fi

# Strip trailing slash
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
  -H "X-Api-Key: ${QOBRIX_KEY}"
  -H "X-Api-User: ${QOBRIX_USER}"
  --max-time 30
)

if [[ -n "$BODY" ]]; then
  CURL_ARGS+=(-d "$BODY")
fi

curl "${CURL_ARGS[@]}" "$FULL_URL"
