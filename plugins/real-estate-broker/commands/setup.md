---
description: Configure Qobrix CRM and WaSender API credentials
allowed-tools: [Bash, AskUserQuestion, Read, Write]
---

# Setup Real Estate Broker Plugin

Configure or reconfigure API credentials for the Qobrix CRM and WaSender WhatsApp integrations. Works in both **Claude Code** and **Claude Cowork** — credentials are stored in the persistent `.claude` directory so you only set up once.

User arguments: $ARGUMENTS

If the user passed "reset" or "reconfigure", delete the existing credentials file first.

## Steps

1. **Resolve the credentials directory.** This path differs between Claude Code (persistent `$HOME`) and Cowork (sandboxed `$HOME`, persistent mount at `/sessions/*/mnt/.claude`). Run this snippet first to compute `$CLAUDE_DIR`:

   ```bash
   CLAUDE_DIR=""
   if [[ -d /sessions ]]; then
     for d in /sessions/*/mnt/.claude; do
       [[ -d "$d" ]] && CLAUDE_DIR="$d" && break
     done
   fi
   [[ -z "$CLAUDE_DIR" ]] && CLAUDE_DIR="$HOME/.claude"
   echo "Using: $CLAUDE_DIR"
   ```

   Use `$CLAUDE_DIR` for all subsequent paths.

2. **Check if credentials already exist:**
   ```bash
   cat "$CLAUDE_DIR/plugins/data/real-estate-broker/credentials.json" 2>/dev/null
   ```

3. If credentials exist and user didn't say "reset", show current config (masked) and ask if they want to update.

4. **Collect credentials from the user.** Ask for all at once:
   - **Qobrix API URL** — must start with `https://`, e.g. `https://yourcompany.eu1.qobrix.com`
   - **Qobrix API Key** — long alphanumeric token from Settings > API
   - **Qobrix API User** — the User ID (UUID) shown when generating the API key
   - **WaSender API Key** — token from wasenderapi.com

5. **Store credentials:**
   ```bash
   mkdir -p "$CLAUDE_DIR/plugins/data/real-estate-broker"
   cat > "$CLAUDE_DIR/plugins/data/real-estate-broker/credentials.json" << 'CREDENTIALS'
   {
     "qobrix_api_url": "VALUE",
     "qobrix_api_key": "VALUE",
     "qobrix_api_user": "VALUE",
     "wasender_api_key": "VALUE"
   }
   CREDENTIALS
   chmod 600 "$CLAUDE_DIR/plugins/data/real-estate-broker/credentials.json"
   ```

6. **Verify Qobrix connection:**
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/properties?limit=1"
   ```

7. **Verify WaSender connection:**
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" GET "/api/status"
   ```

8. **Report results:**
   - If both succeed: show connected status and suggest next actions ("daily summary", "import listing", etc.)
   - If one fails: show the error and offer to re-enter that credential
