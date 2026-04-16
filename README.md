# INDEX AI — Claude Code Plugin Marketplace

Plugins for real estate professionals in Cyprus.  
CRM automation, WhatsApp messaging, listing imports, and lead management — powered by Claude Code.

---

## Quick Start

**1. Add the marketplace:**

```
/plugin marketplace add github:index-cy/index-ai
```

**2. Install a plugin:**

```
/plugin install real-estate-broker@index-ai
```

During installation you'll be prompted for your coWork CRM URL, API key, and WaSender API key. Sensitive keys go straight to your system keychain.

That's it. You're ready to go.

---

## Available Plugins

### real-estate-broker

Full real estate broker toolkit connecting **coWork CRM** and **WhatsApp** (WaSender API).

| Feature | What it does |
|---------|-------------|
| Daily Summary | Morning briefing with tasks, leads, and pipeline |
| Follow-up Reminders | Flags stale deals by urgency |
| Lead Capture | Parses inquiries into CRM contacts |
| Send Properties | Formats and sends listings via WhatsApp |
| Import Listing | Scrapes Bazaraki/Index/BSC URLs into CRM |
| Appointment Scheduling | Creates viewings + WhatsApp confirmations |
| Property Matching | Scores properties against buyer preferences |
| Update Opportunity | Pipeline stage management with notes |

**Requirements:** coWork CRM account with API access, WaSender API account.

[Full documentation](plugins/real-estate-broker/README.md)

---

## How It Works

- No MCP servers required — plugins use direct API calls via shell scripts
- Sensitive credentials stored in the system keychain, non-sensitive config in Claude Code settings
- Plugins auto-update when we push changes to this repo

---

## Coming Soon

More plugins are in development. If you have ideas or need a custom plugin, reach out at info@index.cy.

---

## License

MIT — see [LICENSE](LICENSE) for details.
