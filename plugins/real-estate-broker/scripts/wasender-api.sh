#!/usr/bin/env bash
# WaSender WhatsApp API helper — thin wrapper around curl.
#
# Usage:
#   wasender-api.sh POST /api/send-message '{"to":"35799123456","text":"Hello"}'
#   wasender-api.sh GET  /api/status
#
# Credential resolution:
#   1. CLAUDE_PLUGIN_OPTION_WASENDER_API_KEY env var
#   2. Cowork persistent mount: /sessions/*/mnt/.claude/...
#   3. Local Claude Code: $HOME/.claude/...

set -euo pipefail

WASENDER_KEY="${CLAUDE_PLUGIN_OPTION_WASENDER_API_KEY:-}"

# Resolve the Claude data directory
CLAUDE_DIR=""
if [[ -d /sessions ]]; then
  for d in /sessions/*/mnt/.claude; do
    [[ -d "$d" ]] && CLAUDE_DIR="$d" && break
  done
fi
[[ -z "$CLAUDE_DIR" ]] && CLAUDE_DIR="$HOME/.claude"

CREDS_FILE="$CLAUDE_DIR/plugins/data/real-estate-broker/credentials.json"

if [[ -z "$WASENDER_KEY" && -f "$CREDS_FILE" ]]; then
  WASENDER_KEY=$(python3 -c "import json; print(json.load(open('$CREDS_FILE')).get('wasender_api_key',''))" 2>/dev/null || echo "")
fi

if [[ -z "$WASENDER_KEY" ]]; then
  echo '{"error":"not_configured","message":"WaSender API key not set. Run /setup to configure it."}' >&2
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
