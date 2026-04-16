#!/usr/bin/env bash
# WaSender WhatsApp API helper — thin wrapper around curl.
#
# Usage:
#   wasender-api.sh POST /api/send-message '{"to":"35799123456","text":"Hello"}'
#   wasender-api.sh GET  /api/status
#
# Credentials are read from ~/.claude/plugins/data/real-estate-broker/credentials.json
# Run /setup to configure.

set -euo pipefail

CREDS_FILE="$HOME/.claude/plugins/data/real-estate-broker/credentials.json"

if [[ ! -f "$CREDS_FILE" ]]; then
  echo '{"error":"not_configured","message":"Plugin not configured. Run /setup to enter your Qobrix CRM and WaSender API credentials."}' >&2
  exit 1
fi

WASENDER_KEY=$(python3 -c "import json; print(json.load(open('$CREDS_FILE'))['wasender_api_key'])" 2>/dev/null)

if [[ -z "$WASENDER_KEY" ]]; then
  echo '{"error":"missing_credentials","message":"WaSender API key is missing. Run /setup to reconfigure."}' >&2
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
