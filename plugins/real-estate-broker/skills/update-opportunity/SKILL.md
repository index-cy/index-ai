---
name: update-opportunity
description: >
  Update an opportunity or deal in Qobrix CRM. Use when the user says "update
  the deal", "move opportunity to next stage", "update CRM", "change deal status",
  "add notes to opportunity", "update the pipeline", "mark deal as", or wants to
  modify any aspect of an existing opportunity in Qobrix.
version: 1.0.0
---

# Update Opportunity in Qobrix CRM

Modify an existing opportunity/deal in the Qobrix CRM pipeline — change stage, add notes, update amount, set next actions, or reassign.

## API Access

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" METHOD "/api/v2/ENDPOINT" '[BODY]'
```

If the script returns `"error":"not_configured"`, tell the user to run `/setup` to configure their API credentials.

## Workflow

1. **Identify the opportunity.** If the user mentions a customer name or property, search:

   By customer name:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/contacts?search=first_name%20contains%20%22{name}%22&limit=10"
   ```
   Then filter opportunities by contact:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/opportunities?search=contact_id%20%3D%3D%20%22{contact_id}%22&limit=10"
   ```

   By stage:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/opportunities?search=stage%20%3D%3D%20%22{stage}%22&limit=25"
   ```

   If multiple matches, present a numbered list and ask the user to choose.

2. **Fetch current state.**
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/opportunities/{id}"
   ```
   Show current details: stage, amount, contact, property, notes, last activity.

3. **Determine changes.** Based on the user's request, identify what needs updating. Common updates:
   - **Stage change**: new > contacted > viewing > offer > negotiation > closed_won / closed_lost
   - **Amount**: update the deal value
   - **Notes**: add notes about what happened
   - **Next action**: set what needs to happen next and when

4. **Confirm and update.** Show the user what will change (before > after) and get confirmation.
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" PUT "/api/v2/opportunities/{id}" \
     '{"stage":"{new_stage}","notes":"{updated_notes}"}'
   ```

5. **Create follow-up task if needed.**
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" POST "/api/v2/tasks" \
     '{"title":"{next_action}","due_date":"{date}","opportunity_id":"{id}","type":"follow_up"}'
   ```

## Stage Definitions

| Stage | Description | Typical Next Actions |
|-------|-------------|---------------------|
| new | Fresh lead/inquiry | Contact customer, qualify interest |
| contacted | Initial contact made | Schedule viewing, send properties |
| viewing | Viewing scheduled or completed | Get feedback, send more options |
| offer | Offer submitted | Wait for response, negotiate |
| negotiation | Active negotiation | Counter-offer, legal review |
| closed_won | Deal completed | Process paperwork |
| closed_lost | Deal lost | Record reason, follow up later |

## Important Notes

- Always show current state before applying changes so the user can verify the right opportunity.
- When moving to "closed_lost", prompt for a reason.
- When moving to "closed_won", confirm the final amount.
- Log meaningful notes — these become the deal history for the team.

## Reference Files

- **`references/qobrix-search-expressions.md`** — Search expression syntax reference
