---
name: follow-up-reminders
description: >
  Track customer follow-ups and flag contacts who haven't been reached in too long.
  Use when the user says "who needs follow-up", "overdue follow-ups", "who haven't
  I contacted", "check follow-ups", "follow-up reminders", or wants to see which
  customers need attention.
version: 1.0.0
---

# Follow-up Reminders

Identify contacts and opportunities that need follow-up based on last activity date and deal stage.

## API Access

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" METHOD "/api/v2/ENDPOINT" '[BODY]'
bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" METHOD "/api/ENDPOINT" '[BODY]'
```

If either script returns `"error":"not_configured"`, tell the user to run `/setup` to configure their API credentials.

## Workflow

1. **Get overdue tasks.**
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/tasks?search=status%20%3D%3D%20%22pending%22%20and%20end_date%20%3C%20TODAY&limit=50"
   ```

2. **Get active opportunities.**
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/opportunities?search=stage%20not%20in%20%5B%22closed_won%22%2C%22closed_lost%22%5D&limit=100"
   ```
   For each, check the activity log:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/activity-logs?related_to={opportunity_id}&limit=5"
   ```

3. **Apply follow-up rules** based on deal stage:

   | Stage | Max days since last contact | Urgency |
   |-------|---------------------------|---------|
   | new | 1 day | CRITICAL — respond ASAP |
   | contacted | 3 days | HIGH — maintain momentum |
   | viewing | 2 days | HIGH — get feedback or schedule |
   | offer | 1 day | CRITICAL — deals can slip |
   | negotiation | 2 days | CRITICAL — keep it moving |

4. **Present the follow-up list** sorted by urgency:

   ```
   FOLLOW-UP NEEDED ({count} contacts)

   CRITICAL
   - {Contact Name} — {Stage} — last contact {X} days ago
     Deal: {Property/opportunity summary}
     Suggested: {call / WhatsApp / email}

   HIGH
   - {Contact Name} — {Stage} — last contact {X} days ago
     Deal: {Property/opportunity summary}

   DUE SOON
   - {Contact Name} — due for follow-up tomorrow
   ```

5. **Offer actions:**
   - "Want me to draft WhatsApp messages for the critical follow-ups?"
   - "Should I schedule follow-up calls in Qobrix?"
   - "Want me to send a batch message to contacts in the 'contacted' stage?"

## Quick Follow-up Actions

When the user picks a contact to follow up with, offer to:

- Draft and send a WhatsApp message:
  ```bash
  bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" POST "/api/send-message" '{"to":"{phone}","text":"{message}"}'
  ```
- Create a follow-up task in Qobrix:
  ```bash
  bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" POST "/api/v2/tasks" '{"title":"Follow up with {name}","due_date":"{date}","contact_id":"{id}","type":"follow_up"}'
  ```
- Update the opportunity notes

## Important Notes

- The follow-up thresholds above are defaults. The user may want to customize them.
- Weekend days should ideally not count toward the threshold (business days only).
- For "closed_won" and "closed_lost" deals, don't flag follow-ups unless specifically asked.
- Group follow-ups by urgency, not alphabetically, so the broker focuses on what matters most.
