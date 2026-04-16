---
description: Configure Qobrix CRM and WaSender API credentials
allowed-tools: [Bash, AskUserQuestion, Read, Write]
---

# Setup Real Estate Broker Plugin

Configure or reconfigure API credentials for the Qobrix CRM and WaSender WhatsApp integrations.

User arguments: $ARGUMENTS

If the user passed "reset" or "reconfigure", delete the existing credentials file first.

## Steps

1. Check if credentials already exist:
   ```bash
   cat "$HOME/.claude/plugins/data/real-estate-broker/credentials.json" 2>/dev/null
   ```

2. If credentials exist and user didn't say "reset", show current config (masked) and ask if they want to update.

3. Collect credentials from the user. Ask for all at once:
   - **Qobrix API URL** — must start with `https://`, e.g. `https://yourcompany.eu1.qobrix.com`
   - **Qobrix API Key** — long alphanumeric token from Settings > API
   - **Qobrix API User** — email of the API user account
   - **WaSender API Key** — token from wasenderapi.com

4. Store credentials:
   ```bash
   mkdir -p "$HOME/.claude/plugins/data/real-estate-broker"
   cat > "$HOME/.claude/plugins/data/real-estate-broker/credentials.json" << 'CREDENTIALS'
   {
     "qobrix_api_url": "VALUE",
     "qobrix_api_key": "VALUE",
     "qobrix_api_user": "VALUE",
     "wasender_api_key": "VALUE"
   }
   CREDENTIALS
   chmod 600 "$HOME/.claude/plugins/data/real-estate-broker/credentials.json"
   ```

5. Verify Qobrix connection:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/users/self"
   ```

6. Verify WaSender connection:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" GET "/api/status"
   ```

7. Report results:
   - If both succeed: show connected status and suggest next actions
   - If one fails: show the error and offer to re-enter that credential
