# Real Estate Broker — Claude Code Plugin

Real estate broker toolkit for **coWork CRM** and **WhatsApp** (WaSender API).  
Manage listings, leads, viewings, follow-ups, and send property selections to clients — all from Claude Code.

---

## Install

From the INDEX AI marketplace:

```
/plugin install real-estate-broker@index-ai
```

During installation, you'll be prompted for:

| Credential | Where to find it |
|-----------|-----------------|
| **coWork API URL** | Your instance URL, e.g. `https://yourcompany.cowork.io` |
| **coWork API Key** | Settings > API in your coWork dashboard |
| **WaSender API Key** | Your WaSender dashboard at wasenderapi.com |

Sensitive credentials are stored in your system keychain — never in plaintext config files.

---

## What's Inside

### Skills (auto-triggered by Claude)

| Skill | Triggers on | What it does |
|-------|------------|-------------|
| **daily-summary** | "daily summary", "morning briefing", "what's on my plate" | Tasks, leads, pipeline snapshot |
| **follow-up-reminders** | "who needs follow-up", "overdue follow-ups" | Flags stale deals by urgency |
| **lead-capture** | "new inquiry", "capture lead", "process this email" | Parses inquiries, creates CRM contacts |
| **send-properties** | "send properties to", "WhatsApp listings to" | Formats and sends via WhatsApp |
| **import-listing** | Paste a Bazaraki/Index/BSC URL | Scrapes, maps fields, creates in CRM |
| **appointment-scheduling** | "schedule a viewing", "book appointment" | Creates task + sends WhatsApp confirmation |
| **property-matching** | "match properties for", "find listings for" | Scores properties against buyer prefs |
| **update-opportunity** | "update the deal", "move to next stage" | Pipeline stage changes with notes |

### Commands (slash commands)

| Command | Description |
|---------|------------|
| `/new-lead` | Quick-create a lead from email or manual entry |

---

## How It Works

This plugin uses **direct API calls** (no MCP servers required). Two shell scripts handle authentication:

- `scripts/cowork-api.sh` — calls coWork CRM REST API
- `scripts/wasender-api.sh` — calls WaSender WhatsApp API

Credentials are injected automatically by Claude Code as environment variables from the `userConfig` you filled in at install time. Skills tell Claude *what* to do and *which API calls* to make. Claude runs the shell scripts, reads the JSON responses, and acts accordingly.

---

## Updates

The plugin auto-updates from this GitHub repo. When we push changes, everyone gets the new version on their next Claude Code session.

---

## Reconfigure Credentials

To update your API credentials, go to your Claude Code settings and edit the plugin configuration for `real-estate-broker`.

---

## Requirements

- [Claude Code](https://claude.ai/code) (CLI, desktop, or web)
- A coWork CRM account with API access enabled
- A WaSender API account with an active WhatsApp session
- `curl` (pre-installed on macOS/Linux)

---

## Security

- Sensitive API keys are stored in the system keychain (macOS Keychain / Windows Credential Manager)
- Non-sensitive config (like the API URL) is stored in Claude Code settings
- API keys are never committed to git or sent anywhere except to their respective APIs
- All API communication uses HTTPS

---

## License

MIT
