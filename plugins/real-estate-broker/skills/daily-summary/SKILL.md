---
name: daily-summary
description: >
  Generate a daily briefing for the broker with tasks, follow-ups, appointments,
  new leads, and pipeline status. Use when the user says "daily summary", "morning
  briefing", "what do I need to do today", "what's on my plate", "start my day",
  "brief me", or asks for an overview of their current workload.
version: 1.0.0
---

# Daily Summary / Morning Briefing

Compile a comprehensive daily briefing pulling data from coWork CRM and WhatsApp.

## API Access

All API calls use the helper scripts. See `references/api-cheatsheet.md` for full endpoint reference.

```bash
# coWork CRM
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cowork-api.sh" METHOD "/api/v2/ENDPOINT" '[BODY]'

# WaSender WhatsApp
bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" METHOD "/api/ENDPOINT" '[BODY]'
```

If either script returns `"error":"not_configured"`, tell the user to reinstall the plugin or check their plugin configuration.

## Workflow

Gather data from coWork CRM in parallel where possible, then present a structured briefing.

### 1. Gather Data

**Today's tasks:**
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cowork-api.sh" GET "/api/v2/tasks?search=status%20%3D%3D%20%22pending%22%20and%20start_date%20%3C%3D%20TODAY&limit=50"
```

**Overdue tasks:**
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cowork-api.sh" GET "/api/v2/tasks?search=status%20%3D%3D%20%22pending%22%20and%20end_date%20%3C%20TODAY&limit=50"
```

**New/unprocessed leads:**
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cowork-api.sh" GET "/api/v2/opportunities?search=stage%20%3D%3D%20%22new%22&limit=25"
```

**Pipeline overview (count by stage):**
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cowork-api.sh" GET "/api/v2/opportunities?limit=100"
```
Group results client-side by `stage` to build counts.

**WhatsApp status (optional):**
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" GET "/api/status"
```

### 2. Compile Briefing

Present the briefing in this structure:

```
Good morning! Here's your daily briefing for {date}:

TODAY'S TASKS ({count})
{List each task: type icon + title + related contact/property + time if scheduled}
- 10:00 — Viewing at {property} with {contact}
- 14:00 — Follow-up call with {contact}
- Send contract to {contact}

OVERDUE ({count})
{List overdue tasks with how many days overdue}
- {task} — {X} days overdue

NEW LEADS ({count})
{List new unprocessed leads with source}
- {Name} — interested in {type} in {location} (via {source})

PIPELINE SNAPSHOT
- New: {count}
- Contacted: {count}
- Viewing: {count}
- Offer: {count}
- Negotiation: {count}
- Won this month: {count}

SUGGESTED ACTIONS
{Based on the data, suggest 2-3 priority actions for the day}
```

### 3. Offer Follow-ups

After presenting the briefing, offer:
- "Want me to send follow-up messages to any overdue contacts?"
- "Should I prepare property selections for the new leads?"
- "Want details on any of these items?"

## Important Notes

- Keep the briefing scannable — use short lines and clear sections.
- Highlight the most urgent items (overdue tasks, hot leads, upcoming viewings).
- If there are no items in a section, skip it rather than showing "0 items."
- The pipeline snapshot helps the broker see their overall business health at a glance.
