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
#   1. CLAUDE_PLUGIN_OPTION_* env vars (if userConfig support lands)
#   2. Cowork persistent mount: /sessions/*/mnt/.claude/...
#   3. Local Claude Code: $HOME/.claude/...

set -euo pipefail

# Prefer env vars (future-proofing for userConfig)
QOBRIX_URL="${CLAUDE_PLUGIN_OPTION_QOBRIX_API_URL:-}"
QOBRIX_KEY="${CLAUDE_PLUGIN_OPTION_QOBRIX_API_KEY:-}"
QOBRIX_USER="${CLAUDE_PLUGIN_OPTION_QOBRIX_API_USER:-}"

# Resolve the Claude data directory: prefer Cowork persistent mount
CLAUDE_DIR=""
if [[ -d /sessions ]]; then
  for d in /sessions/*/mnt/.claude; do
    [[ -d "$d" ]] && CLAUDE_DIR="$d" && break
  done
fi
[[ -z "$CLAUDE_DIR" ]] && CLAUDE_DIR="$HOME/.claude"

CREDS_FILE="$CLAUDE_DIR/plugins/data/real-estate-broker/credentials.json"

# Fall back to credentials file for any unset value
if [[ -f "$CREDS_FILE" ]]; then
  [[ -z "$QOBRIX_URL"  ]] && QOBRIX_URL=$(python3  -c "import json; print(json.load(open('$CREDS_FILE')).get('qobrix_api_url',''))"  2>/dev/null || echo "")
  [[ -z "$QOBRIX_KEY"  ]] && QOBRIX_KEY=$(python3  -c "import json; print(json.load(open('$CREDS_FILE')).get('qobrix_api_key',''))"  2>/dev/null || echo "")
  [[ -z "$QOBRIX_USER" ]] && QOBRIX_USER=$(python3 -c "import json; print(json.load(open('$CREDS_FILE')).get('qobrix_api_user',''))" 2>/dev/null || echo "")
fi

if [[ -z "$QOBRIX_URL" || -z "$QOBRIX_KEY" || -z "$QOBRIX_USER" ]]; then
  echo '{"error":"not_configured","message":"Qobrix credentials not set. Run /setup to configure them."}' >&2
  exit 1
fi

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
