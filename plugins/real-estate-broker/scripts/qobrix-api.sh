#!/usr/bin/env bash
# Qobrix CRM API helper — thin wrapper around curl.
#
# Usage:
#   qobrix-api.sh GET  /api/v2/properties?limit=10
#   qobrix-api.sh POST /api/v2/properties '{"name":"Test"}'
#   qobrix-api.sh PUT  /api/v2/properties/UUID '{"status":"available"}'
#   qobrix-api.sh DELETE /api/v2/properties/UUID
#
# Credentials are read from ~/.claude/plugins/data/real-estate-broker/credentials.json
# Run /setup to configure.

set -euo pipefail

CREDS_FILE="$HOME/.claude/plugins/data/real-estate-broker/credentials.json"

if [[ ! -f "$CREDS_FILE" ]]; then
  echo '{"error":"not_configured","message":"Plugin not configured. Run /setup to enter your Qobrix CRM and WaSender API credentials."}' >&2
  exit 1
fi

QOBRIX_URL=$(python3 -c "import json; print(json.load(open('$CREDS_FILE'))['qobrix_api_url'])" 2>/dev/null)
QOBRIX_KEY=$(python3 -c "import json; print(json.load(open('$CREDS_FILE'))['qobrix_api_key'])" 2>/dev/null)
QOBRIX_USER=$(python3 -c "import json; print(json.load(open('$CREDS_FILE'))['qobrix_api_user'])" 2>/dev/null)

if [[ -z "$QOBRIX_URL" || -z "$QOBRIX_KEY" ]]; then
  echo '{"error":"missing_credentials","message":"Qobrix API URL or key is missing. Run /setup to reconfigure."}' >&2
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
  -H "X-Api-Key: ${QOBRIX_KEY}"
  -H "X-Api-User: ${QOBRIX_USER}"
  --max-time 30
)

if [[ -n "$BODY" ]]; then
  CURL_ARGS+=(-d "$BODY")
fi

curl "${CURL_ARGS[@]}" "$FULL_URL"
